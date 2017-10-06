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
"""SalishSeaCmd run sub-command plug-in unit tests
"""
from io import StringIO
try:
    from pathlib import Path
except ImportError:
    # Python 2.7
    from pathlib2 import Path
try:
    from unittest.mock import call, Mock, patch
except ImportError:
    # Python 2.7
    from mock import call, Mock, patch

import cliff.app
import pytest
import yaml

import salishsea_cmd.run


@pytest.fixture
def run_cmd():
    import salishsea_cmd.run
    return salishsea_cmd.run.Run(Mock(spec=cliff.app.App), [])


class TestParser:
    """Unit tests for `salishsea run` sub-command command-line parser.
    """

    def test_get_parser(self, run_cmd):
        parser = run_cmd.get_parser('salishsea run')
        assert parser.prog == 'salishsea run'

    def test_parsed_args_defaults(self, run_cmd):
        parser = run_cmd.get_parser('salishsea run')
        parsed_args = parser.parse_args(['foo', 'baz'])
        assert parsed_args.desc_file == Path('foo')
        assert parsed_args.results_dir == 'baz'
        assert parsed_args.max_deflate_jobs == 4
        assert not parsed_args.nemo34
        assert not parsed_args.nocheck_init
        assert not parsed_args.no_submit
        assert not parsed_args.separate_deflate
        assert parsed_args.waitjob == 0
        assert not parsed_args.quiet

    @pytest.mark.parametrize(
        'flag, attr', [
            ('--nemo3.4', 'nemo34'),
            ('--nocheck-initial-conditions', 'nocheck_init'),
            ('--no-submit', 'no_submit'),
            ('--separate-deflate', 'separate_deflate'),
            ('-q', 'quiet'),
            ('--quiet', 'quiet'),
        ]
    )
    def test_parsed_args_boolean_flags(self, flag, attr, run_cmd):
        parser = run_cmd.get_parser('salishsea run')
        parsed_args = parser.parse_args(['foo', 'baz', flag])
        assert getattr(parsed_args, attr)


@patch('salishsea_cmd.run.log')
@patch('salishsea_cmd.run.run', return_value='qsub message')
class TestTakeAction:
    """Unit tests for `salishsea run` sub-command take_action() method.
    """

    def test_take_action(self, m_run, m_log, run_cmd):
        parsed_args = Mock(
            desc_file='desc file',
            results_dir='results dir',
            max_deflate_jobs=4,
            nemo34=False,
            nocheck_init=False,
            no_deflate=False,
            no_submit=False,
            separate_deflate=False,
            waitjob=0,
            quiet=False
        )
        run_cmd.run(parsed_args)
        m_run.assert_called_once_with(
            'desc file', 'results dir', 4, False, False, False, False, False,
            0, False
        )
        m_log.info.assert_called_once_with('qsub message')

    def test_take_action_quiet(self, m_run, m_log, run_cmd):
        parsed_args = Mock(
            desc_file='desc file',
            results_dir='results dir',
            nemo34=False,
            quiet=True,
        )
        run_cmd.run(parsed_args)
        assert not m_log.info.called


