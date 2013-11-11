"""Salish Sea NEMO run prepare sub-command processor

Sets up the necesaary symbolic links for a Salish Sea NEMO run in a specified
directory and changes the pwd to that directory.


Copyright 2013 The Salish Sea MEOPAR Contributors
and The University of British Columbia

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
from __future__ import absolute_import
import logging
import os
import subprocess
import sys
import uuid
from . import utils


__all__ = ['main']


log = logging.getLogger('prepare')
log.setLevel(logging.DEBUG)
log.addHandler(utils.make_stdout_logger())
log.addHandler(utils.make_stderr_logger())


def main(run_desc, args):
    """Set up for the Salish Sea NEMO run described in run_desc.

    A UUID named directory is created and symbolic links are created
    in the directory to the files and directories specifed to run NEMO.
    The output of :command:`hg heads .` is recorded in the directory
    for the NEMO-code and NEMO-forcing repos that the symlinks point to.
    The path to the run directory is logged to the console on completion
    of the set-up.

    :arg run_desc: Run description data structure.
    :type run_desc: dict

    :arg args: Command line arguments and option values
    :type args: :class:`argparse.Namespace`
    """
    nemo_code_repo, nemo_bin_dir = _check_nemo_exec(run_desc, args)
    starting_dir = os.getcwd()
    run_dir = _make_run_dir(run_desc)
    _make_run_set_links(args, run_dir, starting_dir)
    _make_nemo_code_links(nemo_code_repo, nemo_bin_dir, run_dir, starting_dir)
    _make_grid_links(run_desc, run_dir, starting_dir)
    _make_forcing_links(run_desc, run_dir, starting_dir)
    if not args.quiet:
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
            'Error: {} not found - did you forget to build it?'
            .format(nemo_exec))
        sys.exit(2)
    iom_server_exec = os.path.join(nemo_bin_dir, 'server.exe')
    if not os.path.exists(iom_server_exec) and not args.quiet:
        log.warn(
            'Warning: {} not found - are you running without key_iomput?'
            .format(iom_server_exec)
        )
    return nemo_code_repo, nemo_bin_dir


def _make_run_dir(run_desc):
    run_dir = os.path.join(
        run_desc['paths']['runs directory'], str(uuid.uuid1()))
    os.mkdir(run_dir)
    return run_dir


def _make_run_set_links(args, run_dir, starting_dir):
    run_set_dir = os.path.dirname(os.path.abspath(args.desc_file.name))
    run_set_files = (
        (args.iodefs, 'iodef.xml'),
        (args.namelist, 'namelist'),
        (args.desc_file.name, os.path.basename(args.desc_file.name)),
        ('xmlio_server.def', 'xmlio_server.def'),
    )
    os.chdir(run_dir)
    for source, link_name in run_set_files:
        os.symlink(
            os.path.join(run_set_dir, os.path.basename(source)),
            link_name)
    os.chdir(starting_dir)


def _make_nemo_code_links(nemo_code_repo, nemo_bin_dir, run_dir, starting_dir):
    nemo_exec = os.path.join(nemo_bin_dir, 'nemo.exe')
    os.chdir(run_dir)
    os.symlink(nemo_exec, 'nemo.exe')
    iom_server_exec = os.path.join(nemo_bin_dir, 'server.exe')
    if os.path.exists(iom_server_exec):
        os.symlink(iom_server_exec, 'server.exe')
    with open('NEMO-code_tip.txt', 'wt') as f:
        f.writelines(hg_heads(nemo_code_repo))
    os.chdir(starting_dir)


def _make_grid_links(run_desc, run_dir, starting_dir):
    nemo_forcing_dir = os.path.abspath(run_desc['paths']['forcing'])
    grid_dir = os.path.join(nemo_forcing_dir, 'grid')
    grid_files = (
        (run_desc['grid']['coordinates'], 'coordinates.nc'),
        (run_desc['grid']['bathymetry'], 'bathy_meter.nc'),
    )
    os.chdir(run_dir)
    for source, link_name in grid_files:
        os.symlink(os.path.join(grid_dir, source), link_name)
    os.chdir(starting_dir)


def _make_forcing_links(run_desc, run_dir, starting_dir):
    nemo_forcing_dir = os.path.abspath(run_desc['paths']['forcing'])
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
    os.symlink(ic_source, ic_link_name)
    for source, link_name in forcing_dirs:
        os.symlink(os.path.join(nemo_forcing_dir, source), link_name)
    with open('NEMO-forcing_tip.txt', 'wt') as f:
        f.writelines(hg_heads(nemo_forcing_dir))
    os.chdir(starting_dir)


def hg_heads(repo, revs=['.']):
    """Return the result of the :command:`hg -R repo heads revs` command.

    :arg repo: Repository root directory.
    :type repo: str

    :arg revs: Revisions for which to show branch heads.
               The default :kbd:`.` causes the head(s) of the currently
               checked out branch to be returned.
    :type revs: list

    :returns: Output of the command.
    :rtype: str
    """
    cmd = ['hg', '-R', repo, 'heads'] + revs
    return subprocess.check_output(cmd)
