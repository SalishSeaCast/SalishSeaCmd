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
"""SalishSeaCmd lib module unit tests.
"""
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

import pytest

import salishsea_cmd.lib


@patch('salishsea_cmd.lib.logger')
class TestGetNProcessors:
    """Unit tests for get_n_processors function.
    """

    @pytest.mark.parametrize(
        'lpe_key',
        [
            'land processor elimination',
            'Land processor elimination',  # Backward compatibility
        ]
    )
    def test_without_land_processor_elimination(self, m_logger, lpe_key):
        run_desc = {'MPI decomposition': '8x18', 'grid': {lpe_key: False}}
        n_processors = salishsea_cmd.lib.get_n_processors(
            run_desc, Path('run_dir')
        )
        assert not m_logger.warning.called
        assert n_processors == 144

    def test_no_land_processor_elimination_warning(self, m_logger):
        run_desc = {
            'MPI decomposition': '8x18',
        }
        n_processors = salishsea_cmd.lib.get_n_processors(
            run_desc, Path('run_dir')
        )
        assert m_logger.warning.called
        assert n_processors == 144

    @pytest.mark.parametrize(
        'lpe_key',
        [
            'land processor elimination',
            'Land processor elimination',  # Backward compatibility
        ]
    )
    @patch('salishsea_cmd.lib._lookup_lpe_n_processors', return_value=88)
    def test_mpi_lpe_mapping_absolute_path(
        self, m_lookup, m_logger, lpe_key, tmpdir
    ):
        lpe_mpi_mapping = tmpdir.ensure('bathymetry_201702.csv')
        run_desc = {
            'MPI decomposition': '8x18',
            'grid': {
                lpe_key: str(lpe_mpi_mapping)
            }
        }
        n_processors = salishsea_cmd.lib.get_n_processors(
            run_desc, Path('run_dir')
        )
        m_lookup.assert_called_once_with(Path(str(lpe_mpi_mapping)), 8, 18)
        assert n_processors == 88

    @pytest.mark.parametrize(
        'lpe_key',
        [
            'land processor elimination',
            'Land processor elimination',  # Backward compatibility
        ]
    )
    @patch('salishsea_cmd.lib._lookup_lpe_n_processors', return_value=88)
    def test_mpi_lpe_mapping_relative_path(
        self, m_lookup, m_logger, lpe_key, tmpdir
    ):
        p_forcing = tmpdir.ensure_dir('NEMO-forcing')
        run_desc = {
            'MPI decomposition': '8x18',
            'paths': {
                'forcing': str(p_forcing)
            },
            'grid': {
                lpe_key: 'bathymetry_201702.csv'
            }
        }
        n_processors = salishsea_cmd.lib.get_n_processors(
            run_desc, Path('run_dir')
        )
        m_lookup.assert_called_once_with(
            Path(str(p_forcing.join('grid', 'bathymetry_201702.csv'))), 8, 18
        )
        assert n_processors == 88

    @pytest.mark.parametrize(
        'lpe_key',
        [
            'land processor elimination',
            'Land processor elimination',  # Backward compatibility
        ]
    )
    @patch('salishsea_cmd.lib._lookup_lpe_n_processors', return_value=None)
    def test_no_mpi_lpe_mapping(self, m_lookup, m_logger, lpe_key, tmpdir):
        p_forcing = tmpdir.ensure_dir('NEMO-forcing')
        run_desc = {
            'MPI decomposition': '8x18',
            'paths': {
                'forcing': str(p_forcing)
            },
            'grid': {
                lpe_key: 'bathymetry_201702.csv'
            }
        }
        with pytest.raises(ValueError):
            salishsea_cmd.lib.get_n_processors(run_desc, Path('run_dir'))
        assert m_logger.error.called