@patch(
    'salishsea_cmd.run.subprocess.check_output', return_value='43.orca2.ibb'
)
@patch(
    'salishsea_cmd.run._build_deflate_script', return_value=u'deflate script'
)
@patch('salishsea_cmd.run._build_batch_script', return_value=u'batch script')
@patch('salishsea_cmd.run.lib.get_n_processors', return_value=144)
@patch('salishsea_cmd.run.lib.load_run_desc')
@patch('salishsea_cmd.run.api.prepare')
class TestRun:
    """Unit tests for `salishsea run` run() function.
    """

    @pytest.mark.parametrize(
        'nemo34, sep_xios_server, xios_servers', [
            (True, None, 0),
            (False, False, 0),
            (False, True, 4),
        ]
    )
    def test_run_submit(
        self, m_prepare, m_lrd, m_gnp, m_bbs, m_bds, m_sco, nemo34,
        sep_xios_server, xios_servers, tmpdir
    ):
        p_run_dir = tmpdir.ensure_dir('run_dir')
        m_prepare.return_value = Path(str(p_run_dir))
        p_results_dir = tmpdir.ensure_dir('results_dir')
        if not nemo34:
            m_lrd.return_value = {
                'output': {
                    'separate XIOS server': sep_xios_server,
                    'XIOS servers': xios_servers,
                }
            }
        with patch('salishsea_cmd.run.os.getenv', return_value='orcinus'):
            qsb_msg = salishsea_cmd.run.run(
                Path('SalishSea.yaml'), str(p_results_dir), nemo34=nemo34
            )
        m_prepare.assert_called_once_with(
            Path('SalishSea.yaml'), nemo34, False
        )
        m_lrd.assert_called_once_with(Path('SalishSea.yaml'))
        m_gnp.assert_called_once_with(m_lrd(), Path(m_prepare()))
        m_bbs.assert_called_once_with(
            m_lrd(), 'SalishSea.yaml', 144, xios_servers, 4,
            Path(str(p_results_dir)),
            Path(str(p_run_dir)), 'orcinus', nemo34, False, False
        )
        m_sco.assert_called_once_with(['qsub', 'SalishSeaNEMO.sh'],
                                      universal_newlines=True)
        assert p_run_dir.join('SalishSeaNEMO.sh').check(file=True)
        assert qsb_msg == '43.orca2.ibb'

    @pytest.mark.parametrize(
        'nemo34, sep_xios_server, xios_servers', [
            (True, None, 0),
            (False, False, 0),
            (False, True, 4),
        ]
    )
    def test_run_submit_waitjob(
        self, m_prepare, m_lrd, m_gnp, m_bbs, m_bds, m_sco, nemo34,
        sep_xios_server, xios_servers, tmpdir
    ):
        p_run_dir = tmpdir.ensure_dir('run_dir')
        m_prepare.return_value = Path(str(p_run_dir))
        p_results_dir = tmpdir.ensure_dir('results_dir')
        if not nemo34:
            m_lrd.return_value = {
                'output': {
                    'separate XIOS server': sep_xios_server,
                    'XIOS servers': xios_servers,
                }
            }
        with patch('salishsea_cmd.run.os.getenv', return_value='orcinus'):
            qsb_msg = salishsea_cmd.run.run(
                Path('SalishSea.yaml'),
                str(p_results_dir),
                nemo34=nemo34,
                waitjob=42
            )
        m_prepare.assert_called_once_with(
            Path('SalishSea.yaml'), nemo34, False
        )
        m_lrd.assert_called_once_with(Path('SalishSea.yaml'))
        m_gnp.assert_called_once_with(m_lrd(), Path(m_prepare()))
        m_bbs.assert_called_once_with(
            m_lrd(), 'SalishSea.yaml', 144, xios_servers, 4,
            Path(str(p_results_dir)),
            Path(str(p_run_dir)), 'orcinus', nemo34, False, False
        )
        m_sco.assert_called_once_with([
            'qsub', '-W', 'depend=afterok:42', 'SalishSeaNEMO.sh'
        ],
                                      universal_newlines=True)
        assert p_run_dir.join('SalishSeaNEMO.sh').check(file=True)
        assert qsb_msg == '43.orca2.ibb'

    @pytest.mark.parametrize(
        'nemo34, sep_xios_server, xios_servers', [
            (True, None, 0),
            (False, False, 0),
            (False, True, 4),
        ]
    )
    def test_run_no_submit(
        self, m_prepare, m_lrd, m_gnp, m_bbs, m_bds, m_sco, nemo34,
        sep_xios_server, xios_servers, tmpdir
    ):
        p_run_dir = tmpdir.ensure_dir('run_dir')
        m_prepare.return_value = Path(str(p_run_dir))
        p_results_dir = tmpdir.ensure_dir('results_dir')
        if not nemo34:
            m_lrd.return_value = {
                'output': {
                    'separate XIOS server': sep_xios_server,
                    'XIOS servers': xios_servers,
                }
            }
        with patch('salishsea_cmd.run.os.getenv', return_value='orcinus'):
            qsb_msg = salishsea_cmd.run.run(
                Path('SalishSea.yaml'),
                str(p_results_dir),
                nemo34=nemo34,
                no_submit=True
            )
        m_prepare.assert_called_once_with(
            Path('SalishSea.yaml'), nemo34, False
        )
        m_lrd.assert_called_once_with(Path('SalishSea.yaml'))
        m_gnp.assert_called_once_with(m_lrd(), Path(m_prepare()))
        m_bbs.assert_called_once_with(
            m_lrd(), 'SalishSea.yaml', 144, xios_servers, 4,
            Path(str(p_results_dir)),
            Path(str(p_run_dir)), 'orcinus', nemo34, False, False
        )
        assert p_run_dir.join('SalishSeaNEMO.sh').check(file=True)
        assert not m_sco.called
        assert qsb_msg is None

    @pytest.mark.parametrize('nemo34, xios_servers', [
        (True, 0),
        (False, 1),
    ])
    def test_run_no_deflate(
        self, m_prepare, m_lrd, m_gnp, m_bbs, m_bds, m_sco, nemo34,
        xios_servers, tmpdir
    ):
        p_run_dir = tmpdir.ensure_dir('run_dir')
        m_prepare.return_value = Path(str(p_run_dir))
        p_results_dir = tmpdir.ensure_dir('results_dir')
        if not nemo34:
            m_lrd.return_value = {
                'output': {
                    'separate XIOS server': True,
                    'XIOS servers': xios_servers,
                }
            }
        with patch('salishsea_cmd.run.os.getenv', return_value='orcinus'):
            qsb_msg = salishsea_cmd.run.run(
                Path('SalishSea.yaml'),
                str(p_results_dir),
                nemo34=nemo34,
                no_deflate=True,
            )
        m_prepare.assert_called_once_with(
            Path('SalishSea.yaml'), nemo34, False
        )
        m_lrd.assert_called_once_with(Path('SalishSea.yaml'))
        m_gnp.assert_called_once_with(m_lrd(), Path(m_prepare()))
        m_bbs.assert_called_once_with(
            m_lrd(), 'SalishSea.yaml', 144, xios_servers, 4,
            Path(str(p_results_dir)),
            Path(str(p_run_dir)), 'orcinus', nemo34, True, False
        )
        m_sco.assert_called_once_with(['qsub', 'SalishSeaNEMO.sh'],
                                      universal_newlines=True)
        assert p_run_dir.join('SalishSeaNEMO.sh').check(file=True)
        assert qsb_msg == '43.orca2.ibb'

    @pytest.mark.parametrize('nemo34, xios_servers', [
        (True, 0),
        (False, 1),
    ])
    def test_run_separate_deflate(
        self, m_prepare, m_lrd, m_gnp, m_bbs, m_bds, m_sco, nemo34,
        xios_servers, tmpdir
    ):
        p_run_dir = tmpdir.ensure_dir('run_dir')
        m_prepare.return_value = Path(str(p_run_dir))
        p_results_dir = tmpdir.ensure_dir('results_dir')
        if not nemo34:
            m_lrd.return_value = {
                'output': {
                    'separate XIOS server': True,
                    'XIOS servers': xios_servers,
                }
            }
        with patch('salishsea_cmd.run.os.getenv', return_value='orcinus'):
            qsb_msg = salishsea_cmd.run.run(
                Path('SalishSea.yaml'),
                str(p_results_dir),
                nemo34=nemo34,
                separate_deflate=True,
            )
        m_prepare.assert_called_once_with(
            Path('SalishSea.yaml'), nemo34, False
        )
        m_lrd.assert_called_once_with(Path('SalishSea.yaml'))
        m_gnp.assert_called_once_with(m_lrd(), Path(m_prepare()))
        m_bbs.assert_called_once_with(
            m_lrd(), 'SalishSea.yaml', 144, xios_servers, 4,
            Path(str(p_results_dir)),
            Path(str(p_run_dir)), 'orcinus', nemo34, False, True
        )
        assert m_bds.call_args_list == [
            call(
                m_lrd(), '*_grid_[TUVW]*.nc', 'grid',
                Path(str(p_results_dir)), 'orcinus', nemo34
            ),
            call(
                m_lrd(), '*_ptrc_T*.nc', 'ptrc',
                Path(str(p_results_dir)), 'orcinus', nemo34
            ),
            call(
                m_lrd(), '*_dia[12]_T*.nc', 'dia',
                Path(str(p_results_dir)), 'orcinus', nemo34
            ),
        ]
        assert p_run_dir.join('SalishSeaNEMO.sh').check(file=True)
        assert p_run_dir.join('deflate_grid.sh').check(file=True)
        assert p_run_dir.join('deflate_ptrc.sh').check(file=True)
        assert p_run_dir.join('deflate_dia.sh').check(file=True)
        assert m_sco.call_args_list == [
            call(['qsub', 'SalishSeaNEMO.sh'], universal_newlines=True),
            call(['qsub', '-W', 'depend=afterok:43', 'deflate_grid.sh'],
                 universal_newlines=True),
            call(['qsub', '-W', 'depend=afterok:43', 'deflate_ptrc.sh'],
                 universal_newlines=True),
            call(['qsub', '-W', 'depend=afterok:43', 'deflate_dia.sh'],
                 universal_newlines=True),
        ]


