# Copyright 2013-2017 The Salish Sea MEOPAR Contributors
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
"""SalishSeaCmd get_cgrf sub-command plug-in unit tests
"""
try:
    from unittest.mock import call, Mock, patch
except ImportError:
    # Python 2.7
    from mock import call, Mock, patch

import arrow
import cliff.app
import pytest

import salishsea_cmd.get_cgrf


@pytest.fixture
def get_cgrf_cmd():
    import salishsea_cmd.get_cgrf
    return salishsea_cmd.get_cgrf.GetCGRF(Mock(spec=cliff.app.App), [])


def test_get_parser(get_cgrf_cmd):
    parser = get_cgrf_cmd.get_parser('salishsea get_cgrf')
    assert parser.prog == 'salishsea get_cgrf'


@patch('salishsea_cmd.get_cgrf._get_cgrf')
@patch('salishsea_cmd.get_cgrf._rebase_cgrf_time')
@patch('salishsea_cmd.get_cgrf._correct_pressure')
@patch('salishsea_cmd.get_cgrf.os.chdir')
@patch('salishsea_cmd.get_cgrf.os.mkdir')
@patch('salishsea_cmd.get_cgrf.os.remove')
@patch('salishsea_cmd.get_cgrf.os.removedirs')
@patch('salishsea_cmd.get_cgrf.tempfile.NamedTemporaryFile')
@patch('salishsea_cmd.get_cgrf.os.listdir')
def test_take_action_calls_get_cgrf(
    m_listdir,
    m_NTF,
    m_rmdir,
    m_rm,
    m_mkdir,
    m_chdir,
    m_rebase,
    m_corr_press,
    m_get_cgrf,
    get_cgrf_cmd,
):
    """take_action calls _get_cgrf for expected dates
    """
    m_NTF().__enter__().name = 'tmp'
    args = Mock(
        start_date=arrow.get(2014, 1, 1),
        days=2,
        userid='foo',
        passwd='bar',
    )
    get_cgrf_cmd.take_action(args)
    expected = [
        call(arrow.get(2013, 12, 31), 'foo', 'tmp'),
        call(arrow.get(2014, 1, 1), 'foo', 'tmp'),
        call(arrow.get(2014, 1, 2), 'foo', 'tmp'),
    ]
    assert m_get_cgrf.mock_calls == expected


@patch('salishsea_cmd.get_cgrf._rebase_cgrf_time')
@patch('salishsea_cmd.get_cgrf._correct_pressure')
@patch('salishsea_cmd.get_cgrf._get_cgrf')
@patch('salishsea_cmd.get_cgrf.os.chdir')
@patch('salishsea_cmd.get_cgrf.os.mkdir')
@patch('salishsea_cmd.get_cgrf.os.remove')
@patch('salishsea_cmd.get_cgrf.os.removedirs')
@patch('salishsea_cmd.get_cgrf.tempfile.NamedTemporaryFile')
@patch('salishsea_cmd.get_cgrf.os.listdir')
def test_take_action_calls_rebase_cgrf_time(
    m_listdir,
    m_NTF,
    m_rmdirs,
    m_rm,
    m_mkdir,
    m_chdir,
    m_get_cgrf,
    m_rebase,
    m_corr_press,
    get_cgrf_cmd,
):
    """take_action calls _rebase_cgrf_time for expected dates
    """
    m_NTF().__enter__().name = 'tmp'
    args = Mock(
        start_date=arrow.get(2014, 1, 7),
        days=2,
        userid='foo',
        passwd='bar',
    )
    get_cgrf_cmd.take_action(args)
    expected = [
        call(arrow.get(2014, 1, 7)),
        call(arrow.get(2014, 1, 8)),
    ]
    assert m_rebase.mock_calls == expected


