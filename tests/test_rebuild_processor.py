"""Salish Sea NEMO results rebuild sub-command processor unit tests


Copyright 2013 Doug Latornell and The University of British Columbia

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
from mock import patch
import pytest
from salishsea_cmd import rebuild_processor


@patch('salishsea_cmd.rebuild_processor.os.path.lexists')
def test_find_rebuild_nemo_script_found(mock_lexists):
    """_find_rebuild_nemo_exec returns script name if executable exists
    """
    mock_lexists.return_value = True
    script = rebuild_processor._find_rebuild_nemo_script('NEMO-code')
    assert script == 'NEMO-code/NEMOGCM/TOOLS/REBUILD_NEMO/rebuild_nemo'


@patch('salishsea_cmd.rebuild_processor.log.error')
@patch('salishsea_cmd.rebuild_processor.os.path.lexists')
def test_find_rebuild_nemo_script_not_found(mock_lexists, mock_log):
    """_find_rebuild_nemo_exec logs error if executable not found
    """
    mock_lexists.return_value = False
    with pytest.raises(SystemExit):
        rebuild_processor._find_rebuild_nemo_script('NEMO-code')
    assert mock_log.called


@patch('salishsea_cmd.rebuild_processor.glob.glob')
def test_get_results_files(mock_glob):
    """_get_results_files returns list of name-roots and count of files
    """
    mock_glob.side_effect = (
        ['foo_0000.nc', 'bar_0000.nc'],
        ['foo_0000.nc', 'foo_0001.nc', 'foo_0002.nc'],
    )
    name_roots, ncores = rebuild_processor._get_results_files()
    assert name_roots == ['foo', 'bar']
    assert ncores == 3


@patch('salishsea_cmd.rebuild_processor.log.error')
def test_get_results_files_none_found(mock_log):
    """_get_results_files logs error if no results files exists
    """
    with pytest.raises(SystemExit):
        rebuild_processor._get_results_files()
    assert mock_log.called
