#  Copyright 2013-2021 The Salish Sea MEOPAR Contributors
#  and The University of British Columbia
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
"""SalishSeaCmd command plug-in for split-results sub-command.

Split the results of a multi-day SalishSeaCast NEMO model run
(e.g. a hindcast run) into daily results directories.
The results files are renamed so that they look like they came from a
single day run so that ERDDAP will accept them
(i.e. SalishSea_*_yyyymmdd_yyyymmdd_*.nc).
The run description files are left in the first run day's directory.
The restart files are moved to the last run day's directory.
"""
import logging
import os
from pathlib import Path
import shutil

import arrow
import arrow.parser
import cliff.command

log = logging.getLogger(__name__)


class SplitResults(cliff.command.Command):
    """Split the results of a multi-day SalishSeaCast NEMO model run (e.g. a hindcast run)
    into daily results directories.
    """

    def get_parser(self, prog_name):
        parser = super(SplitResults, self).get_parser(prog_name)
        parser.description = """
            Split the results of the multi-day SalishSeaCast NEMO model run in SOURCE_DIR 
            into daily results directories.
        """
        parser.add_argument(
            "source_dir",
            metavar="SOURCE_DIR",
            type=Path,
            help="Multi-day results directory to split into daily directories",
        )
        parser.add_argument(
            "-q", "--quiet", action="store_true", help="Don't show progress messages."
        )
        return parser

    def take_action(self, parsed_args):
        """Execute the `salishsea split-results` sub-coomand.

        :param parsed_args: Arguments and options parsed from the command-line.
        :type parsed_args: :class:`argparse.Namespace` instance
        """
        split_results(parsed_args.source_dir, parsed_args.quiet)


def split_results(source_dir, quiet):
    """Split the results of a multi-day SalishSeaCast NEMO model run
    (e.g. a hindcast run) into daily results directories.

    The results files are renamed so that they look like they came from a
    single day run so that ERDDAP will accept them
    (i.e. SalishSea_*_yyyymmdd_yyyymmdd_*.nc).

    The run description files are left in the first run day's directory.

    The restart files are moved to the last run day's directory.

    :param source_dir: Multi-day results directory to split into daily directories.
    :type source_dir: :py:class:`pathlib.Path`

    :param boolean quiet: Don't show progress messages.
                          The default is to show progress messages.
    """
    if not source_dir.exists() or not source_dir.is_dir():
        log.error(
            "run results directory not found: {source_dir}".format(
                source_dir=source_dir
            )
        )
        raise SystemExit(2)
    try:
        run_start_date = arrow.get(source_dir.name, "DDMMMYY")
    except arrow.parser.ParserError:
        log.error(
            "run results directory name is not in DDMMMYY format (e.g. 01jan07): {.name}".format(
                source_dir
            )
        )
        raise SystemExit(2)
    if not quiet:
        log.info(
            "splitting {source_dir} results files into daily directories".format(
                source_dir=source_dir
            )
        )
    last_date = run_start_date
    for nc_file in source_dir.glob("*.nc"):
        if "restart" in os.fspath(nc_file):
            # Restart files will be moved once last run day directory is created
            continue
        date = arrow.get(nc_file.stem[-8:], "YYYYMMDD")
        last_date = max(date, last_date)
        dest_dir = _mk_dest_dir(source_dir, date)
        _move_results_nc_file(nc_file, dest_dir, date)
    for restart_file in source_dir.glob("SalishSea_*_restart*.nc"):
        dest_dir = source_dir.parent / last_date.format("DDMMMYY").lower()
        _move_restart_file(restart_file, dest_dir)


def _mk_dest_dir(source_dir, date):
    """Separate function for testability.

    :param :py:class:`pathlib.Path` source_dir:
    :param :py:class:`arrow.Arrow` date:

    :rtype: :py:class:`pathlib.Path`
    """
    dest_dir = source_dir.parent / date.format("DDMMMYY").lower()
    dest_dir.mkdir(exist_ok=True)
    return dest_dir


def _move_results_nc_file(nc_file, dest_dir, date):
    """Separate function for testability.

    :param :py:class:`pathlib.Path` nc_file:
    :param :py:class:`pathlib.Path` dest_dir:
    :param :py:class:`arrow.Arrow` date:
    """
    if nc_file.stem.startswith("SalishSea_1"):
        fn = Path(
            "{nc_file_prefix}_{nc_file_date}_{nc_file_date}_{nc_file_grid}".format(
                nc_file_prefix=nc_file.stem[:12],
                nc_file_date=date.format("YYYYMMDD"),
                nc_file_grid=nc_file.stem[31:37],
            )
        ).with_suffix(".nc")
    else:
        fn = Path(nc_file.stem[:-18]).with_suffix(".nc")
    dest = dest_dir / fn
    shutil.move(os.fspath(nc_file), os.fspath(dest))
    log.info("moved {nc_file} to {dest}".format(nc_file=nc_file, dest=dest))


def _move_restart_file(restart_file, dest_dir):
    """Separate function for testability.

    :param :py:class:`pathlib.Path` restart_file:
    :param :py:class:`pathlib.Path` dest_dir:
    """
    shutil.move(os.fspath(restart_file), os.fspath(dest_dir))
    log.info(
        "moved {restart_file} to {dest_dir}/".format(
            restart_file=restart_file, dest_dir=dest_dir
        )
    )
