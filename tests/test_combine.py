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

"""SalishSeaCmd combine sub-command plug-in unit tests
"""
from __future__ import absolute_import

import cliff.app
from mock import (
    Mock,
    patch,
)
import pytest

from salishsea_cmd import combine


@pytest.fixture
def combine_app():
    import salishsea_cmd.combine
    return salishsea_cmd.combine.Combine(Mock(spec=cliff.app.App), [])


def test_get_parser(combine_app):
    parser = combine_app.get_parser('salishsea combine')
    assert parser.prog == 'salishsea combine'


@patch('salishsea_cmd.combine.os.path.realpath')
@patch('salishsea_cmd.combine.os.path.lexists')
def test_find_rebuild_nemo_script_found(mock_lexists, mock_realpath):
    """_find_rebuild_nemo_exec returns script name if executable exists
    """
    mock_realpath.return_value = (
        'NEMO-code/NEMOGCM/CONFIG/SalishSea/BLD/bin/nemo.exe')
    mock_lexists.return_value = True
    script = combine._find_rebuild_nemo_script()
    assert script == 'NEMO-code/NEMOGCM/TOOLS/REBUILD_NEMO/rebuild_nemo'


@patch('salishsea_cmd.combine.log.error')
@patch('salishsea_cmd.combine.os.path.lexists')
def test_find_rebuild_nemo_script_not_found(mock_lexists, mock_log):
    """_find_rebuild_nemo_exec logs error if executable not found
    """
    mock_lexists.return_value = False
    with pytest.raises(SystemExit):
        combine._find_rebuild_nemo_script()
    assert mock_log.called


@patch('salishsea_cmd.combine.glob.glob')
def test_get_results_files(mock_glob):
    """_get_results_files returns list of name-roots and count of files
    """
    mock_glob.side_effect = (
        ['foo_0000.nc', 'bar_0000.nc'],
        ['foo_0000.nc', 'foo_0001.nc', 'foo_0002.nc'],
    )
    args = Mock(delete_restart=False)
    name_roots, ncores = combine._get_results_files(args)
    assert name_roots == ['foo', 'bar']
    assert ncores == 3


@patch('salishsea_cmd.combine.log.error')
def test_get_results_files_none_found(mock_log):
    """_get_results_files logs error if no results files exists
    """
    args = Mock(delete_restart=False)
    with pytest.raises(SystemExit):
        combine._get_results_files(args)
    assert mock_log.called


@patch('salishsea_cmd.combine.glob.glob')
@patch('salishsea_cmd.combine.os.remove')
def test_get_results_files_delete_restart(mock_rm, mock_glob):
    """_get_results_files deletes restart files
    """
    mock_glob.side_effect = (
        ['baz_restart_0000.nc', 'baz_restart_0001.nc'],
        ['foo_0000.nc', 'bar_0000.nc'],
        ['foo_0000.nc', 'foo_0001.nc', 'foo_0002.nc'],
    )
    args = Mock(delete_restart=True)
    combine._get_results_files(args)
    assert mock_rm.call_count == 2


@patch('salishsea_cmd.combine.subprocess.check_output')
def test_combine_results_files(mock_chk_out):
    """_combine_results_files calls subprocess.check_output for each name-root
    """
    combine._combine_results_files(
        'rebuild_nemo', ['foo', 'bar'], 16)
    assert mock_chk_out.call_count == 2


@patch('salishsea_cmd.combine.os.renames')
def test_move_results_pwd(mock_renames):
    """_move_results does nothing if results_dir is pwd
    """
    combine._move_results(['foo'], './')
    assert not mock_renames.called


@patch('salishsea_cmd.combine.os.renames')
def test_move_results_renames(mock_renames):
    """_move_results calls os.renames for each results file
    """
    combine._move_results(['foo', 'bar'], 'baz')
    assert mock_renames.call_count == 2


def test_result_files():
    """_results_files generator yields name-root with .nc appended
    """
    fn = next(combine._results_files(['foo', 'bar']))
    assert fn == 'foo.nc'


@patch('salishsea_cmd.combine._results_files')
def test_compress_results_no_compress(mock_res_files):
    """_compress_results does nothing when args.no_compress is False
    """
    args = Mock(no_compress=True)
    combine._compress_results(['foo', 'bar'], args)
    assert not mock_res_files.called
