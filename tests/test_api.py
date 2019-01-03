# Copyright 2013-2019 The Salish Sea MEOPAR Contributors
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
try:
    from unittest.mock import Mock, patch
except ImportError:
    # Python 2.7
    from mock import Mock, patch

import cliff.app
import cliff.command
import pytest

import salishsea_cmd.api


class TestRunDescription:
    def test_no_arguments(self):
        run_desc = salishsea_cmd.api.run_description()
        expected = {
            'config_name': 'SalishSea',
            'run_id': None,
            'walltime': None,
            'MPI decomposition': '8x18',
            'paths': {
                'NEMO code config': None,
                'XIOS': None,
                'forcing': None,
                'runs directory': None,
            },
            'grid': {
                'coordinates': 'coordinates_seagrid_SalishSea.nc',
                'bathymetry': 'bathy_meter_SalishSea2.nc',
            },
            'forcing': None,
            'namelists': {
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
                ]
            },
            'output': {
                'domain': 'domain_def.xml',
                'fields': None,
                'separate XIOS server': True,
                'XIOS servers': 1,
            },
        }
        assert run_desc == expected

    def test_all_arguments(self):
        run_desc = salishsea_cmd.api.run_description(
            config_name='SOG',
            run_id='foo',
            walltime='1:00:00',
            mpi_decomposition='6x14',
            NEMO_code_config='$HOME/NEMO-code/NEMOGCM/CONFIG',
            XIOS_code='../../XIOS/',
            forcing_path='../../NEMO-forcing/',
            runs_dir='../../SalishSea/',
            forcing={},
            init_conditions='../../22-25Sep/SalishSea_00019008_restart.nc',
            namelists={}
        )
        expected = {
            'config_name': 'SOG',
            'run_id': 'foo',
            'walltime': '1:00:00',
            'MPI decomposition': '6x14',
            'paths': {
                'NEMO code config': '$HOME/NEMO-code/NEMOGCM/CONFIG',
                'XIOS': '../../XIOS/',
                'forcing': '../../NEMO-forcing/',
                'runs directory': '../../SalishSea/',
            },
            'grid': {
                'coordinates': 'coordinates_seagrid_SalishSea.nc',
                'bathymetry': 'bathy_meter_SalishSea2.nc',
            },
            'forcing': {},
            'namelists': {},
            'output': {
                'domain': 'domain_def.xml',
                'fields':
                '$HOME/NEMO-code/NEMOGCM/CONFIG/SHARED/field_def.xml',
                'separate XIOS server': True,
                'XIOS servers': 1,
            }
        }
        assert run_desc == expected


class TestRunSubcommand(object):
    def test_command_not_found_raised(self):
        app = Mock(spec=cliff.app.App)
        app_args = Mock(debug=True)
        with pytest.raises(ValueError):
            return_code = salishsea_cmd.api._run_subcommand(app, app_args, [])
            assert return_code == 2

    @patch('salishsea_cmd.api.log.error')
    def test_command_not_found_logged(self, m_log):
        app = Mock(spec=cliff.app.App)
        app_args = Mock(debug=False)
        return_code = salishsea_cmd.api._run_subcommand(app, app_args, [])
        assert m_log.called
        assert return_code == 2

    @patch('salishsea_cmd.api.cliff.commandmanager.CommandManager')
    @patch('salishsea_cmd.api.log.exception')
    def test_command_exception_logged(self, m_log, m_cmd_mgr):
        app = Mock(spec=cliff.app.App)
        app_args = Mock(debug=True)
        cmd_factory = Mock(spec=cliff.command.Command)
        cmd_factory().take_action.side_effect = Exception
        m_cmd_mgr().find_command.return_value = (cmd_factory, 'bar', 'baz')
        salishsea_cmd.api._run_subcommand(app, app_args, ['foo'])
        assert m_log.called

    @patch('salishsea_cmd.api.cliff.commandmanager.CommandManager')
    @patch('salishsea_cmd.api.log.error')
    def test_command_exception_logged_as_error(self, m_log, m_cmd_mgr):
        app = Mock(spec=cliff.app.App)
        app_args = Mock(debug=False)
        cmd_factory = Mock(spec=cliff.command.Command)
        cmd_factory().take_action.side_effect = Exception
        m_cmd_mgr().find_command.return_value = (cmd_factory, 'bar', 'baz')
        salishsea_cmd.api._run_subcommand(app, app_args, ['foo'])
        assert m_log.called
