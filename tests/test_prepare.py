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

"""SalishSeaCmd prepare sub-command plug-in unit tests
"""
import os
from unittest.mock import (
    call,
    patch,
    Mock,
)

import cliff.app
import pytest


@pytest.fixture
def prepare_module():
    from salishsea_cmd import prepare
    return prepare


@pytest.fixture
def prepare_cmd(prepare_module):
    return prepare_module.Prepare(Mock(spec=cliff.app.App), [])


class TestGetParser:
    """Unit tests for `salishsea prepare` sub-command command-line parser.
    """
    def test_get_parser(self, prepare_cmd):
        parser = prepare_cmd.get_parser('salishsea prepare')
        assert parser.prog == 'salishsea prepare'

    def test_parsed_args_defaults(self, prepare_cmd):
        parser = prepare_cmd.get_parser('salishsea prepare')
        parsed_args = parser.parse_args(['foo', 'bar'])
        assert parsed_args.desc_file == 'foo'
        assert parsed_args.iodefs == 'bar'
        assert not parsed_args.nemo34
        assert not parsed_args.quiet

    def test_parsed_args_nemo34(self, prepare_cmd):
        parser = prepare_cmd.get_parser('salishsea prepare')
        parsed_args = parser.parse_args(['foo', 'bar', '--nemo3.4'])
        assert parsed_args.desc_file == 'foo'
        assert parsed_args.iodefs == 'bar'
        assert parsed_args.nemo34

    def test_parsed_args_quiet(self, prepare_cmd):
        parser = prepare_cmd.get_parser('salishsea prepare')
        parsed_args = parser.parse_args(['foo', 'bar', '-q'])
        assert parsed_args.desc_file == 'foo'
        assert parsed_args.iodefs == 'bar'
        assert parsed_args.quiet


class TestPrepare:
    """Unit tests for `salishsea prepare` prepare() function.
    """
    @patch.object(prepare_module().lib, 'load_run_desc')
    @patch.object(
        prepare_module(), '_check_nemo_exec', return_value=('repo', 'bin_dir'))
    @patch.object(prepare_module(), '_check_xios_exec')
    @patch.object(prepare_module().os.path, 'dirname')
    @patch.object(prepare_module(), '_make_run_dir')
    @patch.object(prepare_module(), '_make_namelist')
    @patch.object(prepare_module(), '_copy_run_set_files')
    @patch.object(prepare_module(), '_make_nemo_code_links')
    @patch.object(prepare_module(), '_make_grid_links')
    @patch.object(prepare_module(), '_make_forcing_links')
    @patch.object(prepare_module(), '_check_atmos_files')
    def test_prepare_nemo34(
        self, m_caf, m_mfl, m_mgl, m_mncl, m_crsf, m_mnl, m_mrd, m_dirname,
        m_cxe, m_cne, m_lrd, prepare_module,
    ):
        run_dir = prepare_module.prepare(
            'SalishSea.yaml', 'iodefs.xml', nemo34=True)
        m_lrd.assert_called_once_with('SalishSea.yaml')
        m_cne.assert_called_once_with(m_lrd(), True)
        assert not m_cxe.called
        m_dirname.assert_called_once_with(os.path.abspath('SalishSea.yaml'))
        m_mrd.assert_called_once_with(m_lrd())
        m_mnl.assert_called_once_with(m_dirname(), m_lrd(), m_mrd(), True)
        m_crsf.assert_called_once_with(
            'SalishSea.yaml', m_dirname(), 'iodefs.xml', m_mrd(), True)
        m_mncl.assert_called_once_with('repo', 'bin_dir', m_mrd())
        m_mgl.assert_called_once_with(m_lrd(), m_mrd())
        m_mfl.assert_called_once_with(m_lrd(), m_mrd())
        m_caf.assert_called_once_with(m_lrd(), m_mrd())
        assert run_dir == m_mrd()

    @patch.object(prepare_module().lib, 'load_run_desc')
    @patch.object(
        prepare_module(), '_check_nemo_exec', return_value=('repo', 'bin_dir'))
    @patch.object(prepare_module(), '_check_xios_exec')
    @patch.object(prepare_module().os.path, 'dirname')
    @patch.object(prepare_module(), '_make_run_dir')
    @patch.object(prepare_module(), '_make_namelist')
    @patch.object(prepare_module(), '_copy_run_set_files')
    @patch.object(prepare_module(), '_make_nemo_code_links')
    @patch.object(prepare_module(), '_make_grid_links')
    @patch.object(prepare_module(), '_make_forcing_links')
    @patch.object(prepare_module(), '_check_atmos_files')
    def test_prepare_nemo36(
        self, m_caf, m_mfl, m_mgl, m_mncl, m_crsf, m_mnl, m_mrd, m_dirname,
        m_cxe, m_cne, m_lrd, prepare_module,
    ):
        run_dir = prepare_module.prepare(
            'SalishSea.yaml', 'iodefs.xml', nemo34=False)
        m_lrd.assert_called_once_with('SalishSea.yaml')
        m_cne.assert_called_once_with(m_lrd(), False)
        m_cxe.assert_called_once_with(m_lrd())
        m_dirname.assert_called_once_with(os.path.abspath('SalishSea.yaml'))
        m_mrd.assert_called_once_with(m_lrd())
        m_mnl.assert_called_once_with(m_dirname(), m_lrd(), m_mrd(), False)
        m_crsf.assert_called_once_with(
            'SalishSea.yaml', m_dirname(), 'iodefs.xml', m_mrd(), False)
        m_mncl.assert_called_once_with('repo', 'bin_dir', m_mrd())
        m_mgl.assert_called_once_with(m_lrd(), m_mrd())
        m_mfl.assert_called_once_with(m_lrd(), m_mrd())
        m_caf.assert_called_once_with(m_lrd(), m_mrd())
        assert run_dir == m_mrd()


