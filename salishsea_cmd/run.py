# Copyright 2013-2017 The Salish Sea MEOPAR Contributors
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

Prepare for, execute, and gather the results of a run of the
Salish Sea NEMO model.
"""
from __future__ import division

import datetime
import logging
import math
import os
try:
    from pathlib import Path
except ImportError:
    # Python 2.7
    from pathlib2 import Path
import shlex
import socket
import subprocess

import cliff.command
from nemo_cmd.fspath import fspath
from nemo_cmd.prepare import get_run_desc_value

from salishsea_cmd import api, lib

log = logging.getLogger(__name__)


class Run(cliff.command.Command):
    """Prepare, execute, and gather results from a Salish Sea NEMO model run.
    """

    def get_parser(self, prog_name):
        parser = super(Run, self).get_parser(prog_name)
        parser.description = '''
            Prepare, execute, and gather the results from a Salish Sea NEMO-3.6
            run described in DESC_FILE.
            The results files from the run are gathered in RESULTS_DIR.

            If RESULTS_DIR does not exist it will be created.
        '''
        parser.add_argument(
            'desc_file',
            metavar='DESC_FILE',
            type=Path,
            help='run description YAML file'
        )
        parser.add_argument(
            'results_dir',
            metavar='RESULTS_DIR',
            help='directory to store results into'
        )
        parser.add_argument(
            '--max-deflate-jobs',
            dest='max_deflate_jobs',
            type=int,
            default=4,
            help='''
            Maximum number of concurrent sub-processes to
            use for netCDF deflating. Defaults to 4.'''
        )
        parser.add_argument(
            '--nemo3.4',
            dest='nemo34',
            action='store_true',
            help='''
            Do a NEMO-3.4 run;
            the default is to do a NEMO-3.6 run'''
        )
        parser.add_argument(
            '--nocheck-initial-conditions',
            dest='nocheck_init',
            action='store_true',
            help='''
            Suppress checking of the initial conditions link.
            Useful if you are submitting a job to wait on a
            previous job'''
        )
        parser.add_argument(
            '--no-submit',
            dest='no_submit',
            action='store_true',
            help='''
            Prepare the temporary run directory, and the bash script to execute
            the NEMO run, but don't submit the run to the queue.
            This is useful during development runs when you want to hack on the
            bash script and/or use the same temporary run directory more than
            once.
            '''
        )
        parser.add_argument(
            '--separate-deflate',
            dest='separate_deflate',
            action='store_true',
            help='''
            Produce separate bash scripts to deflate the run results and qsub
            them to run as serial jobs after the NEMO run finishes via the
            `qsub -W depend=afterok` feature.
            '''
        )
        parser.add_argument(
            '--waitjob',
            type=int,
            default=0,
            help='''
            Use -W waitjob in call to qsub, to make current job
            wait for on waitjob.  WAITJOB is the queue job number.
            '''
        )
        parser.add_argument(
            '-q',
            '--quiet',
            action='store_true',
            help="Don't show the run directory path or job submission message."
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
            parsed_args.desc_file, parsed_args.results_dir,
            parsed_args.max_deflate_jobs, parsed_args.nemo34,
            parsed_args.nocheck_init, parsed_args.no_submit,
            parsed_args.separate_deflate, parsed_args.waitjob,
            parsed_args.quiet
        )
        if not parsed_args.quiet and not parsed_args.separate_deflate:
            log.info(qsub_msg)


def run(
    desc_file,
    results_dir,
    max_deflate_jobs=4,
    nemo34=False,
    nocheck_init=False,
    no_submit=False,
    separate_deflate=False,
    waitjob=0,
    quiet=False
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

    :param str results_dir: Path of the directory in which to store the run
                            results;
                            it will be created if it does not exist.

    :param int max_deflate_jobs: Maximum number of concurrent sub-processes to
                                 use for netCDF deflating.

    :param boolean nemo34: Prepare a NEMO-3.4 run;
                           the default is to prepare a NEMO-3.6 run

    :param boolean nocheck_init: Suppress initial condition link check
                                 the default is to check

    :param boolean no_submit: Prepare the temporary run directory,
                              and the bash script to execute the NEMO run,
                              but don't submit the run to the queue.
                              
    :param boolean separate_deflate: Produce separate bash scripts to deflate 
                                     the run results and qsub them to run as 
                                     serial jobs after the NEMO run finishes.

    :param int waitjob: use -W waitjob in call to qsub, to make current job
                        wait for on waitjob.  Waitjob is the queue job number

    :param boolean quiet: Don't show the run directory path message;
                          the default is to show the temporary run directory 
                          path.

    :returns: Message generated by queue manager upon submission of the
              run script.
    :rtype: str
    """
    run_dir = api.prepare(desc_file, nemo34, nocheck_init)
    if not quiet:
        log.info('Created run directory {}'.format(run_dir))
    run_desc = lib.load_run_desc(desc_file)
    nemo_processors = lib.get_n_processors(run_desc, run_dir)
    separate_xios_server = get_run_desc_value(
        run_desc, ('output', 'separate XIOS server')
    )
    if not nemo34 and separate_xios_server:
        xios_processors = get_run_desc_value(
            run_desc, ('output', 'XIOS servers')
        )
    else:
        xios_processors = 0
    results_dir = Path(results_dir)
    system = os.getenv('WGSYSTEM') or socket.gethostname().split('.')[0]
    batch_script = _build_batch_script(
        run_desc,
        fspath(desc_file), nemo_processors, xios_processors, max_deflate_jobs,
        results_dir, run_dir, system, nemo34, separate_deflate
    )
    batch_file = run_dir / 'SalishSeaNEMO.sh'
    with batch_file.open('wt') as f:
        f.write(batch_script)
    if no_submit:
        return
    if separate_deflate:
        patterns = ('*_grid_[TUVW]*.nc', '*_ptrc_T*.nc', '*_dia[12]_T*.nc')
        result_types = ('grid', 'ptrc', 'dia')
        for pattern, result_type in zip(patterns, result_types):
            deflate_script = _build_deflate_script(
                run_desc, pattern, result_type, results_dir, system, nemo34
            )
            script_file = run_dir / 'deflate_{}.sh'.format(result_type)
            with script_file.open('wt') as f:
                f.write(deflate_script)
    starting_dir = Path.cwd()
    os.chdir(fspath(run_dir))
    if waitjob:
        cmd = (
            'qsub -W depend=afterok:{waitjob} SalishSeaNEMO.sh'.format(
                waitjob=waitjob
            )
        )
    else:
        cmd = 'qsub SalishSeaNEMO.sh'
    qsub_msg = subprocess.check_output(
        shlex.split(cmd), universal_newlines=True
    )
    if separate_deflate:
        log.info(
            'SalishSeaNEMO.sh queued as {qsub_msg}'.format(qsub_msg=qsub_msg)
        )
        nemo_job_no = int(qsub_msg.split('.')[0])
        for result_type in result_types:
            deflate_script = 'deflate_{result_type}.sh'.format(
                result_type=result_type
            )
            cmd = ((
                'qsub -W depend=afterok:{nemo_job_no} ' + deflate_script
            ).format(nemo_job_no=nemo_job_no, deflate_script=deflate_script))
            deflate_qsub_msg = subprocess.check_output(
                shlex.split(cmd), universal_newlines=True
            )
            log.info(
                '{deflate_script} queued after {qsub_msg} as '
                '{deflate_qsub_msg}'.format(
                    deflate_script=deflate_script,
                    qsub_msg=qsub_msg,
                    deflate_qsub_msg=deflate_qsub_msg
                )
            )
    os.chdir(fspath(starting_dir))
    return qsub_msg


