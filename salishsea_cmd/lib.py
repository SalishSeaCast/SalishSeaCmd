# Copyright 2013-2014 The Salish Sea MEOPAR Contributors
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

"""SalishSeaCmd command plug-in for prepare sub-command.

Sets up the necesaary symbolic links for a Salish Sea NEMO run
in a specified directory and changes the pwd to that directory.
"""
from __future__ import absolute_import

import yaml


__all__ = ['load_run_desc']


def load_run_desc(desc_file):
    """Load the run description file contents into a data structure.

    :arg desc_file: Handle of YAML run description file object.
    :type desc_file: file-like object

    :returns: Contents of run description file parsed from YAML into a dict.
    :rtype: dict
    """
    return yaml.load(desc_file)
