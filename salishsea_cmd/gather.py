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

"""SalishSeaCmd command plug-in for gather sub-command.

Gather results files from a Salish Sea NEMO run into a specified directory.
"""
from __future__ import absolute_import

import logging
import os
import shutil

import cliff.command

from . import (
    api,
    lib,
)


__all__ = ['Gather']


log = logging.getLogger(__name__)


class Gather(cliff.command.Command):
    """Gather results from a NEMO run; includes combining MPI results files
    """
    def get_parser(self, prog_name):
        parser = super(Gather, self).get_parser(prog_name)
        parser.description = '''
            Gather the results files from a Salish Sea NEMO run
            described in DESC_FILE into files in RESULTS_DIR.
            The gathering process includes combining
            the per-processor results files,
            compressing them using gzip
            and deleting the per-processor files.

            If RESULTS_DIR does not exist it will be created.
        '''
        parser.add_argument(
            '--no-compress', action='store_true',
            help="don't compress results files")
        lib.add_combine_gather_options(parser)
        return parser

    def take_action(self, parsed_args):
        """Execute the `salishsea gather` sub-command.

        Gather the results files from a Salish Sea NEMO run into
        a results directory.

        The per-processor results files from an MPI run are combined via
        the `salishsea combine` command.
        The run description file,
        namelist,
        and other files that define the run are also gathered into the
        directory given by `parsed_args.results_dir`.
        """
        try:
            api.combine(
                self.app, self.app_args,
                parsed_args.desc_file, parsed_args.results_dir,
                parsed_args.keep_proc_results, parsed_args.no_compress,
                parsed_args.compress_restart, parsed_args.delete_restart)
        except Exception:
            raise
        symlinks = _find_symlinks()
        try:
            _move_results(parsed_args.results_dir, symlinks)
        except Exception:
            raise
        _delete_symlinks(symlinks)


def _find_symlinks():
    return {fn for fn in os.listdir('.') if os.path.islink(fn)}


def _delete_symlinks(symlinks):
    log.info('Deleting symbolic links...')
    for fn in symlinks:
        os.remove(fn)


def _move_results(results_dir, symlinks):
    abs_results_dir = os.path.abspath(results_dir)
    if os.path.samefile(os.getcwd(), abs_results_dir):
        return
    log.info('Moving run definition and non-netCDF results files...')
    for fn in os.listdir('.'):
        if fn not in symlinks:
            shutil.move(
                os.path.join('.', fn), os.path.join(abs_results_dir, fn))
