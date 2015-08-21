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


@patch.object(prepare_module().shutil, 'copy2')
def test_copy_run_set_files_no_path(m_copy, prepare_module):
    """_copy_run_set_files creates correct symlink for source w/o path
    """
    desc_file = 'foo.yaml'
    pwd = os.getcwd()
    with patch('salishsea_cmd.prepare.os.chdir'):
        prepare_module._copy_run_set_files(
            desc_file, pwd, 'iodef.xml', 'run_dir')
    expected = [
        call(os.path.join(pwd, 'iodef.xml'), 'iodef.xml'),
        call(os.path.join(pwd, 'foo.yaml'), 'foo.yaml'),
        call(os.path.join(pwd, 'xmlio_server.def'), 'xmlio_server.def'),
    ]
    assert m_copy.call_args_list == expected


@patch.object(prepare_module().shutil, 'copy2')
def test_copy_run_set_files_relative_path(m_copy, prepare_module):
    """_copy_run_set_files creates correct symlink for relative path source
    """
    desc_file = 'foo.yaml'
    pwd = os.getcwd()
    with patch.object(prepare_module.os, 'chdir'):
        prepare_module._copy_run_set_files(
            desc_file, pwd, '../iodef.xml', 'run_dir')
    expected = [
        call(os.path.join(os.path.dirname(pwd), 'iodef.xml'), 'iodef.xml'),
        call(os.path.join(pwd, 'foo.yaml'), 'foo.yaml'),
        call(os.path.join(pwd, 'xmlio_server.def'), 'xmlio_server.def'),
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
