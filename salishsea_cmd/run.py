#  Copyright 2013 – present by the SalishSeaCast Project Contributors
#  and The University of British Columbia
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

# SPDX-License-Identifier: Apache-2.0


"""SalishSeaCmd command plug-in for run sub-command.

Prepare for, execute, and gather the results of a run of the SalishSeaCast NEMO model.
"""
import copy
import datetime
import logging
import math
import os
import shlex
import socket
import subprocess
import tempfile
import textwrap
from pathlib import Path

import arrow
import cliff.command
import f90nml
import nemo_cmd
import yaml
from nemo_cmd.prepare import get_n_processors, get_run_desc_value, load_run_desc

from salishsea_cmd import api

log = logging.getLogger(__name__)

SYSTEM = (
    os.getenv("CC_CLUSTER")
    or os.getenv("UBC_CLUSTER")
    or os.getenv("WGSYSTEM")
    or socket.gethostname().split(".")[0]
)

SEPARATE_DEFLATE_JOBS = {
    # deflate job type: file pattern
    "grid": "*_grid_[TUVW]*.nc",
    "ptrc": "*_ptrc_T*.nc",
    "dia": "*_dia[12]_T*.nc",
}


class Run(cliff.command.Command):
    """Prepare, execute, and gather results from a SalishSeaCast NEMO model run."""

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.description = """
            Prepare, execute, and gather the results from a SalishSeaCast NEMO
            run described in DESC_FILE.
            The results files from the run are gathered in RESULTS_DIR.

            If RESULTS_DIR does not exist it will be created.
        """
        parser.add_argument(
            "desc_file",
            metavar="DESC_FILE",
            type=Path,
            help="run description YAML file",
        )
        parser.add_argument(
            "results_dir",
            metavar="RESULTS_DIR",
            type=Path,
            help="directory to store results into",
        )
        parser.add_argument(
            "--cores-per-node",
            dest="cores_per_node",
            default="",
            help="""
            Number of cores/node to use in PBS or SBATCH directives.
            Use this option to override the default cores/node that are specified in the code
            for each HPC cluster.
            """,
        )
        parser.add_argument(
            "--cpu-arch",
            dest="cpu_arch",
            default="",
            help="""
            CPU architecture to use in PBS or SBATCH directives.
            Use this to override the default CPU architecture on HPC clusters that have
            more than one type of CPU;
            e.g. sockeye (cascade is default, skylake is alternative)
            or cedar (skylake is default, broadwell is alternative).
            This option must be used in conjunction with --core-per-node.
            """,
        )
        parser.add_argument(
            "--deflate",
            dest="deflate",
            action="store_true",
            help="""
            Include "salishsea deflate" command in the bash script.
            Use this option, or the --separate-deflate option
            if you are *not* using on-the-fly deflation in XIOS-2;
            i.e. you are using more than 1 XIOS-2 process and/or
            do not have the compression_level="4" attribute set in all of
            the file_group definitions in your file_def.xml file.
            """,
        )
        parser.add_argument(
            "--max-deflate-jobs",
            dest="max_deflate_jobs",
            type=int,
            default=4,
            help="""
            Maximum number of concurrent sub-processes to
            use for netCDF deflating. Defaults to 4.""",
        )
        parser.add_argument(
            "--nocheck-initial-conditions",
            dest="nocheck_init",
            action="store_true",
            help="""
            Suppress checking of the initial conditions link.
            Useful if you are submitting a job to wait on a
            previous job""",
        )
        parser.add_argument(
            "--no-submit",
            dest="no_submit",
            action="store_true",
            help="""
            Prepare the temporary run directory, and the bash script to execute
            the NEMO run, but don't submit the run to the queue.
            This is useful during development runs when you want to hack on the
            bash script and/or use the same temporary run directory more than
            once.
            """,
        )
        parser.add_argument(
            "--separate-deflate",
            dest="separate_deflate",
            action="store_true",
            help="""
            Produce separate bash scripts to deflate the run results and submit
            them to run as serial jobs after the NEMO run finishes via the
            queue manager's job chaining feature.
            """,
        )
        parser.add_argument(
            "--waitjob",
            default="0",
            help="""
            Make this job wait for to start until the successful completion of
            WAITJOB.  WAITJOB is the queue job number of the job to wait for.
            """,
        )
        parser.add_argument(
            "-q",
            "--quiet",
            action="store_true",
            help="Don't show the run directory path or job submission message.",
        )
        return parser

    def take_action(self, parsed_args):
        """Execute the `salishsea run` sub-coomand.

        The message generated upon submission of the run to the queue
        manager is logged to the console.

        :param parsed_args: Arguments and options parsed from the command-line.
        :type parsed_args: :class:`argparse.Namespace` instance
        """
        qsub_msg = run(
            parsed_args.desc_file,
            parsed_args.results_dir,
            cores_per_node=parsed_args.cores_per_node,
            cpu_arch=parsed_args.cpu_arch,
            deflate=parsed_args.deflate,
            max_deflate_jobs=parsed_args.max_deflate_jobs,
            nocheck_init=parsed_args.nocheck_init,
            no_submit=parsed_args.no_submit,
            separate_deflate=parsed_args.separate_deflate,
            waitjob=parsed_args.waitjob,
            quiet=parsed_args.quiet,
        )
        if not parsed_args.quiet and not parsed_args.separate_deflate:
            log.info(qsub_msg)


