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
"""SalishSeaCmd command plug-in for prepare sub-command.

Sets up the necessary symbolic links for a Salish Sea NEMO run
in a specified directory and changes the pwd to that directory.
"""
import functools
import logging
import os

try:
    from pathlib import Path
except ImportError:
    # Python 2.7
    from pathlib2 import Path
import shutil
import time
import xml.etree.ElementTree

import arrow
import cliff.command
import nemo_cmd
import nemo_cmd.api
import nemo_cmd.prepare
from nemo_cmd.prepare import get_run_desc_value

from salishsea_cmd import lib

logger = logging.getLogger(__name__)


class Prepare(cliff.command.Command):
    """Prepare a Salish Sea NEMO run.
    """

    def get_parser(self, prog_name):
        parser = super(Prepare, self).get_parser(prog_name)
        parser.description = '''
            Set up the Salish Sea NEMO described in DESC_FILE
            and print the path to the run directory.
        '''
        parser.add_argument(
            'desc_file',
            metavar='DESC_FILE',
            type=Path,
            help='run description YAML file'
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
            '-q',
            '--quiet',
            action='store_true',
            help="don't show the run directory path on completion"
        )
        return parser

    def take_action(self, parsed_args):
        """Execute the `salishsea prepare` sub-command.

        A UUID named directory is created and symbolic links are created
        in the directory to the files and directories specifed to run NEMO.
        The output of :command:`hg parents` is recorded in the directory
        for the NEMO-code and NEMO-forcing repos that the symlinks point to.
        The path to the run directory is logged to the console on completion
        of the set-up.
        """
        run_dir = prepare(parsed_args.desc_file, parsed_args.nocheck_init)
        if not parsed_args.quiet:
            logger.info('Created run directory {}'.format(run_dir))
        return run_dir


def prepare(desc_file, nocheck_init):
    """Create and prepare the temporary run directory.

    The temporary run directory is created with a UUID as its name.
    Symbolic links are created in the directory to the files and
    directories specifed to run NEMO.
    The output of :command:`hg parents` is recorded in the directory
    for the NEMO-code and NEMO-forcing repos that the symlinks point to.
    The path to the run directory is returned.

    :param desc_file: File path/name of the YAML run description file.
    :type desc_file: :py:class:`pathlib.Path`

    :arg nocheck_init: Suppress initial condition link check the
                       default is to check
    :type nocheck_init: boolean

    :returns: Path of the temporary run directory
    :rtype: :py:class:`pathlib.Path`
    """
    run_desc = lib.load_run_desc(desc_file)
    nemo_bin_dir = nemo_cmd.prepare.check_nemo_exec(run_desc)
    xios_bin_dir = nemo_cmd.prepare.check_xios_exec(run_desc)
    nemo_cmd.api.find_rebuild_nemo_script(run_desc)
    run_set_dir = nemo_cmd.resolved_path(desc_file).parent
    run_dir = nemo_cmd.prepare.make_run_dir(run_desc)
    nemo_cmd.prepare.make_namelists(run_set_dir, run_desc, run_dir)
    nemo_cmd.prepare.copy_run_set_files(
        run_desc, desc_file, run_set_dir, run_dir
    )
    _make_executable_links(nemo_bin_dir, run_dir, xios_bin_dir)
    _make_grid_links(run_desc, run_dir)
    _make_forcing_links(run_desc, run_dir)
    _make_restart_links(run_desc, run_dir, nocheck_init)
    _record_vcs_revisions(run_desc, run_dir)
    _add_agrif_files(run_desc, desc_file, run_set_dir, run_dir, nocheck_init)
    return run_dir


