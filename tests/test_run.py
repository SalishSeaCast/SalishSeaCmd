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

"""SalishSeaCmd run sub-command plug-in unit tests
"""
from io import StringIO
from unittest.mock import Mock

import cliff.app
import pytest
import yaml


@pytest.fixture
def run_module():
    import salishsea_cmd.run
    return salishsea_cmd.run


@pytest.fixture
def run_cmd():
    import salishsea_cmd.run
    return salishsea_cmd.run.Run(Mock(spec=cliff.app.App), [])


class TestGetParser:
    """Unit tests for `salishsea run` sub-command command-line parser.
    """
    def test_get_parser(self, run_cmd):
        parser = run_cmd.get_parser('salishsea run')
        assert parser.prog == 'salishsea run'

    def test_parsed_args_defaults(self, run_cmd):
        parser = run_cmd.get_parser('salishsea run')
        parsed_args = parser.parse_args(['foo', 'bar', 'baz'])
        assert parsed_args.desc_file == 'foo'
        assert parsed_args.iodefs == 'bar'
        assert parsed_args.results_dir == 'baz'
        assert not parsed_args.nemo34
        assert not parsed_args.quiet
        assert not parsed_args.compress
        assert not parsed_args.keep_proc_results
        assert not parsed_args.compress_restart
        assert not parsed_args.delete_restart

    @pytest.mark.parametrize('flag, attr', [
        ('--nemo3.4', 'nemo34'),
        ('-q', 'quiet'),
        ('--quiet', 'quiet'),
        ('--compress', 'compress'),
        ('--compress', 'compress'),
        ('--keep-proc-results', 'keep_proc_results'),
        ('--compress-restart', 'compress_restart'),
        ('--delete-restart', 'delete_restart'),
    ])
    def test_parsed_args_flags(self, flag, attr, run_cmd):
        parser = run_cmd.get_parser('salishsea run')
        parsed_args = parser.parse_args(['foo', 'bar', 'baz', flag])
        assert getattr(parsed_args, attr)


def test_walltime_leading_zero(run_module):
    """Ensure correct handling of walltime w/ leading zero in YAML desc file

    re: issue#16
    """
    desc_file = StringIO(
        'run_id: foo\n'
        'walltime: 01:02:03\n')
    run_desc = yaml.load(desc_file)
    pbs_directives = run_module._pbs_common(
        run_desc, 42, 'me@example.com', 'foo/')
    assert u'walltime=1:02:03' in pbs_directives


def test_walltime_no_leading_zero(run_module):
    """Ensure correct handling of walltime w/o leading zero in YAML desc file

    re: issue#16
    """
    desc_file = StringIO(
        'run_id: foo\n'
        'walltime: 1:02:03\n')
    run_desc = yaml.load(desc_file)
    pbs_directives = run_module._pbs_common(
        run_desc, 42, 'me@example.com', 'foo/')
    assert u'walltime=1:02:03' in pbs_directives


def test_number_of_nodes_missing(run_module):
    """KeyError raised & msg logged when nodes key missing from YAML desc file
    """
    desc_file = StringIO(
        'run_id: foo\n'
        'walltime: 1:02:03\n')
    run_desc = yaml.load(desc_file)
    with pytest.raises(KeyError):
        run_module._pbs_features(run_desc, 'jasper')


def test_processors_per_node_missing(run_module):
    """KeyError raised & msg logged when ppn key missing from YAML desc file
    """
    desc_file = StringIO(
        'run_id: foo\n'
        'walltime: 1:02:03\n'
        'nodes: 27\n')
    run_desc = yaml.load(desc_file)
    with pytest.raises(KeyError):
        run_module._pbs_features(run_desc, 'jasper')


def test_nodes_ppn(run_module):
    """KeyError raised & msg logged when ppn key missing from YAML desc file
    """
    desc_file = StringIO(
        'run_id: foo\n'
        'walltime: 1:02:03\n'
        'nodes: 27\n'
        'processors_per_node: 12\n')
    run_desc = yaml.load(desc_file)
    pbs_features = run_module._pbs_features(run_desc, 'jasper')
    assert u'#PBS -l nodes=27:ppn=12' in pbs_features
