#  Copyright 2013 – present by the SalishSeaCast Project Contributors
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

# SPDX-License-Identifier: Apache-2.0


"""SalishSeaCmd prepare sub-command plug-in unit tests"""

import os
from pathlib import Path
from unittest.mock import call, Mock, patch

import cliff.app
import nemo_cmd.prepare
import pytest
import salishsea_cmd.prepare


@pytest.fixture
def prepare_cmd():
    return salishsea_cmd.prepare.Prepare(Mock(spec=cliff.app.App), [])


class TestParser:
    """Unit tests for `salishsea prepare` sub-command command-line parser."""

    def test_get_parser(self, prepare_cmd):
        parser = prepare_cmd.get_parser("salishsea prepare")
        assert parser.prog == "salishsea prepare"

    def test_parsed_args_defaults(self, prepare_cmd):
        parser = prepare_cmd.get_parser("salishsea prepare")
        parsed_args = parser.parse_args(["foo"])
        assert parsed_args.desc_file == Path("foo")
        assert not parsed_args.quiet

    @pytest.mark.parametrize("flag, attr", [("-q", "quiet"), ("--quiet", "quiet")])
    def test_parsed_args_flags(self, flag, attr, prepare_cmd):
        parser = prepare_cmd.get_parser("salishsea prepare")
        parsed_args = parser.parse_args(["foo", flag])
        assert getattr(parsed_args, attr)


@patch("nemo_cmd.prepare.load_run_desc")
@patch("nemo_cmd.prepare.check_nemo_exec", return_value="nemo_bin_dir")
@patch("nemo_cmd.prepare.check_xios_exec", return_value="xios_bin_dir")
@patch("nemo_cmd.api.find_rebuild_nemo_script")
@patch("nemo_cmd.resolved_path")
@patch("nemo_cmd.prepare.make_run_dir")
@patch("nemo_cmd.prepare.make_namelists")
@patch("nemo_cmd.prepare.copy_run_set_files")
@patch("nemo_cmd.prepare.make_executable_links")
@patch("nemo_cmd.prepare.make_grid_links")
@patch("nemo_cmd.prepare.make_forcing_links")
@patch("nemo_cmd.prepare.make_restart_links")
@patch("salishsea_cmd.prepare._record_vcs_revisions")
@patch("nemo_cmd.prepare.add_agrif_files")
class TestPrepare:
    """Unit tests for `salishsea prepare` prepare() function."""

    def test_prepare(
        self,
        m_aaf,
        m_rvr,
        m_mrl,
        m_mfl,
        m_mgl,
        m_mel,
        m_crsf,
        m_mnl,
        m_mrd,
        m_resolved_path,
        m_frns,
        m_cxe,
        m_cne,
        m_lrd,
    ):
        run_dir = salishsea_cmd.prepare.prepare(
            Path("SalishSea.yaml"), nocheck_init=False
        )
        m_lrd.assert_called_once_with(Path("SalishSea.yaml"))
        m_cne.assert_called_once_with(m_lrd())
        m_cne.assert_called_once_with(m_lrd())
        m_frns.assert_called_once_with(m_lrd())
        m_resolved_path.assert_called_once_with(Path("SalishSea.yaml"))
        m_mrd.assert_called_once_with(m_lrd())
        m_mnl.assert_called_once_with(m_resolved_path().parent, m_lrd(), m_mrd())
        m_crsf.assert_called_once_with(
            m_lrd(), Path("SalishSea.yaml"), m_resolved_path().parent, m_mrd()
        )
        m_mel.assert_called_once_with("nemo_bin_dir", m_mrd(), "xios_bin_dir")
        m_mgl.assert_called_once_with(m_lrd(), m_mrd())
        m_mfl.assert_called_once_with(m_lrd(), m_mrd())
        m_mrl.assert_called_once_with(m_lrd(), m_mrd(), False)
        m_aaf.assert_called_once_with(
            m_lrd(), Path("SalishSea.yaml"), m_resolved_path().parent, m_mrd(), False
        )
        m_rvr.assert_called_once_with(m_lrd(), m_mrd())
        assert run_dir == m_mrd()


