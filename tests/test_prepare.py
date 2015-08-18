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
from __future__ import absolute_import

import os
from unittest.mock import (
    call,
    patch,
    Mock,
)

import cliff.app
import pytest

from salishsea_cmd import prepare


@pytest.fixture
def prepare_cmd():
    import salishsea_cmd.prepare
    return salishsea_cmd.prepare.Prepare(Mock(spec=cliff.app.App), [])


def test_get_parser(prepare_cmd):
    parser = prepare_cmd.get_parser('salishsea prepare')
    assert parser.prog == 'salishsea prepare'


@patch('salishsea_cmd.prepare.shutil.copy2')
def test_copy_run_set_files_no_path(m_copy):
    """_copy_run_set_files creates correct symlink for source w/o path
    """
    desc_file = 'foo.yaml'
    pwd = os.getcwd()
    with patch('salishsea_cmd.prepare.os.chdir'):
        prepare._copy_run_set_files(desc_file, pwd, 'iodef.xml', 'run_dir')
    expected = [
        call(os.path.join(pwd, 'iodef.xml'), 'iodef.xml'),
        call(os.path.join(pwd, 'foo.yaml'), 'foo.yaml'),
        call(os.path.join(pwd, 'xmlio_server.def'), 'xmlio_server.def'),
    ]
    assert m_copy.call_args_list == expected


@patch('salishsea_cmd.prepare.shutil.copy2')
def test_copy_run_set_files_relative_path(m_copy):
    """_copy_run_set_files creates correct symlink for relative path source
    """
    desc_file = 'foo.yaml'
    pwd = os.getcwd()
    with patch('salishsea_cmd.prepare.os.chdir'):
        prepare._copy_run_set_files(desc_file, pwd, '../iodef.xml', 'run_dir')
    expected = [
        call(os.path.join(os.path.dirname(pwd), 'iodef.xml'), 'iodef.xml'),
        call(os.path.join(pwd, 'foo.yaml'), 'foo.yaml'),
        call(os.path.join(pwd, 'xmlio_server.def'), 'xmlio_server.def'),
    ]
    assert m_copy.call_args_list == expected


@patch('salishsea_cmd.prepare.log')
def test_make_grid_links_no_forcing_dir(m_log):
    run_desc = {
        'paths': {
            'forcing': 'foo',
        },
    }
    prepare._remove_run_dir = Mock()
    p_exists = patch(
        'salishsea_cmd.prepare.os.path.exists', return_value=False)
    p_abspath = patch(
        'salishsea_cmd.prepare.os.path.abspath',
        side_effect=lambda path: path)
    with pytest.raises(SystemExit), p_exists, p_abspath:
        prepare._make_grid_links(run_desc, 'run_dir')
    m_log.error.assert_called_once_with(
        'foo not found; cannot create symlinks - '
        'please check the forcing path in your run description file')
    prepare._remove_run_dir.assert_called_once_with('run_dir')


@patch('salishsea_cmd.prepare.log')
def test_make_grid_links_no_link_path(m_log):
    run_desc = {
        'paths': {
            'forcing': 'foo',
        },
        'grid': {
            'coordinates': 'coordinates.nc',
            'bathymetry': 'bathy.nc',
        },
    }
    prepare._remove_run_dir = Mock()
    p_exists = patch(
        'salishsea_cmd.prepare.os.path.exists',
        side_effect=[True, False])
    p_abspath = patch(
        'salishsea_cmd.prepare.os.path.abspath',
        side_effect=lambda path: path)
    p_chdir = patch('salishsea_cmd.prepare.os.chdir')
    with pytest.raises(SystemExit), p_exists, p_abspath, p_chdir:
        prepare._make_grid_links(run_desc, 'run_dir')
    m_log.error.assert_called_once_with(
        'foo/grid/coordinates.nc not found; cannot create symlink - '
        'please check the forcing path and grid file names '
        'in your run description file')
    prepare._remove_run_dir.assert_called_once_with('run_dir')


@patch('salishsea_cmd.prepare.log')
def test_make_forcing_links_no_forcing_dir(m_log):
    run_desc = {
        'paths': {
            'forcing': 'foo',
        },
    }
    prepare._remove_run_dir = Mock()
    p_exists = patch(
        'salishsea_cmd.prepare.os.path.exists', return_value=False)
    p_abspath = patch(
        'salishsea_cmd.prepare.os.path.abspath',
        side_effect=lambda path: path)
    with pytest.raises(SystemExit), p_exists, p_abspath:
        prepare._make_forcing_links(run_desc, 'run_dir')
    m_log.error.assert_called_once_with(
        'foo not found; cannot create symlinks - '
        'please check the forcing path in your run description file')
    prepare._remove_run_dir.assert_called_once_with('run_dir')


@pytest.mark.parametrize(
    'link_path, expected',
    [
        ('SalishSea_00475200_restart.nc', 'SalishSea_00475200_restart.nc'),
        ('initial_strat/', 'foo/initial_strat/'),
    ],
)
@patch('salishsea_cmd.prepare.log')
def test_make_forcing_links_no_restart_path(m_log, link_path, expected):
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
    prepare._remove_run_dir = Mock()
    p_exists = patch(
        'salishsea_cmd.prepare.os.path.exists',
        side_effect=[True, False])
    p_abspath = patch(
        'salishsea_cmd.prepare.os.path.abspath',
        side_effect=lambda path: path)
    p_chdir = patch('salishsea_cmd.prepare.os.chdir')
    with pytest.raises(SystemExit), p_exists, p_abspath, p_chdir:
        prepare._make_forcing_links(run_desc, 'run_dir')
    m_log.error.assert_called_once_with(
        '{} not found; cannot create symlink - '
        'please check the forcing path and initial conditions file names '
        'in your run description file'.format(expected))
    prepare._remove_run_dir.assert_called_once_with('run_dir')


@patch('salishsea_cmd.prepare.log')
def test_make_forcing_links_no_forcing_path(m_log):
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
    prepare._remove_run_dir = Mock()
    p_exists = patch(
        'salishsea_cmd.prepare.os.path.exists',
        side_effect=[True, True, False])
    p_abspath = patch(
        'salishsea_cmd.prepare.os.path.abspath',
        side_effect=lambda path: path)
    p_chdir = patch('salishsea_cmd.prepare.os.chdir')
    p_symlink = patch('salishsea_cmd.prepare.os.symlink')
    with pytest.raises(SystemExit), p_exists, p_abspath, p_chdir, p_symlink:
        prepare._make_forcing_links(run_desc, 'run_dir')
    m_log.error.assert_called_once_with(
        'foo/bar not found; cannot create symlink - '
        'please check the forcing paths and file names '
        'in your run description file')
    prepare._remove_run_dir.assert_called_once_with('run_dir')
