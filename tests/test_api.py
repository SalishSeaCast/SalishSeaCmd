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

"""SalishSeaCmd combine sub-command plug-in unit tests
"""
from io import StringIO
from unittest.mock import (
    Mock,
    patch,
)

import cliff.app
import cliff.command
import pytest
import yaml


@pytest.fixture
def api_module():
    from salishsea_cmd import api
    return api


class TestCombine(object):
    @patch('salishsea_cmd.api._run_subcommand')
    def test_combine_default_args(self, m_run_subcommand, api_module):
        app, app_args = Mock(spec=cliff.app.App), []
        api_module.combine(app, app_args, 'run_desc_file', 'results_dir')
        m_run_subcommand.assert_called_once_with(
            app, app_args, ['combine', 'run_desc_file', 'results_dir'])

    @patch('salishsea_cmd.api._run_subcommand')
    def test_combine_keep_proc_results_arg(self, m_run_subcommand, api_module):
        app, app_args = Mock(spec=cliff.app.App), []
        api_module.combine(
            app, app_args, 'run_desc_file', 'results_dir',
            keep_proc_results=True)
        m_run_subcommand.assert_called_once_with(
            app, app_args,
            ['combine', 'run_desc_file', 'results_dir', '--keep-proc-results'])

    @patch('salishsea_cmd.api._run_subcommand')
    def test_combine_no_compress_arg(self, m_run_subcommand, api_module):
        app, app_args = Mock(spec=cliff.app.App), []
        api_module.combine(
            app, app_args, 'run_desc_file', 'results_dir',
            no_compress=True)
        m_run_subcommand.assert_called_once_with(
            app, app_args,
            ['combine', 'run_desc_file', 'results_dir', '--no-compress'])

    @patch('salishsea_cmd.api._run_subcommand')
    def test_combine_compress_restart_arg(self, m_run_subcommand, api_module):
        app, app_args = Mock(spec=cliff.app.App), []
        api_module.combine(
            app, app_args, 'run_desc_file', 'results_dir',
            compress_restart=True)
        m_run_subcommand.assert_called_once_with(
            app, app_args,
            ['combine', 'run_desc_file', 'results_dir', '--compress-restart'])

    @patch('salishsea_cmd.api._run_subcommand')
    def test_combine_delete_restart_arg(self, m_run_subcommand, api_module):
        app, app_args = Mock(spec=cliff.app.App), []
        api_module.combine(
            app, app_args, 'run_desc_file', 'results_dir',
            delete_restart=True)
        m_run_subcommand.assert_called_once_with(
            app, app_args,
            ['combine', 'run_desc_file', 'results_dir', '--delete-restart'])

    @patch('salishsea_cmd.api._run_subcommand')
    def test_combine_all_args(self, m_run_subcommand, api_module):
        app, app_args = Mock(spec=cliff.app.App), []
        api_module.combine(
            app, app_args, 'run_desc_file', 'results_dir',
            keep_proc_results=True, no_compress=True, compress_restart=True,
            delete_restart=True)
        m_run_subcommand.assert_called_once_with(
            app, app_args,
            ['combine', 'run_desc_file', 'results_dir', '--keep-proc-results',
             '--no-compress', '--compress-restart', '--delete-restart'])


