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

"""SalishSeaCmd command plug-in for prepare sub-command.

Sets up the necesaary symbolic links for a Salish Sea NEMO run
in a specified directory and changes the pwd to that directory.
"""
from __future__ import absolute_import

import logging
import os
import shutil
import sys
import uuid

import arrow
import cliff.command

from . import lib
import salishsea_tools.hg_commands as hg
from salishsea_tools.namelist import namelist2dict


__all__ = ['Prepare']


log = logging.getLogger(__name__)


class Prepare(cliff.command.Command):
    """Prepare a Salish Sea NEMO run
    """

    def get_parser(self, prog_name):
        parser = super(Prepare, self).get_parser(prog_name)
        parser.description = '''
            Set up the Salish Sea NEMO run described in DESC_FILE
            and print the path to the run directory.
        '''
        parser.add_argument(
            'desc_file', metavar='DESC_FILE', type=open,
            help='run description YAML file')
        parser.add_argument(
            'iodefs', metavar='IO_DEFS',
            help='NEMO IOM server defs file for run')
        parser.add_argument(
            '-q', '--quiet', action='store_true',
            help="don't show the run directory path on completion")
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
        run_desc = lib.load_run_desc(parsed_args.desc_file)
        nemo_code_repo, nemo_bin_dir = _check_nemo_exec(run_desc, parsed_args)
        starting_dir = os.getcwd()
        run_dir = _make_run_dir(run_desc)
        _make_namelist(parsed_args, run_desc, run_dir)
        _copy_run_set_files(parsed_args, run_dir, starting_dir)
        _make_nemo_code_links(
            nemo_code_repo, nemo_bin_dir, run_dir, starting_dir)
        _make_grid_links(run_desc, run_dir, starting_dir)
        _make_forcing_links(run_desc, run_dir, starting_dir)
        _check_atmos_files(run_desc, run_dir)
        if not parsed_args.quiet:
            log.info('Created run directory {}'.format(run_dir))
        return run_dir


def _check_nemo_exec(run_desc, args):
    nemo_code_repo = os.path.abspath(run_desc['paths']['NEMO-code'])
    config_dir = os.path.join(
        nemo_code_repo, 'NEMOGCM', 'CONFIG', run_desc['config_name'])
    nemo_bin_dir = os.path.join(nemo_code_repo, config_dir, 'BLD', 'bin')
    nemo_exec = os.path.join(nemo_bin_dir, 'nemo.exe')
    if not os.path.exists(nemo_exec):
        log.error(
            '{} not found - did you forget to build it?'
            .format(nemo_exec))
        sys.exit(2)
    iom_server_exec = os.path.join(nemo_bin_dir, 'server.exe')
    if not os.path.exists(iom_server_exec) and not args.quiet:
        log.warn(
            '{} not found - are you running without key_iomput?'
            .format(iom_server_exec)
        )
    return nemo_code_repo, nemo_bin_dir


def _make_run_dir(run_desc):
    run_dir = os.path.join(
        run_desc['paths']['runs directory'], str(uuid.uuid1()))
    os.mkdir(run_dir)
    return run_dir


def _remove_run_dir(run_dir):
    if not os.path.exists(run_dir):
        return
    for fn in os.listdir(run_dir):
        os.remove(os.path.join(run_dir, fn))
    os.rmdir(run_dir)


def _make_namelist(args, run_desc, run_dir):
    run_set_dir = os.path.dirname(os.path.abspath(args.desc_file.name))
    namelists = run_desc['namelists']
    with open(os.path.join(run_dir, 'namelist'), 'wt') as namelist:
        for nl in namelists:
            try:
                with open(os.path.join(run_set_dir, nl), 'rt') as f:
                    namelist.writelines(f.readlines())
                    namelist.write('\n\n')
            except IOError as e:
                log.error(e)
                _remove_run_dir(run_dir)
                sys.exit(2)
        namelist.writelines(EMPTY_NAMELISTS)


def _copy_run_set_files(args, run_dir, starting_dir):
    run_set_dir = os.path.dirname(os.path.abspath(args.desc_file.name))
    run_set_files = (
        (args.iodefs, 'iodef.xml'),
        (args.desc_file.name, os.path.basename(args.desc_file.name)),
        ('xmlio_server.def', 'xmlio_server.def'),
    )
    os.chdir(run_dir)
    for source, dest_name in run_set_files:
        source_path = os.path.normpath(os.path.join(run_set_dir, source))
        shutil.copy2(source_path, dest_name)
    os.chdir(starting_dir)