def run(
    desc_file,
    results_dir,
    cores_per_node="",
    cpu_arch="",
    deflate=False,
    max_deflate_jobs=4,
    nocheck_init=False,
    no_submit=False,
    separate_deflate=False,
    waitjob="0",
    quiet=False,
):
    """Create and populate a temporary run directory, and a run script,
    and submit the run to the queue manager.

    The temporary run directory is created and populated via the
    :func:`SalishSeaCmd.api.prepare` API function.
    The system-specific run script is stored in :file:`SalishSeaNEMO.sh`
    in the run directory.
    That script is submitted to the queue manager in a subprocess.

    :param desc_file: File path/name of the run description YAML file.
    :type desc_file: :py:class:`pathlib.Path`

    :param results_dir: Path of the directory in which to store the run results;
                        it will be created if it does not exist.
    :type results_dir: :py:class:`pathlib.Path`

    :param str cores_per_node: Number of cores/node to use in PBS or SBATCH directives.
                               Use this option to override the default cores/node that are
                               specified in the code for each HPC cluster.

    :param str cpu_arch: CPU architecture to use in PBS or SBATCH directives.
                         Use this to override the default CPU architecture on
                         HPC clusters that have more than one type of CPU;
                         e.g. sockeye (cascade is default, skylake is alternative)
                         or cedar (skylake is default, broadwell is alternative).
                         This option must be used in conjunction with --core-per-node.

    :param boolean deflate: Include "salishsea deflate" command in the bash
                            script.

    :param int max_deflate_jobs: Maximum number of concurrent sub-processes to
                                 use for netCDF deflating.

    :param boolean nocheck_init: Suppress initial condition link check
                                 the default is to check

    :param boolean no_submit: Prepare the temporary run directory,
                              and the bash script to execute the NEMO run,
                              but don't submit the run to the queue.

    :param boolean separate_deflate: Produce separate bash scripts to deflate
                                     the run results and qsub them to run as
                                     serial jobs after the NEMO run finishes.

    :param str waitjob: Job number of the job to wait for successful completion
                        of before starting this job.

    :param boolean quiet: Don't show the run directory path message;
                          the default is to show the temporary run directory
                          path.

    :returns: Message generated by queue manager upon submission of the
              run script.
    :rtype: str
    """
    queue_job_cmd = {
        "beluga": "sbatch",
        "cedar": "sbatch",
        "delta": "qsub -q mpi",  # optimum.eoas.ubc.ca login node
        "graham": "sbatch",
        "omega": "qsub -q mpi",  # optimum.eoas.ubc.ca login node
        "orcinus": "qsub",
        "salish": "bash",
        "seawolf1": "qsub",  # orcinus.westgrid.ca login node
        "seawolf2": "qsub",  # orcinus.westgrid.ca login node
        "seawolf3": "qsub",  # orcinus.westgrid.ca login node
        "sigma": "qsub -q mpi",  # optimum.eoas.ubc.ca login node
        "sockeye": "sbatch",
    }.get(SYSTEM, "qsub")
    results_dir = nemo_cmd.resolved_path(results_dir)
    run_segments, first_seg_no = _calc_run_segments(desc_file, results_dir)
    submit_job_msg = "Submitted jobs"
    for seg_no, (run_desc, desc_file, results_dir, namelist_namrun_patch) in enumerate(
        run_segments, start=first_seg_no
    ):
        with tempfile.TemporaryDirectory() as tmp_run_desc_dir:
            if isinstance(desc_file, str):
                # Segmented run requires construction of segment YAML files & namelist files
                # in temporary storage
                segment_namrun = _write_segment_namrun_namelist(
                    run_desc, namelist_namrun_patch, Path(tmp_run_desc_dir)
                )
                restart_dir = (
                    None
                    if seg_no == first_seg_no
                    else run_segments[seg_no - first_seg_no - 1][2]
                )
                run_desc, segment_desc_file = _write_segment_desc_file(
                    run_desc,
                    desc_file,
                    restart_dir,
                    segment_namrun,
                    Path(tmp_run_desc_dir),
                )
            else:
                segment_desc_file = desc_file
            run_dir, batch_file = _build_tmp_run_dir(
                run_desc,
                segment_desc_file,
                results_dir,
                cores_per_node,
                cpu_arch,
                deflate,
                max_deflate_jobs,
                separate_deflate,
                nocheck_init,
                quiet,
            )
        results_dir.mkdir(parents=True, exist_ok=True)
        if no_submit:
            return
        msg = _submit_job(batch_file, queue_job_cmd, waitjob=waitjob)
        if separate_deflate:
            _submit_separate_deflate_jobs(batch_file, msg, queue_job_cmd)
        if len(run_segments) != 1:
            submit_job_msg = f"{submit_job_msg} {msg.split()[-1]}"
            nocheck_init = True
            waitjob = msg
        else:
            submit_job_msg = msg
    return submit_job_msg


