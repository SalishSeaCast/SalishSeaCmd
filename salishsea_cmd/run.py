# Copyright 2013-2014 The Salish Sea MEOPAR Contributors
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
from __future__ import absolute_import

import datetime
import logging
import os
import subprocess

import cliff.command
import pathlib

from . import (
    api,
    lib,
)
from salishsea_tools.namelist import namelist2dict


__all__ = ['Run', 'td2hms']


log = logging.getLogger(__name__)


class Run(cliff.command.Command):
    """Prepare, execute, and gather results from a Salish Sea NEMO model run
    """
    def get_parser(self, prog_name):
        parser = super(Run, self).get_parser(prog_name)
        parser.description = '''
            Prepare, execute, and gather the results from a Salish Sea NEMO
            run described in DESC_FILE and IO_DEFS.
            The results files from the run are gathered in RESULTS_DIR.

            If RESULTS_DIR does not exist it will be created.
        '''
        parser.add_argument(
            'desc_file', metavar='DESC_FILE', type=open,
            help='run description YAML file')
        parser.add_argument(
            'iodefs', metavar='IO_DEFS',
            help='NEMO IOM server defs file for run')
        parser.add_argument(
            'results_dir', metavar='RESULTS_DIR',
            help='directory to store results into')
        parser.add_argument(
            '-q', '--quiet', action='store_true',
            help="don't show the run directory path or job submission message")
        parser.add_argument(
            '--compress', action='store_true',
            help='compress results files')
        parser.add_argument(
            '--keep-proc-results', action='store_true',
            help="don't delete per-processor results files")
        parser.add_argument(
            '--compress-restart', action='store_true',
            help="compress restart file(s)")
        parser.add_argument(
            '--delete-restart', action='store_true',
            help="delete restart file(s)")
        return parser

    def take_action(self, parsed_args):
        run_dir_name = api.prepare(
            self.app, self.app_args,
            parsed_args.desc_file.name, parsed_args.iodefs,
            parsed_args.quiet)
        run_dir = pathlib.Path(run_dir_name).resolve()
        namelist = namelist2dict((run_dir/'namelist').as_posix())
        procs = namelist['nammpp'][0]['jpnij']
        email = '{user}@eos.ubc.ca'.format(user=os.getenv('USER'))
        results_dir = os.path.abspath(parsed_args.results_dir)
        system = os.getenv('WGSYSTEM')
        gather_opts = ''
        if parsed_args.keep_proc_results:
            ' '.join((gather_opts, '--keep-proc-results'))
        if not parsed_args.compress:
            ' '.join((gather_opts, '--no-compress'))
        if parsed_args.compress_restart:
            ' '.join((gather_opts, '--compress-restart'))
        if parsed_args.delete_restart:
            ' '.join((gather_opts, '--delete-restart'))
        batch_script = _build_batch_script(
            parsed_args.desc_file, procs, email, results_dir, system,
            run_dir.as_posix(), gather_opts)
        batch_file = run_dir/'SalishSeaNEMO.sh'
        with batch_file.open('wt') as f:
            f.write(batch_script)
        starting_dir = pathlib.Path.cwd()
        os.chdir(run_dir.as_posix())
        qsub_msg = subprocess.check_output(
            'qsub SalishSeaNEMO.sh'.split(), universal_newlines=True)
        os.chdir(starting_dir.as_posix())
        if not parsed_args.quiet:
            log.info(qsub_msg)


def _build_batch_script(
    desc_file, procs, email, results_dir, system, run_dir, gather_opts,
):
    run_desc = lib.load_run_desc(desc_file)
    script = (
        u'#!/bin/bash\n'
        u'\n'
        u'{pbs_common}'
        u'{pbs_features}\n'
        u'{defns}\n'
        u'{modules}\n'
        u'{execute}\n'
        u'{fix_permissions}\n'
        u'{cleanup}'
        .format(
            pbs_common=_pbs_common(run_desc, procs, email, results_dir),
            pbs_features=_pbs_features(system),
            defns=_definitions(
                run_desc['run_id'], desc_file.name, run_dir, results_dir,
                gather_opts),
            modules=_modules(system),
            execute=_execute(),
            fix_permissions=_fix_permissions(),
            cleanup=_cleanup(),
        )
    )
    return script


