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

"""Utility functions for use by SalishSeaCmd command plug-ins.
"""
from __future__ import absolute_import

import subprocess

import yaml


__all__ = [
    'add_combine_gather_options',
    'load_run_desc',
    'netcdf4_deflate',
]


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


def add_combine_gather_options(parser):
    """Add options that are common to combine and gather sub-commands.
    """
    parser.add_argument(
        'desc_file', metavar='DESC_FILE',
        help='file path/name of run description YAML file')
    parser.add_argument(
        'results_dir', metavar='RESULTS_DIR',
        help='directory to store results into')
    parser.add_argument(
        '--keep-proc-results', action='store_true',
        help="don't delete per-processor results files")
    parser.add_argument(
        '--compress-restart', action='store_true',
        help="compress restart file(s)")
    parser.add_argument(
        '--delete-restart', action='store_true',
        help="delete restart file(s)")


def netcdf4_deflate(filename, dfl_lvl=4):
    """Run `ncks -4 -L dfl_lvl` on filename *in place*.

    The result is a netCDF4 file with its variables compressed
    with Lempel-Ziv deflation.

    :arg filename: Path/filename of the netCDF file to process.
    :type filename: string

    :arg dfl_lvl: Lempel-Ziv deflation level to use.
    :type dfl_lvl: int

    :returns: Output of the ncks command.
    :rtype: string
    """
    result = subprocess.check_output(
        ['ncks', '-4', '-L{}'.format(dfl_lvl), '-O', filename, filename],
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )
    return result
