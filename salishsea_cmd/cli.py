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
from . import __version__


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
    parser.add_argument(
        '--version', action='version',
        version=__version__.number + __version__.release)
    return parser
