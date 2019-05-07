# Copyright 2013-2019 The Salish Sea MEOPAR Contributors
# and The University of British Columbia

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""SalishSeaCmd command plug-in for run sub-command.

Prepare for, execute, and gather the results of a run of the Salish Sea NEMO model.
"""
import copy
import datetime
import logging
import math
import os
from pathlib import Path
import shlex
import socket
import subprocess
import tempfile

import arrow
import cliff.command
import f90nml
import nemo_cmd
from nemo_cmd.prepare import get_n_processors, get_run_desc_value, load_run_desc
import yaml

from salishsea_cmd import api

log = logging.getLogger(__name__)

SYSTEM = (
    os.getenv("WGSYSTEM")
    or os.getenv("CC_CLUSTER")
    or socket.gethostname().split(".")[0]
)

SEPARATE_DEFLATE_JOBS = {
    # deflate job type: file pattern
    "grid": "*_grid_[TUVW]*.nc",
    "ptrc": "*_ptrc_T*.nc",
    "dia": "*_dia[12]_T*.nc",
}


class Run(cliff.command.Command):
    """Prepare, execute, and gather results from a Salish Sea NEMO model run.
    """

    def get_parser(self, prog_name):
        parser = super(Run, self).get_parser(prog_name)
        parser.description = """
            Prepare, execute, and gather the results from a Salish Sea NEMO-3.6
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
            "--cedar-broadwell",
            dest="cedar_broadwell",
            action="store_true",
            help="""
            Use broadwell (32 cores/node) nodes on cedar instead of the 
            default skylake (48 cores/node) nodes.
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
            type=int,
            default=0,
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
            cedar_broadwell=parsed_args.cedar_broadwell,
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
    cedar_broadwell=False,
    deflate=False,
    max_deflate_jobs=4,
    nocheck_init=False,
    no_submit=False,
    separate_deflate=False,
    waitjob=0,
    quiet=False,
):
    """Create and populate a temporary run directory, and a run script,
    and submit the run to the queue manager.

    The temporary run directory is created and populated via the
    :func:`SalishSeaCmd.api.prepare` API function.
    The system-specific run script is stored in :file:`SalishSeaNEMO.sh`
    in the run directory.
    That script is submitted to the queue manager in a subprocess.

    :param desc_file: File path/name of the YAML run description file.
    :type desc_file: :py:class:`pathlib.Path`

    :param results_dir: Path of the directory in which to store the run results;
                        it will be created if it does not exist.
    :type results_dir: :py:class:`pathlib.Path`

    :param boolean cedar_broadwell: Use broadwell (32 cores/node) on cedar.

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

    :param int waitjob: Job number of the job to wait for successful completion
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
        "orcinus": "qsub",
        "salish": "qsub",
        "sigma": "qsub -q mpi",  # optimum.eoas.ubc.ca login node
    }.get(SYSTEM, "qsub")
    results_dir = nemo_cmd.resolved_path(results_dir)
    run_segments = _calc_run_segments(desc_file, results_dir)
    submit_job_msg = "Submitted jobs"
    for run_desc, desc_file, results_dir, namelist_namrun_patch in run_segments:
        with tempfile.TemporaryDirectory() as tmp_run_desc_dir:
            if isinstance(desc_file, str):
                # Segmented run requires construction of segment YAML files & namelist files
                # in temporary storage
                segment_namrun = _write_segment_namrun_namelist(
                    run_desc, namelist_namrun_patch, Path(tmp_run_desc_dir)
                )
                run_desc, segment_desc_file = _write_segment_desc_file(
                    run_desc, segment_namrun, desc_file, Path(tmp_run_desc_dir)
                )
            else:
                segment_desc_file = desc_file
            run_dir, batch_file = _build_tmp_run_dir(
                run_desc,
                segment_desc_file,
                results_dir,
                cedar_broadwell,
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
        return [(run_desc, desc_file, results_dir, {})]
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
    for i in range(n_segments):
        segment_run_id = "{i}_{base_run_id}".format(i=i, base_run_id=base_run_id)
        segment_run_desc = copy.deepcopy(run_desc)
        segment_run_desc["run_id"] = segment_run_id
        nn_it000 = int(start_timestep + i * days_per_segment * timesteps_per_day)
        date0 = min(start_date.shift(days=+i * days_per_segment), end_date)
        segment_days = min(
            days_per_segment,
            (end_date - start_date.shift(days=+i * days_per_segment)).days,
        )
        nn_itend = int(nn_it000 + segment_days * timesteps_per_day - 1)
        run_segments.append(
            (
                # Run description dict for the segment
                segment_run_desc,
                # Run description YAML file name for the segment
                "{file_stem}_{i}{suffix}".format(
                    file_stem=desc_file.stem, i=i, suffix=desc_file.suffix
                ),
                # Results directory for the segment
                results_dir.parent
                / "{dir_name}_{i}".format(dir_name=results_dir.name, i=i),
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
    return run_segments


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


def _write_segment_desc_file(run_desc, segment_namrun, desc_file, tmp_run_desc_dir):
    """
    :param dict run_desc: Run description dictionary.

    :param segment_namrun: File path and name of namelist section file containing
                           namrun for the segment.
    :type segment_namrun: :py:class:`pathlib.Path`

    :paramstr  desc_file: Name of the YAML run description file for segment.

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
    nml = f90nml.read(segment_namrun)
    restart_timestep = nml["namrun"]["nn_it000"] - 1
    restart_date = arrow.get(str(nml["namrun"]["nn_date0"] - 1), "YYYYMMDD")
    for name, path in get_run_desc_value(run_desc, ("restart",)).items():
        path = Path(path)
        name_tail = path.name.split("_", 2)[-1]
        restart_path = path.parent.parent / restart_date.format("DDMMMYY").lower()
        restart_path = restart_path / f"SalishSea_{restart_timestep:08d}_{name_tail}"
        run_desc["restart"][name] = os.fspath(restart_path)
    # write temporary run description file for segment
    with (tmp_run_desc_dir / desc_file).open("wt") as f:
        yaml.safe_dump(run_desc, f, default_flow_style=False)
    return run_desc, tmp_run_desc_dir / desc_file


def _build_tmp_run_dir(
    run_desc,
    desc_file,
    results_dir,
    cedar_broadwell,
    deflate,
    max_deflate_jobs,
    separate_deflate,
    nocheck_init,
    quiet,
):
    run_dir = api.prepare(desc_file, nocheck_init)
    if not quiet:
        log.info("Created run directory {}".format(run_dir))
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
        cedar_broadwell,
    )
    batch_file = run_dir / "SalishSeaNEMO.sh"
    with batch_file.open("wt") as f:
        f.write(batch_script)
    if separate_deflate:
        for deflate_job, pattern in SEPARATE_DEFLATE_JOBS.items():
            deflate_script = _build_deflate_script(
                run_desc, pattern, deflate_job, results_dir
            )
            script_file = run_dir / "deflate_{}.sh".format(deflate_job)
            with script_file.open("wt") as f:
                f.write(deflate_script)
    return run_dir, batch_file


def _submit_job(batch_file, queue_job_cmd, waitjob):
    if waitjob:
        depend_opt = (
            "-W depend=afterok" if queue_job_cmd.startswith("qsub") else "-d afterok"
        )
        cmd = "{submit_cmd} {depend_opt}:{waitjob} {batch_file}".format(
            submit_cmd=queue_job_cmd,
            depend_opt=depend_opt,
            batch_file=batch_file,
            waitjob=waitjob,
        )
    else:
        cmd = "{submit_cmd} {batch_file}".format(
            submit_cmd=queue_job_cmd, batch_file=batch_file
        )
    submit_job_msg = subprocess.run(
        shlex.split(cmd), check=True, universal_newlines=True, stdout=subprocess.PIPE
    ).stdout
    return submit_job_msg


def _submit_separate_deflate_jobs(batch_file, submit_job_msg, queue_job_cmd):
    nemo_job_no = submit_job_msg.split()[-1]
    log.info(
        "{batch_file} queued as job {nemo_job_no}".format(
            batch_file=batch_file, nemo_job_no=nemo_job_no
        )
    )
    run_dir = batch_file.parent
    depend_opt = (
        "-W depend=afterok" if queue_job_cmd.startswith("qsub") else "-d afterok"
    )
    for deflate_job in SEPARATE_DEFLATE_JOBS:
        deflate_script = "{run_dir}/deflate_{deflate_job}.sh".format(
            run_dir=run_dir, deflate_job=deflate_job
        )
        cmd = "{submit_cmd} {depend_opt}:{nemo_job_no} {deflate_script}".format(
            submit_cmd=queue_job_cmd,
            depend_opt=depend_opt,
            nemo_job_no=nemo_job_no,
            deflate_script=deflate_script,
        )
        deflate_job_msg = subprocess.run(
            shlex.split(cmd),
            check=True,
            universal_newlines=True,
            stdout=subprocess.PIPE,
        ).stdout
        deflate_job_no = deflate_job_msg.split()[-1]
        log.info(
            "{run_dir}/{deflate_script} queued after job {nemo_job_no} as job "
            "{deflate_job_no}".format(
                run_dir=run_dir,
                deflate_script=deflate_script,
                nemo_job_no=nemo_job_no,
                deflate_job_no=deflate_job_no,
            )
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
    cedar_broadwell,
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

    :param boolean cedar_broadwell: Use broadwell (32 cores/node) nodes on
                                    cedar.

    :returns: Bash script to execute the run.
    :rtype: str
    """
    script = "#!/bin/bash\n"
    try:
        email = get_run_desc_value(run_desc, ("email",), fatal=False)
    except KeyError:
        email = "{user}@eoas.ubc.ca".format(user=os.getenv("USER"))
    if SYSTEM in {"beluga", "cedar", "graham"}:
        script = "\n".join(
            (
                script,
                "{sbatch_directives}\n".format(
                    sbatch_directives=_sbatch_directives(
                        run_desc,
                        nemo_processors + xios_processors,
                        cedar_broadwell,
                        email,
                        results_dir,
                    )
                ),
            )
        )
    else:
        procs_per_node = 20 if SYSTEM in {"delta", "sigma"} else 0
        script = "\n".join(
            (
                script,
                "{pbs_directives}\n".format(
                    pbs_directives=_pbs_directives(
                        run_desc,
                        nemo_processors + xios_processors,
                        email,
                        results_dir,
                        procs_per_node,
                    )
                ),
            )
        )
    if SYSTEM == "orcinus":
        script += "#PBS -l partition=QDR\n"
    script = "\n".join(
        (
            script,
            "{defns}\n"
            "{modules}\n"
            "{execute}\n"
            "{fix_permissions}\n"
            "{cleanup}".format(
                defns=_definitions(run_desc, desc_file, run_dir, results_dir, deflate),
                modules=_modules(),
                execute=_execute(
                    nemo_processors,
                    xios_processors,
                    deflate,
                    max_deflate_jobs,
                    separate_deflate,
                ),
                fix_permissions=_fix_permissions(),
                cleanup=_cleanup(),
            ),
        )
    )
    return script


def _sbatch_directives(
    run_desc,
    n_processors,
    cedar_broadwell,
    email,
    results_dir,
    mem="125G",
    deflate=False,
    result_type="",
):
    """Return the SBATCH directives used to run NEMO on a cluster that uses the
    Slurm Workload Manager for job scheduling.

    The string that is returned is intended for inclusion in a bash script
    that will submitted be to the cluster queue manager via the
    :command:`sbatch` command.

    :param dict run_desc: Run description dictionary.

    :param int n_processors: Number of processors that the run will be
                             executed on; the sum of NEMO and XIOS processors.

    :param boolean cedar_broadwell: Use broadwell (32 cores/node) nodes on
                                    cedar.

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
    constraint = "broadwell" if SYSTEM == "cedar" and cedar_broadwell else "skylake"
    try:
        processors_per_node = {"beluga": 40, "cedar": 48, "graham": 32}[SYSTEM]
    except KeyError:
        log.error("unknown system: {system}".format(system=SYSTEM))
        raise SystemExit(2)
    if SYSTEM == "cedar" and cedar_broadwell:
        processors_per_node = 32
    nodes = math.ceil(n_processors / processors_per_node)
    mem = {"beluga": "92G", "cedar": "0", "graham": "125G"}.get(SYSTEM, mem)
    if deflate:
        run_id = "{result_type}_{run_id}_deflate".format(
            run_id=run_id, result_type=result_type
        )
    try:
        td = datetime.timedelta(seconds=get_run_desc_value(run_desc, ("walltime",)))
    except TypeError:
        t = datetime.datetime.strptime(
            get_run_desc_value(run_desc, ("walltime",)), "%H:%M:%S"
        ).time()
        td = datetime.timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
    walltime = _td2hms(td)
    if SYSTEM == "cedar":
        sbatch_directives = (
            "#SBATCH --job-name={run_id}\n" "#SBATCH --constraint={constraint}\n"
        ).format(run_id=run_id, constraint=constraint)
    else:
        sbatch_directives = "#SBATCH --job-name={run_id}\n".format(run_id=run_id)
    sbatch_directives += (
        "#SBATCH --nodes={nodes}\n"
        "#SBATCH --ntasks-per-node={processors_per_node}\n"
        "#SBATCH --mem={mem}\n"
        "#SBATCH --time={walltime}\n"
        "#SBATCH --mail-user={email}\n"
        "#SBATCH --mail-type=ALL\n"
    ).format(
        nodes=int(nodes),
        processors_per_node=processors_per_node,
        mem=mem,
        walltime=walltime,
        email=email,
    )
    try:
        account = get_run_desc_value(run_desc, ("account",), fatal=False)
        sbatch_directives += "#SBATCH --account={account}\n".format(account=account)
    except KeyError:
        account = "rrg-allen" if SYSTEM in {"beluga", "cedar"} else "def-allen"
        sbatch_directives += "#SBATCH --account={account}\n".format(account=account)
        log.info(
            (
                "No account found in run description YAML file, "
                "so assuming {account}. If sbatch complains you can specify a "
                "different account with a YAML line like account: def-allen"
            ).format(account=account)
        )
    stdout = (
        "stdout_deflate_{result_type}".format(result_type=result_type)
        if deflate
        else "stdout"
    )
    stderr = (
        "stderr_deflate_{result_type}".format(result_type=result_type)
        if deflate
        else "stderr"
    )
    sbatch_directives += (
        "# stdout and stderr file paths/names\n"
        "#SBATCH --output={stdout}\n"
        "#SBATCH --error={stderr}\n"
    ).format(stdout=results_dir / stdout, stderr=results_dir / stderr)
    return sbatch_directives


def _pbs_directives(
    run_desc,
    n_processors,
    email,
    results_dir,
    procs_per_node=0,
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
        procs_directive = "#PBS -l procs={procs}".format(procs=n_processors)
    else:
        nodes = math.ceil(n_processors / procs_per_node)
        procs_directive = "#PBS -l nodes={nodes}:ppn={procs_per_node}".format(
            nodes=nodes, procs_per_node=procs_per_node
        )
    if deflate:
        run_id = "{result_type}_{run_id}_deflate".format(
            run_id=run_id, result_type=result_type
        )
    try:
        td = datetime.timedelta(seconds=get_run_desc_value(run_desc, ("walltime",)))
    except TypeError:
        t = datetime.datetime.strptime(
            get_run_desc_value(run_desc, ("walltime",)), "%H:%M:%S"
        ).time()
        td = datetime.timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
    walltime = _td2hms(td)
    pbs_directives = (
        "#PBS -N {run_id}\n"
        "#PBS -S /bin/bash\n"
        "{procs_directive}\n"
        "# memory per processor\n"
        "#PBS -l pmem={pmem}\n"
        "#PBS -l walltime={walltime}\n"
        "# email when the job [b]egins and [e]nds, or is [a]borted\n"
        "#PBS -m bea\n"
        "#PBS -M {email}\n"
    ).format(
        run_id=run_id,
        procs_directive=procs_directive,
        pmem=pmem,
        walltime=walltime,
        email=email,
    )
    if stderr_stdout:
        stdout = (
            "stdout_deflate_{result_type}".format(result_type=result_type)
            if deflate
            else "stdout"
        )
        stderr = (
            "stderr_deflate_{result_type}".format(result_type=result_type)
            if deflate
            else "stderr"
        )
        pbs_directives += (
            "# stdout and stderr file paths/names\n"
            "#PBS -o {results_dir}/{stdout}\n"
            "#PBS -e {results_dir}/{stderr}\n"
        ).format(results_dir=results_dir, stdout=stdout, stderr=stderr)
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
    return "{0[0]}:{0[1]:02d}:{0[2]:02d}".format(hms)


def _definitions(run_desc, run_desc_file, run_dir, results_dir, deflate):
    salishsea_cmd = {
        "cedar": Path("${HOME}", ".local", "bin", "salishsea"),
        "delta": Path("${PBS_O_HOME}", "bin", "salishsea"),
        "graham": Path("${HOME}", ".local", "bin", "salishsea"),
        "orcinus": Path("${PBS_O_HOME}", ".local", "bin", "salishsea"),
        "sigma": Path("${PBS_O_HOME}", "bin", "salishsea"),
        "salish": Path("${HOME}", ".local", "bin", "salishsea"),
    }.get(SYSTEM, Path("${HOME}", ".local", "bin", "salishsea"))
    defns = (
        'RUN_ID="{run_id}"\n'
        'RUN_DESC="{run_desc_file}"\n'
        'WORK_DIR="{run_dir}"\n'
        'RESULTS_DIR="{results_dir}"\n'
        'COMBINE="{salishsea_cmd} combine"\n'
    ).format(
        run_id=get_run_desc_value(run_desc, ("run_id",)),
        run_desc_file=run_desc_file,
        run_dir=run_dir,
        results_dir=results_dir,
        salishsea_cmd=salishsea_cmd,
    )
    if deflate:
        defns += 'DEFLATE="{salishsea_cmd} deflate"\n'.format(
            salishsea_cmd=salishsea_cmd
        )
    defns += 'GATHER="{salishsea_cmd} gather"\n'.format(salishsea_cmd=salishsea_cmd)
    return defns


def _modules():
    modules = {
        "beluga": (
            "module load netcdf-fortran-mpi/4.4.4\n" "module load python/3.7.0\n"
        ),
        "cedar": (
            "module load netcdf-fortran-mpi/4.4.4\n" "module load python/3.7.0\n"
        ),
        "delta": "module load Miniconda/3\n" "module load OpenMPI/4.0.0/GCC/SYSTEM\n",
        "graham": (
            "module load netcdf-fortran-mpi/4.4.4\n" "module load python/3.7.0\n"
        ),
        "orcinus": (
            "module load intel\n"
            "module load intel/14.0/netcdf-4.3.3.1_mpi\n"
            "module load intel/14.0/netcdf-fortran-4.4.0_mpi\n"
            "module load intel/14.0/hdf5-1.8.15p1_mpi\n"
            "module load intel/14.0/nco-4.5.2\n"
            "module load python\n"
        ),
        "salish": "",
        "sigma": "module load Miniconda/3\n" "module load OpenMPI/4.0.0/GCC/SYSTEM\n",
    }.get(SYSTEM, "")
    return modules


def _execute(
    nemo_processors, xios_processors, deflate, max_deflate_jobs, separate_deflate
):
    mpirun = {
        "cedar": "mpirun",
        "delta": "mpiexec -hostfile $(openmpi_nodefile)",
        "graham": "mpirun",
        "orcinus": "mpirun",
        "salish": "/usr/bin/mpirun",
        "sigma": "mpiexec -hostfile $(openmpi_nodefile)",
    }.get(SYSTEM, "mpirun")
    mpirun = {
        "cedar": "{mpirun} -np {np} ./nemo.exe".format(
            mpirun=mpirun, np=nemo_processors
        ),
        "delta": "{mpirun} -bind-to core -np {np} ./nemo.exe".format(
            mpirun=mpirun, np=nemo_processors
        ),
        "graham": "{mpirun} -np {np} ./nemo.exe".format(
            mpirun=mpirun, np=nemo_processors
        ),
        "orcinus": "{mpirun} -np {np} ./nemo.exe".format(
            mpirun=mpirun, np=nemo_processors
        ),
        "salish": "{mpirun} -np {np} ./nemo.exe".format(
            mpirun=mpirun, np=nemo_processors
        ),
        "sigma": "{mpirun} -bind-to core -np {np} ./nemo.exe".format(
            mpirun=mpirun, np=nemo_processors
        ),
    }.get(
        SYSTEM, "{mpirun} -np {np} ./nemo.exe".format(mpirun=mpirun, np=nemo_processors)
    )
    if xios_processors:
        mpirun = {
            "cedar": "{mpirun} : -np {np} ./xios_server.exe".format(
                mpirun=mpirun, np=xios_processors
            ),
            "delta": "{mpirun} : -bind-to core -np {np} ./xios_server.exe".format(
                mpirun=mpirun, np=xios_processors
            ),
            "graham": "{mpirun} : -np {np} ./xios_server.exe".format(
                mpirun=mpirun, np=xios_processors
            ),
            "orcinus": "{mpirun} : -np {np} ./xios_server.exe".format(
                mpirun=mpirun, np=xios_processors
            ),
            "salish": "{mpirun} : -np {np} ./xios_server.exe".format(
                mpirun=mpirun, np=xios_processors
            ),
            "sigma": "{mpirun} : -bind-to core -np {np} ./xios_server.exe".format(
                mpirun=mpirun, np=xios_processors
            ),
        }.get(
            SYSTEM,
            "{mpirun} : -np {np} ./xios_server.exe".format(
                mpirun=mpirun, np=xios_processors
            ),
        )
    script = (
        "mkdir -p ${RESULTS_DIR}\n"
        "cd ${WORK_DIR}\n"
        'echo "working dir: $(pwd)"\n'
        "\n"
        'echo "Starting run at $(date)"\n'
    )
    script += "{mpirun}\n".format(mpirun=mpirun)
    script += (
        "MPIRUN_EXIT_CODE=$?\n"
        'echo "Ended run at $(date)"\n'
        "\n"
        'echo "Results combining started at $(date)"\n'
        "${COMBINE} ${RUN_DESC} --debug\n"
        'echo "Results combining ended at $(date)"\n'
    )
    if deflate and not separate_deflate:
        if SYSTEM in {"beluga", "cedar", "graham"}:
            # Load the nco module just before deflation because it replaces
            # the netcdf-mpi and netcdf-fortran-mpi modules with their non-mpi
            # variants
            script += (
                "\n"
                'echo "Results deflation started at $(date)"\n'
                "module load nco/4.6.6\n"
                "${{DEFLATE}} *_ptrc_T*.nc *_prod_T*.nc *_carp_T*.nc *_grid_[TUVW]*.nc \\"
                "  *_turb_T*.nc *_dia[12n]_T*.nc FVCOM*.nc Slab_[UV]*.nc *_mtrc_T*.nc \\"
                "  --jobs {max_deflate_jobs} --debug\n"
                'echo "Results deflation ended at $(date)"\n'
            ).format(max_deflate_jobs=max_deflate_jobs)
        else:
            script += (
                "\n"
                'echo "Results deflation started at $(date)"\n'
                "${{DEFLATE}} *_ptrc_T*.nc *_prod_T*.nc *_carp_T*.nc *_grid_[TUVW]*.nc \\"
                "  *_turb_T*.nc *_dia[12n]_T*.nc FVCOM*.nc Slab_[UV]*.nc *_mtrc_T*.nc \\"
                "  --jobs {max_deflate_jobs} --debug\n"
                'echo "Results deflation ended at $(date)"\n'
            ).format(max_deflate_jobs=max_deflate_jobs)
    script += (
        "\n"
        'echo "Results gathering started at $(date)"\n'
        "${GATHER} ${RESULTS_DIR} --debug\n"
        'echo "Results gathering ended at $(date)"\n'
    )
    return script


def _fix_permissions():
    script = (
        "chmod go+rx ${RESULTS_DIR}\n"
        "chmod g+rw ${RESULTS_DIR}/*\n"
        "chmod o+r ${RESULTS_DIR}/*\n"
    )
    return script


def _cleanup():
    script = (
        'echo "Deleting run directory" >>${RESULTS_DIR}/stdout\n'
        "rmdir $(pwd)\n"
        'echo "Finished at $(date)" >>${RESULTS_DIR}/stdout\n'
        "exit ${MPIRUN_EXIT_CODE}\n"
    )
    return script


def _build_deflate_script(run_desc, pattern, result_type, results_dir):
    script = "#!/bin/bash\n"
    try:
        email = get_run_desc_value(run_desc, ("email",))
    except KeyError:
        email = "{user}@eos.ubc.ca".format(user=os.getenv("USER"))
    pmem = "2500mb" if result_type == "ptrc" else "2000mb"
    script = "\n".join(
        (
            script,
            "{pbs_directives}\n".format(
                pbs_directives=_pbs_directives(
                    run_desc,
                    1,
                    email,
                    results_dir,
                    pmem=pmem,
                    deflate=True,
                    result_type=result_type,
                )
            ),
        )
    )
    script += (
        'RESULTS_DIR="{results_dir}"\n'
        'DEFLATE="${{PBS_O_HOME}}/.local/bin/salishsea deflate"\n'
        "\n"
        "{modules}\n"
        "cd ${{RESULTS_DIR}}\n"
        'echo "Results deflation started at $(date)"\n'
        "${{DEFLATE}} {pattern} --jobs 1 --debug\n"
        "DEFLATE_EXIT_CODE=$?\n"
        'echo "Results deflation ended at $(date)"\n'
        "\n"
        "chmod g+rw ${{RESULTS_DIR}}/*\n"
        "chmod o+r ${{RESULTS_DIR}}/*\n"
        "\n"
        "exit ${{DEFLATE_EXIT_CODE}}\n"
    ).format(results_dir=results_dir, modules=_modules(), pattern=pattern)
    return script
