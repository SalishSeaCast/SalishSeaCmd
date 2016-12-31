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
"""SalishSeaCmd lib module unit tests.
"""
import salishsea_cmd.lib


class TestGetNProcessors:
    """Unit tests for get_n_processors function.
    """

    def test_without_land_processor_elimination(self):
        run_desc = {
            'MPI decomposition': '8x18',
            'Land processor elimination': False,
        }
        n_processors = salishsea_cmd.lib.get_n_processors(run_desc)
        assert n_processors == 144

    def test_with_land_processor_elimination(self):
        run_desc = {'MPI decomposition': '8x18'}
        n_processors = salishsea_cmd.lib.get_n_processors(run_desc)
        assert n_processors == 88