def _make_executable_links(nemo_bin_dir, run_dir, xios_bin_dir):
    """Create symlinks in run_dir to the NEMO and I/O server executables
    and record the code repository revision(s) used for the run.

    The NEMO code revision record is the output of the
    :command:`hg parents` in the NEMO code repo.
    It is stored in the :file:`NEMO-code_rev.txt` file in run_dir.

    For NEMO-3.6 runs the XIOS code revision record is the output of the
    :command:`hg parents` in the XIOS code repo.
    It is stored in the :file:`XIOS-code_rev.txt` file in run_dir.

    :param nemo_bin_dir: Absolute path of directory containing NEMO executable.
    :type nemo_bin_dir: :py:class:`pathlib.Path`

    :param run_dir: Path of the temporary run directory.
    :type run_dir: :py:class:`pathlib.Path`

    :param xios_bin_dir: Absolute path of directory containing XIOS executable.
    :type xios_bin_dir: :py:class:`pathlib.Path`
    """
    nemo_exec = nemo_bin_dir / 'nemo.exe'
    (run_dir / 'nemo.exe').symlink_to(nemo_exec)
    iom_server_exec = nemo_bin_dir / 'server.exe'
    xios_server_exec = xios_bin_dir / 'xios_server.exe'
    (run_dir / 'xios_server.exe').symlink_to(xios_server_exec)


def _make_grid_links(run_desc, run_dir, agrif_n=None):
    """Create symlinks in run_dir to the file names that NEMO expects
    for the bathymetry and coordinates files given in the run_desc dict.

    For AGRIF sub-grids, the symlink names are prefixed with the agrif_n;
    e.g. 1_coordinates.nc.

    :param dict run_desc: Run description dictionary.

    :param run_dir: Path of the temporary run directory.
    :type run_dir: :py:class:`pathlib.Path`

    :param int agrif_n: AGRIF sub-grid number.

    :raises: SystemExit
    """
    coords_keys = ('grid', 'coordinates')
    coords_filename = 'coordinates.nc'
    bathy_keys = ('grid', 'bathymetry')
    bathy_filename = 'bathy_meter.nc'
    if agrif_n is not None:
        coords_keys = (
            'grid', 'AGRIF_{agrif_n}'.format(agrif_n=agrif_n), 'coordinates'
        )
        coords_filename = '{agrif_n}_coordinates.nc'.format(agrif_n=agrif_n)
        bathy_keys = (
            'grid', 'AGRIF_{agrif_n}'.format(agrif_n=agrif_n), 'bathymetry'
        )
        bathy_filename = '{agrif_n}_bathy_meter.nc'.format(agrif_n=agrif_n)
    coords_path = get_run_desc_value(
        run_desc, coords_keys, expand_path=True, run_dir=run_dir
    )
    bathy_path = get_run_desc_value(
        run_desc, bathy_keys, expand_path=True, run_dir=run_dir
    )
    if coords_path.is_absolute() and bathy_path.is_absolute():
        grid_paths = ((coords_path, coords_filename),
                      (bathy_path, bathy_filename))
    else:
        nemo_forcing_dir = get_run_desc_value(
            run_desc, ('paths', 'forcing'), resolve_path=True, run_dir=run_dir
        )
        grid_dir = nemo_forcing_dir / 'grid'
        grid_paths = ((grid_dir / coords_path, coords_filename),
                      (grid_dir / bathy_path, bathy_filename))
    for source, link_name in grid_paths:
        if not source.exists():
            logger.error(
                '{} not found; cannot create symlink - '
                'please check the forcing path and grid file names '
                'in your run description file'.format(source)
            )
            nemo_cmd.prepare.remove_run_dir(run_dir)
            raise SystemExit(2)
        (run_dir / link_name).symlink_to(source)


def _resolve_forcing_path(run_desc, keys, run_dir):
    """Calculate a resolved path for a forcing path.
    
    If the path in the run description is absolute, resolve any symbolic links,
    etc. in it.
    
    If the path is relative, append it to the NEMO-forcing repo path from the
    run description.
    
    :param dict run_desc: Run description dictionary.

    :param tuple keys: Key sequence in the :kbd:`forcing` section of the 
                       run description for which the resolved path calculated.
                    
    :param run_dir: Path of the temporary run directory.
    :type run_dir: :py:class:`pathlib.Path`

    :return: Resolved path
    :rtype: :py:class:`pathlib.Path`

    :raises: :py:exc:`SystemExit` if the NEMO-forcing repo path does not exist
    """
    path = get_run_desc_value(
        run_desc, (('forcing',) + keys), expand_path=True, fatal=False
    )
    if path.is_absolute():
        return path.resolve()
    nemo_forcing_dir = get_run_desc_value(
        run_desc, ('paths', 'forcing'), resolve_path=True, run_dir=run_dir
    )
    return nemo_forcing_dir / path


