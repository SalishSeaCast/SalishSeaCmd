"""Salish Sea NEMO get_cgrf sub-command processor unit tests

Copyright 2014 The Salish Sea MEOPAR Contributors
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
from mock import (
    call,
    Mock,
    patch,
)
import arrow
from salishsea_cmd import get_cgrf_processor


@patch('salishsea_cmd.get_cgrf_processor._get_cgrf')
@patch('salishsea_cmd.get_cgrf_processor._rebase_cgrf_time')
@patch('salishsea_cmd.get_cgrf_processor.os.chdir')
@patch('salishsea_cmd.get_cgrf_processor.os.remove')
@patch('salishsea_cmd.get_cgrf_processor.tempfile.NamedTemporaryFile')
def test_main_calls_get_cgrf(
    mock_NTF, mock_rm, mock_chdir, mock_rebase, mock_get_cgrf,
):
    """main calls _get_cgrf for expected dates
    """
    mock_NTF().__enter__().name = 'tmp'
    args = Mock(
        start_date=arrow.get(2014, 1, 1),
        days=2,
        userid='foo',
        passwd='bar',
    )
    get_cgrf_processor.main(args)
    expected = [
        call(arrow.get(2013, 12, 31), 'foo', 'tmp'),
        call(arrow.get(2014, 1, 1), 'foo', 'tmp'),
        call(arrow.get(2014, 1, 2), 'foo', 'tmp'),
    ]
    assert mock_get_cgrf.mock_calls == expected


@patch('salishsea_cmd.get_cgrf_processor._rebase_cgrf_time')
@patch('salishsea_cmd.get_cgrf_processor._get_cgrf')
@patch('salishsea_cmd.get_cgrf_processor.os.chdir')
@patch('salishsea_cmd.get_cgrf_processor.os.remove')
@patch('salishsea_cmd.get_cgrf_processor.tempfile.NamedTemporaryFile')
def test_main_calls_rebase_cgrf_time(
    mock_NTF, mock_rm, mock_chdir, mock_get_cgrf, mock_rebase,
):
    """main calls _rebase_cgrf_time for expected dates
    """
    mock_NTF().__enter__().name = 'tmp'
    args = Mock(
        start_date=arrow.get(2014, 1, 7),
        days=2,
        userid='foo',
        passwd='bar',
    )
    get_cgrf_processor.main(args)
    expected = [
        call(arrow.get(2014, 1, 7)),
        call(arrow.get(2014, 1, 8)),
    ]
    assert mock_rebase.mock_calls == expected


@patch('salishsea_cmd.get_cgrf_processor.log.info')
@patch('salishsea_cmd.get_cgrf_processor.os.path.exists', return_value=True)
@patch('salishsea_cmd.get_cgrf_processor.os.listdir', return_value=range(8))
def test_get_cgrf_dst_dir_exists(mock_listdir, mock_exists, mock_log):
    """_get_cgrf logs msg and returns if CGRF day dir exists & contains 8 files
    """
    get_cgrf_processor._get_cgrf(arrow.get(2014, 1, 6), 'foo', 'bar')
    mock_log.assert_called_once_with('2014-01-06 dataset already downloaded')


@patch('salishsea_cmd.get_cgrf_processor.log.info')
@patch('salishsea_cmd.get_cgrf_processor.subprocess.check_call')
@patch('salishsea_cmd.get_cgrf_processor.os.chmod')
@patch('salishsea_cmd.get_cgrf_processor.os.listdir', return_value=[])
def test_get_cgrf_dst_dir(mock_listdir, mock_chmod, mock_call, mock_log):
    """_get_cgrf logs info with expected destination directory
    """
    get_cgrf_processor._get_cgrf(arrow.get(2014, 1, 2), 'foo', 'bar')
    mock_log.assert_called_once_with('Downloading 2014-01-02')


@patch('salishsea_cmd.get_cgrf_processor.subprocess.check_call')
@patch('salishsea_cmd.get_cgrf_processor.os.chmod')
@patch('salishsea_cmd.get_cgrf_processor.os.listdir', return_value=[])
def test_get_cgrf_rsync(mock_listdir, mock_chmod, mock_call):
    """_get_cgrf invokes expected rsync commend
    """
    get_cgrf_processor._get_cgrf(arrow.get(2014, 1, 2), 'foo', 'bar')
    expected = (
        'rsync -rlt --password-file=bar '
        'foo@goapp.ocean.dal.ca::canadian_GDPS_reforecasts_v1/'
        '2014/2014010200/ 2014-01-02/'
    ).split()
    mock_call.assert_called_once_with(expected)


@patch('salishsea_cmd.get_cgrf_processor.subprocess.check_call')
@patch('salishsea_cmd.get_cgrf_processor.os.chmod')
@patch('salishsea_cmd.get_cgrf_processor.os.listdir', return_value=['baz.gz'])
def test_get_cgrf_unzip(mock_listdir, mock_chmod, mock_call):
    """_get_cgrf invokes expected unzip commend
    """
    get_cgrf_processor._get_cgrf(arrow.get(2014, 1, 2), 'foo', 'bar')
    assert mock_call.mock_calls[1] == call(['gunzip', '2014-01-02/baz.gz'])


@patch('salishsea_cmd.get_cgrf_processor.subprocess.check_call')
def test_get_cgrf_hyperslab(mock_call):
    """_get_cgrf_hyperslab invokes expected ncks command
    """
    day = arrow.get(2014, 1, 7)
    with patch('salishsea_cmd.get_cgrf_processor.RSYNC_MIRROR_DIR',
               '/foo/rsync-mirror'):
        get_cgrf_processor._get_cgrf_hyperslab(day, 'u10', 18, 23, 'tmp1.nc')
    expected = (
        'ncks -4 -L1 -O -d time_counter,18,23 '
        '/foo/rsync-mirror/2014-01-07/2014010700_u10.nc tmp1.nc'
    ).split()
    mock_call.assert_called_once_with(expected)


@patch('salishsea_cmd.get_cgrf_processor.subprocess.check_call')
def test_merge_cgrf_hyperslabs(mock_call):
    """_merge_cgrf_hyperslabs invokes expected ncrcat command
    """
    day = arrow.get(2014, 1, 7)
    with patch('salishsea_cmd.get_cgrf_processor.NEMO_ATMOS_DIR',
               '/foo/NEMO-atmos'):
        get_cgrf_processor._merge_cgrf_hyperslabs(
            day, 'u10', 'tmp1.nc', 'tmp2.nc')
    expected = (
        'ncrcat -O '
        'tmp1.nc tmp2.nc '
        '/foo/NEMO-atmos/u10_y2014m01d07.nc'
    ).split()
    mock_call.assert_called_once_with(expected)
