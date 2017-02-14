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
"""Utility functions for use by SalishSeaCmd command plug-ins.
"""
import os

import yaml


def load_run_desc(desc_file):
    """Load the run description file contents into a data structure.

    :arg desc_file: File path/name of YAML run description file.
    :type desc_file: str

    :returns: Contents of run description file parsed from YAML into a dict.
    :rtype: dict
    """
    with open(desc_file, 'rt') as f:
        run_desc = yaml.load(f)
    return run_desc


def get_n_processors(run_desc):
    """Return the total number of processors required for the run as
    specified by the MPI decomposition key in the run description.

    :arg dict run_desc: Run description dictionary.

    :returns: Number of processors required for the run.
    :rtype: int
    """
    jpni, jpnj = map(int, run_desc['MPI decomposition'].split('x'))
    if run_desc.get('Land processor elimination', True):
        csvpath = os.path.dirname(os.path.abspath(__file__))
        csvfile = os.path.join(csvpath, 'salish.csv')
        with open(csvfile, 'r') as f:
            for line in f:
                cjpni, cjpnj, cnw = map(int, line.split(','))
                if jpni == cjpni and jpnj == cjpnj:
                    return cnw
    return jpni * jpnj
