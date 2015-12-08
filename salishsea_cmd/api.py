# Copyright 2013-2015 The Salish Sea MEOPAR Contributors
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

"""Salish Sea NEMO command processor API

Application programming interface for the Salish Sea NEMO command
processor.
Provides Python function interfaces to command processor sub-commands
for use in other sub-command processor modules,
and by other software.
"""
import logging
import os
import subprocess

import cliff.commandmanager
import yaml

from salishsea_cmd import prepare as prepare_plug_in


__all__ = ['combine', 'prepare', 'run_description', 'run_in_subprocess']


log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(name)s %(levelname)s: %(message)s')
handler.setFormatter(formatter)
log.addHandler(handler)


def combine(
    app,
    app_args,
    run_desc_file,
    results_dir,
    keep_proc_results=False,
    no_compress=False,
    compress_restart=False,
    delete_restart=False,
):
    """Run the NEMO :program:`rebuild_nemo` tool for each set of
    per-processor results files.

    The output of :program:`rebuild_nemo` for each file set is logged
    at the INFO level.
    The combined results files that :program:`rebuild_nemo` produces
    are moved to the directory given by :py:obj:`results_dir`.

    :arg app: Application instance invoking the command.
    :type app: :py:class:`cliff.app.App`

    :arg app_args: Application arguments.
    :type app_args: :py:class:`argparse.Namespace`

    :arg run_desc_file: File path/name of the run description YAML file.
    :type run_desc_file: str

    :arg results_dir: Directory to store results into.
    :type results_dir: str

    :arg keep_proc_results: Don't delete per-processor results files;
                            defaults to :py:obj:`False`.
    :type keep_proc_results: Boolean

    :arg no_compress: Don't compress results files;
                      defaults to :py:obj:`False`.
    :type no_compress: Boolean

    :arg compress_restart: Compress restart file(s);
                           defaults to :py:obj:`False`.
    :type compress_restart: Boolean

    :arg delete_restart: Delete restart file(s);
                         defaults to :py:obj:`False`.
    :type delete_restart: Boolean
    """
    argv = ['combine', run_desc_file, results_dir]
    if keep_proc_results:
        argv.append('--keep-proc-results')
    if no_compress:
        argv.append('--no-compress')
    if compress_restart:
        argv.append('--compress-restart')
    if delete_restart:
        argv.append('--delete-restart')
    result = _run_subcommand(app, app_args, argv)
    return result


def prepare(run_desc_file, iodefs_file, nemo34=False):
    """Prepare a Salish Sea NEMO run.

    A UUID named temporary run directory is created and symbolic links
    are created in the directory to the files and directories specifed
    to run NEMO.
    The output of :command:`hg parents` is recorded in the directory
    for the NEMO-code and NEMO-forcing repos that the symlinks point to.
    The path to the run directory is returned.

    :arg str run_desc_file: File path/name of the run description YAML
                            file.

    :arg str iodefs_file:  File path/name of the NEMO IOM server defs file
                           for the run.

    :arg boolean nemo34: Prepare a NEMO-3.4 run;
                         the default is to prepare a NEMO-3.6 run

    :returns: Path of the temporary run directory
    :rtype: str
    """
    return prepare_plug_in.prepare(run_desc_file, iodefs_file, nemo34)