@patch('salishsea_cmd.get_cgrf.os.removedirs')
@patch('salishsea_cmd.get_cgrf._rebase_cgrf_time')
@patch('salishsea_cmd.get_cgrf._correct_pressure')
@patch('salishsea_cmd.get_cgrf._get_cgrf')
@patch('salishsea_cmd.get_cgrf.os.chdir')
@patch('salishsea_cmd.get_cgrf.os.mkdir')
@patch('salishsea_cmd.get_cgrf.os.remove')
@patch('salishsea_cmd.get_cgrf.tempfile.NamedTemporaryFile')
@patch('salishsea_cmd.get_cgrf.os.listdir', return_value=['bar'])
def test_take_action_removes_rsync_dirs(
    m_listdir,
    m_NTF,
    m_rm,
    m_chdir,
    m_mkdir,
    m_get_cgrf,
    m_rebase,
    m_corr_press,
    m_rmdir,
    get_cgrf_cmd,
):
    """take_action removes rsync-ed CGRF diretories
    """
    m_NTF().__enter__().name = 'tmp'
    args = Mock(
        start_date=arrow.get(2014, 1, 8),
        days=2,
        userid='foo',
        passwd='bar',
    )
    with patch('salishsea_cmd.get_cgrf.RSYNC_MIRROR_DIR', '/foo/rsync-mirror'):
        get_cgrf_cmd.take_action(args)
    expected = [
        call('/foo/rsync-mirror/2014-01-07'),
        call('/foo/rsync-mirror/2014-01-08'),
        call('/foo/rsync-mirror/2014-01-09'),
    ]
    assert m_rmdir.mock_calls == expected


@patch('salishsea_cmd.get_cgrf.log.info')
@patch('salishsea_cmd.get_cgrf.os.path.exists', return_value=True)
@patch('salishsea_cmd.get_cgrf.os.listdir', return_value=range(8))
def test_get_cgrf_dst_dir_exists(m_listdir, m_exists, m_log):
    """_get_cgrf logs msg and returns if CGRF day dir exists & contains 8 files
    """
    salishsea_cmd.get_cgrf._get_cgrf(arrow.get(2014, 1, 6), 'foo', 'bar')
    m_log.assert_called_once_with('2014-01-06 dataset already downloaded')


@patch('salishsea_cmd.get_cgrf.log.info')
@patch('salishsea_cmd.get_cgrf.subprocess.check_call')
@patch('salishsea_cmd.get_cgrf.os.chmod')
@patch('salishsea_cmd.get_cgrf.os.listdir', return_value=[])
def test_get_cgrf_dst_dir(m_listdir, m_chmod, m_call, m_log):
    """_get_cgrf logs info with expected destination directory
    """
    salishsea_cmd.get_cgrf._get_cgrf(arrow.get(2014, 1, 2), 'foo', 'bar')
    m_log.assert_called_once_with('Downloading 2014-01-02')


@patch('salishsea_cmd.get_cgrf.subprocess.check_call')
@patch('salishsea_cmd.get_cgrf.os.chmod')
@patch('salishsea_cmd.get_cgrf.os.listdir', return_value=[])
def test_get_cgrf_rsync(m_listdir, m_chmod, m_call):
    """_get_cgrf invokes expected rsync commend
    """
    salishsea_cmd.get_cgrf._get_cgrf(arrow.get(2014, 1, 2), 'foo', 'bar')
    expected = (
        'rsync -rlt --password-file=bar '
        'foo@goapp.ocean.dal.ca::canadian_GDPS_reforecasts_v1/'
        '2014/2014010200/ 2014-01-02/'
    ).split()
    m_call.assert_called_once_with(expected)


@patch('salishsea_cmd.get_cgrf.subprocess.check_call')
@patch('salishsea_cmd.get_cgrf.os.chmod')
@patch('salishsea_cmd.get_cgrf.os.listdir', return_value=['baz.gz'])
def test_get_cgrf_unzip(m_listdir, m_chmod, m_call):
    """_get_cgrf invokes expected unzip commend
    """
    salishsea_cmd.get_cgrf._get_cgrf(arrow.get(2014, 1, 2), 'foo', 'bar')
    assert m_call.mock_calls[1] == call(['gunzip', '2014-01-02/baz.gz'])


@patch('salishsea_cmd.get_cgrf._get_cgrf_hyperslab')
@patch('salishsea_cmd.get_cgrf._merge_cgrf_hyperslabs')
@patch('salishsea_cmd.get_cgrf.nc')
@patch('salishsea_cmd.get_cgrf._improve_cgrf_file')
def test_rebase_cgrf_time_calls_get_cgrf_hyperslab(
    m_improve,
    m_nc,
    m_merge,
    m_get_slab,
):
    """_rebase_cgrf_time calls _get_cgrf_hyperslab with expected args
    """
    day = arrow.get(2014, 1, 8)
    prev_day = day.replace(days=-1)
    vars = 'precip q2 qlw qsw slp t2 u10 v10'.split()
    expected = []
    for var in vars:
        expected.append(call(prev_day, var, 18, 23, 'tmp1.nc'))
        expected.append(call(day, var, 0, 17, 'tmp2.nc'))
    salishsea_cmd.get_cgrf._rebase_cgrf_time(day)
    assert m_get_slab.mock_calls == expected