def _calc_run_segments(desc_file, results_dir):
    run_desc = load_run_desc(desc_file)
    if "segmented run" not in run_desc:
        first_seg_no = 0
        return [(run_desc, desc_file, results_dir, {})], first_seg_no
    base_run_id = get_run_desc_value(run_desc, ("run_id",))
    start_date = arrow.get(
        get_run_desc_value(run_desc, ("segmented run", "start date"))
    )
    start_timestep = get_run_desc_value(run_desc, ("segmented run", "start time step"))
    end_date = arrow.get(get_run_desc_value(run_desc, ("segmented run", "end date")))
    days_per_segment = get_run_desc_value(
        run_desc, ("segmented run", "days per segment")
    )
    namelist_namdom = get_run_desc_value(
        run_desc, ("segmented run", "namelists", "namdom"), expand_path=True
    )
    rn_rdt = f90nml.read(namelist_namdom)["namdom"]["rn_rdt"]
    timesteps_per_day = 24 * 60 * 60 / rn_rdt
    n_segments = _calc_n_segments(run_desc)
    run_segments = []
    first_seg_no = get_run_desc_value(
        run_desc, ("segmented run", "first segment number")
    )
    for i, seg_no in enumerate(range(first_seg_no, first_seg_no + n_segments)):
        segment_run_id = f"{seg_no}_{base_run_id}"
        segment_run_desc = copy.deepcopy(run_desc)
        segment_run_desc["run_id"] = segment_run_id
        nn_it000 = int(start_timestep + i * days_per_segment * timesteps_per_day)
        date0 = min(start_date.shift(days=+i * days_per_segment), end_date)
        segment_days = min(
            days_per_segment,
            (end_date - start_date.shift(days=+i * days_per_segment)).days + 1,
        )
        nn_itend = int(nn_it000 + segment_days * timesteps_per_day - 1)
        run_segments.append(
            (
                # Run description dict for the segment
                segment_run_desc,
                # Run description YAML file name for the segment
                f"{desc_file.stem}_{seg_no}{desc_file.suffix}",
                # Results directory for the segment
                results_dir.parent / f"{results_dir.name}_{seg_no}",
                # f90nml namelist patch for the segment for the namelist containing namrum
                {
                    "namrun": {
                        "nn_it000": nn_it000,
                        "nn_itend": nn_itend,
                        "nn_date0": int(date0.format("YYYYMMDD")),
                    }
                },
            )
        )
    return run_segments, first_seg_no


def _calc_n_segments(run_desc):
    run_start_date = arrow.get(
        get_run_desc_value(run_desc, ("segmented run", "start date"))
    )
    run_end_date = arrow.get(
        get_run_desc_value(run_desc, ("segmented run", "end date"))
    )
    days_per_segment = get_run_desc_value(
        run_desc, ("segmented run", "days per segment")
    )

    n_segments_delta = (run_end_date.shift(days=+1) - run_start_date) / days_per_segment
    n_segments = n_segments_delta.days + math.ceil(
        n_segments_delta.seconds / (60 * 60 * 24)
    )
    return n_segments


def _write_segment_namrun_namelist(run_desc, namelist_namrun_patch, tmp_run_desc_dir):
    """
    :param dict run_desc: Run description dictionary.

    :param dict namelist_namrun_patch: f90nml patch for namrun namelist for the segment.

    :param tmp_run_desc_dir: Temporary directory where the namelists and run description
                             files for segments are stored.
    :type tmp_run_desc_dir: :py:class:`pathlib.Path`

    :return: File path and name of namelist section file containing namrun namelist
             for the segment.
    :rtype: :py:class:`pathlib.Path`
    """
    namelist_namrun = get_run_desc_value(
        run_desc, ("segmented run", "namelists", "namrun"), expand_path=True
    )
    f90nml.patch(
        namelist_namrun, namelist_namrun_patch, tmp_run_desc_dir / namelist_namrun.name
    )
    return tmp_run_desc_dir / namelist_namrun.name


def _write_segment_desc_file(
    run_desc, desc_file, restart_dir, segment_namrun, tmp_run_desc_dir
):
    """
    :param dict run_desc: Run description dictionary.

    :param str desc_file: Name of the run description YAML file for segment.

    :param restart_dir: Directory path in which to find the restart file(s)
                        for the segments.
                        Use :py:obj:`None` for segment 0 to avoid replacing the
                        restart directory path in the base run description YAML file.
    :type restart_dir: :py:class:`pathlib.Path` or None

    :param segment_namrun: File path and name of namelist section file containing
                           namrun for the segment.
    :type segment_namrun: :py:class:`pathlib.Path`

    :param tmp_run_desc_dir: Temporary directory where the namelists and run description
                             files for segments are stored.
    :type tmp_run_desc_dir: :py:class:`pathlib.Path`

    :return: Run description dict updated with namrun namelist section and
             restart file(s) paths,
             File path and name of temporary run description file for the segment.
    :rtype: 2-tuple
    """
    # namrun namelist for segment
    namelist_namrun = get_run_desc_value(
        run_desc, ("segmented run", "namelists", "namrun")
    )
    namelist_namrun_index = run_desc["namelists"]["namelist_cfg"].index(namelist_namrun)
    run_desc["namelists"]["namelist_cfg"][namelist_namrun_index] = os.fspath(
        segment_namrun
    )
    # restart file(s) for segment
    if restart_dir is not None:
        nml = f90nml.read(segment_namrun)
        restart_timestep = nml["namrun"]["nn_it000"] - 1
        for name, path in get_run_desc_value(run_desc, ("restart",)).items():
            path = Path(path)
            name_head = path.name.split("_")[0]
            name_tail = path.name.split("_", 2)[-1]
            restart_path = (
                restart_dir / f"{name_head}_{restart_timestep:08d}_{name_tail}"
            )
            run_desc["restart"][name] = os.fspath(restart_path)
    # walltime for segment
    segment_walltime = get_run_desc_value(
        run_desc, ("segmented run", "segment walltime")
    )
    run_desc["walltime"] = segment_walltime
    # write temporary run description file for segment
    with (tmp_run_desc_dir / desc_file).open("wt") as f:
        yaml.safe_dump(run_desc, f, default_flow_style=False)
    return run_desc, tmp_run_desc_dir / desc_file