class TestRunDescription(object):
    @pytest.mark.parametrize('nemo34', [True, False])
    def test_no_arguments(self, nemo34, api_module):
        run_desc = api_module.run_description(nemo34=nemo34)
        expected = {
            'config_name': 'SalishSea',
            'run_id': None,
            'walltime': None,
            'MPI decomposition': '8x18',
            'paths': {
                'NEMO-code': None,
                'forcing': None,
                'runs directory': None,
            },
            'grid': {
                'coordinates': 'coordinates_seagrid_SalishSea.nc',
                'bathymetry': 'bathy_meter_SalishSea2.nc',
            },
            'forcing': {
                'atmospheric':
                    '/results/forcing/atmospheric/GEM2.5/operational/',
                'initial conditions': None,
                'open boundaries': 'open_boundaries/',
                'rivers': 'rivers/',
            },
        }
        if nemo34:
            expected['forcing'] = {
                'atmospheric':
                    '/results/forcing/atmospheric/GEM2.5/operational/',
                'initial conditions': None,
                'open boundaries': 'open_boundaries/',
                'rivers': 'rivers/',
            }
            expected['namelists'] = [
                'namelist.time',
                'namelist.domain',
                'namelist.surface',
                'namelist.lateral',
                'namelist.bottom',
                'namelist.tracers',
                'namelist.dynamics',
                'namelist.compute',
            ]
        else:
            expected['paths']['XIOS'] = None
            expected['forcing'] = None
            expected['namelists'] = {
                'namelist_cfg': [
                    'namelist.time',
                    'namelist.domain',
                    'namelist.surface',
                    'namelist.lateral',
                    'namelist.bottom',
                    'namelist.tracer',
                    'namelist.dynamics',
                    'namelist.vertical',
                    'namelist.compute',
                ]}
            expected['output'] = {
                'domain': 'domain_def.xml',
                'fields': None,
                'separate XIOS server': True,
                'XIOS servers': 1,
            }
        assert run_desc == expected

    @pytest.mark.parametrize('nemo34, namelists', [
        (True, []),
        (False, {}),
    ])
    def test_all_arguments(self, nemo34, namelists, api_module):
        XIOS_code = None if nemo34 else '../../XIOS/'
        run_desc = api_module.run_description(
            config_name='SOG',
            run_id='foo',
            walltime='1:00:00',
            mpi_decomposition='6x14',
            NEMO_code='../../NEMO-code/',
            XIOS_code=XIOS_code,
            forcing_path='../../NEMO-forcing/',
            runs_dir='../../SalishSea/',
            init_conditions='../../22-25Sep/SalishSea_00019008_restart.nc',
            forcing={},
            namelists=namelists,
            nemo34=nemo34,
        )
        expected = {
            'config_name': 'SOG',
            'run_id': 'foo',
            'walltime': '1:00:00',
            'MPI decomposition': '6x14',
            'paths': {
                'NEMO-code': '../../NEMO-code/',
                'forcing': '../../NEMO-forcing/',
                'runs directory': '../../SalishSea/',
            },
            'grid': {
                'coordinates': 'coordinates_seagrid_SalishSea.nc',
                'bathymetry': 'bathy_meter_SalishSea2.nc',
            },
            'forcing': {},
            'namelists': namelists,
        }
        if not nemo34:
            expected['paths']['XIOS'] = '../../XIOS/'
            expected['namelists'] = {}
            expected['output'] = {
                'domain': 'domain_def.xml',
                'fields':
                    '../../NEMO-code/NEMOGCM/CONFIG/SHARED/field_def.xml',
                'separate XIOS server': True,
                'XIOS servers': 1,
            }
        assert run_desc == expected


class TestRunSubcommand(object):
    def test_command_not_found_raised(self, api_module):
        app = Mock(spec=cliff.app.App)
        app_args = Mock(debug=True)
        with pytest.raises(ValueError):
            return_code = api_module._run_subcommand(app, app_args, [])
            assert return_code == 2

    @patch('salishsea_cmd.api.log.error')
    def test_command_not_found_logged(self, m_log, api_module):
        app = Mock(spec=cliff.app.App)
        app_args = Mock(debug=False)
        return_code = api_module._run_subcommand(app, app_args, [])
        assert m_log.called
        assert return_code == 2

    @patch('salishsea_cmd.api.cliff.commandmanager.CommandManager')
    @patch('salishsea_cmd.api.log.exception')
    def test_command_exception_logged(self, m_log, m_cmd_mgr, api_module):
        app = Mock(spec=cliff.app.App)
        app_args = Mock(debug=True)
        cmd_factory = Mock(spec=cliff.command.Command)
        cmd_factory().take_action.side_effect = Exception
        m_cmd_mgr().find_command.return_value = (cmd_factory, 'bar', 'baz')
        api_module._run_subcommand(app, app_args, ['foo'])
        assert m_log.called

    @patch('salishsea_cmd.api.cliff.commandmanager.CommandManager')
    @patch('salishsea_cmd.api.log.error')
    def test_command_exception_logged_as_error(
        self,
        m_log,
        m_cmd_mgr,
        api_module,
    ):
        app = Mock(spec=cliff.app.App)
        app_args = Mock(debug=False)
        cmd_factory = Mock(spec=cliff.command.Command)
        cmd_factory().take_action.side_effect = Exception
        m_cmd_mgr().find_command.return_value = (cmd_factory, 'bar', 'baz')
        api_module._run_subcommand(app, app_args, ['foo'])
        assert m_log.called


class TestPbsCommon:
    """Unit tests for `salishsea run` pbs_common() function.
    """
    def test_walltime_leading_zero(self, api_module):
        """Ensure correct handling of walltime w/ leading zero in YAML desc file

        re: issue#16
        """
        desc_file = StringIO(
            'run_id: foo\n'
            'walltime: 01:02:03\n')
        run_desc = yaml.load(desc_file)
        pbs_directives = api_module.pbs_common(
            run_desc, 42, 'me@example.com', 'foo/')
        assert 'walltime=1:02:03' in pbs_directives

    def test_walltime_no_leading_zero(self, api_module):
        """Ensure correct handling of walltime w/o leading zero in YAML desc file

        re: issue#16
        """
        desc_file = StringIO(
            'run_id: foo\n'
            'walltime: 1:02:03\n')
        run_desc = yaml.load(desc_file)
        pbs_directives = api_module.pbs_common(
            run_desc, 42, 'me@example.com', 'foo/')
        assert 'walltime=1:02:03' in pbs_directives