def _make_forcing_links(run_desc, run_dir):
    """For a NEMO-3.6 run, create symlinks in run_dir to the forcing
    directory/file names given in the run description forcing section.

    :param dict run_desc: Run description dictionary.

    :param run_dir: Path of the temporary run directory.
    :type run_dir: :py:class:`pathlib.Path`

    :raises: :py:exc:`SystemExit` if a symlink target does not exist
    """
    link_checkers = {
        'atmospheric': _check_atmospheric_forcing_link,
    }
    link_names = get_run_desc_value(run_desc, ('forcing',), run_dir=run_dir)
    for link_name in link_names:
        source = _resolve_forcing_path(
            run_desc, (link_name, 'link to'), run_dir
        )
        if not source.exists():
            logger.error(
                '{} not found; cannot create symlink - '
                'please check the forcing paths and file names '
                'in your run description file'.format(source)
            )
            nemo_cmd.prepare.remove_run_dir(run_dir)
            raise SystemExit(2)
        (run_dir / link_name).symlink_to(source)
        try:
            link_checker = get_run_desc_value(
                run_desc, ('forcing', link_name, 'check link'),
                run_dir=run_dir,
                fatal=False
            )
            link_checkers[link_checker['type']](
                run_dir, source, link_checker['namelist filename']
            )
        except KeyError:
            if 'check link' not in link_names[link_name]:
                # No forcing link checker specified
                pass
            else:
                if link_checker is not None:
                    logger.error(
                        'unknown forcing link checker: {}'
                        .format(link_checker)
                    )
                    nemo_cmd.prepare.remove_run_dir(run_dir)
                    raise SystemExit(2)


def _check_atmospheric_forcing_link(run_dir, link_path, namelist_filename):
    """Confirm that the atmospheric forcing files necessary for the run
    are present.

    Sections of the namelist file are parsed to determine
    the necessary files, and the date ranges required for the run.
    
    This is the atmospheric forcing link check function used for NEMO-3.6 runs.

    :param run_dir: Path of the temporary run directory.
    :type run_dir: :py:class:`pathlib.Path`
    
    :param :py:class:`pathlib.Path` link_path: Path of the atmospheric forcing
                                               files collection.
    
    :param str namelist_filename: File name of the namelist to parse for
                                  atmospheric file names and date ranges.

    :raises: :py:exc:`SystemExit` if an atmospheric forcing file does not exist
    """
    namelist = nemo_cmd.namelist.namelist2dict(
        nemo_cmd.fspath(run_dir / namelist_filename)
    )
    if not namelist['namsbc'][0]['ln_blk_core']:
        return
    start_date = arrow.get(str(namelist['namrun'][0]['nn_date0']), 'YYYYMMDD')
    it000 = namelist['namrun'][0]['nn_it000']
    itend = namelist['namrun'][0]['nn_itend']
    dt = namelist['namdom'][0]['rn_rdt']
    end_date = start_date.replace(seconds=(itend - it000) * dt - 1)
    qtys = (
        'sn_wndi sn_wndj sn_qsr sn_qlw sn_tair sn_humi sn_prec sn_snow'.split()
    )
    core_dir = namelist['namsbc_core'][0]['cn_dir']
    file_info = {
        'core': {
            'dir': core_dir,
            'params': [],
        },
    }
    for qty in qtys:
        flread_params = namelist['namsbc_core'][0][qty]
        file_info['core']['params'].append(
            (flread_params[0], flread_params[5])
        )
    if namelist['namsbc'][0]['ln_apr_dyn']:
        apr_dir = namelist['namsbc_apr'][0]['cn_dir']
        file_info['apr'] = {
            'dir': apr_dir,
            'params': [],
        }
        flread_params = namelist['namsbc_apr'][0]['sn_apr']
        file_info['apr']['params'].append((flread_params[0], flread_params[5]))
    startm1 = start_date.replace(days=-1)
    for r in arrow.Arrow.range('day', startm1, end_date):
        for v in file_info.values():
            for basename, period in v['params']:
                if period == 'daily':
                    file_path = os.path.join(
                        v['dir'], '{basename}_'
                        'y{date.year}m{date.month:02d}d{date.day:02d}.nc'
                        .format(basename=basename, date=r)
                    )
                elif period == 'yearly':
                    file_path = os.path.join(
                        v['dir'], '{basename}.nc'.format(basename=basename)
                    )
                if not (run_dir / file_path).exists():
                    logger.error(
                        '{file_path} not found; '
                        'please confirm that atmospheric forcing files '
                        'for {startm1} through '
                        '{end} are in the {dir} collection, '
                        'and that atmospheric forcing paths in your '
                        'run description and surface boundary conditions '
                        'namelist are in agreement.'.format(
                            file_path=file_path,
                            startm1=startm1.format('YYYY-MM-DD'),
                            end=end_date.format('YYYY-MM-DD'),
                            dir=link_path,
                        )
                    )
                    nemo_cmd.prepare.remove_run_dir(run_dir)
                    raise SystemExit(2)