def _build_batch_script(
    run_desc, desc_file, nemo_processors, xios_processors, max_deflate_jobs,
    results_dir, run_dir, system, nemo34, separate_deflate
):
    """Build the Bash script that will execute the run.

    :param dict run_desc: Run description dictionary.

    :param str desc_file: File path/name of the YAML run description file.

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

    :param str system: Name of the system that the run will be executed on;
                       e.g. :kbd:`salish`, :kbd:`orcinus`

    :param boolean nemo34: Build batch script for a NEMO-3.4 run;
                           the default is to do so for a NEMO-3.6 run.
                              
    :param boolean separate_deflate: Produce separate bash scripts to deflate 
                                     the run results and qsub them to run as 
                                     serial jobs after the NEMO run finishes.

    :returns: Bash script to execute the run.
    :rtype: str
    """
    script = u'#!/bin/bash\n'
    try:
        email = get_run_desc_value(run_desc, ('email',))
    except KeyError:
        email = u'{user}@eos.ubc.ca'.format(user=os.getenv('USER'))
    script = u'\n'.join((
        script, u'{pbs_common}'
        u'{pbs_features}\n'.format(
            pbs_common=_pbs_common(
                run_desc, nemo_processors + xios_processors, email,
                fspath(results_dir)
            ),
            pbs_features=_pbs_features(
                nemo_processors + xios_processors, system
            )
        )
    ))
    script = u'\n'.join((
        script, u'{defns}\n'
        u'{modules}\n'
        u'{execute}\n'
        u'{fix_permissions}\n'
        u'{cleanup}'.format(
            defns=_definitions(
                run_desc, desc_file, run_dir, results_dir, system
            ),
            modules=_modules(system, nemo34),
            execute=_execute(
                nemo_processors, xios_processors, max_deflate_jobs,
                separate_deflate
            ),
            fix_permissions=_fix_permissions(),
            cleanup=_cleanup(),
        )
    ))
    return script


