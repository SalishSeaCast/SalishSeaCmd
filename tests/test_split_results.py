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
"""SalishSeaCmd split-results sub-command plug-in unit tests
"""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import arrow
import cliff.app
import pytest

from salishsea_cmd import split_results


@pytest.fixture
def split_results_cmd():
    return split_results.SplitResults(Mock(spec=cliff.app.App), [])


class TestParser:
    """Unit tests for `salishsea split-results` sub-command command-line parser."""

    def test_get_parser(self, split_results_cmd):
        parser = split_results_cmd.get_parser("salishsea split-results")
        assert parser.prog == "salishsea split-results"

    def test_parser_description(self, split_results_cmd):
        parser = split_results_cmd.get_parser("salishsea split-results")
        assert parser.description.strip().startswith("Split the results")

    def test_source_dir_argument(self, split_results_cmd):
        parser = split_results_cmd.get_parser("salishsea split-results")
        assert parser._actions[1].dest == "source_dir"
        assert parser._actions[1].metavar == "SOURCE_DIR"
        assert parser._actions[1].type == Path
        assert parser._actions[1].help

    def test_quiet_option(self, split_results_cmd):
        parser = split_results_cmd.get_parser("salishsea split-results")
        assert parser._actions[2].dest == "quiet"
        assert parser._actions[2].option_strings == ["-q", "--quiet"]
        assert parser._actions[2].const is True
        assert parser._actions[2].default is False
        assert parser._actions[2].help

    def test_parsed_args_defaults(self, split_results_cmd):
        parser = split_results_cmd.get_parser("salishsea split-results")
        parsed_args = parser.parse_args(["/scratch/hindcast_v201905_long/01jan07/"])
        assert parsed_args.source_dir == Path("/scratch/hindcast_v201905_long/01jan07/")
        assert not parsed_args.quiet

    @pytest.mark.parametrize("flag", ["-q", "--quiet"])
    def test_parsed_args_quiet_options(self, flag, split_results_cmd):
        parser = split_results_cmd.get_parser("salishsea split-results")
        parsed_args = parser.parse_args(
            ["/scratch/hindcast_v201905_long/01jan07/", flag]
        )
        assert parsed_args.quiet is True


@patch("salishsea_cmd.split_results.split_results", autospec=True)
class TestTakeAction:
    """Unit tests for `salishsea split-results` sub-command take_action() method."""

    @pytest.mark.parametrize("quiet", (True, False))
    def test_take_action(self, m_split_results, quiet, split_results_cmd):
        parsed_args = SimpleNamespace(
            source_dir=Path("/scratch/hindcast_v201905_long/01jan07/"), quiet=quiet
        )
        split_results_cmd.run(parsed_args)
        m_split_results.assert_called_once_with(
            Path("/scratch/hindcast_v201905_long/01jan07/"), quiet
        )


@patch("salishsea_cmd.split_results.log", autospec=True)
class TestSplitResults:
    """Unit tests for `salishsea split-results` sub-command split_results() function."""

    @patch("salishsea_cmd.split_results.Path.exists", return_value=False, autospec=True)
    def test_source_dir_not_exists(self, m_exists, m_log, split_results_cmd):
        parsed_args = SimpleNamespace(
            source_dir=Path("/scratch/hindcast_v201905_long/01jan07/"), quiet=False
        )
        with pytest.raises(SystemExit):
            split_results_cmd.run(parsed_args)
        assert m_log.error.called

    @patch("salishsea_cmd.split_results.Path.exists", return_value=True, autospec=True)
    @patch("salishsea_cmd.split_results.Path.is_dir", return_value=False, autospec=True)
    def test_source_dir_not_directory(
        self, m_is_dir, m_exists, m_log, split_results_cmd
    ):
        parsed_args = SimpleNamespace(
            source_dir=Path("/scratch/hindcast_v201905_long/01jan07/"), quiet=False
        )
        with pytest.raises(SystemExit):
            split_results_cmd.run(parsed_args)
        assert m_log.error.called

    @patch("salishsea_cmd.split_results.Path.exists", return_value=True, autospec=True)
    @patch("salishsea_cmd.split_results.Path.is_dir", return_value=True, autospec=True)
    def test_bad_source_dir_name_format(
        self, m_is_dir, m_exists, m_log, split_results_cmd
    ):
        parsed_args = SimpleNamespace(
            source_dir=Path("/scratch/hindcast_v201905_long/2017-01-01/"), quiet=False
        )
        with pytest.raises(SystemExit):
            split_results_cmd.run(parsed_args)
        assert m_log.error.called


