# Copyright 2013-2016 The Salish Sea MEOPAR Contributors
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
import logging
import os
import shutil
import time
import uuid
import xml.etree.ElementTree

import arrow
import cliff.command

import salishsea_tools.hg_commands as hg
from salishsea_tools.namelist import namelist2dict

from salishsea_cmd import lib

log = logging.getLogger(__name__)


class Prepare(cliff.command.Command):
    """Prepare a Salish Sea NEMO run
    """

    def get_parser(self, prog_name):
        parser = super(Prepare, self).get_parser(prog_name)
        parser.description = '''
            Set up the Salish Sea NEMO described in DESC_FILE
            and print the path to the run directory.
        '''
        parser.add_argument(
            'desc_file', metavar='DESC_FILE', help='run description YAML file'
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
            '--nemo3.4',
            dest='nemo34',
            action='store_true',
            help='''
            Prepare a NEMO-3.4 run;
            the default is to prepare a NEMO-3.6 run'''
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
        run_dir = prepare(
            parsed_args.desc_file, parsed_args.nemo34, parsed_args.nocheck_init
        )
        if not parsed_args.quiet:
            log.info('Created run directory {}'.format(run_dir))
        return run_dir


def prepare(desc_file, nemo34, nocheck_init):
    """Create and prepare the temporary run directory.

    The temporary run directory is created with a UUID as its name.
    Symbolic links are created in the directory to the files and
    directories specifed to run NEMO.
    The output of :command:`hg parents` is recorded in the directory
    for the NEMO-code and NEMO-forcing repos that the symlinks point to.
    The path to the run directory is returned.

    :arg desc_file: File path/name of the YAML run description file.
    :type desc_file: str

    :arg nemo34: Prepare a NEMO-3.4 run;
                 the default is to prepare a NEMO-3.6 run
    :type nemo34: boolean

    :arg nocheck_init: Suppress initial condition link check the
                       default is to check
    :type nocheck_init: boolean

    :returns: Path of the temporary run directory
    :rtype: str
    """
    run_desc = lib.load_run_desc(desc_file)
    nemo_code_repo, nemo_bin_dir = _check_nemo_exec(run_desc, nemo34)
    xios_code_repo, xios_bin_dir = (
        _check_xios_exec(run_desc) if not nemo34 else (None, None)
    )
    run_set_dir = os.path.dirname(os.path.abspath(desc_file))
    run_dir = _make_run_dir(run_desc)
    _make_namelists(run_set_dir, run_desc, run_dir, nemo_code_repo, nemo34)
    _copy_run_set_files(run_desc, desc_file, run_set_dir, run_dir, nemo34)
    _make_executable_links(
        nemo_code_repo, nemo_bin_dir, run_dir, nemo34, xios_code_repo,
        xios_bin_dir
    )
    _make_grid_links(run_desc, run_dir)
    _make_forcing_links(run_desc, run_dir, nemo34, nocheck_init)
    return run_dir


def _check_nemo_exec(run_desc, nemo34):
    """Calculate absolute paths of NEMO code repo & NEMO executable's
    directory.

    Confirm that the NEMO executable exists, raising a SystemExit
    exception if it does not.

    For NEMO-3.4 runs, confirm check that the IOM server executable
    exists, issuing a warning if it does not.

    :arg run_desc: Run description dictionary.
    :type run_desc: dict

    :arg nemo34: Prepare a NEMO-3.4 run;
                 the default is to prepare a NEMO-3.6 run
    :type nemo34: boolean

    :returns: Absolute paths of NEMO code repo & NEMO executable's
              directory.
    :rtype: 2-tuple

    :raises: SystemExit
    """
    nemo_code_repo = os.path.abspath(
        os.path.expandvars(os.path.expanduser(run_desc['paths']['NEMO-code']))
    )
    config_dir = os.path.join(
        nemo_code_repo, 'NEMOGCM', 'CONFIG', run_desc['config_name']
    )
    nemo_bin_dir = os.path.join(nemo_code_repo, config_dir, 'BLD', 'bin')
    nemo_exec = os.path.join(nemo_bin_dir, 'nemo.exe')
    if not os.path.exists(nemo_exec):
        log.error(
            '{} not found - did you forget to build it?'.format(nemo_exec)
        )
        raise SystemExit(2)
    if nemo34:
        iom_server_exec = os.path.join(nemo_bin_dir, 'server.exe')
        if not os.path.exists(iom_server_exec):
            log.warn(
                '{} not found - are you running without key_iomput?'
                .format(iom_server_exec)
            )
    return nemo_code_repo, nemo_bin_dir


def _check_xios_exec(run_desc):
    """Calculate absolute path of XIOS code repo & XIOS executable's
    directory.

    Confirm that the XIOS executable exists, raising a SystemExit
    exception if it does not.

    :arg run_desc: Run description dictionary.
    :type run_desc: dict

    :returns: Absolute paths of XIO code repo & XIOS executable's
              directory.
    :rtype: 2-tuple

    :raises: SystemExit
    """
    xios_code_repo = os.path.abspath(run_desc['paths']['XIOS'])
    xios_bin_dir = os.path.join(xios_code_repo, 'bin')
    xios_exec = os.path.join(xios_bin_dir, 'xios_server.exe')
    if not os.path.exists(xios_exec):
        log.error(
            '{} not found - did you forget to build it?'.format(xios_exec)
        )
        raise SystemExit(2)
    return xios_code_repo, xios_bin_dir


def _make_run_dir(run_desc):
    """Create the directory from which NEMO will be run.

    The location is the directory comes from the run description,
    and its name is a hostname- and time-based UUID.

    :arg run_desc: Run description dictionary.
    :type run_desc: dict
    """
    run_dir = os.path.join(
        run_desc['paths']['runs directory'], str(uuid.uuid1())
    )
    os.mkdir(run_dir)
    return run_dir


def _remove_run_dir(run_dir):
    """Remove all files from run_dir, then remove run_dir.

    Intended to be used as a clean-up operation when some other part
    of the prepare process fails.

    :arg run_dir: Path of the temporary run directory.
    :type run_dir: str
    """
    # Allow time for the OS to flush file buffers to disk
    time.sleep(0.1)
    try:
        for fn in os.listdir(run_dir):
            os.remove(os.path.join(run_dir, fn))
        os.rmdir(run_dir)
    except OSError:
        pass


def _make_namelists(run_set_dir, run_desc, run_dir, nemo_code_repo, nemo34):
    """Build the namelist file(s) for the run in run_dir by concatenating
    the list(s) of namelist section files provided in run_desc.

    If any of the required namelist section files are missing,
    delete the run directory and raise a SystemExit exception.

    :arg run_set_dir: Directory containing the run description file,
                      from which relative paths for the namelist section
                      files start.
    :type run_set_dir: str

    :arg run_desc: Run description dictionary.
    :type run_desc: dict

    :arg run_dir: Path of the temporary run directory.
    :type run_dir: str

    :arg nemo_code_repo: Absolute path of NEMO code repo.
    :type nemo_code_repo: str

    :arg nemo34: Prepare a NEMO-3.4 run;
                 the default is to prepare a NEMO-3.6 run
    :type nemo34: boolean

    :raises: SystemExit
    """
    if nemo34:
        _make_namelist_nemo34(run_set_dir, run_desc, run_dir)
    else:
        _make_namelists_nemo36(run_set_dir, run_desc, run_dir, nemo_code_repo)


def _make_namelist_nemo34(run_set_dir, run_desc, run_dir):
    """Build the namelist file for the NEMO-3.4 run in run_dir by
    concatenating the list of namelist section files provided in run_desc.

    If any of the required namelist section files are missing,
    delete the run directory and raise a SystemExit exception.

    :arg run_set_dir: Directory containing the run description file,
                      from which relative paths for the namelist section
                      files start.
    :type run_set_dir: str

    :arg run_desc: Run description dictionary.
    :type run_desc: dict

    :arg run_dir: Path of the temporary run directory.
    :type run_dir: str

    :raises: SystemExit
    """
    namelists = run_desc['namelists']
    namelist_filename = 'namelist'
    with open(os.path.join(run_dir, namelist_filename), 'wt') as namelist:
        for nl in namelists:
            try:
                with open(os.path.join(run_set_dir, nl), 'rt') as f:
                    namelist.writelines(f.readlines())
                    namelist.write('\n\n')
            except IOError as e:
                log.error(e)
                _remove_run_dir(run_dir)
                raise SystemExit(2)
        namelist.writelines(EMPTY_NAMELISTS)
    _set_mpi_decomposition(namelist_filename, run_desc, run_dir)


def _make_namelists_nemo36(run_set_dir, run_desc, run_dir, nemo_code_repo):
    """Build the namelist files for the NEMO-3.6 run in run_dir by
    concatenating the lists of namelist section files provided in run_desc.

    If any of the required namelist section files are missing,
    delete the run directory and raise a SystemExit exception.

    :arg run_set_dir: Directory containing the run description file,
                      from which relative paths for the namelist section
                      files start.
    :type run_set_dir: str

    :arg run_desc: Run description dictionary.
    :type run_desc: dict

    :arg run_dir: Path of the temporary run directory.
    :type run_dir: str

    :arg nemo_code_repo: Absolute path of NEMO code repo.
    :type nemo_code_repo: str

    :raises: SystemExit
    """
    for namelist_filename in run_desc['namelists']:
        with open(os.path.join(run_dir, namelist_filename), 'wt') as namelist:
            for nl in run_desc['namelists'][namelist_filename]:
                try:
                    with open(os.path.join(run_set_dir, nl), 'rt') as f:
                        namelist.writelines(f.readlines())
                        namelist.write('\n\n')
                except IOError as e:
                    log.error(e)
                    _remove_run_dir(run_dir)
                    raise SystemExit(2)
        ref_namelist = namelist_filename.replace('_cfg', '_ref')
        ref_namelist_path = os.path.join(
            nemo_code_repo, 'NEMOGCM', 'CONFIG', 'SHARED', ref_namelist
        )
        saved_cwd = os.getcwd()
        os.chdir(run_dir)
        os.symlink(ref_namelist_path, ref_namelist)
        os.chdir(saved_cwd)
    if 'namelist_cfg' in run_desc['namelists']:
        _set_mpi_decomposition('namelist_cfg', run_desc, run_dir)
    else:
        log.error(
            'No namelist_cfg key found in namelists section of run '
            'description'
        )
        raise SystemExit(2)


def _set_mpi_decomposition(namelist_filename, run_desc, run_dir):
    """Update the &nammpp namelist jpni & jpnj values with the MPI
    decomposition values from the run description.

    A SystemExit exeception is raise if there is no MPI decomposition
    specified in the run description.

    :arg namelist_filename: The name of the namelist file.
    :type namelist_filename: str

    :arg run_desc: Run description dictionary.
    :type run_desc: dict

    :arg run_dir: Path of the temporary run directory.
    :type run_dir: str

    :raises: SystemExit
    """
    try:
        jpni, jpnj = run_desc['MPI decomposition'].split('x')
    except KeyError:
        log.error(
            'MPI decomposition value not found in YAML run description file. '
            'Please add a line like:\n'
            '  MPI decomposition: 8x18\n'
            'that says how you want the domain distributed over the '
            'processors in the i (longitude) and j (latitude) dimensions.'
        )
        _remove_run_dir(run_dir)
        raise SystemExit(2)
    jpnij = str(lib.get_n_processors(run_desc))
    with open(os.path.join(run_dir, namelist_filename), 'rt') as f:
        lines = f.readlines()
    for key, new_value in {'jpni': jpni, 'jpnj': jpnj, 'jpnij': jpnij}.items():
        value, i = _get_namelist_value(key, lines)
        lines[i] = lines[i].replace(value, new_value)
    with open(os.path.join(run_dir, namelist_filename), 'wt') as f:
        f.writelines(lines)


def _get_namelist_value(key, lines):
    """Return the value corresponding to key in lines, and the index
    at which key was found.

    lines is expected to be a NEMO namelist in the form of a list of strings.

    :arg key: The namelist key to find the value and line number of.
    :type key: str

    :arg lines: The namelist lines.
    :type lines: list

    :returns: The value corresponding to key,
              and the index in lines at check key was found.
    :rtype: 2-tuple
    """
    line_index = [
        i for i, line in enumerate(lines)
        if line.strip() and line.split()[0] == key
    ][-1]
    value = lines[line_index].split()[2]
    return value, line_index


def _copy_run_set_files(run_desc, desc_file, run_set_dir, run_dir, nemo34):
    """Copy the run-set files given into run_dir.

    For all versions of NEMO the YAML run description file and the
    IO defs files (both from the command-line) are copied.
    The IO defs file is copied as :file:`iodef.xml` because that is the
    name that NEMO-3.4 or XIOS expects.

    For NEMO-3.4, the :file:`xmlio_server.def` file is also copied.

    For NEMO-3.6, the domain defs and field defs files used by XIOS
    are also copied.
    Those file paths/names of those file are taken from the :kbd:`output`
    stanza of the YAML run description file.
    They are copied to :file:`domain_def.xml` and :file:`field_def.xml`,
    repectively, because those are the file names that XIOS expects.

    :arg run_desc: Run description dictionary.
    :type run_desc: dict

    :arg desc_file: File path/name of the YAML run description file.
    :type desc_file: str

    :arg run_set_dir: Directory containing the run description file,
                      from which relative paths for the namelist section
                      files start.
    :type run_set_dir: str

    :arg run_dir: Path of the temporary run directory.
    :type run_dir: str

    :arg nemo34: Prepare a NEMO-3.4 run;
                 the default is to prepare a NEMO-3.6 run
    :type nemo34: boolean
    """
    run_set_files = [
        (os.path.abspath(run_desc['output']['files']), 'iodef.xml'),
        (os.path.join(run_set_dir, desc_file), os.path.basename(desc_file)),
    ]
    if nemo34:
        run_set_files.append((
            os.path.join(run_set_dir, 'xmlio_server.def'), 'xmlio_server.def'
        ))
    else:
        run_set_files.extend([
            (os.path.abspath(run_desc['output']['domain']), 'domain_def.xml'),
            (os.path.abspath(run_desc['output']['fields']), 'field_def.xml'),
        ])
    saved_cwd = os.getcwd()
    os.chdir(run_dir)
    for source, dest_name in run_set_files:
        source_path = os.path.normpath(source)
        shutil.copy2(source_path, dest_name)
    if not nemo34:
        _set_xios_server_mode(run_desc, run_dir)
    os.chdir(saved_cwd)


def _set_xios_server_mode(run_desc, run_dir):
    """Update the :file:`iodef.xml` :kbd:`xios` context :kbd:`using_server`
    variable text with the :kbd:`separate XIOS server` value from the
    run description.

    :arg dict run_desc: Run description dictionary.

    :arg str run_dir: Path of the temporary run directory.

    :raises: SystemExit
    """
    try:
        sep_xios_server = run_desc['output']['separate XIOS server']
    except KeyError:
        log.error(
            'separate XIOS server key/value not found in output section '
            'of YAML run description file. '
            'Please add lines like:\n'
            '  separate XIOS server: True\n'
            '  XIOS servers: 1\n'
            'that say whether to run the XIOS server(s) attached or detached, '
            'and how many of them to use.'
        )
        _remove_run_dir(run_dir)
        raise SystemExit(2)
    tree = xml.etree.ElementTree.parse('iodef.xml')
    root = tree.getroot()
    using_server = root.find(
        'context[@id="xios"]//variable[@id="using_server"]'
    )
    using_server.text = 'true' if sep_xios_server else 'false'
    using_server_line = xml.etree.ElementTree.tostring(using_server).decode()
    with open('iodef.xml', 'rt') as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        if 'using_server' in line:
            lines[i] = using_server_line
            break
    with open('iodef.xml', 'wt') as f:
        f.writelines(lines)


def _make_executable_links(
    nemo_code_repo,
    nemo_bin_dir,
    run_dir,
    nemo34,
    xios_code_repo,
    xios_bin_dir,
):
    """Create symlinks in run_dir to the NEMO and I/O server executables
    and record the code repository revision(s) used for the run.

    The NEMO code revision record is the output of the
    :command:`hg parents` in the NEMO code repo.
    It is stored in the :file:`NEMO-code_rev.txt` file in run_dir.

    For NEMO-3.6 runs the XIOS code revision record is the output of the
    :command:`hg parents` in the XIOS code repo.
    It is stored in the :file:`XIOS-code_rev.txt` file in run_dir.

    :arg str nemo_code_repo: Absolute path of NEMO code repo.

    :arg str nemo_bin_dir: Absolute path of directory containing NEMO
                           executable.

    :arg str run_dir: Path of the temporary run directory.

    :arg boolean nemo34: Make executable links for a NEMO-3.4 run
                         if :py:obj:`True`,
                         otherwise make links for a NEMO-3.6 run.

    :arg str xios_code_repo: Absolute path of XIOS code repo.

    :arg str xios_bin_dir: Absolute path of directory containing XIOS
                           executable.
    """
    nemo_exec = os.path.join(nemo_bin_dir, 'nemo.exe')
    saved_cwd = os.getcwd()
    os.chdir(run_dir)
    os.symlink(nemo_exec, 'nemo.exe')
    with open('NEMO-code_rev.txt', 'wt') as f:
        f.writelines(hg.parents(nemo_code_repo, verbose=True))
    iom_server_exec = os.path.join(nemo_bin_dir, 'server.exe')
    if nemo34 and os.path.exists(iom_server_exec):
        os.symlink(iom_server_exec, 'server.exe')
    if not nemo34:
        xios_server_exec = os.path.join(xios_bin_dir, 'xios_server.exe')
        os.symlink(xios_server_exec, 'xios_server.exe')
        with open('XIOS-code_rev.txt', 'wt') as f:
            f.writelines(hg.parents(xios_code_repo, verbose=True))
    os.chdir(saved_cwd)


def _make_grid_links(run_desc, run_dir):
    """Create symlinks in run_dir to the file names that NEMO expects
    to the bathymetry and coordinates files given in the run_desc dict.

    :arg dict run_desc: Run description dictionary.

    :arg str run_dir: Path of the temporary run directory.

    :raises: SystemExit
    """
    nemo_forcing_dir = os.path.abspath(run_desc['paths']['forcing'])
    if not os.path.exists(nemo_forcing_dir):
        log.error(
            '{} not found; cannot create symlinks - '
            'please check the forcing path in your run description file'
            .format(nemo_forcing_dir)
        )
        _remove_run_dir(run_dir)
        raise SystemExit(2)
    grid_dir = os.path.join(nemo_forcing_dir, 'grid')
    grid_files = (
        (run_desc['grid']['coordinates'], 'coordinates.nc'),
        (run_desc['grid']['bathymetry'], 'bathy_meter.nc'),
    )
    saved_cwd = os.getcwd()
    os.chdir(run_dir)
    for source, link_name in grid_files:
        link_path = os.path.join(grid_dir, source)
        if not os.path.exists(link_path):
            log.error(
                '{} not found; cannot create symlink - '
                'please check the forcing path and grid file names '
                'in your run description file'.format(link_path)
            )
            _remove_run_dir(run_dir)
            raise SystemExit(2)
        os.symlink(link_path, link_name)
    os.chdir(saved_cwd)


def _make_forcing_links(run_desc, run_dir, nemo34, nocheck_init):
    """Create symlinks in run_dir to the forcing directory/file names,
    and record the NEMO-forcing repo revision used for the run.

    The NEMO-forcing revision record is the output of the
    :command:`hg parents` in the NEMO-forcing repo.
    It is stored in the :file:`NEMO-forcing_rev.txt` file in run_dir.

    :arg dict run_desc: Run description dictionary.

    :arg str run_dir: Path of the temporary run directory.

    :arg boolean nemo34: Make forcing links for a NEMO-3.4 run
                         if :py:obj:`True`,
                         otherwise make links for a NEMO-3.6 run.

    :arg nocheck_init: Suppress initial condition link check
                       the default is to check
    :type nocheck_init: boolean

    :raises: :py:exc:`SystemExit` if the NEMO-forcing repo path does not
             exist
    """
    nemo_forcing_dir = os.path.abspath(run_desc['paths']['forcing'])
    if not os.path.exists(nemo_forcing_dir):
        log.error(
            '{} not found; cannot create symlinks - '
            'please check the forcing path in your run description file'
            .format(nemo_forcing_dir)
        )
        _remove_run_dir(run_dir)
        raise SystemExit(2)
    if nemo34:
        _make_forcing_links_nemo34(run_desc, run_dir, nocheck_init)
    else:
        _make_forcing_links_nemo36(run_desc, run_dir, nocheck_init)
    with open(os.path.join(run_dir, 'NEMO-forcing_rev.txt'), 'wt') as f:
        f.writelines(hg.parents(nemo_forcing_dir, verbose=True))


def _make_forcing_links_nemo34(run_desc, run_dir, nocheck_init):
    """For a NEMO-3.4 run, create symlinks in run_dir to the forcing
    directory/file names that the Salish Sea model uses by convention.

    :arg dict run_desc: Run description dictionary.

    :arg str run_dir: Path of the temporary run directory.

    :arg nocheck_init: Suppress initial condition link check
                       the default is to check
    :type nocheck_init: boolean

    :raises: :py:exc:`SystemExit` if a symlink target does not exist
    """
    nemo_forcing_dir = os.path.abspath(run_desc['paths']['forcing'])
    init_conditions = run_desc['forcing']['initial conditions']
    if 'restart' in init_conditions:
        ic_source = os.path.abspath(init_conditions)
        ic_link_name = os.path.join(run_dir, 'restart.nc')
    else:
        ic_source = os.path.join(nemo_forcing_dir, init_conditions)
        ic_link_name = os.path.join(run_dir, 'initial_strat')
    forcing_dirs = ((
        run_desc['forcing']['atmospheric'],
        os.path.join(run_dir, 'NEMO-atmos')
    ), (
        run_desc['forcing']['open boundaries'],
        os.path.join(run_dir, 'open_boundaries')
    ), (run_desc['forcing']['rivers'], os.path.join(run_dir, 'rivers')))
    if not os.path.exists(ic_source) and not nocheck_init:
        log.error(
            '{} not found; cannot create symlink - '
            'please check the forcing path and initial conditions file names '
            'in your run description file'.format(ic_source)
        )
        _remove_run_dir(run_dir)
        raise SystemExit(2)
    os.symlink(ic_source, ic_link_name)
    for source, link_name in forcing_dirs:
        link_path = os.path.join(nemo_forcing_dir, source)
        if not os.path.exists(link_path):
            log.error(
                '{} not found; cannot create symlink - '
                'please check the forcing paths and file names '
                'in your run description file'.format(link_path)
            )
            _remove_run_dir(run_dir)
            raise SystemExit(2)
        os.symlink(link_path, link_name)
    _check_atmos_files(run_desc, run_dir)


def _make_forcing_links_nemo36(run_desc, run_dir, nocheck_init):
    """For a NEMO-3.6 run, create symlinks in run_dir to the forcing
    directory/file names given in the run description forcing section.

    :arg dict run_desc: Run description dictionary.

    :arg str run_dir: Path of the temporary run directory.

    :arg nocheck_init: Suppress initial condition link check
                       the default is to check
    :type nocheck_init: boolean

    :raises: :py:exc:`SystemExit` if a symlink target does not exist
    """
    link_checkers = {'atmospheric': _check_atmospheric_forcing_link,}
    nemo_forcing_dir = os.path.abspath(run_desc['paths']['forcing'])
    for link_name in run_desc['forcing']:
        link_path = run_desc['forcing'][link_name]['link to']
        if not os.path.isabs(link_path):
            link_path = os.path.join(nemo_forcing_dir, link_path)
        if not os.path.exists(link_path):
            if link_name not in {
                'restart.nc', 'restart_trc.nc'
            } or not nocheck_init:
                log.error(
                    '{} not found; cannot create symlink - '
                    'please check the forcing paths and file names '
                    'in your run description file'.format(link_path)
                )
                _remove_run_dir(run_dir)
                raise SystemExit(2)
        os.symlink(link_path, os.path.join(run_dir, link_name))
        try:
            link_checker = run_desc['forcing'][link_name]['check link']
            link_checkers[link_checker['type']](
                run_desc, run_dir, link_path, link_checker['namelist filename']
            )
        except KeyError:
            if 'check link' not in run_desc['forcing'][link_name]:
                # No forcing link checker specified
                pass
            else:
                if link_checker is not None:
                    log.error(
                        'unknown forcing link checker: {}'
                        .format(link_checker)
                    )
                    _remove_run_dir(run_dir)
                    raise SystemExit(2)


def _check_atmospheric_forcing_link(
    run_desc,
    run_dir,
    link_path,
    namelist_filename,
):
    """Confirm that the atmospheric forcing files necessary for the run
    are present.

    Sections of the namelist file are parsed to determine
    the necessary files, and the date ranges required for the run.
    """
    namelist = namelist2dict(os.path.join(run_dir, namelist_filename))
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
                        v['dir'],
                        '{basename}_'
                        'y{date.year}m{date.month:02d}d{date.day:02d}.nc'
                        .format(
                            basename=basename, date=r
                        )
                    )
                elif period == 'yearly':
                    file_path = os.path.join(
                        v['dir'], '{basename}.nc'.format(basename=basename)
                    )
                if not os.path.exists(os.path.join(run_dir, file_path)):
                    log.error(
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
                    _remove_run_dir(run_dir)
                    raise SystemExit(2)


def _check_atmos_files(run_desc, run_dir):
    """Confirm that the atmospheric forcing files necessary for the run
    are present. Sections of the namelist file are parsed to determine
    the necessary files, and the date ranges required for the run.

    :arg dict run_desc: Run description dictionary.

    :arg str run_dir: Path of the temporary run directory.

    :raises: SystemExit
    """
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
                        v['dir'],
                        '{basename}_'
                        'y{date.year}m{date.month:02d}d{date.day:02d}.nc'
                        .format(
                            basename=basename, date=r
                        )
                    )
                elif period == 'yearly':
                    file_path = os.path.join(
                        v['dir'], '{basename}.nc'.format(basename=basename)
                    )
                if not os.path.exists(os.path.join(run_dir, file_path)):
                    nemo_forcing_dir = os.path.abspath(
                        run_desc['paths']['forcing']
                    )
                    atmos_dir = run_desc['forcing']['atmospheric']
                    log.error(
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
                            dir=os.path.join(nemo_forcing_dir, atmos_dir),
                        )
                    )
                    _remove_run_dir(run_dir)
                    raise SystemExit(2)


# All of the namelists that NEMO-3.4 requires, but empty so that they result
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