def _build_tmp_run_dir(
    run_desc,
    desc_file,
    results_dir,
    cores_per_node,
    cpu_arch,
    deflate,
    max_deflate_jobs,
    separate_deflate,
    nocheck_init,
    quiet,
):
    run_dir = api.prepare(desc_file, nocheck_init)
    if not quiet:
        log.info(f"Created run directory {run_dir}")
    nemo_processors = get_n_processors(run_desc, run_dir)
    separate_xios_server = get_run_desc_value(
        run_desc, ("output", "separate XIOS server")
    )
    if separate_xios_server:
        xios_processors = get_run_desc_value(run_desc, ("output", "XIOS servers"))
    else:
        xios_processors = 0
    batch_script = _build_batch_script(
        run_desc,
        desc_file,
        nemo_processors,
        xios_processors,
        max_deflate_jobs,
        results_dir,
        run_dir,
        deflate,
        separate_deflate,
        cores_per_node,
        cpu_arch,
    )
    batch_file = run_dir / "SalishSeaNEMO.sh"
    with batch_file.open("wt") as f:
        f.write(batch_script)
    if separate_deflate:
        for deflate_job, pattern in SEPARATE_DEFLATE_JOBS.items():
            deflate_script = _build_deflate_script(
                run_desc, pattern, deflate_job, results_dir
            )
            script_file = run_dir / f"deflate_{deflate_job}.sh"
            with script_file.open("wt") as f:
                f.write(deflate_script)
    return run_dir, batch_file


def _submit_job(batch_file, queue_job_cmd, waitjob):
    if waitjob != "0":
        match queue_job_cmd.split(" ")[0]:
            case "qsub":
                depend_opt = "-W depend=afterok"
            case "sbatch":
                depend_opt = "-d afterok"
            case _:
                log.error(
                    f"dependent jobs are not available for systems that launch jobs with "
                    f"{queue_job_cmd}"
                )
                raise SystemExit(2)
        cmd = f"{queue_job_cmd} {depend_opt}:{waitjob} {batch_file}"
    else:
        cmd = f"{queue_job_cmd} {batch_file}"
    if queue_job_cmd == "bash":
        subprocess.Popen(shlex.split(cmd), start_new_session=True)
        return f"{cmd} started"
    submit_job_msg = subprocess.run(
        shlex.split(cmd), check=True, universal_newlines=True, stdout=subprocess.PIPE
    ).stdout
    return submit_job_msg


def _submit_separate_deflate_jobs(batch_file, submit_job_msg, queue_job_cmd):
    nemo_job_no = submit_job_msg.split()[-1]
    log.info(f"{batch_file} queued as job {nemo_job_no}")
    run_dir = batch_file.parent
    depend_opt = (
        "-W depend=afterok" if queue_job_cmd.startswith("qsub") else "-d afterok"
    )
    for deflate_job in SEPARATE_DEFLATE_JOBS:
        deflate_script = f"{run_dir}/deflate_{deflate_job}.sh"
        cmd = f"{queue_job_cmd} {depend_opt}:{nemo_job_no} {deflate_script}"
        deflate_job_msg = subprocess.run(
            shlex.split(cmd),
            check=True,
            universal_newlines=True,
            stdout=subprocess.PIPE,
        ).stdout
        deflate_job_no = deflate_job_msg.split()[-1]
        log.info(
            f"{run_dir}/{deflate_script} queued after job {nemo_job_no} "
            f"as job {deflate_job_no}"
        )


def _build_batch_script(
    run_desc,
    desc_file,
    nemo_processors,
    xios_processors,
    max_deflate_jobs,
    results_dir,
    run_dir,
    deflate,
    separate_deflate,
    cores_per_node,
    cpu_arch,
):
    """Build the Bash script that will execute the run.

    :param dict run_desc: Run description dictionary.

    :param desc_file: File path/name of the YAML run description file.
    :type desc_file: :py:class:`pathlib.Path`

    :param int nemo_processors: Number of processors that NEMO will be executed
                                on.

    :param int xios_processors: Number of processors that XIOS will be executed
                                on.

    :param int max_deflate_jobs: Maximum number of concurrent sub-processes to
                                 use for netCDF deflating.

    :param results_dir: Path of the directory in which to store the run
                        results;
                        it will be created if it does not exist.
    :type results_dir: :py:class:`pathlib.Path`

    :param run_dir: Path of the temporary run directory.
    :type run_dir: :py:class:`pathlib.Path`

    :param boolean deflate: Include "salishsea deflate" command in the bash
                            script.

    :param boolean separate_deflate: Produce separate bash scripts to deflate
                                     the run results and qsub them to run as
                                     serial jobs after the NEMO run finishes.

    :param str cores_per_node: Number of cores/node to use in PBS or SBATCH directives.

    :param str cpu_arch: CPU architecture to use in PBS or SBATCH directives.

    :returns: Bash script to execute the run.
    :rtype: str
    """
    script = "#!/bin/bash\n"
    try:
        email = get_run_desc_value(run_desc, ("email",), fatal=False)
    except KeyError:
        email = f"{os.getenv('USER')}@eoas.ubc.ca"
    if SYSTEM == "salish":
        # salish doesn't use a scheduler, so no sbatch or PBS directives in its script
        pass
    elif SYSTEM in {"beluga", "cedar", "graham", "narval", "sockeye"}:
        procs_per_node = {
            "beluga": 40 if not cores_per_node else int(cores_per_node),
            "cedar": 48 if not cores_per_node else int(cores_per_node),
            "graham": 32 if not cores_per_node else int(cores_per_node),
            "narval": 64 if not cores_per_node else int(cores_per_node),
            "sockeye": 40 if not cores_per_node else int(cores_per_node),
        }[SYSTEM]
        script = "\n".join(
            (
                script,
                f"{_sbatch_directives(run_desc, nemo_processors + xios_processors, procs_per_node, cpu_arch, email, results_dir, )}\n",
            )
        )
    else:
        try:
            procs_per_node = {
                "delta": 20 if not cores_per_node else int(cores_per_node),
                "omega": 20 if not cores_per_node else int(cores_per_node),
                "sigma": 20 if not cores_per_node else int(cores_per_node),
                "orcinus": 12 if not cores_per_node else int(cores_per_node),
                "seawolf1": 12 if not cores_per_node else int(cores_per_node),
                "seawolf2": 12 if not cores_per_node else int(cores_per_node),
                "seawolf3": 12 if not cores_per_node else int(cores_per_node),
            }[SYSTEM]
        except KeyError:
            log.error(f"unknown system: {SYSTEM}")
            raise SystemExit(2)
        script = "\n".join(
            (
                script,
                f"{_pbs_directives(run_desc, nemo_processors + xios_processors, email, results_dir, procs_per_node, cpu_arch, )}\n",
            )
        )
    redirect_stdout_stderr = True if SYSTEM == "salish" else False
    execute_section = _execute(
        nemo_processors,
        xios_processors,
        deflate,
        max_deflate_jobs,
        separate_deflate,
        redirect_stdout_stderr,
    )
    script = "\n".join(
        (
            script,
            f"{_definitions(run_desc, desc_file, run_dir, results_dir, deflate)}\n"
            f"{_modules()}\n"
            f"{execute_section}\n"
            f"{_fix_permissions()}\n"
            f"{_cleanup()}",
        )
    )
    return script


