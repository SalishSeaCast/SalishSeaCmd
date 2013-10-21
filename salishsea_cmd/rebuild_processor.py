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
import logging
import os
import sys
from . import utils


__all__ = ['main']


log = logging.getLogger('rebuild')
log.setLevel(logging.DEBUG)
log.addHandler(utils.make_stderr_logger())


def main(run_desc):
    print(run_desc)
    rebuild_nemo_exec = _find_rebuild_nemo_exec(
        run_desc['paths']['NEMO-code'])


def _find_rebuild_nemo_exec(nemo_code_path):
    rebuild_nemo_exec = os.path.join(
        nemo_code_path,
        'NEMOGCM/TOOLS/REBUILD_NEMO/rebuild_nemo.exe',
    )
    if not os.path.lexists(rebuild_nemo_exec):
        log.error(
            'Error: {} not found - did you forget to build it?'
            .format(rebuild_nemo_exec))
        sys.exit(2)
    return rebuild_nemo_exec