def _make_nemo_code_links(nemo_code_repo, nemo_bin_dir, run_dir, starting_dir):
    nemo_exec = os.path.join(nemo_bin_dir, 'nemo.exe')
    os.chdir(run_dir)
    os.symlink(nemo_exec, 'nemo.exe')
    iom_server_exec = os.path.join(nemo_bin_dir, 'server.exe')
    if os.path.exists(iom_server_exec):
        os.symlink(iom_server_exec, 'server.exe')
    with open('NEMO-code_rev.txt', 'wt') as f:
        f.writelines(hg.parents(nemo_code_repo, verbose=True))
    os.chdir(starting_dir)


def _make_grid_links(run_desc, run_dir, starting_dir):
    nemo_forcing_dir = os.path.abspath(run_desc['paths']['forcing'])
    if not os.path.exists(nemo_forcing_dir):
        log.error(
            '{} not found; cannot create symlinks - '
            'please check the forcing path in your run description file'
            .format(nemo_forcing_dir)
        )
        _remove_run_dir(run_dir)
        sys.exit(2)
    grid_dir = os.path.join(nemo_forcing_dir, 'grid')
    grid_files = (
        (run_desc['grid']['coordinates'], 'coordinates.nc'),
        (run_desc['grid']['bathymetry'], 'bathy_meter.nc'),
    )
    os.chdir(run_dir)
    for source, link_name in grid_files:
        link_path = os.path.join(grid_dir, source)
        if not os.path.exists(link_path):
            log.error(
                '{} not found; cannot create symlink - '
                'please check the forcing path and grid file names '
                'in your run description file'
                .format(link_path))
            _remove_run_dir(run_dir)
            sys.exit(2)
        os.symlink(link_path, link_name)
    os.chdir(starting_dir)


def _make_forcing_links(run_desc, run_dir, starting_dir):
    nemo_forcing_dir = os.path.abspath(run_desc['paths']['forcing'])
    if not os.path.exists(nemo_forcing_dir):
        log.error(
            '{} not found; cannot create symlinks - '
            'please check the forcing path in your run description file'
            .format(nemo_forcing_dir)
        )
        _remove_run_dir(run_dir)
        sys.exit(2)
    init_conditions = run_desc['forcing']['initial conditions']
    if 'restart' in init_conditions:
        ic_source = os.path.abspath(init_conditions)
        ic_link_name = 'restart.nc'
    else:
        ic_source = os.path.join(nemo_forcing_dir, init_conditions)
        ic_link_name = 'initial_strat'
    forcing_dirs = (
        (run_desc['forcing']['atmospheric'], 'NEMO-atmos'),
        (run_desc['forcing']['open boundaries'], 'open_boundaries'),
        (run_desc['forcing']['rivers'], 'rivers')
    )
    os.chdir(run_dir)
    if not os.path.exists(ic_source):
        log.error(
            '{} not found; cannot create symlink - '
            'please check the forcing path and initial conditions file names '
            'in your run description file'
            .format(ic_source))
        _remove_run_dir(run_dir)
        sys.exit(2)
    os.symlink(ic_source, ic_link_name)
    for source, link_name in forcing_dirs:
        link_path = os.path.join(nemo_forcing_dir, source)
        if not os.path.exists(link_path):
            log.error(
                '{} not found; cannot create symlink - '
                'please check the forcing paths and file names '
                'in your run description file'
                .format(link_path))
            _remove_run_dir(run_dir)
            sys.exit(2)
        os.symlink(link_path, link_name)
    with open('NEMO-forcing_rev.txt', 'wt') as f:
        f.writelines(hg.parents(nemo_forcing_dir, verbose=True))
    os.chdir(starting_dir)