class TestBuildBatchScript:
    """Unit test for _build_batch_script() function.
    """

    @pytest.mark.parametrize('no_deflate', [
        True,
        False,
    ])
    def test_bugaboo(self, no_deflate):
        desc_file = StringIO(
            u'run_id: foo\n'
            u'walltime: 01:02:03\n'
            u'email: me@example.com'
        )
        run_desc = yaml.load(desc_file)
        script = salishsea_cmd.run._build_batch_script(
            run_desc,
            'SalishSea.yaml',
            nemo_processors=42,
            xios_processors=1,
            max_deflate_jobs=4,
            results_dir=Path('results_dir'),
            run_dir=Path(),
            system='bugaboo',
            nemo34=False,
            no_deflate=no_deflate,
            separate_deflate=False
        )
        expected = (
            u'#!/bin/bash\n'
            u'\n'
            u'#PBS -N foo\n'
            u'#PBS -S /bin/bash\n'
            u'#PBS -l procs=43\n'
            u'# memory per processor\n'
            u'#PBS -l pmem=2000mb\n'
            u'#PBS -l walltime=1:02:03\n'
            u'# email when the job [b]egins and [e]nds, or is [a]borted\n'
            u'#PBS -m bea\n'
            u'#PBS -M me@example.com\n'
            u'# stdout and stderr file paths/names\n'
            u'#PBS -o results_dir/stdout\n'
            u'#PBS -e results_dir/stderr\n'
            u'\n'
            u'\n'
            u'RUN_ID="foo"\n'
            u'RUN_DESC="SalishSea.yaml"\n'
            u'WORK_DIR="."\n'
            u'RESULTS_DIR="results_dir"\n'
            u'COMBINE="${PBS_O_HOME}/.local/bin/salishsea combine"\n'
        )
        if not no_deflate:
            expected += (
                u'DEFLATE="${PBS_O_HOME}/.local/bin/salishsea deflate"\n'
            )
        expected += (
            u'GATHER="${PBS_O_HOME}/.local/bin/salishsea gather"\n'
            u'\n'
            u'module load python\n'
            u'module load intel/15.0.2\n'
            u'\n'
            u'mkdir -p ${RESULTS_DIR}\n'
            u'cd ${WORK_DIR}\n'
            u'echo "working dir: $(pwd)"\n'
            u'\n'
            u'echo "Starting run at $(date)"\n'
            u'mpirun -np 42 ./nemo.exe : -np 1 ./xios_server.exe\n'
            u'MPIRUN_EXIT_CODE=$?\n'
            u'echo "Ended run at $(date)"\n'
            u'\n'
            u'echo "Results combining started at $(date)"\n'
            u'${COMBINE} ${RUN_DESC} --debug\n'
            u'echo "Results combining ended at $(date)"\n'
        )
        if not no_deflate:
            expected += (
                u'\n'
                u'echo "Results deflation started at $(date)"\n'
                u'${DEFLATE} *_grid_[TUVW]*.nc *_ptrc_T*.nc *_dia[12]_T*.nc '
                u'--jobs 4 --debug\n'
                u'echo "Results deflation ended at $(date)"\n'
            )
        expected += (
            u'\n'
            u'echo "Results gathering started at $(date)"\n'
            u'${GATHER} ${RESULTS_DIR} --debug\n'
            u'echo "Results gathering ended at $(date)"\n'
            u'\n'
            u'chmod go+rx ${RESULTS_DIR}\n'
            u'chmod g+rw ${RESULTS_DIR}/*\n'
            u'chmod o+r ${RESULTS_DIR}/*\n'
            u'\n'
            u'echo "Deleting run directory" >>${RESULTS_DIR}/stdout\n'
            u'rmdir $(pwd)\n'
            u'echo "Finished at $(date)" >>${RESULTS_DIR}/stdout\n'
            u'exit ${MPIRUN_EXIT_CODE}\n'
        )
        assert script == expected

    @pytest.mark.parametrize(
        'system, no_deflate', [
            ('cedar', True),
            ('cedar', False),
            ('graham', True),
            ('graham', False),
        ]
    )
    def test_cedar_graham(self, system, no_deflate):
        desc_file = StringIO(
            u'run_id: foo\n'
            u'walltime: 01:02:03\n'
            u'email: me@example.com'
        )
        run_desc = yaml.load(desc_file)
        script = salishsea_cmd.run._build_batch_script(
            run_desc,
            'SalishSea.yaml',
            nemo_processors=42,
            xios_processors=1,
            max_deflate_jobs=4,
            results_dir=Path('results_dir'),
            run_dir=Path(),
            system=system,
            nemo34=False,
            no_deflate=no_deflate,
            separate_deflate=False
        )
        expected = (
            u'#!/bin/bash\n'
            u'\n'
            u'#SBATCH --job-name=foo\n'
            u'#SBATCH --nodes=2\n'
            u'#SBATCH --ntasks-per-node=32\n'
            u'#SBATCH --mem=127G\n'
            u'#SBATCH --time=1:02:03\n'
            u'#SBATCH --mail-user=me@example.com\n'
            u'#SBATCH --mail-type=ALL\n'
            u'#SBATCH --account=def-allen\n'
            u'# stdout and stderr file paths/names\n'
            u'#SBATCH --output=results_dir/stdout\n'
            u'#SBATCH --error=results_dir/stderr\n'
            u'\n'
            u'\n'
            u'RUN_ID="foo"\n'
            u'RUN_DESC="SalishSea.yaml"\n'
            u'WORK_DIR="."\n'
            u'RESULTS_DIR="results_dir"\n'
            u'COMBINE="${HOME}/.local/bin/salishsea combine"\n'
        )
        if not no_deflate:
            expected += (u'DEFLATE="${HOME}/.local/bin/salishsea deflate"\n')
        expected += (
            u'GATHER="${HOME}/.local/bin/salishsea gather"\n'
            u'\n'
            u'module load netcdf-mpi/4.4.1.1\n'
            u'module load netcdf-fortran-mpi/4.4.4\n'
            u'module load python27-scipy-stack/2017a\n'
            u'\n'
            u'mkdir -p ${RESULTS_DIR}\n'
            u'cd ${WORK_DIR}\n'
            u'echo "working dir: $(pwd)"\n'
            u'\n'
            u'echo "Starting run at $(date)"\n'
            u'mpirun -np 42 ./nemo.exe : -np 1 ./xios_server.exe\n'
            u'MPIRUN_EXIT_CODE=$?\n'
            u'echo "Ended run at $(date)"\n'
            u'\n'
            u'echo "Results combining started at $(date)"\n'
            u'${COMBINE} ${RUN_DESC} --debug\n'
            u'echo "Results combining ended at $(date)"\n'
        )
        if not no_deflate:
            expected += (
                u'\n'
                u'echo "Results deflation started at $(date)"\n'
                u'module load nco/4.6.6\n'
                u'${DEFLATE} *_grid_[TUVW]*.nc *_ptrc_T*.nc *_dia[12]_T*.nc '
                u'--jobs 4 --debug\n'
                u'echo "Results deflation ended at $(date)"\n'
            )
        expected += (
            u'\n'
            u'echo "Results gathering started at $(date)"\n'
            u'${GATHER} ${RESULTS_DIR} --debug\n'
            u'echo "Results gathering ended at $(date)"\n'
            u'\n'
            u'chmod go+rx ${RESULTS_DIR}\n'
            u'chmod g+rw ${RESULTS_DIR}/*\n'
            u'chmod o+r ${RESULTS_DIR}/*\n'
            u'\n'
            u'echo "Deleting run directory" >>${RESULTS_DIR}/stdout\n'
            u'rmdir $(pwd)\n'
            u'echo "Finished at $(date)" >>${RESULTS_DIR}/stdout\n'
            u'exit ${MPIRUN_EXIT_CODE}\n'
        )
        assert script == expected

    @pytest.mark.parametrize('no_deflate', [
        True,
        False,
    ])
    def test_orcinus(self, no_deflate):
        desc_file = StringIO(
            u'run_id: foo\n'
            u'walltime: 01:02:03\n'
            u'email: me@example.com'
        )
        run_desc = yaml.load(desc_file)
        script = salishsea_cmd.run._build_batch_script(
            run_desc,
            'SalishSea.yaml',
            nemo_processors=42,
            xios_processors=1,
            max_deflate_jobs=4,
            results_dir=Path('results_dir'),
            run_dir=Path(),
            system='orcinus',
            nemo34=False,
            no_deflate=no_deflate,
            separate_deflate=False
        )
        expected = (
            u'#!/bin/bash\n'
            u'\n'
            u'#PBS -N foo\n'
            u'#PBS -S /bin/bash\n'
            u'#PBS -l procs=43\n'
            u'# memory per processor\n'
            u'#PBS -l pmem=2000mb\n'
            u'#PBS -l walltime=1:02:03\n'
            u'# email when the job [b]egins and [e]nds, or is [a]borted\n'
            u'#PBS -m bea\n'
            u'#PBS -M me@example.com\n'
            u'# stdout and stderr file paths/names\n'
            u'#PBS -o results_dir/stdout\n'
            u'#PBS -e results_dir/stderr\n'
            u'\n'
            u'#PBS -l partition=QDR\n'
            u'\n'
            u'RUN_ID="foo"\n'
            u'RUN_DESC="SalishSea.yaml"\n'
            u'WORK_DIR="."\n'
            u'RESULTS_DIR="results_dir"\n'
            u'COMBINE="${PBS_O_HOME}/.local/bin/salishsea combine"\n'
        )
        if not no_deflate:
            expected += (
                u'DEFLATE="${PBS_O_HOME}/.local/bin/salishsea deflate"\n'
            )
        expected += (
            u'GATHER="${PBS_O_HOME}/.local/bin/salishsea gather"\n'
            u'\n'
            u'module load intel\n'
            u'module load intel/14.0/netcdf-4.3.3.1_mpi\n'
            u'module load intel/14.0/netcdf-fortran-4.4.0_mpi\n'
            u'module load intel/14.0/hdf5-1.8.15p1_mpi\n'
            u'module load intel/14.0/nco-4.5.2\n'
            u'module load python\n'
            u'\n'
            u'mkdir -p ${RESULTS_DIR}\n'
            u'cd ${WORK_DIR}\n'
            u'echo "working dir: $(pwd)"\n'
            u'\n'
            u'echo "Starting run at $(date)"\n'
            u'mpirun -np 42 ./nemo.exe : -np 1 ./xios_server.exe\n'
            u'MPIRUN_EXIT_CODE=$?\n'
            u'echo "Ended run at $(date)"\n'
            u'\n'
            u'echo "Results combining started at $(date)"\n'
            u'${COMBINE} ${RUN_DESC} --debug\n'
            u'echo "Results combining ended at $(date)"\n'
        )
        if not no_deflate:
            expected += (
                u'\n'
                u'echo "Results deflation started at $(date)"\n'
                u'${DEFLATE} *_grid_[TUVW]*.nc *_ptrc_T*.nc *_dia[12]_T*.nc '
                u'--jobs 4 --debug\n'
                u'echo "Results deflation ended at $(date)"\n'
            )
        expected += (
            u'\n'
            u'echo "Results gathering started at $(date)"\n'
            u'${GATHER} ${RESULTS_DIR} --debug\n'
            u'echo "Results gathering ended at $(date)"\n'
            u'\n'
            u'chmod go+rx ${RESULTS_DIR}\n'
            u'chmod g+rw ${RESULTS_DIR}/*\n'
            u'chmod o+r ${RESULTS_DIR}/*\n'
            u'\n'
            u'echo "Deleting run directory" >>${RESULTS_DIR}/stdout\n'
            u'rmdir $(pwd)\n'
            u'echo "Finished at $(date)" >>${RESULTS_DIR}/stdout\n'
            u'exit ${MPIRUN_EXIT_CODE}\n'
        )
        assert script == expected

    @pytest.mark.parametrize('no_deflate', [
        True,
        False,
    ])
    def test_salish(self, no_deflate):
        desc_file = StringIO(
            u'run_id: foo\n'
            u'walltime: 01:02:03\n'
            u'email: me@example.com'
        )
        run_desc = yaml.load(desc_file)
        script = salishsea_cmd.run._build_batch_script(
            run_desc,
            'SalishSea.yaml',
            nemo_processors=6,
            xios_processors=1,
            max_deflate_jobs=4,
            results_dir=Path('results_dir'),
            run_dir=Path(),
            system='salish',
            nemo34=False,
            no_deflate=no_deflate,
            separate_deflate=False
        )
        expected = (
            u'#!/bin/bash\n'
            u'\n'
            u'#PBS -N foo\n'
            u'#PBS -S /bin/bash\n'
            u'#PBS -l procs=7\n'
            u'# memory per processor\n'
            u'#PBS -l pmem=2000mb\n'
            u'#PBS -l walltime=1:02:03\n'
            u'# email when the job [b]egins and [e]nds, or is [a]borted\n'
            u'#PBS -m bea\n'
            u'#PBS -M me@example.com\n'
            u'# stdout and stderr file paths/names\n'
            u'#PBS -o results_dir/stdout\n'
            u'#PBS -e results_dir/stderr\n'
            u'\n'
            u'\n'
            u'RUN_ID="foo"\n'
            u'RUN_DESC="SalishSea.yaml"\n'
            u'WORK_DIR="."\n'
            u'RESULTS_DIR="results_dir"\n'
            u'COMBINE="${HOME}/.local/bin/salishsea combine"\n'
        )
        if not no_deflate:
            expected += (u'DEFLATE="${HOME}/.local/bin/salishsea deflate"\n')
        expected += (
            u'GATHER="${HOME}/.local/bin/salishsea gather"\n'
            u'\n'
            u'\n'
            u'mkdir -p ${RESULTS_DIR}\n'
            u'cd ${WORK_DIR}\n'
            u'echo "working dir: $(pwd)"\n'
            u'\n'
            u'echo "Starting run at $(date)"\n'
            u'mpirun -np 6 ./nemo.exe : -np 1 ./xios_server.exe\n'
            u'MPIRUN_EXIT_CODE=$?\n'
            u'echo "Ended run at $(date)"\n'
            u'\n'
            u'echo "Results combining started at $(date)"\n'
            u'${COMBINE} ${RUN_DESC} --debug\n'
            u'echo "Results combining ended at $(date)"\n'
        )
        if not no_deflate:
            expected += (
                u'\n'
                u'echo "Results deflation started at $(date)"\n'
                u'${DEFLATE} *_grid_[TUVW]*.nc *_ptrc_T*.nc *_dia[12]_T*.nc '
                u'--jobs 4 --debug\n'
                u'echo "Results deflation ended at $(date)"\n'
            )
        expected += (
            u'\n'
            u'echo "Results gathering started at $(date)"\n'
            u'${GATHER} ${RESULTS_DIR} --debug\n'
            u'echo "Results gathering ended at $(date)"\n'
            u'\n'
            u'chmod go+rx ${RESULTS_DIR}\n'
            u'chmod g+rw ${RESULTS_DIR}/*\n'
            u'chmod o+r ${RESULTS_DIR}/*\n'
            u'\n'
            u'echo "Deleting run directory" >>${RESULTS_DIR}/stdout\n'
            u'rmdir $(pwd)\n'
            u'echo "Finished at $(date)" >>${RESULTS_DIR}/stdout\n'
            u'exit ${MPIRUN_EXIT_CODE}\n'
        )
        assert script == expected


