"""Salish Sea NEMO results rebuild sub-command processor

Combines per-processor files from an MPI Salish Sea NEMO run into single files
with the same name-root.


Copyright 2013 Doug Latornell and The University of British Columbia

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
from __future__ import absolute_import
import glob
import logging
import os
import subprocess
import sys
from . import utils


__all__ = ['main']


log = logging.getLogger('rebuild')
log.setLevel(logging.DEBUG)
log.addHandler(utils.make_stdout_logger)
log.addHandler(utils.make_stderr_logger())


def main(run_desc):
    rebuild_nemo_exec = _find_rebuild_nemo_exec(run_desc['paths']['NEMO-code'])
    name_roots, ncores = _get_results_files()
    for fn in name_roots:
        result = subprocess.check_output(
            [rebuild_nemo_exec, fn, str(ncores)],
            stderr=subprocess.STDOUT,
            universal_newlines=True)
        log.info(result)


def _find_rebuild_nemo_exec(nemo_code_path):
    rebuild_nemo_exec = os.path.join(
        nemo_code_path,
        'NEMOGCM/TOOLS/REBUILD_NEMO/rebuild_nemo.exe')
    if not os.path.lexists(rebuild_nemo_exec):
        log.error(
            'Error: {} not found - did you forget to build it?'
            .format(rebuild_nemo_exec))
        sys.exit(2)
    rebuild_nemo_script = os.path.splitext(rebuild_nemo_exec)[0]
    return rebuild_nemo_script


def _get_results_files():
    result_pattern = '*_0000.nc'
    name_roots = [fn[:-8] for fn in glob.glob(result_pattern)]
    if not name_roots:
        log.error(
            'Error: no files found that match the {} pattern'
            .format(result_pattern))
        sys.exit(2)
    ncores = len(glob.glob(name_roots[0] + '_[0-9][0-9][0-9][0-9].nc'))
    return name_roots, ncores