def _pbs_common(run_desc, procs, email, results_dir, pmem='2gb'):
    walltime = td2hms(datetime.timedelta(seconds=run_desc['walltime']))
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
        u'#PBS -o {results_dir}/stdout\n'
        u'#PBS -e {results_dir}/stderr\n'
    ).format(
        run_id=run_desc['run_id'],
        procs=procs,
        pmem=pmem,
        walltime=walltime,
        email=email,
        results_dir=results_dir,
    )
    return pbs_directives


def td2hms(timedelta):
    """Return a string that is the timedelta value formated as H:M:S
    with leading zeros on the minutes and seconds values.

    :arg timedelta: Time interval to format.
    :type timedelta: :py:obj:datetime.timedelta

    :returns: H:M:S string with leading zeros on the minutes and seconds
              values.
    :rtype: unicode
    """
    seconds = int(timedelta.total_seconds())
    periods = (
        ('hour', 60*60),
        ('minute', 60),
        ('second', 1),
    )
    hms = []
    for period_name, period_seconds in periods:
        period_value, seconds = divmod(seconds, period_seconds)
        hms.append(period_value)
    return u'{0[0]}:{0[1]:02d}:{0[2]:02d}'.format(hms)


def _pbs_features(system):
    pbs_features = u''
    if system == 'jasper':
        pbs_features = (
            u'#PBS -l feature=X5675\n'
        )
    elif system == 'orcinus':
        pbs_features = (
            u'#PBS -l partition=QDR\n'
        )
    return pbs_features


def _definitions(run_id, run_desc_file, run_dir, results_dir, gather_opts):
    mpirun = 'mpirun'
    run_suffix = ''
    salishsea_cmd = '${PBS_O_HOME}/.local/bin/salishsea'
    defns = (
        u'RUN_ID={run_id}\n'
        u'RUN_DESC={run_desc_file}\n'
        u'WORK_DIR={run_dir}\n'
        u'RESULTS_DIR={results_dir}\n'
        u'MPIRUN={mpirun}\n'
        u'RUN_SUFFIX="{run_suffix}"\n'
        u'GATHER="{salishsea_cmd} gather"\n'
        u'GATHER_OPTS="{gather_opts}"\n'
    ).format(
        run_id=run_id,
        run_desc_file=run_desc_file,
        run_dir=run_dir,
        results_dir=results_dir,
        mpirun=mpirun,
        run_suffix=run_suffix,
        salishsea_cmd=salishsea_cmd,
        gather_opts=gather_opts,
    )
    return defns


def _modules(system):
    modules = ''
    if system == 'jasper':
        modules = (
            u'module load application/python/2.7.3\n'
            u'module load library/netcdf/4.1.3\n'
            u'module load library/szip/2.1\n'
        )
    elif system == 'orcinus':
        modules = (
            u'module load intel\n'
            u'module load intel\14.0\netcdf_hdf5\n'
            u'module load python\n'
        )
    return modules


def _execute():
    script = (
        u'cd ${WORK_DIR}\n'
        u'echo "working dir: $(pwd)"\n'
        u'\n'
        u'echo "Starting run at $(date)"\n'
        u'mkdir -p ${RESULTS_DIR}\n'
        u'${MPIRUN} ./nemo.exe ${RUN_SUFFIX}\n'
        u'echo "Ended run at $(date)"\n'
        u'\n'
        u'echo "Results gathering started at $(date)"\n'
        u'${GATHER} ${GATHER_OPTS} ${RUN_DESC} ${RESULTS_DIR}\n'
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
        u'echo "Scheduling cleanup of run directory"\n'
        u'echo rmdir $(pwd) > /tmp/${RUN_ID}_cleanup\n'
        u'at now + 1 minutes -f /tmp/${RUN_ID}_cleanup 2>&1\n'
    )
    return script
