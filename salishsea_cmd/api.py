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

"""Salish Sea NEMO command processor API

Application programming interface for the Salish Sea NEMO command
processor.
Provides Python function interfaces to command processor sub-commands
for use in other sub-command processor modules,
and by other software.
"""
from __future__ import absolute_import

import salishsea_cmd


__all__ = ['combine']


def combine(
    run_desc_file,
    results_dir,
    keep_proc_results=False,
    no_compress=False,
    compress_restart=False,
    delete_restart=False,
):
    """Run the NEMO :program:`rebuild_nemo` tool for each set of
    per-processor results files.

    The output of :program:`rebuild_nemo` for each file set is logged
    at the INFO level.
    The combined results files that :program:`rebuild_nemo` produces
    are moved to the directory given by :py:obj:`results_dir`.

    :arg results_dir: Directory to store results into.
    :type results_dir: str

    :arg keep_proc_results: Don't delete per-processor results files;
                            defaults to :py:obj:`False`.
    :type keep_proc_results: Boolean

    :arg no_compress: Don't compress results files;
                      defaults to :py:obj:`False`.
    :type no_compress: Boolean

    :arg compress_restart: Compress restart file(s);
                           defaults to :py:obj:`False`.
    :type compress_restart: Boolean

    :arg delete_restart: Delete restart file(s);
                         defaults to :py:obj:`False`.
    :type delete_restart: Boolean
    """
    app = salishsea_cmd.main.SalishSeaApp()
    args = ['combine', run_desc_file, results_dir]
    if keep_proc_results:
        args.append('--keep-proc-results')
    if no_compress:
        args.append('--no-compress')
    if compress_restart:
        args.append('--compress-restart')
    if delete_restart:
        args.append('--delete-restart')
    app.run(args)
