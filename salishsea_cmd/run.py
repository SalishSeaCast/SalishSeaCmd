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

"""SalishSeaCmd command plug-in for run sub-command.

Prepare for, execute, and gather the results of a run of the
Salish Sea NEMO model.
"""
from __future__ import absolute_import

import logging

import cliff.command

from . import lib


__all__ = ['Run']


log = logging.getLogger(__name__)


class Run(cliff.command.Command):
    """Prepare, execute, and gather results from a Salish Sea NEMO model run
    """
    def get_parser(self, prog_name):
        parser = super(Run, self).get_parser(prog_name)
        parser.description = '''
            Prepare, execute, and gather the results from a Salish Sea NEMO
            run described in DESC_FILE and IO_DEFS.
            The results files from the run are gathered in RESULTS_DIR.

            If RESULTS_DIR does not exist it will be created.
        '''
        parser.add_argument(
            'desc_file', metavar='DESC_FILE', type=open,
            help='run description YAML file')
        parser.add_argument(
            'iodefs', metavar='IO_DEFS',
            help='NEMO IOM server defs file for run')
        parser.add_argument(
            'results_dir', metavar='RESULTS_DIR',
            help='directory to store results into')
        parser.add_argument(
            '--compress', action='store_true',
            help='compress results files')
        parser.add_argument(
            '--keep-proc-results', action='store_true',
            help="don't delete per-processor results files")
        parser.add_argument(
            '--compress-restart', action='store_true',
            help="compress restart file(s)")
        parser.add_argument(
            '--delete-restart', action='store_true',
            help="delete restart file(s)")
        return parser

    def take_action(self, parsed_args):
        pass