def _sbatch_directives(
    run_desc,
    n_processors,
    procs_per_node,
    cpu_arch,
    email,
    results_dir,
    mem="0",
    deflate=False,
    result_type="",
):
    """Return the SBATCH directives used to run NEMO on a cluster that uses the
    Slurm Workload Manager for job scheduling.

    The string that is returned is intended for inclusion in a bash script
    that will be submitted to the cluster queue manager via the
    :command:`sbatch` command.

    :param dict run_desc: Run description dictionary.

    :param int n_processors: Number of processors that the run will be
                             executed on; the sum of NEMO and XIOS processors.

    :param int procs_per_node: Number of processors per node.

    :param str cpu_arch: CPU architecture to use in PBS or SBATCH directives.

    :param str email: Email address to send job begin, end & abort
                      notifications to.

    :param results_dir: Directory to store results into.
    :type results_dir: :py:class:`pathlib.Path`

    :param str mem: Memory per node.

    :param boolean deflate: Return directives for a run results deflation job
                            when :py:obj:`True`.

    :param str result_type: Run result type ('grid', 'ptrc', or 'dia') for
                            deflation job.

    :returns: SBATCH directives for run script.
    :rtype: Unicode str
    """
    run_id = get_run_desc_value(run_desc, ("run_id",))
    nodes = math.ceil(n_processors / procs_per_node)
    mem = {
        "beluga": "92G",
        "cedar": "0",
        "graham": "0",
        "narval": "0",
        "sockeye": "186gb",
    }.get(SYSTEM, mem)
    if deflate:
        run_id = f"{result_type}_{run_id}_deflate"
    try:
        td = datetime.timedelta(seconds=get_run_desc_value(run_desc, ("walltime",)))
    except TypeError:
        t = datetime.datetime.strptime(
            get_run_desc_value(run_desc, ("walltime",)), "%H:%M:%S"
        ).time()
        td = datetime.timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
    walltime = _td2hms(td)
    if SYSTEM in {"cedar", "sockeye"} and cpu_arch:
        sbatch_directives = (
            f"#SBATCH --job-name={run_id}\n" f"#SBATCH --constraint={cpu_arch}\n"
        )
    else:
        sbatch_directives = f"#SBATCH --job-name={run_id}\n"
    sbatch_directives += (
        f"#SBATCH --nodes={int(nodes)}\n"
        f"#SBATCH --ntasks-per-node={procs_per_node}\n"
        f"#SBATCH --mem={mem}\n"
        f"#SBATCH --time={walltime}\n"
        f"#SBATCH --mail-user={email}\n"
        f"#SBATCH --mail-type=ALL\n"
    )
    try:
        account = get_run_desc_value(run_desc, ("account",), fatal=False)
        sbatch_directives += f"#SBATCH --account={account}\n"
    except KeyError:
        accounts = {
            "graham": "rrg-allen",
            "sockeye": "st-sallen1-1",
        }
        try:
            account = accounts[SYSTEM]
        except KeyError:
            account = "def-allen"
        sbatch_directives += f"#SBATCH --account={account}\n"
        log.info(
            f"No account found in run description YAML file, "
            f"so assuming {account}. If sbatch complains you can specify a "
            f"different account with a YAML line like account: def-allen"
        )
    stdout = f"stdout_deflate_{result_type}" if deflate else "stdout"
    stderr = f"stderr_deflate_{result_type}" if deflate else "stderr"
    sbatch_directives += (
        f"# stdout and stderr file paths/names\n"
        f"#SBATCH --output={results_dir / stdout}\n"
        f"#SBATCH --error={results_dir / stderr}\n"
    )
    return sbatch_directives