def _pbs_common(
    run_desc,
    n_processors,
    email,
    results_dir,
    pmem='2000mb',
    deflate=False,
    result_type=''
):
    """Return the common PBS directives used to run NEMO in a TORQUE/PBS
    multiple processor context.

    The string that is returned is intended for inclusion in a bash script
    that will be to the TORQUE/PBS queue manager via the :command:`qsub`
    command.

    :param dict run_desc: Run description dictionary.

    :param int n_processors: Number of processors that the run will be
                             executed on.
                             For NEMO-3.6 runs this is the sum of NMEO and
                             XIOS processors.

    :param str email: Email address to send job begin, end & abort
                    notifications to.

    :param str results_dir: Directory to store results into.

    :param str pmem: Memory per processor.

    :param boolean deflate: Return directives for a run results deflation job
                            when :py:obj:`True`.

    :param str result_type: Run result type ('grid', 'ptrc', or 'dia') for
                            deflation job.

    :returns: PBS directives for run script.
    :rtype: Unicode str
    """
    run_id = get_run_desc_value(run_desc, ('run_id',))
    if deflate:
        run_id = '{result_type}_{run_id}_deflate'.format(
            run_id=run_id, result_type=result_type
        )
    try:
        td = datetime.timedelta(
            seconds=get_run_desc_value(run_desc, ('walltime',))
        )
    except TypeError:
        t = datetime.datetime.strptime(
            get_run_desc_value(run_desc, ('walltime',)), '%H:%M:%S'
        ).time()
        td = datetime.timedelta(
            hours=t.hour, minutes=t.minute, seconds=t.second
        )
    walltime = _td2hms(td)
    pbs_directives = (
        u'#PBS -N {run_id}\n'
        u'#PBS -S /bin/bash\n'
        u'#PBS -l procs={procs}\n'
        u'# memory per processor\n'
        u'#PBS -l pmem={pmem}\n'
        u'#PBS -l walltime={walltime}\n'
        u'# email when the job [b]egins and [e]nds, or is [a]borted\n'
        u'#PBS -m bea\n'
        u'#PBS -M {email}\n'
        u'# stdout and stderr file paths/names\n'
    ).format(
        run_id=run_id,
        procs=n_processors,
        pmem=pmem,
        walltime=walltime,
        email=email,
    )
    stdout = (
        'stdout_deflate_{result_type}'.format(result_type=result_type)
        if deflate else 'stdout'
    )
    stderr = (
        'stderr_deflate_{result_type}'.format(result_type=result_type)
        if deflate else 'stderr'
    )
    pbs_directives += (
        u'#PBS -o {results_dir}/{stdout}\n'
        u'#PBS -e {results_dir}/{stderr}\n'
    ).format(
        results_dir=results_dir, stdout=stdout, stderr=stderr
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
    periods = (('hour', 60 * 60), ('minute', 60), ('second', 1),)
    hms = []
    for period_name, period_seconds in periods:
        period_value, seconds = divmod(seconds, period_seconds)
        hms.append(period_value)
    return u'{0[0]}:{0[1]:02d}:{0[2]:02d}'.format(hms)


def _pbs_features(n_processors, system):
    pbs_features = u''
    if system == 'jasper':
        ppn = 12
        nodes = math.ceil(n_processors / ppn)
        pbs_features = (
            u'#PBS -l feature=X5675\n'
            u'#PBS -l nodes={}:ppn={}\n'.format(int(nodes), ppn)
        )
    elif system == 'orcinus':
        pbs_features = u'#PBS -l partition=QDR\n'
    return pbs_features


def _definitions(run_desc, run_desc_file, run_dir, results_dir, system):
    home = u'${HOME}' if system == 'salish' else u'${PBS_O_HOME}'
    defns = (
        u'RUN_ID="{run_id}"\n'
        u'RUN_DESC="{run_desc_file}"\n'
        u'WORK_DIR="{run_dir}"\n'
        u'RESULTS_DIR="{results_dir}"\n'
        u'COMBINE="{salishsea_cmd} combine"\n'
        u'DEFLATE="{salishsea_cmd} deflate"\n'
        u'GATHER="{salishsea_cmd} gather"\n'
    ).format(
        run_id=get_run_desc_value(run_desc, ('run_id',)),
        run_desc_file=run_desc_file,
        run_dir=run_dir,
        results_dir=results_dir,
        salishsea_cmd=os.path.join(home, '.local/bin/salishsea'),
    )
    return defns


def _modules(system, nemo34):
    modules = u''
    if system == 'jasper':
        modules = (
            u'module load application/python/2.7.3\n'
            u'module load library/netcdf/4.1.3\n'
            u'module load library/szip/2.1\n'
            u'module load application/nco/4.3.9\n'
        )
    elif system == 'orcinus':
        if nemo34:
            modules = (
                u'module load intel\n'
                u'module load intel/14.0/netcdf_hdf5\n'
                u'module load python\n'
            )
        else:
            modules = (
                u'module load intel\n'
                u'module load intel/14.0/netcdf-4.3.3.1_mpi\n'
                u'module load intel/14.0/netcdf-fortran-4.4.0_mpi\n'
                u'module load intel/14.0/hdf5-1.8.15p1_mpi\n'
                u'module load intel/14.0/nco-4.5.2\n'
                u'module load python\n'
            )
    return modules


def _execute(
    nemo_processors, xios_processors, max_deflate_jobs, separate_deflate
):
    mpirun = u'mpirun -np {procs} ./nemo.exe'.format(procs=nemo_processors)
    if xios_processors:
        mpirun = u' '.join(
            (mpirun, ':', '-np', str(xios_processors), './xios_server.exe')
        )
    script = (
        u'mkdir -p ${RESULTS_DIR}\n'
        u'cd ${WORK_DIR}\n'
        u'echo "working dir: $(pwd)"\n'
        u'\n'
        u'echo "Starting run at $(date)"\n'
    )
    script += u'{mpirun}\n'.format(mpirun=mpirun)
    script += (
        u'MPIRUN_EXIT_CODE=$?\n'
        u'echo "Ended run at $(date)"\n'
        u'\n'
        u'echo "Results combining started at $(date)"\n'
        u'${COMBINE} ${RUN_DESC} --debug\n'
        u'echo "Results combining ended at $(date)"\n'
    )
    if not separate_deflate:
        script += (
            u'\n'
            u'echo "Results deflation started at $(date)"\n'
            u'${{DEFLATE}} *_grid_[TUVW]*.nc *_ptrc_T*.nc *_dia[12]_T*.nc '
            u'--jobs {max_deflate_jobs} --debug\n'
            u'echo "Results deflation ended at $(date)"\n'
        ).format(max_deflate_jobs=max_deflate_jobs)
    script += (
        u'\n'
        u'echo "Results gathering started at $(date)"\n'
        u'${GATHER} ${RESULTS_DIR} --debug\n'
        u'echo "Results gathering ended at $(date)"\n'
    )
    return script


def _fix_permissions():
    script = (
        u'chmod go+rx ${RESULTS_DIR}\n'
        u'chmod g+rw ${RESULTS_DIR}/*\n'
        u'chmod o+r ${RESULTS_DIR}/*\n'
    )
    return script


def _cleanup():
    script = (
        u'echo "Deleting run directory" >>${RESULTS_DIR}/stdout\n'
        u'rmdir $(pwd)\n'
        u'echo "Finished at $(date)" >>${RESULTS_DIR}/stdout\n'
        u'exit ${MPIRUN_EXIT_CODE}\n'
    )
    return script


def _build_deflate_script(
    run_desc, pattern, result_type, results_dir, system, nemo34
):
    script = u'#!/bin/bash\n'
    try:
        email = get_run_desc_value(run_desc, ('email',))
    except KeyError:
        email = u'{user}@eos.ubc.ca'.format(user=os.getenv('USER'))
    pmem = '2500mb' if result_type == 'ptrc' else '2000mb'
    script = u'\n'.join((
        script, u'{pbs_common}\n'.format(
            pbs_common=_pbs_common(
                run_desc,
                1,
                email,
                fspath(results_dir),
                pmem=pmem,
                deflate=True,
                result_type=result_type
            ),
        )
    ))
    script += (
        u'RESULTS_DIR="{results_dir}"\n'
        u'DEFLATE="${{PBS_O_HOME}}/.local/bin/salishsea deflate"\n'
        u'\n'
        u'{modules}\n'
        u'cd ${{RESULTS_DIR}}\n'
        u'echo "Results deflation started at $(date)"\n'
        u'${{DEFLATE}} {pattern} --jobs 1 --debug\n'
        u'DEFLATE_EXIT_CODE=$?\n'
        u'echo "Results deflation ended at $(date)"\n'
        u'\n'
        u'chmod g+rw ${{RESULTS_DIR}}/*\n'
        u'chmod o+r ${{RESULTS_DIR}}/*\n'
        u'\n'
        u'exit ${{DEFLATE_EXIT_CODE}}\n'
    ).format(
        results_dir=results_dir,
        modules=_modules(system, nemo34),
        pattern=pattern
    )
    return script