class TestRecordVCSRevisions:
    """Unit tests for `salishsea prepare` _record_vcs_revisions() function."""

    def test_no_paths_forcing_key(self):
        run_desc = {}
        with pytest.raises(SystemExit):
            salishsea_cmd.prepare._record_vcs_revisions(run_desc, Path("run_dir"))

    @pytest.mark.parametrize(
        "config_name_key, nemo_code_config_key",
        [("config name", "NEMO code config"), ("config_name", "NEMO-code-config")],
    )
    @patch("nemo_cmd.prepare.write_repo_rev_file")
    def test_write_repo_rev_file_default_calls(
        self, m_write, config_name_key, nemo_code_config_key, tmp_path
    ):
        nemo_code_repo = tmp_path / Path("NEMO-3.6-code")
        nemo_config = nemo_code_repo / Path("NEMOGCM", "CONFIG")
        nemo_config.mkdir(parents=True)
        xios_code_repo = tmp_path / Path("XIOS")
        xios_code_repo.mkdir()
        run_desc = {
            config_name_key: "SalishSea",
            "paths": {
                nemo_code_config_key: os.fspath(nemo_config),
                "XIOS": os.fspath(xios_code_repo),
            },
        }
        salishsea_cmd.prepare._record_vcs_revisions(run_desc, Path("run_dir"))
        assert m_write.call_args_list == [
            call(
                nemo_code_repo,
                Path("run_dir"),
                nemo_cmd.prepare.get_git_revision,
            ),
            call(
                xios_code_repo,
                Path("run_dir"),
                nemo_cmd.prepare.get_git_revision,
            ),
        ]

    @pytest.mark.parametrize(
        "config_name_key, nemo_code_config_key",
        [("config name", "NEMO code config"), ("config_name", "NEMO-code-config")],
    )
    @patch("nemo_cmd.prepare.write_repo_rev_file")
    def test_write_repo_rev_file_vcs_revisions_hg_call(
        self, m_write, config_name_key, nemo_code_config_key, tmp_path
    ):
        nemo_code_repo = tmp_path / Path("NEMO-3.6-code")
        nemo_config = nemo_code_repo / Path("NEMOGCM", "CONFIG")
        nemo_config.mkdir(parents=True)
        xios_code_repo = tmp_path / Path("XIOS")
        xios_code_repo.mkdir()
        nemo_forcing = tmp_path / Path("NEMO-forcing")
        nemo_forcing.mkdir()
        ss_run_sets = tmp_path / Path("SS-run-sets")
        ss_run_sets.mkdir()
        run_desc = {
            config_name_key: "SalishSea",
            "paths": {
                nemo_code_config_key: os.fspath(nemo_config),
                "XIOS": os.fspath(xios_code_repo),
                "forcing": os.fspath(nemo_forcing),
            },
            "vcs revisions": {"hg": [os.fspath(ss_run_sets)]},
        }
        salishsea_cmd.prepare._record_vcs_revisions(run_desc, Path("run_dir"))
        assert m_write.call_args_list[-1] == call(
            Path(os.fspath(ss_run_sets)),
            Path("run_dir"),
            nemo_cmd.prepare.get_hg_revision,
        )

    @pytest.mark.parametrize(
        "config_name_key, nemo_code_config_key",
        [("config name", "NEMO code config"), ("config_name", "NEMO-code-config")],
    )
    @patch("nemo_cmd.prepare.write_repo_rev_file")
    def test_write_repo_rev_file_vcs_revisions_git_call(
        self, m_write, config_name_key, nemo_code_config_key, tmp_path
    ):
        nemo_code_repo = tmp_path / Path("NEMO-3.6-code")
        nemo_config = nemo_code_repo / Path("NEMOGCM", "CONFIG")
        nemo_config.mkdir(parents=True)
        xios_code_repo = tmp_path / Path("XIOS")
        xios_code_repo.mkdir()
        nemo_forcing = tmp_path / Path("NEMO-forcing")
        nemo_forcing.mkdir()
        ss_run_sets = tmp_path / Path("SS-run-sets")
        ss_run_sets.mkdir()
        run_desc = {
            config_name_key: "SalishSea",
            "paths": {
                nemo_code_config_key: os.fspath(nemo_config),
                "XIOS": os.fspath(xios_code_repo),
                "forcing": os.fspath(nemo_forcing),
            },
            "vcs revisions": {"git": [os.fspath(ss_run_sets)]},
        }
        salishsea_cmd.prepare._record_vcs_revisions(run_desc, Path("run_dir"))
        assert m_write.call_args_list[-1] == call(
            Path(os.fspath(ss_run_sets)),
            Path("run_dir"),
            nemo_cmd.prepare.get_git_revision,
        )

    @pytest.mark.parametrize(
        "config_name_key, nemo_code_config_key",
        [("config name", "NEMO code config"), ("config_name", "NEMO-code-config")],
    )
    @patch("nemo_cmd.prepare.write_repo_rev_file")
    def test_write_repo_rev_file_vcs_revisions_git_call_no_dups(
        self, m_write, config_name_key, nemo_code_config_key, tmp_path
    ):
        nemo_code_repo = tmp_path / Path("NEMO-3.6-code")
        nemo_config = nemo_code_repo / Path("NEMOGCM", "CONFIG")
        nemo_config.mkdir(parents=True)
        xios_code_repo = tmp_path / Path("XIOS")
        xios_code_repo.mkdir()
        nemo_forcing = tmp_path / Path("NEMO-forcing")
        nemo_forcing.mkdir()
        ss_run_sets = tmp_path / Path("SS-run-sets")
        ss_run_sets.mkdir()
        run_desc = {
            config_name_key: "SalishSea",
            "paths": {
                nemo_code_config_key: os.fspath(nemo_config),
                "XIOS": os.fspath(xios_code_repo),
                "forcing": os.fspath(nemo_forcing),
            },
            "vcs revisions": {
                "git": [os.fspath(ss_run_sets), os.fspath(nemo_code_repo)]
            },
        }
        salishsea_cmd.prepare._record_vcs_revisions(run_desc, Path("run_dir"))
        assert m_write.call_args_list[-1] == call(
            Path(os.fspath(ss_run_sets)),
            Path("run_dir"),
            nemo_cmd.prepare.get_git_revision,
        )