def _pbs_directives(
    run_desc,
    n_processors,
    email,
    results_dir,
    procs_per_node=0,
    cpu_arch="",
    pmem="2000mb",
    deflate=False,
    result_type="",
    stderr_stdout=True,
):
    """Return the PBS directives used to run NEMO on a cluster that uses the
    TORQUE resource manager for job scheduling.

    The string that is returned is intended for inclusion in a bash script
    that will be to the cluster queue manager via the :command:`qsub` command.

    :param dict run_desc: Run description dictionary.

    :param int n_processors: Number of processors that the run will be
                             executed on; i.e. the sum of NEMO and XIOS processors.

    :param str email: Email address to send job begin, end & abort
                      notifications to.

    :param results_dir: Directory to store results into.
    :type results_dir: :py:class:`pathlib.Path`

    :param int procs_per_node: Number of processors per node.
                               Defaults to 0 to produce
                               :kbd:`#PBS -l procs=n_processors` directive.
                               Otherwise produces
                               :kbd:`#PBS -l nodes=n:ppn=procs_per_node` directive.

    :param str cpu_arch: CPU architecture to use in PBS or SBATCH directives.

    :param str pmem: Memory per processor.

    :param boolean deflate: Return directives for a run results deflation job
                            when :py:obj:`True`.

    :param str result_type: Run result type ('grid', 'ptrc', or 'dia') for
                            deflation job.

    :param boolean stderr_stdout: When :py:obj:`False`, don't include directives
                                  to put stderr and stdout in results directory.
                                  Added for use in run scripts generated by
                                  :kbd:`run_NEMO` worker that do per-command
                                  redirection to stderr and stdout.

    :returns: PBS directives for run script.
    :rtype: Unicode str
    """
    run_id = get_run_desc_value(run_desc, ("run_id",))
    if not procs_per_node:
        procs_directive = f"#PBS -l procs={n_processors}"
    else:
        nodes = math.ceil(n_processors / procs_per_node)
        procs_directive = f"#PBS -l nodes={nodes}:ppn={procs_per_node}"
    if deflate:
        run_id = f"{result_type}_{run_id}_deflate"
    try:
        td = datetime.timedelta(seconds=get_run_desc_value(run_desc, ("walltime",)))
    except TypeError:
        t = datetime.datetime.strptime(
            get_run_desc_value(run_desc, ("walltime",)), "%H:%M:%S"
        ).time()
        td = datetime.timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
    walltime = _td2hms(td)
    pbs_directives = textwrap.dedent(
        f"""\
        #PBS -N {run_id}
        #PBS -S /bin/bash
        #PBS -l walltime={walltime}
        # email when the job [b]egins and [e]nds, or is [a]borted
        #PBS -m bea
        #PBS -M {email}
        """
    )
    if SYSTEM == "orcinus" or SYSTEM.startswith("seawolf"):
        pbs_directives += "#PBS -l partition=QDR\n"
    if SYSTEM == "salish":
        pbs_directives += textwrap.dedent(
            f"""\
            {procs_directive}
            # total memory for job
            #PBS -l mem=64gb
            """
        )
    else:
        pbs_directives += textwrap.dedent(
            f"""\
            {procs_directive}
            # memory per processor
            #PBS -l pmem={pmem}
            """
        )
    if stderr_stdout:
        stdout = f"stdout_deflate_{result_type}" if deflate else "stdout"
        stderr = f"stderr_deflate_{result_type}" if deflate else "stderr"
        pbs_directives += textwrap.dedent(
            f"""\
            # stdout and stderr file paths/names
            #PBS -o {results_dir}/{stdout}
            #PBS -e {results_dir}/{stderr}
            """
        )
    return pbs_directives


def _td2hms(timedelta):
    """Return a string that is the timedelta value formated as H:M:S
    with leading zeros on the minutes and seconds values.

    :param :py:obj:datetime.timedelta timedelta: Time interval to format.

    :returns: H:M:S string with leading zeros on the minutes and seconds
              values.
    :rtype: unicode
    """
    seconds = int(timedelta.total_seconds())
    periods = (("hour", 60 * 60), ("minute", 60), ("second", 1))
    hms = []
    for period_name, period_seconds in periods:
        period_value, seconds = divmod(seconds, period_seconds)
        hms.append(period_value)
    return f"{hms[0]}:{hms[1]:02d}:{hms[2]:02d}"


def _definitions(run_desc, run_desc_file, run_dir, results_dir, deflate):
    salishsea_cmd = {
        "beluga": Path("${HOME}", ".local", "bin", "salishsea"),
        "cedar": Path("${HOME}", ".local", "bin", "salishsea"),
        "delta": Path("${PBS_O_HOME}", "bin", "salishsea"),
        "graham": Path("${HOME}", ".local", "bin", "salishsea"),
        "narval": Path("${HOME}", ".local", "bin", "salishsea"),
        "omega": Path("${PBS_O_HOME}", "bin", "salishsea"),
        "orcinus": Path("${PBS_O_HOME}", ".local", "bin", "salishsea"),
        "sigma": Path("${PBS_O_HOME}", "bin", "salishsea"),
        "salish": Path("${HOME}", ".local", "bin", "salishsea"),
        "seawolf1": Path("${PBS_O_HOME}", ".local", "bin", "salishsea"),
        "seawolf2": Path("${PBS_O_HOME}", ".local", "bin", "salishsea"),
        "seawolf3": Path("${PBS_O_HOME}", ".local", "bin", "salishsea"),
        "sockeye": Path("${HOME}", ".local", "bin", "salishsea"),
    }.get(SYSTEM, Path("${HOME}", ".local", "bin", "salishsea"))
    defns = (
        f'RUN_ID="{get_run_desc_value(run_desc, ("run_id",))}"\n'
        f'RUN_DESC="{run_dir}/{run_desc_file.name}"\n'
        f'WORK_DIR="{run_dir}"\n'
        f'RESULTS_DIR="{results_dir}"\n'
        f'COMBINE="{salishsea_cmd} combine"\n'
    )
    if deflate:
        defns += f'DEFLATE="{salishsea_cmd} deflate"\n'
    defns += f'GATHER="{salishsea_cmd} gather"\n'
    return defns