def _check_atmos_files(run_desc, run_dir):
    """Confirm that the atmospheric forcing files necessary for the run
    are present. Sections of the namelist file are parsed to determine
    the necessary files, and the date ranges required for the run.

    This is the atmospheric forcing link check function used for NEMO-3.4 runs.
    
    :param dict run_desc: Run description dictionary.

    :param run_dir: Path of the temporary run directory.
    :type run_dir: :py:class:`pathlib.Path`

    :raises: :py:exc:`SystemExit` if an atmospheric forcing file does not exist
    """
    namelist = nemo_cmd.namelist.namelist2dict(
        nemo_cmd.fspath(run_dir / 'namelist')
    )
    if not namelist['namsbc'][0]['ln_blk_core']:
        return
    date0 = arrow.get(str(namelist['namrun'][0]['nn_date0']), 'YYYYMMDD')
    it000 = namelist['namrun'][0]['nn_it000']
    itend = namelist['namrun'][0]['nn_itend']
    dt = namelist['namdom'][0]['rn_rdt']
    start_date = date0.replace(seconds=it000 * dt - 1)
    end_date = date0.replace(seconds=itend * dt - 1)
    qtys = (
        'sn_wndi sn_wndj sn_qsr sn_qlw sn_tair sn_humi sn_prec sn_snow'.split()
    )
    core_dir = namelist['namsbc_core'][0]['cn_dir']
    file_info = {
        'core': {
            'dir': core_dir,
            'params': [],
        },
    }
    for qty in qtys:
        flread_params = namelist['namsbc_core'][0][qty]
        file_info['core']['params'].append(
            (flread_params[0], flread_params[5])
        )
    if namelist['namsbc'][0]['ln_apr_dyn']:
        apr_dir = namelist['namsbc_apr'][0]['cn_dir']
        file_info['apr'] = {
            'dir': apr_dir,
            'params': [],
        }
        flread_params = namelist['namsbc_apr'][0]['sn_apr']
        file_info['apr']['params'].append((flread_params[0], flread_params[5]))
    startm1 = start_date.replace(days=-1)
    for r in arrow.Arrow.range('day', startm1, end_date):
        for v in file_info.values():
            for basename, period in v['params']:
                if period == 'daily':
                    file_path = os.path.join(
                        v['dir'], '{basename}_'
                        'y{date.year}m{date.month:02d}d{date.day:02d}.nc'
                        .format(basename=basename, date=r)
                    )
                elif period == 'yearly':
                    file_path = os.path.join(
                        v['dir'], '{basename}.nc'.format(basename=basename)
                    )
                if not (run_dir / file_path).exists():
                    nemo_forcing_dir = get_run_desc_value(
                        run_desc, ('paths', 'forcing'),
                        resolve_path=True,
                        run_dir=run_dir
                    )
                    atmos_dir = _resolve_forcing_path(
                        run_desc, ('atmospheric',), run_dir
                    )
                    logger.error(
                        '{file_path} not found; '
                        'please confirm that atmospheric forcing files '
                        'for {startm1} through '
                        '{end} are in the {dir} collection, '
                        'and that atmospheric forcing paths in your '
                        'run description and surface boundary conditions '
                        'namelist are in agreement.'.format(
                            file_path=file_path,
                            startm1=startm1.format('YYYY-MM-DD'),
                            end=end_date.format('YYYY-MM-DD'),
                            dir=nemo_forcing_dir / atmos_dir,
                        )
                    )
                    nemo_cmd.prepare.remove_run_dir(run_dir)
                    raise SystemExit(2)