class TestCheckNemoExec:
    """Unit tests for `salishsea prepare` _check_nemo_exec() function.
    """
    def test_nemo_code_repo_path(self, prepare_module, tmpdir):
        p_code = tmpdir.ensure_dir('NEMO-3.6-code')
        run_desc = {
            'config_name': 'SalishSea',
            'paths': {'NEMO-code': str(p_code)},
        }
        with patch.object(prepare_module.os.path, 'exists', return_value=True):
            nemo_code_repo, nemo_bin_dir = prepare_module._check_nemo_exec(
                run_desc, nemo34=False)
        assert nemo_code_repo == p_code

    def test_nemo_bin_dir_path(self, prepare_module, tmpdir):
        p_code = tmpdir.ensure_dir('NEMO-3.6-code')
        run_desc = {
            'config_name': 'SalishSea',
            'paths': {'NEMO-code': str(p_code)},
        }
        p_bin_dir = p_code.ensure_dir(
            'NEMOGCM', 'CONFIG', 'SalishSea', 'BLD', 'bin')
        with patch.object(prepare_module.os.path, 'exists', return_value=True):
            nemo_code_repo, nemo_bin_dir = prepare_module._check_nemo_exec(
                run_desc, nemo34=False)
        assert nemo_bin_dir == p_bin_dir

    def test_nemo_exec_not_found(self, prepare_module, tmpdir):
        p_code = tmpdir.ensure_dir('NEMO-3.6-code')
        run_desc = {
            'config_name': 'SalishSea',
            'paths': {'NEMO-code': str(p_code)},
        }
        with pytest.raises(SystemExit):
            prepare_module._check_nemo_exec(run_desc, nemo34=False)

    @patch.object(prepare_module(), 'log')
    def test_iom_server_exec_not_found(self, m_log, prepare_module, tmpdir):
        p_code = tmpdir.ensure_dir('NEMO-3.6-code')
        run_desc = {
            'config_name': 'SalishSea',
            'paths': {'NEMO-code': str(p_code)},
        }
        p_bin_dir = p_code.ensure_dir(
            'NEMOGCM', 'CONFIG', 'SalishSea', 'BLD', 'bin')
        p_exists = patch.object(
            prepare_module.os.path, 'exists', side_effect=[True, False])
        with p_exists:
            nemo_code_repo, nemo_bin_dir = prepare_module._check_nemo_exec(
                run_desc, nemo34=True)
        m_log.warn.assert_called_once_with(
            '{}/server.exe not found - are you running without key_iomput?'
            .format(p_bin_dir))

    def test_nemo36_no_iom_server_check(self, prepare_module, tmpdir):
        p_code = tmpdir.ensure_dir('NEMO-3.6-code')
        run_desc = {
            'config_name': 'SalishSea',
            'paths': {'NEMO-code': str(p_code)},
        }
        p_code.ensure_dir(
            'NEMOGCM', 'CONFIG', 'SalishSea', 'BLD', 'bin')
        with patch.object(prepare_module.os.path, 'exists') as m_exists:
            nemo_code_repo, nemo_bin_dir = prepare_module._check_nemo_exec(
                run_desc, nemo34=False)
        assert m_exists.call_count == 1