def _modules():
    modules = {
        "beluga": textwrap.dedent(
            """\
            module load StdEnv/2020
            module load netcdf-fortran-mpi/4.6.0
            """
        ),
        "cedar": textwrap.dedent(
            """\
            module load StdEnv/2020
            module load netcdf-fortran-mpi/4.6.0
            """
        ),
        "delta": textwrap.dedent(
            """\
            module load OpenMPI/2.1.6/GCC/SYSTEM
            """
        ),
        "graham": textwrap.dedent(
            """\
            module load StdEnv/2020
            module load netcdf-fortran-mpi/4.6.0
            """
        ),
        "narval": textwrap.dedent(
            """\
            module load StdEnv/2020
            module load netcdf-fortran-mpi/4.6.0
            """
        ),
        "omega": textwrap.dedent(
            """\
            module load OpenMPI/2.1.6/GCC/SYSTEM
            """
        ),
        "orcinus": textwrap.dedent(
            """\
            module load intel
            module load intel/14.0/netcdf-4.3.3.1_mpi
            module load intel/14.0/netcdf-fortran-4.4.0_mpi
            module load intel/14.0/hdf5-1.8.15p1_mpi
            module load intel/14.0/nco-4.5.2
            module load python/3.5.0
            module load git
            """
        ),
        "salish": "",
        "seawolf1": textwrap.dedent(
            """\
            module load intel
            module load intel/14.0/netcdf-4.3.3.1_mpi
            module load intel/14.0/netcdf-fortran-4.4.0_mpi
            module load intel/14.0/hdf5-1.8.15p1_mpi
            module load intel/14.0/nco-4.5.2
            module load python/3.5.0
            module load git
            """
        ),
        "seawolf2": textwrap.dedent(
            """\
            module load intel
            module load intel/14.0/netcdf-4.3.3.1_mpi
            module load intel/14.0/netcdf-fortran-4.4.0_mpi
            module load intel/14.0/hdf5-1.8.15p1_mpi
            module load intel/14.0/nco-4.5.2
            module load python/3.5.0
            module load git
            """
        ),
        "seawolf3": textwrap.dedent(
            """\
            module load intel
            module load intel/14.0/netcdf-4.3.3.1_mpi
            module load intel/14.0/netcdf-fortran-4.4.0_mpi
            module load intel/14.0/hdf5-1.8.15p1_mpi
            module load intel/14.0/nco-4.5.2
            module load python/3.5.0
            module load git
            """
        ),
        "sigma": textwrap.dedent(
            """\
            module load OpenMPI/2.1.6/GCC/SYSTEM
            """
        ),
        "sockeye": textwrap.dedent(
            """\
            module load gcc/5.5.0
            module load openmpi/4.1.1-cuda11-3
            module load netcdf-fortran/4.5.3-hdf4-support
            """
        ),
    }.get(SYSTEM, "")
    return modules