@patch('salishsea_cmd.run.log', autospec=True)
class TestSlurm:
    """Unit tests for _slurm() function.
    """

    def test_slurm(self, m_logger):
        desc_file = StringIO(u'run_id: foo\n' u'walltime: 01:02:03\n')
        run_desc = yaml.load(desc_file)
        slurm_directives = salishsea_cmd.run._slurm(
            run_desc, 42, 'me@example.com', Path('foo')
        )
        expected = (
            u'#SBATCH --job-name=foo\n'
            u'#SBATCH --nodes=2\n'
            u'#SBATCH --ntasks-per-node=32\n'
            u'#SBATCH --mem=127G\n'
            u'#SBATCH --time=1:02:03\n'
            u'#SBATCH --mail-user=me@example.com\n'
            u'#SBATCH --mail-type=ALL\n'
            u'#SBATCH --account=def-allen\n'
            u'# stdout and stderr file paths/names\n'
            u'#SBATCH --output=foo/stdout\n'
            u'#SBATCH --error=foo/stderr\n'
        )
        assert slurm_directives == expected
        assert m_logger.info.called

    def test_account_directive(self, m_logger):
        desc_file = StringIO(
            u'run_id: foo\n'
            u'walltime: 01:02:03\n'
            u'account: def-sverdrup\n'
        )
        run_desc = yaml.load(desc_file)
        slurm_directives = salishsea_cmd.run._slurm(
            run_desc, 42, 'me@example.com', Path('foo')
        )
        assert u'#SBATCH --account=def-sverdrup\n' in slurm_directives
        assert not m_logger.info.called


