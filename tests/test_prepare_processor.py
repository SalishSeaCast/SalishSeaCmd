"""Salish Sea NEMO results prepare sub-command processor unit tests


Copyright 2013-2014 The Salish Sea MEOPAR Contributors
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
import os
from mock import (
    call,
    patch,
    Mock,
)
from salishsea_cmd import prepare_processor


@patch('salishsea_cmd.prepare_processor.shutil.copy2')
def test_copy_run_set_files_no_path(mock_copy):
    """_copy_run_set_files creates correct symlink for source w/o path
    """
    args = Mock(iodefs='iodef.xml')
    args.desc_file.name = 'foo'
    with patch('salishsea_cmd.prepare_processor.os.chdir'):
        prepare_processor._copy_run_set_files(args, 'bar', 'baz')
    pwd = os.getcwd()
    expected = [
        call(os.path.join(pwd, 'iodef.xml'), 'iodef.xml'),
        call(os.path.join(pwd, 'foo'), 'foo'),
        call(os.path.join(pwd, 'xmlio_server.def'), 'xmlio_server.def'),
    ]
    assert mock_copy.call_args_list == expected


@patch('salishsea_cmd.prepare_processor.shutil.copy2')
def test_copy_run_set_files_relative_path(mock_copy):
    """_copy_run_set_files creates correct symlink for relative path source
    """
    args = Mock(iodefs='../iodef.xml')
    args.desc_file.name = 'foo'
    with patch('salishsea_cmd.prepare_processor.os.chdir'):
        prepare_processor._copy_run_set_files(args, 'bar', 'baz')
    pwd = os.getcwd()
    expected = [
        call(os.path.join(os.path.dirname(pwd), 'iodef.xml'), 'iodef.xml'),
        call(os.path.join(pwd, 'foo'), 'foo'),
        call(os.path.join(pwd, 'xmlio_server.def'), 'xmlio_server.def'),
    ]
    assert mock_copy.call_args_list == expected
