# Copyright 2013-2018 The Salish Sea MEOPAR Contributors
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

Sets up the necessary symbolic links for a Salish Sea NEMO run
in a specified directory and changes the pwd to that directory.
"""
import functools
import logging
import os

try:
    from pathlib import Path
except ImportError:
    # Python 2.7
    from pathlib2 import Path
import shutil
import time
import xml.etree.ElementTree

import arrow
import cliff.command
import nemo_cmd
import nemo_cmd.api
import nemo_cmd.prepare
from nemo_cmd.prepare import get_run_desc_value

logger = logging.getLogger(__name__)


class Prepare(cliff.command.Command):
    """Prepare a Salish Sea NEMO run.
    """

    def get_parser(self, prog_name):
        parser = super(Prepare, self).get_parser(prog_name)
        parser.description = '''
            Set up the Salish Sea NEMO described in DESC_FILE
            and print the path to the run directory.
        '''
        parser.add_argument(
            'desc_file',
            metavar='DESC_FILE',
            type=Path,
            help='run description YAML file'
        )
        parser.add_argument(
            '--nocheck-initial-conditions',
            dest='nocheck_init',
            action='store_true',
            help='''
            Suppress checking of the initial conditions link.
            Useful if you are submitting a job to wait on a
            previous job'''
        )
        parser.add_argument(
            '-q',
            '--quiet',
            action='store_true',
            help="don't show the run directory path on completion"
        )
        return parser

    def take_action(self, parsed_args):
        """Execute the `salishsea prepare` sub-command.

        A UUID named directory is created and symbolic links are created
        in the directory to the files and directories specifed to run NEMO.
        The output of :command:`hg parents` is recorded in the directory
        for the NEMO-code and NEMO-forcing repos that the symlinks point to.
        The path to the run directory is logged to the console on completion
        of the set-up.
        """
        run_dir = prepare(parsed_args.desc_file, parsed_args.nocheck_init)
        if not parsed_args.quiet:
            logger.info('Created run directory {}'.format(run_dir))
        return run_dir


def prepare(desc_file, nocheck_init):
    """Create and prepare the temporary run directory.

    The temporary run directory is created with a UUID as its name.
    Symbolic links are created in the directory to the files and
    directories specifed to run NEMO.
    The output of :command:`hg parents` is recorded in the directory
    for the NEMO-code and NEMO-forcing repos that the symlinks point to.
    The path to the run directory is returned.

    :param desc_file: File path/name of the YAML run description file.
    :type desc_file: :py:class:`pathlib.Path`

    :arg nocheck_init: Suppress initial condition link check the
                       default is to check
    :type nocheck_init: boolean

    :returns: Path of the temporary run directory
    :rtype: :py:class:`pathlib.Path`
    """
    run_desc = nemo_cmd.prepare.load_run_desc(desc_file)
    nemo_bin_dir = nemo_cmd.prepare.check_nemo_exec(run_desc)
    xios_bin_dir = nemo_cmd.prepare.check_xios_exec(run_desc)
    nemo_cmd.api.find_rebuild_nemo_script(run_desc)
    run_set_dir = nemo_cmd.resolved_path(desc_file).parent
    run_dir = nemo_cmd.prepare.make_run_dir(run_desc)
    nemo_cmd.prepare.make_namelists(run_set_dir, run_desc, run_dir)
    nemo_cmd.prepare.copy_run_set_files(
        run_desc, desc_file, run_set_dir, run_dir
    )
    nemo_cmd.prepare.make_executable_links(nemo_bin_dir, run_dir, xios_bin_dir)
    nemo_cmd.prepare.make_grid_links(run_desc, run_dir)
    nemo_cmd.prepare.make_forcing_links(run_desc, run_dir)
    nemo_cmd.prepare.make_restart_links(run_desc, run_dir, nocheck_init)
    _record_vcs_revisions(run_desc, run_dir)
    nemo_cmd.prepare.add_agrif_files(
        run_desc, desc_file, run_set_dir, run_dir, nocheck_init
    )
    return run_dir


def _record_vcs_revisions(run_desc, run_dir):
    """Record revision and status information from version control system
    repositories in files in the temporary run directory.

    :param dict run_desc: Run description dictionary.

    :param run_dir: Path of the temporary run directory.
    :type run_dir: :py:class:`pathlib.Path`
    """
    try:
        nemo_code_config = get_run_desc_value(
            run_desc, ('paths', 'NEMO code config'),
            resolve_path=True,
            fatal=False
        )
    except KeyError:
        # Alternate key spelling for backward compatibility
        nemo_code_config = get_run_desc_value(
            run_desc, ('paths', 'NEMO-code-config'), resolve_path=True
        )
    xios_code_repo = get_run_desc_value(
        run_desc, ('paths', 'XIOS'), resolve_path=True, run_dir=run_dir
    )
    for repo in (nemo_code_config.parent.parent, xios_code_repo):
        nemo_cmd.prepare.write_repo_rev_file(
            repo, run_dir, nemo_cmd.prepare.get_hg_revision
        )
    if 'vcs revisions' not in run_desc:
        return
    vcs_funcs = {'hg': nemo_cmd.prepare.get_hg_revision}
    vcs_tools = get_run_desc_value(
        run_desc, ('vcs revisions',), run_dir=run_dir
    )
    for vcs_tool in vcs_tools:
        repos = get_run_desc_value(
            run_desc, ('vcs revisions', vcs_tool), run_dir=run_dir
        )
        for repo in repos:
            nemo_cmd.prepare.write_repo_rev_file(
                Path(repo), run_dir, vcs_funcs[vcs_tool]
            )