class TestPbsCommon:
    """Unit tests for `salishsea run` _pbs_common() function.
    """

    @pytest.mark.parametrize(
        'walltime, expected_walltime', [
            ('01:02:03', '1:02:03'),
            ('1:02:03', '1:02:03'),
        ]
    )
    def test_walltime(self, walltime, expected_walltime):
        """Ensure correct handling of walltime w/ leading zero in YAML desc file

        re: issue#16
        """
        desc_file = StringIO(
            u'run_id: foo\n'
            u'walltime: {walltime}\n'.format(walltime=walltime)
        )
        run_desc = yaml.load(desc_file)
        pbs_directives = salishsea_cmd.run._pbs_common(
            run_desc, 42, 'me@example.com', 'foo/'
        )
        expected = 'walltime={expected}'.format(expected=expected_walltime)
        assert expected in pbs_directives


class TestDefinitions:
    """Unit tests for _definitions function.
    """

    @pytest.mark.parametrize(
        'system, home, no_deflate', [
            ('bugaboo', '${PBS_O_HOME}', True),
            ('bugaboo', '${PBS_O_HOME}', False),
            ('cedar', '${HOME}', True),
            ('cedar', '${HOME}', False),
            ('graham', '${HOME}', True),
            ('graham', '${HOME}', False),
            ('orcinus', '${PBS_O_HOME}', True),
            ('orcinus', '${PBS_O_HOME}', False),
            ('salish', '${HOME}', True),
            ('salish', '${HOME}', False),
        ]
    )
    def test_definitions(self, system, home, no_deflate):
        desc_file = StringIO(u'run_id: foo\n')
        run_desc = yaml.load(desc_file)
        defns = salishsea_cmd.run._definitions(
            run_desc, 'SalishSea.yaml',
            Path('run_dir'), Path('results_dir'), system, no_deflate
        )
        expected = (
            u'RUN_ID="foo"\n'
            u'RUN_DESC="SalishSea.yaml"\n'
            u'WORK_DIR="run_dir"\n'
            u'RESULTS_DIR="results_dir"\n'
            u'COMBINE="{home}/.local/bin/salishsea combine"\n'
        ).format(home=home)
        if not no_deflate:
            expected += (u'DEFLATE="{home}/.local/bin/salishsea deflate"\n'
                         ).format(home=home)
        expected += (
            u'GATHER="{home}/.local/bin/salishsea gather"\n'.format(home=home)
        )
        assert defns == expected