class TestCheckXiosExec:
    """Unit tests for `salishsea prepare` _check_xios_exec() function.
    """
    def test_xios_bin_dir_path(self, prepare_module, tmpdir):
        p_xios = tmpdir.ensure_dir('XIOS')
        run_desc = {
            'paths': {'XIOS': str(p_xios)},
        }
        p_bin_dir = p_xios.ensure_dir('bin')
        p_bin_dir.ensure('xios_server.exe')
        xios_bin_dir = prepare_module._check_xios_exec(run_desc)
        assert xios_bin_dir == p_bin_dir

    def test_xios_exec_not_found(self, prepare_module, tmpdir):
        p_xios = tmpdir.ensure_dir('XIOS')
        run_desc = {
            'paths': {'XIOS': str(p_xios)},
        }
        with pytest.raises(SystemExit):
            prepare_module._check_xios_exec(run_desc)


class TestMakeRunDir:
    """Unit test for `salishsea prepare` _make_run_dir() function.
    """
    @patch.object(prepare_module().uuid, 'uuid1', return_value='uuid')
    def test_make_run_dir(self, m_uuid1, prepare_module, tmpdir):
        """_make_run_dir() creates directory w/ UUID v1 name
        """
        p_runs_dir = tmpdir.ensure_dir('SalishSea')
        run_desc = {
            'paths': {'runs directory': str(p_runs_dir)},
        }
        run_dir = prepare_module._make_run_dir(run_desc)
        assert run_dir == os.path.join(str(p_runs_dir), m_uuid1())


class TestRemoveRunDir:
    """Unit tests for `salishsea prepare` _remove_run_dir() function.
    """
    def test_remove_run_dir(self, prepare_module, tmpdir):
        p_run_dir = tmpdir.ensure_dir('run_dir')
        prepare_module._remove_run_dir(str(p_run_dir))
        assert not p_run_dir.check()

    def test_remove_run_dir_file(self, prepare_module, tmpdir):
        p_run_dir = tmpdir.ensure_dir('run_dir')
        p_run_dir.ensure('namelist')
        prepare_module._remove_run_dir(str(p_run_dir))
        assert not p_run_dir.join('namelist').check()
        assert not p_run_dir.check()

    @patch.object(prepare_module().os, 'rmdir')
    def test_remove_run_dir_no_run_dir(self, m_rmdir, prepare_module, tmpdir):
        prepare_module._remove_run_dir('run_dir')
        assert not m_rmdir.called


class TestMakeNamelist:
    """Unit tests for `salishsea prepare` _make_namelist() function.
    """
    @pytest.mark.parametrize('nemo34, namelist_filename', [
        (True, 'namelist'),
        (False, 'namelist_cfg'),
    ])
    def test_make_namelist(
        self, nemo34, namelist_filename, prepare_module, tmpdir,
    ):
        p_run_set_dir = tmpdir.ensure_dir('run_set_dir')
        p_run_set_dir.join('namelist.time').write('&namrun\n&end\n')
        run_desc = {
            'namelists': [
                str(p_run_set_dir.join('namelist.time')),
            ],
        }
        p_run_dir = tmpdir.ensure_dir('run_dir')
        prepare_module._make_namelist(
            str(p_run_set_dir), run_desc, str(p_run_dir), nemo34)
        assert p_run_dir.join(namelist_filename).check()

    @pytest.mark.parametrize('nemo34', [True, False])
    def test_make_namelist_file_not_found_error(
        self, nemo34, prepare_module, tmpdir,
    ):
        p_run_set_dir = tmpdir.ensure_dir('run_set_dir')
        run_desc = {
            'namelists': [
                str(p_run_set_dir.join('namelist.time')),
            ],
        }
        p_run_dir = tmpdir.ensure_dir('run_dir')
        with pytest.raises(SystemExit):
            prepare_module._make_namelist(
                str(p_run_set_dir), run_desc, str(p_run_dir), nemo34)

    def test_nemo34_make_namelist_ends_with_empty_namelists(
        self, prepare_module, tmpdir,
    ):
        p_run_set_dir = tmpdir.ensure_dir('run_set_dir')
        p_run_set_dir.join('namelist.time').write('&namrun\n&end\n')
        run_desc = {
            'namelists': [
                str(p_run_set_dir.join('namelist.time')),
            ],
        }
        p_run_dir = tmpdir.ensure_dir('run_dir')
        prepare_module._make_namelist(
            str(p_run_set_dir), run_desc, str(p_run_dir), nemo34=True)
        namelist = p_run_dir.join('namelist').read()
        assert namelist.endswith(prepare_module.EMPTY_NAMELISTS)

    def test_nemo36_make_namelist_does_not_end_with_empty_namelists(
        self, prepare_module, tmpdir,
    ):
        p_run_set_dir = tmpdir.ensure_dir('run_set_dir')
        p_run_set_dir.join('namelist.time').write('&namrun\n&end\n')
        run_desc = {
            'namelists': [
                str(p_run_set_dir.join('namelist.time')),
            ],
        }
        p_run_dir = tmpdir.ensure_dir('run_dir')
        prepare_module._make_namelist(
            str(p_run_set_dir), run_desc, str(p_run_dir), nemo34=False)
        namelist = p_run_dir.join('namelist_cfg').read()
        assert not namelist.endswith(prepare_module.EMPTY_NAMELISTS)