def _make_restart_links(run_desc, run_dir, nocheck_init, agrif_n=None):
    """For a NEMO-3.6 run, create symlinks in run_dir to the restart
    files given in the run description restart section.

    :param dict run_desc: Run description dictionary.

    :param run_dir: Path of the temporary run directory.
    :type run_dir: :py:class:`pathlib.Path`

    :param boolean nocheck_init: Suppress restart file existence check;
                                 the default is to check

    :param int agrif_n: AGRIF sub-grid number.

    :raises: :py:exc:`SystemExit` if a symlink target does not exist
    """
    keys = ('restart',)
    if agrif_n is not None:
        keys = ('restart', 'AGRIF_{agrif_n}'.format(agrif_n=agrif_n))
    try:
        link_names = get_run_desc_value(
            run_desc, keys, run_dir=run_dir, fatal=False
        )
    except KeyError:
        logger.warning(
            'No restart section found in run description YAML file, '
            'so proceeding on the assumption that initial conditions '
            'have been provided'
        )
        return
    for link_name in link_names:
        if link_name.startswith('AGRIF'):
            continue
        keys = ('restart', link_name)
        if agrif_n is not None:
            keys = (
                'restart', 'AGRIF_{agrif_n}'.format(agrif_n=agrif_n), link_name
            )
            link_name = '{agrif_n}_{link_name}'.format(
                agrif_n=agrif_n, link_name=link_name
            )
        source = get_run_desc_value(run_desc, keys, expand_path=True)
        if not source.exists() and not nocheck_init:
            logger.error(
                '{} not found; cannot create symlink - '
                'please check the restart file paths and file names '
                'in your run description file'.format(source)
            )
            nemo_cmd.prepare.remove_run_dir(run_dir)
            raise SystemExit(2)
        if nocheck_init:
            (run_dir / link_name).symlink_to(source)
        else:
            (run_dir / link_name).symlink_to(source.resolve())


def _record_vcs_revisions(run_desc, run_dir):
    """Record revision and status information from version control system
    repositories in files in the temporary run directory.

    :param dict run_desc: Run description dictionary.

    :param run_dir: Path of the temporary run directory.
    :type run_dir: :py:class:`pathlib.Path`
    """
    try:
        nemo_code_config = get_run_desc_value(
            run_desc, ('paths', 'NEMO code config'),
            resolve_path=True,
            fatal=False
        )
    except KeyError:
        # Alternate key spelling for backward compatibility
        nemo_code_config = get_run_desc_value(
            run_desc, ('paths', 'NEMO-code-config'), resolve_path=True
        )
    xios_code_repo = get_run_desc_value(
        run_desc, ('paths', 'XIOS'), resolve_path=True, run_dir=run_dir
    )
    for repo in (nemo_code_config.parent.parent, xios_code_repo):
        nemo_cmd.prepare.write_repo_rev_file(
            repo, run_dir, nemo_cmd.prepare.get_hg_revision
        )
    if 'vcs revisions' not in run_desc:
        return
    vcs_funcs = {'hg': nemo_cmd.prepare.get_hg_revision}
    vcs_tools = get_run_desc_value(
        run_desc, ('vcs revisions',), run_dir=run_dir
    )
    for vcs_tool in vcs_tools:
        repos = get_run_desc_value(
            run_desc, ('vcs revisions', vcs_tool), run_dir=run_dir
        )
        for repo in repos:
            nemo_cmd.prepare.write_repo_rev_file(
                Path(repo), run_dir, vcs_funcs[vcs_tool]
            )