class TestModules:
    """Unit tests for _modules function.
    """

    @pytest.mark.parametrize('nemo34', [
        True,
        False,
    ])
    def test_unknown_system(self, nemo34):
        modules = salishsea_cmd.run._modules('salish', nemo34)
        assert modules == u''

    @pytest.mark.parametrize('nemo34', [
        True,
        False,
    ])
    def test_bugaboo(self, nemo34):
        modules = salishsea_cmd.run._modules('bugaboo', nemo34)
        expected = (u'module load python\n' u'module load intel/15.0.2\n')
        assert modules == expected

    @pytest.mark.parametrize(
        'system, nemo34', [
            ('cedar', True),
            ('graham', False),
        ]
    )
    def test_cedar_graham(self, system, nemo34):
        modules = salishsea_cmd.run._modules(system, nemo34)
        expected = (
            u'module load netcdf-mpi/4.4.1.1\n'
            u'module load netcdf-fortran-mpi/4.4.4\n'
            u'module load python27-scipy-stack/2017a\n'
        )
        assert modules == expected

    def test_orcinus_nemo36(self):
        modules = salishsea_cmd.run._modules('orcinus', nemo34=False)
        expected = (
            u'module load intel\n'
            u'module load intel/14.0/netcdf-4.3.3.1_mpi\n'
            u'module load intel/14.0/netcdf-fortran-4.4.0_mpi\n'
            u'module load intel/14.0/hdf5-1.8.15p1_mpi\n'
            u'module load intel/14.0/nco-4.5.2\n'
            u'module load python\n'
        )
        assert modules == expected

    def test_orcinus_nemo34(self):
        modules = salishsea_cmd.run._modules('orcinus', nemo34=True)
        expected = (
            u'module load intel\n'
            u'module load intel/14.0/netcdf_hdf5\n'
            u'module load python\n'
        )
        assert modules == expected


