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
"""SalishSeaCmd gather sub-command plug-in unit tests
"""
try:
    from unittest.mock import Mock
except ImportError:
    from mock import Mock

import cliff.app
import pytest


@pytest.fixture
def gather_cmd():
    import salishsea_cmd.gather
    return salishsea_cmd.gather.Gather(Mock(spec=cliff.app.App), [])


def test_get_parser(gather_cmd):
    parser = gather_cmd.get_parser('salishsea gather')
    assert parser.prog == 'salishsea gather'