def _add_agrif_files(run_desc, desc_file, run_set_dir, run_dir, nocheck_init):
    """Add file copies and symlinks to temporary run directory for
    AGRIF runs.

    :param dict run_desc: Run description dictionary.

    :param desc_file: File path/name of the YAML run description file.
    :type desc_file: :py:class:`pathlib.Path`

    :param run_set_dir: Directory containing the run description file,
                        from which relative paths for the namelist section
                        files start.
    :type run_set_dir: :py:class:`pathlib.Path`

    :param run_dir: Path of the temporary run directory.
    :type run_dir: :py:class:`pathlib.Path`

    :param boolean nocheck_init: Suppress restart file existence check;
                                 the default is to check

    :raises: SystemExit if mismatching number of sub-grids is detected
    """
    try:
        get_run_desc_value(run_desc, ('AGRIF',), fatal=False)
    except KeyError:
        # Not an AGRIF run
        return
    fixed_grids = get_run_desc_value(
        run_desc, ('AGRIF', 'fixed grids'), run_dir, resolve_path=True
    )
    shutil.copy2(
        nemo_cmd.fspath(fixed_grids),
        nemo_cmd.fspath(run_dir / 'AGRIF_FixedGrids.in')
    )
    # Get number of sub-grids
    n_sub_grids = 0
    with (run_dir / 'AGRIF_FixedGrids.in').open('rt') as f:
        n_sub_grids = len([
            line for line in f
            if not line.startswith('#') and len(line.split()) == 8
        ])

    run_desc_sections = {
        # sub-grid coordinates and bathymetry files
        'grid':
        functools.partial(_make_grid_links, run_desc, run_dir),
        # sub-grid namelist files
        'namelists':
        functools.partial(
            nemo_cmd.prepare.make_namelists, run_set_dir, run_desc, run_dir
        ),
        # sub-grid output files
        'output':
        functools.partial(
            nemo_cmd.prepare.copy_run_set_files,
            run_desc,
            desc_file,
            run_set_dir,
            run_dir,
        ),
    }
    try:
        # sub-grid restart files
        link_names = get_run_desc_value(
            run_desc, ('restart',), run_dir=run_dir, fatal=False
        )
        run_desc_sections['restart'] = functools.partial(
            _make_restart_links, run_desc, run_dir, nocheck_init
        )
    except KeyError:
        # The parent grid is not being initialized from a restart file,
        # so the sub-grids can't be either
        pass
    for run_desc_section, func in run_desc_sections.items():
        sub_grids_count = 0
        section = get_run_desc_value(run_desc, (run_desc_section,))
        for key in section:
            if key.startswith('AGRIF'):
                sub_grids_count += 1
                agrif_n = int(key.split('_')[1])
                func(agrif_n=agrif_n)
        if sub_grids_count != n_sub_grids:
            logger.error(
                'Expected {n_sub_grids} AGRIF sub-grids in {section} section, '
                'but found {sub_grids_count} - '
                'please check your run description file'.format(
                    n_sub_grids=n_sub_grids,
                    section=run_desc_section,
                    sub_grids_count=sub_grids_count
                )
            )
            nemo_cmd.prepare.remove_run_dir(run_dir)
            raise SystemExit(2)