class TestCopyRunSetFiles:
    """Unit tests for `salishsea prepare` _copy_run_set_files() function.
    """
    @patch.object(prepare_module().shutil, 'copy2')
    def test_nemo34_copy_run_set_files_no_path(self, m_copy, prepare_module):
        """_copy_run_set_files creates correct symlink for source w/o path
        """
        desc_file = 'foo.yaml'
        pwd = os.getcwd()
        with patch('salishsea_cmd.prepare.os.chdir'):
            prepare_module._copy_run_set_files(
                desc_file, pwd, 'iodef.xml', 'run_dir', nemo34=True)
        expected = [
            call(os.path.join(pwd, 'iodef.xml'), 'iodef.xml'),
            call(os.path.join(pwd, 'foo.yaml'), 'foo.yaml'),
            call(os.path.join(pwd, 'xmlio_server.def'), 'xmlio_server.def'),
        ]
        assert m_copy.call_args_list == expected

    @patch.object(prepare_module().shutil, 'copy2')
    def test_nemo36_copy_run_set_files_no_path(self, m_copy, prepare_module):
        """_copy_run_set_files creates correct symlink for source w/o path
        """
        desc_file = 'foo.yaml'
        pwd = os.getcwd()
        with patch('salishsea_cmd.prepare.os.chdir'):
            prepare_module._copy_run_set_files(
                desc_file, pwd, 'iodef.xml', 'run_dir', nemo34=False)
        expected = [
            call(os.path.join(pwd, 'iodef.xml'), 'iodef.xml'),
            call(os.path.join(pwd, 'foo.yaml'), 'foo.yaml'),
        ]
        assert m_copy.call_args_list == expected

    @patch.object(prepare_module().shutil, 'copy2')
    def test_nemo34_copy_run_set_files_relative_path(
        self, m_copy, prepare_module,
    ):
        """_copy_run_set_files creates correct symlink for relative path source
        """
        desc_file = 'foo.yaml'
        pwd = os.getcwd()
        with patch.object(prepare_module.os, 'chdir'):
            prepare_module._copy_run_set_files(
                desc_file, pwd, '../iodef.xml', 'run_dir', nemo34=True)
        expected = [
            call(os.path.join(os.path.dirname(pwd), 'iodef.xml'), 'iodef.xml'),
            call(os.path.join(pwd, 'foo.yaml'), 'foo.yaml'),
            call(os.path.join(pwd, 'xmlio_server.def'), 'xmlio_server.def'),
        ]
        assert m_copy.call_args_list == expected

    @patch.object(prepare_module().shutil, 'copy2')
    def test_nemo36_copy_run_set_files_relative_path(
        self, m_copy, prepare_module,
    ):
        """_copy_run_set_files creates correct symlink for relative path source
        """
        desc_file = 'foo.yaml'
        pwd = os.getcwd()
        with patch.object(prepare_module.os, 'chdir'):
            prepare_module._copy_run_set_files(
                desc_file, pwd, '../iodef.xml', 'run_dir', nemo34=False)
        expected = [
            call(os.path.join(os.path.dirname(pwd), 'iodef.xml'), 'iodef.xml'),
            call(os.path.join(pwd, 'foo.yaml'), 'foo.yaml'),
        ]
        assert m_copy.call_args_list == expected


@patch.object(prepare_module(), 'log')
def test_make_grid_links_no_forcing_dir(m_log, prepare_module):
    run_desc = {
        'paths': {
            'forcing': 'foo',
        },
    }
    prepare_module._remove_run_dir = Mock()
    p_exists = patch.object(
        prepare_module.os.path, 'exists', return_value=False)
    p_abspath = patch.object(
        prepare_module.os.path, 'abspath', side_effect=lambda path: path)
    with pytest.raises(SystemExit), p_exists, p_abspath:
        prepare_module._make_grid_links(run_desc, 'run_dir')
    m_log.error.assert_called_once_with(
        'foo not found; cannot create symlinks - '
        'please check the forcing path in your run description file')
    prepare_module._remove_run_dir.assert_called_once_with('run_dir')