@patch('salishsea_cmd.get_cgrf._merge_cgrf_hyperslabs')
@patch('salishsea_cmd.get_cgrf._get_cgrf_hyperslab')
@patch('salishsea_cmd.get_cgrf.nc')
@patch('salishsea_cmd.get_cgrf._improve_cgrf_file')
def test_rebase_cgrf_time_calls_merge_cgrf_hyperslabs(
    m_improve,
    m_nc,
    m_get_slab,
    m_merge,
):
    """_rebase_cgrf_time calls _merge_cgrf_hyperslabs with expected args
    """
    day = arrow.get(2014, 1, 8)
    vars = 'precip q2 qlw qsw slp t2 u10 v10'.split()
    expected = [call(day, var, 'tmp1.nc', 'tmp2.nc') for var in vars]
    salishsea_cmd.get_cgrf._rebase_cgrf_time(day)
    assert m_merge.mock_calls == expected


@patch('salishsea_cmd.get_cgrf._improve_cgrf_file')
@patch('salishsea_cmd.get_cgrf._get_cgrf_hyperslab')
@patch('salishsea_cmd.get_cgrf._merge_cgrf_hyperslabs')
@patch('salishsea_cmd.get_cgrf.nc')
def test_rebase_cgrf_time_calls_improve_cgrf_file(
    m_nc,
    m_merge,
    m_get_slab,
    m_improve,
):
    """_rebase_cgrf_time calls _improve_cgrf_file with expected args
    """
    day = arrow.get(2014, 1, 8)
    vars = (('precip', 'liquid precipitation'), ('q2', '2m specific humidity'),
            ('qlw', 'long-wave radiation'), ('qsw', 'short-wave radiation'),
            ('slp', 'sea-level atmospheric pressure'),
            ('t2', '2m temperature'), ('u10', 'u-component 10m wind'),
            ('v10', 'v-component 10m wind'),)
    expected = [
        call(var, descr, day, m_nc.Dataset('tmp2.nc').history)
        for var, descr in vars
    ]
    salishsea_cmd.get_cgrf._rebase_cgrf_time(day)
    assert m_improve.mock_calls == expected


@patch('salishsea_cmd.get_cgrf.subprocess.check_call')
def test_get_cgrf_hyperslab(m_chk_call):
    """_get_cgrf_hyperslab invokes expected ncks command
    """
    day = arrow.get(2014, 1, 7)
    with patch('salishsea_cmd.get_cgrf.RSYNC_MIRROR_DIR', '/foo/rsync-mirror'):
        salishsea_cmd.get_cgrf._get_cgrf_hyperslab(
            day, 'u10', 18, 23, 'tmp1.nc'
        )
    expected = (
        'ncks -4 -L4 -O -d time_counter,18,23 '
        '/foo/rsync-mirror/2014-01-07/2014010700_u10.nc tmp1.nc'
    ).split()
    m_chk_call.assert_called_once_with(expected)


@patch('salishsea_cmd.get_cgrf.subprocess.check_output')
def test_merge_cgrf_hyperslabs(m_chk_out):
    """_merge_cgrf_hyperslabs invokes expected ncrcat command
    """
    day = arrow.get(2014, 1, 7)
    with patch('salishsea_cmd.get_cgrf.NEMO_ATMOS_DIR', '/foo/NEMO-atmos'):
        salishsea_cmd.get_cgrf._merge_cgrf_hyperslabs(
            day, 'u10', 'tmp1.nc', 'tmp2.nc'
        )
    expected = (
        'ncrcat -O '
        'tmp1.nc tmp2.nc '
        '/foo/NEMO-atmos/u10_y2014m01d07.nc'
    ).split()
    m_chk_out.assert_called_once_with(
        expected, stderr=-2, universal_newlines=True
    )
