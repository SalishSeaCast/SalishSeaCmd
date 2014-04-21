"""Salish Sea NEMO command processor command line interface


Copyright 2013-2014 The Salish Sea MEOPAR Contributors
and The University of British Columbia

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
import arrow
from . import (
    __version__,
    get_cgrf_processor,
)


__all__ = ['main']


log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def main():
    """Entry point to start the command processor.
    """
    _config_logging()
    cmd_processor = _build_parser()
    if len(sys.argv) == 1:
        cmd_processor.print_help()
        sys.exit(2)
    try:
        args = cmd_processor.parse_args()
    except IOError as e:
        log.error(
            'IOError: Run description file not found: {.filename}'
            .format(e))
        sys.exit(2)
    args.func(args)


def _config_logging():
    root_logger = logging.getLogger()
    # Error log
    stderr = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter('[%(name)s] %(levelname)s: %(message)s')
    stderr.setLevel(logging.WARNING)
    stderr.setFormatter(formatter)
    root_logger.addHandler(stderr)

    # Console log
    class InfoFilter(object):
        def filter(self, record):
            return 1 if record.levelno <= logging.INFO else 0
    console = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(message)s')
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)
    console.addFilter(InfoFilter())
    root_logger.addHandler(console)


def _build_parser():
    parser = argparse.ArgumentParser(
        epilog='''
            Use `%(prog)s <sub-command> --help` to get detailed
            help about a sub-command.''')
    _add_version_arg(parser)
    subparsers = parser.add_subparsers(title='sub-commands')
    _add_get_cgrf_subparser(subparsers)
    return parser


def _add_version_arg(parser):
    parser.add_argument(
        '--version', action='version',
        version=__version__.number + __version__.release)


def _add_get_cgrf_subparser(subparsers):
    """Add a sub-parser for the `salishsea get_cgrf` command.
    """
    parser = subparsers.add_parser(
        'get_cgrf', help='Download and symlink CGRF atmospheric forcing files',
        description='''
        Download CGRF products atmospheric forcing files from Dalhousie rsync
        repository and symlink with the file names that NEMO expects.
        ''')
    parser.add_argument(
        'start_date', metavar='START_DATE', type=_date_string,
        help='1st date to download files for')
    parser.add_argument(
        '-d', '--days', type=int, default=1,
        help='Number of days to download')
    parser.add_argument(
        '--user', dest='userid', metavar='USERID',
        help='User id for Dalhousie CGRF rsync repository')
    parser.add_argument(
        '--password', dest='passwd', metavar='PASSWD',
        help='Passowrd for Dalhousie CGRF rsync repository')
    _add_version_arg(parser)
    parser.set_defaults(func=_do_get_cgrf)


def _date_string(string):
    try:
        value = arrow.get(string)
    except arrow.parser.ParserError:
        raise argparse.ArgumentTypeError(
            'Invalid start date: {}'.format(string))
    if value < arrow.get(2002, 1, 1) or value > arrow.get(2010, 12, 31):
        raise argparse.ArgumentTypeError(
            'Start date out of CGRF range 2002-01-01 to 2010-12-31: {}'
            .format(string))
    return value


def _do_get_cgrf(args):
    get_cgrf_processor.main(args)
