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

"""SalishSeaCmd combine sub-command plug-in unit tests
"""
from unittest.mock import (
    Mock,
    patch,
)

import cliff.app
import pytest


@pytest.fixture(scope='module')
def combine_module():
    from salishsea_cmd import combine
    return combine


@pytest.fixture
def combine_cmd():
    import salishsea_cmd.combine
    return salishsea_cmd.combine.Combine(Mock(spec=cliff.app.App), [])


def test_get_parser(combine_cmd):
    parser = combine_cmd.get_parser('salishsea combine')
    assert parser.prog == 'salishsea combine'


@patch.object(combine_module().os.path, 'realpath')
@patch.object(combine_module().os.path, 'lexists')
def test_find_rebuild_nemo_script_found(
        mock_lexists, mock_realpath, combine_module,
):
    """_find_rebuild_nemo_exec returns script name if executable exists
    """
    mock_realpath.return_value = (
        'NEMO-code/NEMOGCM/CONFIG/SalishSea/BLD/bin/nemo.exe')
    mock_lexists.return_value = True
    script = combine_module._find_rebuild_nemo_script()
    assert script == 'NEMO-code/NEMOGCM/TOOLS/REBUILD_NEMO/rebuild_nemo'


@patch.object(combine_module().log, 'error')
@patch.object(combine_module().os.path, 'lexists')
def test_find_rebuild_nemo_script_not_found(
    mock_lexists, mock_log, combine_module,
):
    """_find_rebuild_nemo_exec logs error if executable not found
    """
    mock_lexists.return_value = False
    with pytest.raises(SystemExit):
        combine_module._find_rebuild_nemo_script()
    assert mock_log.called


@patch.object(combine_module().glob, 'glob')
def test_get_results_files(mock_glob, combine_module):
    """_get_results_files returns list of name-roots and count of files
    """
    mock_glob.side_effect = (
        ['foo_0000.nc', 'bar_0000.nc'],
        ['foo_0000.nc', 'foo_0001.nc', 'foo_0002.nc'],
    )
    args = Mock(delete_restart=False)
    name_roots = combine_module._get_results_files(args)
    assert name_roots == ['foo', 'bar']


@patch.object(combine_module().log, 'error')
def test_get_results_files_none_found(mock_log, combine_module):
    """_get_results_files logs error if no results files exists
    """
    args = Mock(delete_restart=False)
    with pytest.raises(SystemExit):
        combine_module._get_results_files(args)
    assert mock_log.called


@patch.object(combine_module().glob, 'glob')
@patch.object(combine_module().os, 'remove')
def test_get_results_files_delete_restart(mock_rm, mock_glob, combine_module):
    """_get_results_files deletes restart files
    """
    mock_glob.side_effect = (
        ['baz_restart_0000.nc', 'baz_restart_0001.nc'],
        ['foo_0000.nc', 'bar_0000.nc'],
        ['foo_0000.nc', 'foo_0001.nc', 'foo_0002.nc'],
    )
    args = Mock(delete_restart=True)
    combine_module._get_results_files(args)
    assert mock_rm.call_count == 2


@patch.object(combine_module().glob, 'glob')
@patch.object(combine_module().subprocess, 'check_output')
def test_combine_results_files(mock_chk_out, mock_glob, combine_module):
    """_combine_results_files calls subprocess.check_output for each name-root
    """
    mock_glob.side_effect = (
        ['foo_0000.nc', 'foo_0001.nc', 'foo_0002.nc'],
        ['bar_0000.nc', 'bar_0001.nc', 'bar_0002.nc'],
    )
    combine_module._combine_results_files(
        'rebuild_nemo', ['foo', 'bar'], 3)
    assert mock_chk_out.call_count == 2


@patch.object(combine_module().lib, 'netcdf4_deflate')
def test_netcdf4_deflate_results(mock_nc4_dfl, combine_module):
    """_netcdf4_deflate_results calls lib.netcdf4_deflate per name-root
    """
    combine_module._netcdf4_deflate_results(['foo', 'bar'])
    assert mock_nc4_dfl.call_count == 2


@patch.object(combine_module().shutil, 'move')
def test_move_results_pwd(mock_move, combine_module):
    """_move_results does nothing if results_dir is pwd
    """
    combine_module._move_results(['foo'], './')
    assert not mock_move.called


@patch.object(combine_module().shutil, 'move')
@patch.object(combine_module().os, 'makedirs')
def test_move_results_makedirs(mock_makedirs, mock_move, combine_module):
    """_move_results creates results_dir if it doesn't exist
    """
    combine_module._move_results(['foo', 'bar'], 'baz')
    assert mock_makedirs.called


@patch.object(combine_module().os, 'makedirs')
@patch.object(combine_module().shutil, 'move')
def test_move_results_renames(mock_move, mock_makedirs, combine_module):
    """_move_results calls shutil.move for each results file
    """
    combine_module._move_results(['foo', 'bar'], 'baz')
    assert mock_move.call_count == 2


def test_result_files(combine_module):
    """_results_files generator yields name-root with .nc appended
    """
    fn = next(combine_module._results_files(['foo', 'bar']))
    assert fn == 'foo.nc'


@patch.object(combine_module(), '_results_files')
def test_compress_results_no_compress(mock_res_files, combine_module):
    """_compress_results does nothing when args.compress is False
    """
    args = Mock(compress=False)
    combine_module._compress_results(['foo', 'bar'], args)
    assert not mock_res_files.called