def run_description(
    run_id=None,
    walltime=None,
    mpi_decomposition='8x18',
    NEMO_code=None,
    XIOS_code=None,
    forcing=None,
    runs_dir=None,
    init_conditions=None,
    nemo34=False,
):
    """Return a Salish Sea NEMO run description dict template.

    Value may be passed for the keyword arguments to set the value of the
    corresponding items.
    Otherwise,
    the returned run description dict
    that must be updated by assigment statements to provide those values.

    .. note::

        The value of the :kbd:`['forcing']['atmospheric']` item is set to
        :file:`/home/dlatorne/MEOPAR/CGRF/NEMO-atmos/` which is appropriate
        for runs on Westgrid, but needs to be changed for runs on
        :kbd:`salish`.

    :arg str run_id: Job identifier that appears in the :command:`qstat`
                     listing.

    :arg str walltime: Wall-clock time requested for the run.

    :arg str mpi_decomposition: MPI decomposition to use for the run.

    :arg str NEMO_code: Path to the :file:`NEMO-code/` directory where the
                        NEMO executable, etc. for the run are to be found.
                        If a relative path is used it will start from the
                        current directory.

    :arg str XIOS_code: Path to the :file:`XIOS/` directory where the
                        XIOS executable for the run are to be found.
                        If a relative path is used it will start from the
                        current directory.

    :arg str forcing: Path to the :file:`NEMO-forcing/` directory where the
                      netCDF files for the grid coordinates, bathymetry,
                      initial conditions, open boundary conditions, etc.
                      are found.
                      If a relative path is used it will start from the
                      current directory.

    :arg str runs_dir: Path to the directory where run directories will be
                       created.
                       If a relative path is used it will start from the
                       current directory.

    :arg str init_conditions: Name of sub-directory in :file:`NEMO-forcing/`
                              where initial conditions files are to be found,
                              or the path to and name of a restart file.
                              If a relative path is used for a restart file
                              it will start from the  current directory.

    :arg boolean nemo34: Return run description dict template a NEMO-3.4
                         run;
                         the default is to return the dict for a
                         NEMO-3.6 run.
    """
    run_description = {
        'config_name': 'SalishSea',
        'MPI decomposition': mpi_decomposition,
        'run_id': run_id,
        'walltime': walltime,
        'paths': {
            'NEMO-code': NEMO_code,
            'forcing': forcing,
            'runs directory': runs_dir,
        },
        'grid': {
            'coordinates': 'coordinates_seagrid_SalishSea.nc',
            'bathymetry': 'bathy_meter_SalishSea2.nc',
        },
        'forcing': {
            'atmospheric': '/results/forcing/atmospheric/GEM2.5/operational/',
            'initial conditions': init_conditions,
            'open boundaries': 'open_boundaries/',
            'rivers': 'rivers/',
        },
        'namelists': [
            'namelist.time',
            'namelist.domain',
            'namelist.surface',
            'namelist.lateral',
            'namelist.bottom',
            'namelist.tracers',
            'namelist.dynamics',
            'namelist.compute',
        ],
    }
    if not nemo34:
        run_description['paths']['XIOS'] = XIOS_code
        run_description['output'] = {
            'domain': 'domain_def.xml',
            'fields': None,
            'separate XIOS server': True,
            'XIOS servers': 1,
        }
        if NEMO_code is not None:
            run_description['output']['fields'] = os.path.join(
                NEMO_code, 'NEMOGCM/CONFIG/SHARED/field_def.xml')
    return run_description


def run_in_subprocess(
    run_id, run_desc, iodefs_file, results_dir, nemo34=False,
):
    """Execute `salishsea run` in a subprocess.

    :arg str run_id: Job identifier that appears in the :command:`qstat`
                     listing.
                     A temporary run description YAML file is created
                     with the name :file:`{run_id}_subprocess_run.yaml`.

    :arg dict run_desc: Run description data structure that will be
                        written to the temporary YAML file.

    :arg str iodefs_file:  File path/name of the NEMO IOM server defs
                           file for the run.

    :arg boolean nemo34: Execute a NEMO-3.4 run;
                         the default is to execute a NEMO-3.6 run

    :arg results_dir: Directory to store results into.
    :type results_dir: str
    """
    yaml_file = '{}_subprocess_run.yaml'.format(run_id)
    with open(yaml_file, 'wt') as f:
        yaml.dump(run_desc, f, default_flow_style=False)
    cmd = ['salishsea', 'run']
    if nemo34:
        cmd.append('--nemo3.4')
    cmd.extend([yaml_file, iodefs_file, results_dir])
    try:
        output = subprocess.check_output(
            cmd, stderr=subprocess.STDOUT, universal_newlines=True)
        for line in output.splitlines():
            if line:
                log.info(line)
    except subprocess.CalledProcessError as e:
        log.error(
            'subprocess {cmd} failed with return code {status}'
            .format(cmd=cmd, status=e.returncode))
        for line in e.output.splitlines():
            if line:
                log.error(line)
    os.unlink(yaml_file)


def _run_subcommand(app, app_args, argv):
    """Run a sub-command with argv as arguments via its plug-in
    interface.

    Based on :py:meth:`cliff.app.run_subcommand`.

    :arg app: Application instance invoking the command.
    :type app: :py:class:`cliff.app.App`

    :arg app_args: Application arguments.
    :type app_args: :py:class:`argparse.Namespace`

    :arg argv: Sub-command arguments.
    :type argv: list
    """
    command_manager = cliff.commandmanager.CommandManager(
        'salishsea.app', convert_underscores=False)
    try:
        subcommand = command_manager.find_command(argv)
    except ValueError as err:
        if app_args.debug:
            raise
        else:
            log.error(err)
        return 2
    cmd_factory, cmd_name, sub_argv = subcommand
    cmd = cmd_factory(app, app_args)
    try:
        cmd_parser = cmd.get_parser(cmd_name)
        parsed_args = cmd_parser.parse_args(sub_argv)
        result = cmd.take_action(parsed_args)
    except Exception as err:
        result = 1
        if app_args.debug:
            log.exception(err)
        else:
            log.error(err)
    return result
