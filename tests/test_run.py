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
    from unittest.mock import Mock, patch
except ImportError:
    # Python 2.7
    from mock import Mock, patch

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
        assert parsed_args.waitjob == 0
        assert not parsed_args.quiet

    @pytest.mark.parametrize(
        'flag, attr', [
            ('--nemo3.4', 'nemo34'),
            ('--nocheck-initial-conditions', 'nocheck_init'),
            ('--no-submit', 'no_submit'),
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
            no_submit=False,
            waitjob=0,
            quiet=False
        )
        run_cmd.run(parsed_args)
        m_run.assert_called_once_with(
            'desc file', 'results dir', 4, False, False, False, 0, False
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


@patch('salishsea_cmd.run.subprocess.check_output', return_value='msg')
@patch('salishsea_cmd.run._build_batch_script', return_value=u'script')
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
        self, m_prepare, m_lrd, m_gnp, m_bbs, m_sco, nemo34, sep_xios_server,
        xios_servers, tmpdir
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
                'SalishSea.yaml', str(p_results_dir), nemo34=nemo34
            )
        m_prepare.assert_called_once_with('SalishSea.yaml', nemo34, False)
        m_lrd.assert_called_once_with('SalishSea.yaml')
        m_gnp.assert_called_once_with(m_lrd(), Path(m_prepare()))
        m_bbs.assert_called_once_with(
            m_lrd(), 'SalishSea.yaml', 144, xios_servers, 4,
            Path(str(p_results_dir)), Path(str(p_run_dir)), 'orcinus', nemo34
        )
        m_sco.assert_called_once_with(['qsub', 'SalishSeaNEMO.sh'],
                                      universal_newlines=True)
        assert qsb_msg == 'msg'

    @pytest.mark.parametrize(
        'nemo34, sep_xios_server, xios_servers', [
            (True, None, 0),
            (False, False, 0),
            (False, True, 4),
        ]
    )
    def test_run_no_submit(
        self, m_prepare, m_lrd, m_gnp, m_bbs, m_sco, nemo34, sep_xios_server,
        xios_servers, tmpdir
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
                'SalishSea.yaml',
                str(p_results_dir),
                nemo34=nemo34,
                no_submit=True
            )
        m_prepare.assert_called_once_with('SalishSea.yaml', nemo34, False)
        m_lrd.assert_called_once_with('SalishSea.yaml')
        m_gnp.assert_called_once_with(m_lrd(), Path(m_prepare()))
        m_bbs.assert_called_once_with(
            m_lrd(), 'SalishSea.yaml', 144, xios_servers, 4,
            Path(str(p_results_dir)), Path(str(p_run_dir)), 'orcinus', nemo34
        )
        assert not m_sco.called
        assert qsb_msg is None


class TestPbsCommon:
    """Unit tests for `salishsea run` pbs_common() function.
    """

    def test_walltime_leading_zero(self):
        """Ensure correct handling of walltime w/ leading zero in YAML desc file

        re: issue#16
        """
        desc_file = StringIO(u'run_id: foo\n' u'walltime: 01:02:03\n')
        run_desc = yaml.load(desc_file)
        pbs_directives = salishsea_cmd.run._pbs_common(
            run_desc, 42, 'me@example.com', 'foo/'
        )
        assert 'walltime=1:02:03' in pbs_directives

    def test_walltime_no_leading_zero(self):
        """Ensure correct handling of walltime w/o leading zero in YAML desc file

        re: issue#16
        """
        desc_file = StringIO(u'run_id: foo\n' u'walltime: 1:02:03\n')
        run_desc = yaml.load(desc_file)
        pbs_directives = salishsea_cmd.run._pbs_common(
            run_desc, 42, 'me@example.com', 'foo/'
        )
        assert 'walltime=1:02:03' in pbs_directives


class TestPbsFeatures:
    """Unit tests for `salishsea run _pbs_features() function.
    """

    @pytest.mark.parametrize('n_processors, nodes', [
        (144, 12),
        (145, 13),
    ])
    def test_jasper(self, n_processors, nodes):
        pbs_features = salishsea_cmd.run._pbs_features(n_processors, 'jasper')
        expected = (
            '#PBS -l feature=X5675\n'
            '#PBS -l nodes={}:ppn=12\n'.format(nodes)
        )
        assert pbs_features == expected

    @pytest.mark.parametrize(
        'system, expected', [
            ('orcinus', '#PBS -l partition=QDR\n'),
            ('salish', ''),
        ]
    )
    def test_orcinus(self, system, expected):
        pbs_features = salishsea_cmd.run._pbs_features(144, system)
        assert pbs_features == expected


class TestExecute:
    """Unit test for _execute function.
    """

    def test_execute(self):
        script = salishsea_cmd.run._execute(
            nemo_processors=42, xios_processors=1, max_deflate_jobs=4
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
        ${DEFLATE} *_grid_[TUVW]*.nc *_ptrc_T*.nc *_dia[12]_T*.nc --jobs 4 --debug
        echo "Results deflation ended at $(date)"
        
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