def _execute(
    nemo_processors,
    xios_processors,
    deflate,
    max_deflate_jobs,
    separate_deflate,
    redirect_stdout_stderr,
):
    redirect = (
        ""
        if not redirect_stdout_stderr
        else " >>${RESULTS_DIR}/stdout 2>>${RESULTS_DIR}/stderr"
    )
    mpirun = {
        "beluga": "mpirun",
        "cedar": "mpirun",
        "delta": "mpiexec -hostfile $(openmpi_nodefile)",
        "graham": "mpirun",
        "narval": "mpirun",
        "omega": "mpiexec -hostfile $(openmpi_nodefile)",
        "orcinus": "mpirun",
        "salish": "/usr/bin/mpirun",
        "seawolf1": "mpirun",
        "seawolf2": "mpirun",
        "seawolf3": "mpirun",
        "sigma": "mpiexec -hostfile $(openmpi_nodefile)",
        "sockeye": "mpirun",
    }.get(SYSTEM, "mpirun")
    mpirun = {
        "beluga": f"{mpirun} -np {nemo_processors} ./nemo.exe",
        "cedar": f"{mpirun} -np {nemo_processors} ./nemo.exe",
        "delta": f"{mpirun} --bind-to core -np {nemo_processors} ./nemo.exe",
        "graham": f"{mpirun} -np {nemo_processors} ./nemo.exe",
        "narval": f"{mpirun} -np {nemo_processors} ./nemo.exe",
        "omega": f"{mpirun} --bind-to core -np {nemo_processors} ./nemo.exe",
        "orcinus": f"{mpirun} -np {nemo_processors} ./nemo.exe",
        "salish": f"{mpirun} --bind-to none -np {nemo_processors} ./nemo.exe",
        "seawolf1": f"{mpirun} -np {nemo_processors} ./nemo.exe",
        "seawolf2": f"{mpirun} -np {nemo_processors} ./nemo.exe",
        "seawolf3": f"{mpirun} -np {nemo_processors} ./nemo.exe",
        "sigma": f"{mpirun} --bind-to core -np {nemo_processors} ./nemo.exe",
        "sockeye": f"{mpirun} --bind-to core -np {nemo_processors} ./nemo.exe",
    }.get(SYSTEM, f"{mpirun} -np {nemo_processors} ./nemo.exe")
    if xios_processors:
        mpirun = {
            "beluga": f"{mpirun} : -np {xios_processors} ./xios_server.exe{redirect}",
            "cedar": f"{mpirun} : -np {xios_processors} ./xios_server.exe{redirect}",
            "delta": f"{mpirun} : --bind-to core -np {xios_processors} ./xios_server.exe{redirect}",
            "graham": f"{mpirun} : -np {xios_processors} ./xios_server.exe{redirect}",
            "narval": f"{mpirun} : -np {xios_processors} ./xios_server.exe{redirect}",
            "omega": f"{mpirun} : --bind-to core -np {xios_processors} ./xios_server.exe{redirect}",
            "orcinus": f"{mpirun} : -np {xios_processors} ./xios_server.exe{redirect}",
            "salish": f"{mpirun} : --bind-to none -np {xios_processors} ./xios_server.exe{redirect}",
            "seawolf1": f"{mpirun} : -np {xios_processors} ./xios_server.exe{redirect}",
            "seawolf2": f"{mpirun} : -np {xios_processors} ./xios_server.exe{redirect}",
            "seawolf3": f"{mpirun} : -np {xios_processors} ./xios_server.exe{redirect}",
            "sigma": f"{mpirun} : --bind-to core -np {xios_processors} ./xios_server.exe{redirect}",
            "sockeye": f"{mpirun} : --bind-to core -np {xios_processors} ./xios_server.exe{redirect}",
        }.get(
            SYSTEM,
            f"{mpirun} : -np {xios_processors} ./xios_server.exe{redirect}",
        )
    redirect = "" if not redirect_stdout_stderr else " >>${RESULTS_DIR}/stdout"
    script = textwrap.dedent(
        f"""\
        mkdir -p ${{RESULTS_DIR}}
        cd ${{WORK_DIR}}
        echo "working dir: $(pwd)"{redirect}

        echo "Starting run at $(date)"{redirect}
        {mpirun}
        MPIRUN_EXIT_CODE=$?
        echo "Ended run at $(date)"{redirect}

        echo "Results combining started at $(date)"{redirect}
        """
    )
    if SYSTEM in {"delta", "omega", "sigma"}:
        # Load GCC-8.3 modules just before combining because rebuild_nemo on optimum
        # is built with them, in contrast to XIOS and NEMO which are built with
        # the system GCC-4.4.7
        script += textwrap.dedent(
            """\
            module load GCC/8.3
            module load OpenMPI/2.1.6/GCC/8.3
            module load ZLIB/1.2/11
            module load use.paustin
            module load HDF5/1.08/20
            module load NETCDF/4.6/1
            """
        )
    script += textwrap.dedent(
        f"""\
        ${{COMBINE}} ${{RUN_DESC}} --debug{redirect}
        echo "Results combining ended at $(date)"{redirect}
        """
    )
    if deflate and not separate_deflate:
        script += textwrap.dedent(
            f"""\

            echo "Results deflation started at $(date)"{redirect}
            """
        )
        if SYSTEM in {"beluga", "cedar", "graham", "narval"}:
            # Load the nco module just before deflation because it replaces
            # the netcdf-mpi and netcdf-fortran-mpi modules with their non-mpi
            # variants
            script += textwrap.dedent(
                """\
                module load nco/4.9.5
                """
            )
        script += textwrap.dedent(
            f"""\
            ${{DEFLATE}} *_ptrc_T*.nc *_prod_T*.nc *_carp_T*.nc *_grid_[TUVW]*.nc \\
              *_turb_T*.nc *_dia[12n]_T*.nc FVCOM*.nc Slab_[UV]*.nc *_mtrc_T*.nc \\
              --jobs {max_deflate_jobs} --debug{redirect}
            echo "Results deflation ended at $(date)"{redirect}
            """
        )
    script += textwrap.dedent(
        f"""\

        echo "Results gathering started at $(date)"{redirect}
        ${{GATHER}} ${{RESULTS_DIR}} --debug{redirect}
        echo "Results gathering ended at $(date)"{redirect}
        """
    )
    return script


def _fix_permissions():
    script = textwrap.dedent(
        """\
        chmod go+rx ${RESULTS_DIR}
        chmod g+rw ${RESULTS_DIR}/*
        chmod o+r ${RESULTS_DIR}/*
        """
    )
    return script


def _cleanup():
    script = textwrap.dedent(
        """\
        echo "Deleting run directory" >>${RESULTS_DIR}/stdout
        rmdir $(pwd)
        echo "Finished at $(date)" >>${RESULTS_DIR}/stdout
        exit ${MPIRUN_EXIT_CODE}
        """
    )
    return script


def _build_deflate_script(run_desc, pattern, result_type, results_dir):
    script = "#!/bin/bash\n"
    try:
        email = get_run_desc_value(run_desc, ("email",))
    except KeyError:
        email = f"{os.getenv('USER')}@eos.ubc.ca"
    pmem = "2500mb" if result_type == "ptrc" else "2000mb"
    script = "\n".join(
        (
            script,
            f"{_pbs_directives(run_desc, 1, email, results_dir, pmem=pmem, deflate=True, result_type=result_type)}\n",
        )
    )
    script += (
        f'RESULTS_DIR="{results_dir}"\n'
        f'DEFLATE="${{PBS_O_HOME}}/.local/bin/salishsea deflate"\n'
        f"\n"
        f"{_modules()}\n"
        f"cd ${{RESULTS_DIR}}\n"
        f'echo "Results deflation started at $(date)"\n'
        f"${{DEFLATE}} {pattern} --jobs 1 --debug\n"
        f"DEFLATE_EXIT_CODE=$?\n"
        f'echo "Results deflation ended at $(date)"\n'
        f"\n"
        f"chmod g+rw ${{RESULTS_DIR}}/*\n"
        f"chmod o+r ${{RESULTS_DIR}}/*\n"
        f"\n"
        f"exit ${{DEFLATE_EXIT_CODE}}\n"
    )
    return script
