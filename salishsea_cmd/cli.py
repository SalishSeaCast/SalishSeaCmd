"""Salish Sea NEMO command processor command line interface


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
from __future__ import (
    absolute_import,
    print_function,
)
import argparse
import logging
import sys
import yaml
from . import (
    __version__,
    combine_processor,
    utils,
)


__all__ = ['main']


log = logging.getLogger('cli')
log.setLevel(logging.DEBUG)
log.addHandler(utils.make_stderr_logger())


def main():
    """Entry point to start the command processor.
    """
    cmd_processor = _build_parser()
    if len(sys.argv) == 1:
        cmd_processor.print_help()
    else:
        try:
            args = cmd_processor.parse_args()
        except IOError as e:
            log.error(
                'IOError: Run description file not found: {.filename}'
                .format(e))
            sys.exit(2)
        args.func(args)


def _build_parser():
    parser = argparse.ArgumentParser(
        epilog='''
            Use `%(prog)s <sub-command> --help` to get detailed
            help about a sub-command.''')
    _add_version_arg(parser)
    subparsers = parser.add_subparsers(title='sub-commands')
    _add_combine_subparser(subparsers)
    return parser


def _add_version_arg(parser):
    parser.add_argument(
        '--version', action='version',
        version=__version__.number + __version__.release)


def _add_combine_subparser(subparsers):
    """Add a sub-parser for the `salishsea combine` command.
    """
    parser = subparsers.add_parser(
        'combine', help='Combine results from an MPI Salish Sea NEMO run.',
        description='''
            Combine the per-processor results files from an MPI
            Salish Sea NEMO run described in DESC_FILE
            into files in RESULTS_DIR
            and compress them using gzip.
            Delete the per-processor files.

            If RESULTS_DIR does not exist it will be created.
            ''')
    parser.add_argument(
        'desc_file', metavar='DESC_FILE', type=open,
        help='run description YAML file')
    parser.add_argument(
        'results_dir', metavar='RESULTS_DIR',
        help='directory to store results into')
    parser.add_argument(
        '--keep-proc-results', action='store_true',
        help="don't delete per-processor results files")
    parser.add_argument(
        '--no-compress', action='store_true',
        help="don't compress results files")
    parser.add_argument(
        '--compress-restart', action='store_true',
        help="compress restart file(s)")
    parser.add_argument(
        '--delete-restart', action='store_true',
        help="delete restart file(s)")
    _add_version_arg(parser)
    parser.set_defaults(func=_do_combine)


def _do_combine(args):
    """Execute the `salishsea combine` command with the specified arguments
    and options.
    """
    run_desc = _load_run_desc(args.desc_file)
    combine_processor.main(run_desc, args)


def _load_run_desc(desc_file):
    return yaml.load(desc_file)