def _check_atmos_files(run_desc, run_dir):
    namelist = namelist2dict(os.path.join(run_dir, 'namelist'))
    if not namelist['namsbc'][0]['ln_blk_core']:
        return
    date0 = arrow.get(str(namelist['namrun'][0]['nn_date0']), 'YYYYMMDD')
    it000 = namelist['namrun'][0]['nn_it000']
    itend = namelist['namrun'][0]['nn_itend']
    dt = namelist['namdom'][0]['rn_rdt']
    start_date = date0.replace(seconds=it000 * dt - 1)
    end_date = date0.replace(seconds=itend * dt - 1)
    qtys = (
        'sn_wndi sn_wndj sn_qsr sn_qlw sn_tair sn_humi sn_prec sn_snow'
        .split())
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
            (flread_params[0], flread_params[5]))
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
                        v['dir'],
                        '{basename}_'
                        'y{date.year}m{date.month:02d}d{date.day:02d}.nc'
                        .format(basename=basename, date=r))
                elif period == 'yearly':
                    file_path = os.path.join(
                        v['dir'], '{basename}.nc'.format(basename=basename))
                if not os.path.exists(os.path.join(run_dir, file_path)):
                    nemo_forcing_dir = os.path.abspath(
                        run_desc['paths']['forcing'])
                    atmos_dir = run_desc['forcing']['atmospheric']
                    log.error(
                        '{file_path} not found; '
                        'please confirm that CGRF files for {startm1} through '
                        '{end} are in the {dir} collection, '
                        'and that atmospheric forcing paths in your '
                        'run description and surface boundary conditions '
                        'namelist are in agreement.'
                        .format(
                            file_path=file_path,
                            startm1=startm1.format('YYYY-MM-DD'),
                            end=end_date.format('YYYY-MM-DD'),
                            dir=os.path.join(nemo_forcing_dir, atmos_dir),
                        )
                    )
                    _remove_run_dir(run_dir)
                    sys.exit(2)


# All of the namelists that NEMO requires, but empty so that they result
# in the defaults defined in the NEMO code being used.
EMPTY_NAMELISTS = """
&namrun        !  Parameters of the run
&end
&nam_diaharm   !  Harmonic analysis of tidal constituents ('key_diaharm')
&end
&namzgr        !  Vertical coordinate
&end
&namzgr_sco    !  s-Coordinate or hybrid z-s-coordinate
&end
&namdom        !  Space and time domain (bathymetry, mesh, timestep)
&end
&namtsd        !  Data : Temperature  & Salinity
&end
&namsbc        !  Surface Boundary Condition (surface module)
&end
&namsbc_ana    !  Analytical surface boundary condition
&end
&namsbc_flx    !  Surface boundary condition : flux formulation
&end
&namsbc_clio   !  CLIO bulk formulae
&end
&namsbc_core   !  CORE bulk formulae
&end
&namsbc_mfs    !  MFS bulk formulae
&end
&namtra_qsr    !  Penetrative solar radiation
&end
&namsbc_rnf    !  Runoffs namelist surface boundary condition
&end
&namsbc_apr    !  Atmospheric pressure used as ocean forcing or in bulk
&end
&namsbc_ssr    !  Surface boundary condition : sea surface restoring
&end
&namsbc_alb    !  Albedo parameters
&end
&namlbc        !  Lateral momentum boundary condition
&end
&namcla        !  Cross land advection
&end
&nam_tide      !  Tide parameters (#ifdef key_tide)
&end
&nambdy        !  Unstructured open boundaries ("key_bdy")
&end
&nambdy_index  !  Open boundaries - definition ("key_bdy")
&end
&nambdy_dta    !  Open boundaries - external data ("key_bdy")
&end
&nambdy_tide   !  Tidal forcing at open boundaries
&end
&nambfr        !  Bottom friction
&end
&nambbc        !  Bottom temperature boundary condition
&end
&nambbl        !  Bottom boundary layer scheme
&end
&nameos        !  Ocean physical parameters
&end
&namtra_adv    !  Advection scheme for tracer
&end
&namtra_ldf    !  Lateral diffusion scheme for tracers
&end
&namtra_dmp    !  Tracer: T & S newtonian damping
&end
&namdyn_adv    !  Formulation of the momentum advection
&end
&namdyn_vor    !  Option of physics/algorithm (not control by CPP keys)
&end
&namdyn_hpg    !  Hydrostatic pressure gradient option
&end
&namdyn_ldf    !  Lateral diffusion on momentum
&end
&namzdf        !  Vertical physics
&end
&namzdf_gls    !  GLS vertical diffusion ("key_zdfgls")
&end
&namsol        !  Elliptic solver / island / free surface
&end
&nammpp        !  Massively Parallel Processing ("key_mpp_mpi)
&end
&namctl        !  Control prints & Benchmark
&end
&namnc4        !  netCDF4 chunking and compression settings ("key_netcdf4")
&end
&namptr        !  Poleward Transport Diagnostic
&end
&namhsb        !  Heat and salt budgets
&end
&namdct        !  Transports through sections
&end
&namsbc_wave   !  External fields from wave model
&end
&namdyn_nept   !  Neptune effect
&end           !  (simplified: lateral & vertical diffusions removed)
&namtrj        !  Handling non-linear trajectory for TAM
&end           !  (output for direct model, input for TAM)
"""