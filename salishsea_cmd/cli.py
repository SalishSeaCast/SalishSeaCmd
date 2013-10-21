"""Salish Sea NEMO command processor

Command line interface


Copyright 2010-2013 Doug Latornell and The University of British Columbia

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
import __version__


__all__ = ['main']


log = logging.getLogger('cli')
log.setLevel(logging.DEBUG)
stderr = logging.StreamHandler()
log.setLevel(logging.ERROR)
formatter = logging.Formatter('%(message)s')
stderr.setFormatter(formatter)
log.addHandler(stderr)


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
    _add_run_subparser(subparsers)
    return parser


def _add_version_arg(parser):
    parser.add_argument(
        '--version', action='version',
        version=__version__.number + __version__.release)


def _add_run_subparser(subparsers):
    """Add a sub-parser for the `ss run` command.
    """
    parser = subparsers.add_parser(
        'run', help='Run Salish Sea NEMO.',
        description='''
            Run Salish Sea NEMO on NUM_CORES cores/processors
            using the run description from DESC_FILE
            and storing the results in RESULTS_DIR.

            If RESULTS_DIR does not exist it will be created.
            ''')
    parser.add_argument(
        'num_cores', metavar='NUM_CORES', type=int,
        help='number of cores/processors to use')
    parser.add_argument(
        'desc_file', metavar='DESC_FILE', type=open,
        help='run description YAML file')
    parser.add_argument(
        'results_dir', metavar='RESULTS_DIR',
        help='directory to store results in')
    parser.add_argument(
        '-n', '--namelist', metavar='NAMELIST', default='namelist',
        help='''
            name of the namelist file to use;
            defaults to %(default)s
        ''')
    _add_version_arg(parser)
    parser.set_defaults(func=_do_run)


def _do_run(args):
    """Execute the `ss run` command with the specified arguments and options.
    """
    print(args)