@patch.object(prepare_module(), 'log')
def test_make_grid_links_no_link_path(m_log, prepare_module):
    run_desc = {
        'paths': {
            'forcing': 'foo',
        },
        'grid': {
            'coordinates': 'coordinates.nc',
            'bathymetry': 'bathy.nc',
        },
    }
    prepare_module._remove_run_dir = Mock()
    p_exists = patch.object(
        prepare_module.os.path, 'exists', side_effect=[True, False])
    p_abspath = patch.object(
        prepare_module.os.path, 'abspath', side_effect=lambda path: path)
    p_chdir = patch.object(prepare_module.os, 'chdir')
    with pytest.raises(SystemExit), p_exists, p_abspath, p_chdir:
        prepare_module._make_grid_links(run_desc, 'run_dir')
    m_log.error.assert_called_once_with(
        'foo/grid/coordinates.nc not found; cannot create symlink - '
        'please check the forcing path and grid file names '
        'in your run description file')
    prepare_module._remove_run_dir.assert_called_once_with('run_dir')


@patch.object(prepare_module(), 'log')
def test_make_forcing_links_no_forcing_dir(m_log, prepare_module):
    run_desc = {
        'paths': {
            'forcing': 'foo',
        },
    }
    prepare_module._remove_run_dir = Mock()
    p_exists = patch.object(
        prepare_module.os.path, 'exists', return_value=False)
    p_abspath = patch.object(
        prepare_module.os.path, 'abspath', side_effect=lambda path: path)
    with pytest.raises(SystemExit), p_exists, p_abspath:
        prepare_module._make_forcing_links(run_desc, 'run_dir')
    m_log.error.assert_called_once_with(
        'foo not found; cannot create symlinks - '
        'please check the forcing path in your run description file')
    prepare_module._remove_run_dir.assert_called_once_with('run_dir')


@pytest.mark.parametrize(
    'link_path, expected',
    [
        ('SalishSea_00475200_restart.nc', 'SalishSea_00475200_restart.nc'),
        ('initial_strat/', 'foo/initial_strat/'),
    ],
)
@patch.object(prepare_module(), 'log')
def test_make_forcing_links_no_restart_path(
    m_log, link_path, expected, prepare_module,
):
    run_desc = {
        'paths': {
            'forcing': 'foo',
        },
        'forcing': {
            'atmospheric': 'bar',
            'initial conditions': link_path,
            'open boundaries': 'open_boundaries/',
            'rivers': 'rivers/',
        },
    }
    prepare_module._remove_run_dir = Mock()
    p_exists = patch.object(
        prepare_module.os.path, 'exists', side_effect=[True, False])
    p_abspath = patch.object(
        prepare_module.os.path, 'abspath', side_effect=lambda path: path)
    p_chdir = patch.object(prepare_module.os, 'chdir')
    with pytest.raises(SystemExit), p_exists, p_abspath, p_chdir:
        prepare_module._make_forcing_links(run_desc, 'run_dir')
    m_log.error.assert_called_once_with(
        '{} not found; cannot create symlink - '
        'please check the forcing path and initial conditions file names '
        'in your run description file'.format(expected))
    prepare_module._remove_run_dir.assert_called_once_with('run_dir')


@patch.object(prepare_module(), 'log')
def test_make_forcing_links_no_forcing_path(m_log, prepare_module):
    run_desc = {
        'paths': {
            'forcing': 'foo',
        },
        'forcing': {
            'atmospheric': 'bar',
            'initial conditions': 'initial_strat/',
            'open boundaries': 'open_boundaries/',
            'rivers': 'rivers/',
        },
    }
    prepare_module._remove_run_dir = Mock()
    p_exists = patch.object(
        prepare_module.os.path, 'exists', side_effect=[True, True, False])
    p_abspath = patch.object(
        prepare_module.os.path, 'abspath', side_effect=lambda path: path)
    p_chdir = patch.object(prepare_module.os, 'chdir')
    p_symlink = patch.object(prepare_module.os, 'symlink')
    with pytest.raises(SystemExit), p_exists, p_abspath, p_chdir, p_symlink:
        prepare_module._make_forcing_links(run_desc, 'run_dir')
    m_log.error.assert_called_once_with(
        'foo/bar not found; cannot create symlink - '
        'please check the forcing paths and file names '
        'in your run description file')
    prepare_module._remove_run_dir.assert_called_once_with('run_dir')