@patch("salishsea_cmd.split_results.Path.mkdir", autospec=True)
class TestMkDestDir:
    """Unit test for `salishsea split-results` sub-command _mk_dest_dir() function."""

    def test_mk_dest_dir(self, m_mkdir):
        dest_dir = split_results._mk_dest_dir(
            Path("/scratch/hindcast_v201905_long/01jan07/"), arrow.get("2007-01-02")
        )
        m_mkdir.assert_called_once_with(dest_dir, exist_ok=True)
        assert dest_dir == Path("/scratch/hindcast_v201905_long/02jan07/")


@patch("salishsea_cmd.split_results.log", autospec=True)
@patch("salishsea_cmd.split_results.shutil.move", autospec=True)
class TestMoveResultsNcFile:
    """Unit tests for `salishsea split-results` sub-command _move_results_nc_file() function."""

    def test_move_nemo_grid_nc_file(self, m_move, m_log):
        split_results._move_results_nc_file(
            Path(
                "/scratch/hindcast_v201905_long/SalishSea_1h_20070101_20070331_grid_T_20070101-20070101.nc"
            ),
            Path("/scratch/hindcast_v201905_long/01jan07/"),
            arrow.get("2007-01-01"),
        )
        m_move.assert_called_once_with(
            "/scratch/hindcast_v201905_long/SalishSea_1h_20070101_20070331_grid_T_20070101-20070101.nc",
            "/scratch/hindcast_v201905_long/01jan07/SalishSea_1h_20070101_20070101_grid_T.nc",
        )
        m_log.info.assert_called_once_with(
            "moved /scratch/hindcast_v201905_long/SalishSea_1h_20070101_20070331_grid_T_20070101-20070101.nc "
            "to /scratch/hindcast_v201905_long/01jan07/SalishSea_1h_20070101_20070101_grid_T.nc"
        )

    def test_move_other_nc_file(self, m_move, m_log):
        split_results._move_results_nc_file(
            Path("/scratch/hindcast_v201905_long/FVCOM_T_20070101-20070101.nc"),
            Path("/scratch/hindcast_v201905_long/01jan07/"),
            arrow.get("2007-01-01"),
        )
        m_move.assert_called_once_with(
            "/scratch/hindcast_v201905_long/FVCOM_T_20070101-20070101.nc",
            "/scratch/hindcast_v201905_long/01jan07/FVCOM_T.nc",
        )
        m_log.info.assert_called_once_with(
            "moved /scratch/hindcast_v201905_long/FVCOM_T_20070101-20070101.nc "
            "to /scratch/hindcast_v201905_long/01jan07/FVCOM_T.nc"
        )


@patch("salishsea_cmd.split_results.log", autospec=True)
@patch("salishsea_cmd.split_results.shutil.move", autospec=True)
class TestMoveRestartFile:
    """Unit tests for `salishsea split-results` sub-command _move_results_nc_file() function."""

    def test_move_restart_file(self, m_move, m_log):
        split_results._move_restart_file(
            Path("/scratch/hindcast_v201905_long/SalishSea_01587600_restart.nc"),
            Path("/scratch/hindcast_v201905_long/31mar07/"),
        )
        m_move.assert_called_once_with(
            "/scratch/hindcast_v201905_long/SalishSea_01587600_restart.nc",
            "/scratch/hindcast_v201905_long/31mar07",
        )
        m_log.info.assert_called_once_with(
            "moved /scratch/hindcast_v201905_long/SalishSea_01587600_restart.nc "
            "to /scratch/hindcast_v201905_long/31mar07/"
        )