class TestExecute:
    """Unit test for _execute function.
    """

    @pytest.mark.parametrize(
        'system', [
            'bugaboo',
            'cedar',
            'graham',
            'orcinus',
            'salish',
        ]
    )
    def test_execute_with_deflate(self, system):
        script = salishsea_cmd.run._execute(
            nemo_processors=42,
            xios_processors=1,
            no_deflate=False,
            max_deflate_jobs=4,
            separate_deflate=False,
            system=system
        )
        expected = '''mkdir -p ${RESULTS_DIR}
        cd ${WORK_DIR}
        echo "working dir: $(pwd)"

        echo "Starting run at $(date)"
        mpirun -np 42 ./nemo.exe : -np 1 ./xios_server.exe
        MPIRUN_EXIT_CODE=$?
        echo "Ended run at $(date)"

        echo "Results combining started at $(date)"
        ${COMBINE} ${RUN_DESC} --debug
        echo "Results combining ended at $(date)"
        
        echo "Results deflation started at $(date)"
        '''
        if system in {'cedar', 'graham'}:
            expected += 'module load nco/4.6.6\n'
        expected += '''${DEFLATE} *_grid_[TUVW]*.nc *_ptrc_T*.nc *_dia[12]_T*.nc --jobs 4 --debug
        echo "Results deflation ended at $(date)"
        
        echo "Results gathering started at $(date)"
        ${GATHER} ${RESULTS_DIR} --debug
        echo "Results gathering ended at $(date)"
        '''
        expected = expected.splitlines()
        for i, line in enumerate(script.splitlines()):
            assert line.strip() == expected[i].strip()

    @pytest.mark.parametrize(
        'no_deflate, separate_deflate', [
            (True, True),
            (True, False),
            (False, True),
        ]
    )
    def test_execute_without_deflate(self, no_deflate, separate_deflate):
        script = salishsea_cmd.run._execute(
            nemo_processors=42,
            xios_processors=1,
            no_deflate=no_deflate,
            max_deflate_jobs=4,
            separate_deflate=separate_deflate,
            system='cedar'
        )
        expected = '''mkdir -p ${RESULTS_DIR}
        cd ${WORK_DIR}
        echo "working dir: $(pwd)"

        echo "Starting run at $(date)"
        mpirun -np 42 ./nemo.exe : -np 1 ./xios_server.exe
        MPIRUN_EXIT_CODE=$?
        echo "Ended run at $(date)"

        echo "Results combining started at $(date)"
        ${COMBINE} ${RUN_DESC} --debug
        echo "Results combining ended at $(date)"
        
        echo "Results gathering started at $(date)"
        ${GATHER} ${RESULTS_DIR} --debug
        echo "Results gathering ended at $(date)"
        '''
        expected = expected.splitlines()
        for i, line in enumerate(script.splitlines()):
            assert line.strip() == expected[i].strip()


class TestCleanup:
    """Unit test for _cleanup() function.
    """

    def test_cleanup(self):
        script = salishsea_cmd.run._cleanup()
        expected = '''echo "Deleting run directory" >>${RESULTS_DIR}/stdout
        rmdir $(pwd)
        echo "Finished at $(date)" >>${RESULTS_DIR}/stdout
        exit ${MPIRUN_EXIT_CODE}
        '''
        expected = expected.splitlines()
        for i, line in enumerate(script.splitlines()):
            assert line.strip() == expected[i].strip()


@pytest.mark.parametrize(
    'pattern, result_type, pmem', [
        ('*_grid_[TUVW]*.nc', 'grid', '2000mb'),
        ('*_ptrc_T*.nc', 'ptrc', '2500mb'),
        ('*_dia[12]_T.nc', 'dia', '2000mb'),
    ]
)
class TestBuildDeflateScript:
    """Unit test for _build_deflate_script() function.
    """

    def test_build_deflate_script_orcinus(
        self, pattern, result_type, pmem, tmpdir
    ):
        run_desc = {
            'run_id': '19sep14_hindcast',
            'walltime': '3:00:00',
            'email': 'test@example.com',
        }
        p_results_dir = tmpdir.ensure_dir('results_dir')
        script = salishsea_cmd.run._build_deflate_script(
            run_desc,
            pattern,
            result_type,
            Path(str(p_results_dir)),
            'orcinus',
            nemo34=False
        )
        expected = '''#!/bin/bash
        
        #PBS -N {result_type}_19sep14_hindcast_deflate
        #PBS -S /bin/bash
        #PBS -l procs=1
        # memory per processor
        #PBS -l pmem={pmem}
        #PBS -l walltime=3:00:00
        # email when the job [b]egins and [e]nds, or is [a]borted
        #PBS -m bea
        #PBS -M test@example.com
        # stdout and stderr file paths/names
        #PBS -o {results_dir}/stdout_deflate_{result_type}
        #PBS -e {results_dir}/stderr_deflate_{result_type}
        
        RESULTS_DIR="{results_dir}"
        DEFLATE="${{PBS_O_HOME}}/.local/bin/salishsea deflate"
        
        module load intel
        module load intel/14.0/netcdf-4.3.3.1_mpi
        module load intel/14.0/netcdf-fortran-4.4.0_mpi
        module load intel/14.0/hdf5-1.8.15p1_mpi
        module load intel/14.0/nco-4.5.2
        module load python

        cd ${{RESULTS_DIR}}
        echo "Results deflation started at $(date)"
        ${{DEFLATE}} {pattern} --jobs 1 --debug
        DEFLATE_EXIT_CODE=$?
        echo "Results deflation ended at $(date)"
        
        chmod g+rw ${{RESULTS_DIR}}/*
        chmod o+r ${{RESULTS_DIR}}/*
        
        exit ${{DEFLATE_EXIT_CODE}}
        '''.format(
            result_type=result_type,
            results_dir=str(p_results_dir),
            pattern=pattern,
            pmem=pmem
        )
        expected = expected.splitlines()
        for i, line in enumerate(script.splitlines()):
            assert line.strip() == expected[i].strip()

    def test_build_deflate_script_pmem(
        self, pattern, result_type, pmem, tmpdir
    ):
        run_desc = {
            'run_id': '19sep14_hindcast',
            'walltime': '3:00:00',
            'email': 'test@example.com',
        }
        p_results_dir = tmpdir.ensure_dir('results_dir')
        script = salishsea_cmd.run._build_deflate_script(
            run_desc,
            pattern,
            result_type,
            Path(str(p_results_dir)),
            'jasper',
            nemo34=False
        )
        if result_type == 'ptrc':
            assert '#PBS -l pmem=2500mb' in script
        else:
            assert '#PBS -l pmem=2000mb' in script
