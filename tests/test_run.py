# Copyright 2013-2019 The Salish Sea MEOPAR Contributors
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
"""SalishSeaCmd run sub-command plug-in unit tests
"""
from io import StringIO
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import textwrap
from unittest.mock import call, Mock, patch

import cliff.app
import f90nml
import pytest
import yaml

import salishsea_cmd.run


@pytest.fixture
def run_cmd():
    import salishsea_cmd.run

    return salishsea_cmd.run.Run(Mock(spec=cliff.app.App), [])


class TestParser:
    """Unit tests for `salishsea run` sub-command command-line parser.
    """

    def test_get_parser(self, run_cmd):
        parser = run_cmd.get_parser("salishsea run")
        assert parser.prog == "salishsea run"

    def test_parsed_args_defaults(self, run_cmd):
        parser = run_cmd.get_parser("salishsea run")
        parsed_args = parser.parse_args(["foo", "baz"])
        assert parsed_args.desc_file == Path("foo")
        assert parsed_args.results_dir == Path("baz")
        assert not parsed_args.cedar_broadwell
        assert not parsed_args.deflate
        assert parsed_args.max_deflate_jobs == 4
        assert not parsed_args.nocheck_init
        assert not parsed_args.no_submit
        assert not parsed_args.separate_deflate
        assert parsed_args.waitjob == "0"
        assert not parsed_args.quiet

    @pytest.mark.parametrize(
        "flag, attr",
        [
            ("--cedar-broadwell", "cedar_broadwell"),
            ("--deflate", "deflate"),
            ("--nocheck-initial-conditions", "nocheck_init"),
            ("--no-submit", "no_submit"),
            ("--separate-deflate", "separate_deflate"),
            ("-q", "quiet"),
            ("--quiet", "quiet"),
        ],
    )
    def test_parsed_args_boolean_flags(self, flag, attr, run_cmd):
        parser = run_cmd.get_parser("salishsea run")
        parsed_args = parser.parse_args(["foo", "baz", flag])
        assert getattr(parsed_args, attr)


@patch("salishsea_cmd.run.log")
@patch("salishsea_cmd.run.run", return_value="job submitted message")
class TestTakeAction:
    """Unit tests for `salishsea run` sub-command take_action() method.
    """

    def test_take_action(self, m_run, m_log, run_cmd):
        parsed_args = Mock(
            desc_file="desc file",
            results_dir="results dir",
            cedar_broadwell=False,
            deflate=False,
            max_deflate_jobs=4,
            nocheck_init=False,
            no_submit=False,
            separate_deflate=False,
            waitjob=0,
            quiet=False,
        )
        run_cmd.run(parsed_args)
        m_run.assert_called_once_with(
            "desc file",
            "results dir",
            cedar_broadwell=False,
            deflate=False,
            max_deflate_jobs=4,
            nocheck_init=False,
            no_submit=False,
            separate_deflate=False,
            waitjob=0,
            quiet=False,
        )
        m_log.info.assert_called_once_with("job submitted message")

    def test_take_action_quiet(self, m_run, m_log, run_cmd):
        parsed_args = Mock(desc_file="desc file", results_dir="results dir", quiet=True)
        run_cmd.run(parsed_args)
        assert not m_log.info.called


@patch("salishsea_cmd.run._submit_separate_deflate_jobs")
@patch("salishsea_cmd.run._submit_job")
@patch("salishsea_cmd.run._build_deflate_script", return_value="deflate script")
@patch("salishsea_cmd.run._build_tmp_run_dir")
@patch("salishsea_cmd.run._calc_run_segments")
@patch("salishsea_cmd.run._write_segment_namrun_namelist")
@patch("salishsea_cmd.run._write_segment_desc_file", return_value=({}, ""))
class TestRun:
    """Unit tests for `salishsea run` run() function.
    """

    @pytest.mark.parametrize(
        "sep_xios_server, xios_servers, system, queue_job_cmd, submit_job_msg",
        [
            (False, 0, "beluga", "sbatch", "Submitted batch job 43"),
            (True, 4, "beluga", "sbatch", "Submitted batch job 43"),
            (False, 0, "cedar", "sbatch", "Submitted batch job 43"),
            (True, 4, "cedar", "sbatch", "Submitted batch job 43"),
            (False, 0, "delta", "qsub -q mpi", "43.admin.default.domain"),
            (True, 4, "delta", "qsub -q mpi", "43.admin.default.domain"),
            (False, 0, "graham", "sbatch", "Submitted batch job 43"),
            (True, 4, "graham", "sbatch", "Submitted batch job 43"),
            (False, 0, "salish", "qsub", "43.master"),
            (True, 4, "salish", "qsub", "43.master"),
            (False, 0, "sigma", "qsub -q mpi", "43.admin.default.domain"),
            (True, 4, "sigma", "qsub -q mpi", "43.admin.default.domain"),
            (False, 0, "sockeye", "qsub", "43.pbsha"),
            (True, 4, "sockeye", "qsub", "43.pbsha"),
            (False, 0, "orcinus", "qsub", "43.orca2.ibb"),
            (True, 4, "orcinus", "qsub", "43.orca2.ibb"),
        ],
    )
    def test_run_submit(
        self,
        m_wsdf,
        m_wsnn,
        m_crs,
        m_btrd,
        m_bds,
        m_sj,
        m_ssdj,
        sep_xios_server,
        xios_servers,
        system,
        queue_job_cmd,
        submit_job_msg,
        tmpdir,
    ):
        p_run_dir = tmpdir.ensure_dir("run_dir")
        p_results_dir = tmpdir.ensure_dir("results_dir")
        m_crs.return_value = (
            [
                (
                    {
                        "output": {
                            "separate XIOS server": sep_xios_server,
                            "XIOS servers": xios_servers,
                        }
                    },
                    Path("SalishSea.yaml"),
                    Path(str(p_run_dir)),
                    {},
                )
            ],
            0,
        )
        m_btrd.return_value = (
            Path(str(p_run_dir)),
            Path(str(p_run_dir), "SalishSeaNEMO.sh"),
        )
        m_sj.return_value = submit_job_msg
        with patch("salishsea_cmd.run.SYSTEM", system):
            submit_job_msg = salishsea_cmd.run.run(
                Path("SalishSea.yaml"), Path(str(p_results_dir))
            )
        m_sj.assert_called_once_with(
            Path(str(p_run_dir), "SalishSeaNEMO.sh"), queue_job_cmd, waitjob="0"
        )
        assert submit_job_msg == submit_job_msg

    @pytest.mark.parametrize(
        "sep_xios_server, xios_servers, system, queue_job_cmd, submit_job_msg",
        [
            (False, 0, "beluga", "sbatch", "Submitted batch job 43"),
            (True, 4, "beluga", "sbatch", "Submitted batch job 43"),
            (False, 0, "cedar", "sbatch", "Submitted batch job 43"),
            (True, 4, "cedar", "sbatch", "Submitted batch job 43"),
            (False, 0, "delta", "qsub -q mpi", "43.admin.default.domain"),
            (True, 4, "delta", "qsub -q mpi", "43.admin.default.domain"),
            (False, 0, "graham", "sbatch", "Submitted batch job 43"),
            (True, 4, "graham", "sbatch", "Submitted batch job 43"),
            (False, 0, "salish", "qsub", "43.master"),
            (True, 4, "salish", "qsub", "43.master"),
            (False, 0, "sigma", "qsub -q mpi", "43.admin.default.domain"),
            (True, 4, "sigma", "qsub -q mpi", "43.admin.default.domain"),
            (False, 0, "sockeye", "qsub", "43.pbsha"),
            (True, 4, "sockeye", "qsub", "43.pbsha"),
            (False, 0, "orcinus", "qsub", "43.orca2.ibb"),
            (True, 4, "orcinus", "qsub", "43.orca2.ibb"),
        ],
    )
    def test_run_waitjob(
        self,
        m_wsdf,
        m_wsnn,
        m_crs,
        m_btrd,
        m_bds,
        m_sj,
        m_ssdj,
        sep_xios_server,
        xios_servers,
        system,
        queue_job_cmd,
        submit_job_msg,
        tmpdir,
    ):
        p_run_dir = tmpdir.ensure_dir("run_dir")
        p_results_dir = tmpdir.ensure_dir("results_dir")
        m_crs.return_value = (
            [
                (
                    {
                        "output": {
                            "separate XIOS server": sep_xios_server,
                            "XIOS servers": xios_servers,
                        }
                    },
                    Path("SalishSea.yaml"),
                    Path(str(p_run_dir)),
                    {},
                )
            ],
            0,
        )
        m_btrd.return_value = (
            Path(str(p_run_dir)),
            Path(str(p_run_dir), "SalishSeaNEMO.sh"),
        )
        m_sj.return_value = submit_job_msg
        with patch("salishsea_cmd.run.SYSTEM", system):
            submit_job_msg = salishsea_cmd.run.run(
                Path("SalishSea.yaml"), Path(str(p_results_dir)), waitjob=42
            )
        m_sj.assert_called_once_with(
            Path(str(p_run_dir), "SalishSeaNEMO.sh"), queue_job_cmd, waitjob=42
        )
        assert submit_job_msg == submit_job_msg

    @pytest.mark.parametrize("sep_xios_server, xios_servers", [(False, 0), (True, 4)])
    def test_run_no_submit(
        self,
        m_wsdf,
        m_wsnn,
        m_crs,
        m_btrd,
        m_bds,
        m_sj,
        m_ssdj,
        sep_xios_server,
        xios_servers,
        tmpdir,
    ):
        p_run_dir = tmpdir.ensure_dir("run_dir")
        p_results_dir = tmpdir.ensure_dir("results_dir")
        m_crs.return_value = (
            [
                (
                    {
                        "output": {
                            "separate XIOS server": sep_xios_server,
                            "XIOS servers": xios_servers,
                        }
                    },
                    Path("SalishSea.yaml"),
                    Path(str(p_run_dir)),
                    {},
                )
            ],
            0,
        )
        m_btrd.return_value = (
            Path(str(p_run_dir)),
            Path(str(p_run_dir), "SalishSeaNEMO.sh"),
        )
        with patch("salishsea_cmd.run.SYSTEM", "orcinus"):
            submit_job_msg = salishsea_cmd.run.run(
                Path("SalishSea.yaml"), Path(str(p_results_dir)), no_submit=True
            )
        assert not m_sj.called
        assert submit_job_msg is None

    @pytest.mark.parametrize("sep_xios_server, xios_servers", [(False, 0), (True, 4)])
    def test_run_no_submit_w_separate_deflate(
        self,
        m_wsdf,
        m_wsnn,
        m_crs,
        m_btrd,
        m_bds,
        m_sj,
        m_ssdj,
        sep_xios_server,
        xios_servers,
        tmpdir,
    ):
        p_run_dir = tmpdir.ensure_dir("run_dir")
        p_results_dir = tmpdir.ensure_dir("results_dir")
        m_crs.return_value = (
            [
                (
                    {
                        "output": {
                            "separate XIOS server": sep_xios_server,
                            "XIOS servers": xios_servers,
                        }
                    },
                    Path("SalishSea.yaml"),
                    Path(str(p_run_dir)),
                    {},
                )
            ],
            0,
        )
        m_btrd.return_value = (
            Path(str(p_run_dir)),
            Path(str(p_run_dir), "SalishSeaNEMO.sh"),
        )
        with patch("salishsea_cmd.run.SYSTEM", "orcinus"):
            submit_job_msg = salishsea_cmd.run.run(
                Path("SalishSea.yaml"),
                Path(str(p_results_dir)),
                no_submit=True,
                separate_deflate=True,
            )
        assert not m_sj.called
        assert submit_job_msg is None

    @pytest.mark.parametrize(
        "sep_xios_server, xios_servers, system, queue_job_cmd, submit_job_msg",
        [
            (False, 0, "beluga", "sbatch", "Submitted batch job 43"),
            (True, 4, "beluga", "sbatch", "Submitted batch job 43"),
            (False, 0, "cedar", "sbatch", "Submitted batch job 43"),
            (True, 4, "cedar", "sbatch", "Submitted batch job 43"),
            (False, 0, "delta", "qsub -q mpi", "43.admin.default.domain"),
            (True, 4, "delta", "qsub -q mpi", "43.admin.default.domain"),
            (False, 0, "graham", "sbatch", "Submitted batch job 43"),
            (True, 4, "graham", "sbatch", "Submitted batch job 43"),
            (False, 0, "salish", "qsub", "43.master"),
            (True, 4, "salish", "qsub", "43.master"),
            (False, 0, "sigma", "qsub -q mpi", "43.admin.default.domain"),
            (True, 4, "sigma", "qsub -q mpi", "43.admin.default.domain"),
            (False, 0, "sockeye", "qsub", "43.pbsha"),
            (True, 4, "sockeye", "qsub", "43.pbsha"),
            (False, 0, "orcinus", "qsub", "43.orca2.ibb"),
            (True, 4, "orcinus", "qsub", "43.orca2.ibb"),
        ],
    )
    def test_run_separate_deflate(
        self,
        m_wsdf,
        m_wsnn,
        m_crs,
        m_btrd,
        m_bds,
        m_sj,
        m_ssdj,
        sep_xios_server,
        xios_servers,
        system,
        queue_job_cmd,
        submit_job_msg,
        tmpdir,
    ):
        p_run_dir = tmpdir.ensure_dir("run_dir")
        p_results_dir = tmpdir.ensure_dir("results_dir")
        m_crs.return_value = (
            [
                (
                    {
                        "output": {
                            "separate XIOS server": sep_xios_server,
                            "XIOS servers": xios_servers,
                        }
                    },
                    Path("SalishSea.yaml"),
                    Path(str(p_run_dir)),
                    {},
                )
            ],
            0,
        )
        m_btrd.return_value = (
            Path(str(p_run_dir)),
            Path(str(p_run_dir), "SalishSeaNEMO.sh"),
        )
        m_sj.return_value = submit_job_msg
        with patch("salishsea_cmd.run.SYSTEM", system):
            submit_job_msg = salishsea_cmd.run.run(
                Path("SalishSea.yaml"), Path(str(p_results_dir)), separate_deflate=True
            )
        m_sj.assert_called_once_with(
            Path(str(p_run_dir), "SalishSeaNEMO.sh"), queue_job_cmd, waitjob="0"
        )
        assert m_ssdj.called
        assert submit_job_msg == submit_job_msg

    @pytest.mark.parametrize(
        "sep_xios_server, xios_servers, system, queue_job_cmd, job_msgs, submit_job_msg",
        [
            (
                False,
                0,
                "beluga",
                "sbatch",
                ("Submitted batch job 43", "Submitted batch job 44"),
                "Submitted batch job 43",
            ),
            (
                True,
                4,
                "beluga",
                "sbatch",
                ("Submitted batch job 43", "Submitted batch job 44"),
                "Submitted batch job 43",
            ),
            (
                False,
                0,
                "cedar",
                "sbatch",
                ("Submitted batch job 43", "Submitted batch job 44"),
                "Submitted batch job 43",
            ),
            (
                True,
                4,
                "cedar",
                "sbatch",
                ("Submitted batch job 43", "Submitted batch job 44"),
                "Submitted batch job 43",
            ),
            (
                False,
                0,
                "delta",
                "qsub -q mpi",
                ("43.admin.default.domain", "44.admin.default.domain"),
                "43.admin.default.domain",
            ),
            (
                True,
                4,
                "delta",
                "qsub -q mpi",
                ("43.admin.default.domain", "44.admin.default.domain"),
                "43.admin.default.domain",
            ),
            (
                False,
                0,
                "graham",
                "sbatch",
                ("Submitted batch job 43", "Submitted batch job 44"),
                "Submitted batch job 43",
            ),
            (
                True,
                4,
                "graham",
                "sbatch",
                ("Submitted batch job 43", "Submitted batch job 44"),
                "Submitted batch job 43",
            ),
            (False, 0, "salish", "qsub", ("43.master", "44.master"), "43.master"),
            (True, 4, "salish", "qsub", ("43.master", "44.master"), "43.master"),
            (
                False,
                0,
                "sigma",
                "qsub -q mpi",
                ("43.admin.default.domain", "44.admin.default.domain"),
                "43.admin.default.domain",
            ),
            (
                True,
                4,
                "sigma",
                "qsub -q mpi",
                ("43.admin.default.domain", "44.admin.default.domain"),
                "43.admin.default.domain",
            ),
            (
                False,
                0,
                "sockeye",
                "qsub",
                ("43.pbsha.ib.sockeye", "44.pbsha.ib.sockeye"),
                "43.pbsha.ib.sockeye",
            ),
            (
                True,
                4,
                "sockeye",
                "qsub",
                ("43.pbsha.ib.sockeye", "44.pbsha.ib.sockeye"),
                "43.pbsha.ib.sockeye",
            ),
            (
                False,
                0,
                "orcinus",
                "qsub",
                ("43.orca2.ibb", "44.orca2.ibb"),
                "43.orca2.ibb",
            ),
            (
                True,
                4,
                "orcinus",
                "qsub",
                ("43.orca2.ibb", "44.orca2.ibb"),
                "43.orca2.ibb",
            ),
        ],
    )
    def test_segmented_run_restart_dirs(
        self,
        m_wsdf,
        m_wsnn,
        m_crs,
        m_btrd,
        m_bds,
        m_sj,
        m_ssdj,
        sep_xios_server,
        xios_servers,
        system,
        queue_job_cmd,
        job_msgs,
        submit_job_msg,
        tmpdir,
    ):
        p_run_dir = tmpdir.ensure_dir("run_dir")
        p_results_dir = tmpdir.ensure_dir("results_dir")
        m_crs.return_value = (
            [
                (
                    yaml.safe_load(
                        StringIO(
                            """
                        run_id: 1_sensitivity

                        segmented run:
                            start date: 2014-11-25
                            start time step: 152634
                            end date: 2014-12-02
                            days per segment: 10
                            first segment number: 1
                            segment walltime: 12:00:00
                            namelists:
                                namrun: ./namelist.time
                                namdom: $PROJECT/SS-run-sets/v201812/namelist.domain
                    """
                        )
                    ),
                    "SalishSea_1.yaml",
                    Path("results_dir_1"),
                    {
                        "namrun": {
                            "nn_it000": 152634,
                            "nn_itend": 152634 + 2160 * 10 - 1,
                            "nn_date0": 20141115,
                        }
                    },
                ),
                (
                    yaml.safe_load(
                        StringIO(
                            """
                        run_id: 2_sensitivity

                        segmented run:
                            start date: 2014-11-25
                            start time step: 152634
                            end date: 2014-12-02
                            days per segment: 10
                            first segment number: 1
                            segment walltime: 12:00:00
                            namelists:
                                namrun: ./namelist.time
                                namdom: $PROJECT/SS-run-sets/v201812/namelist.domain
                    """
                        )
                    ),
                    "SalishSea_2.yaml",
                    Path("results_dir_2"),
                    {
                        "namrun": {
                            "nn_it000": 152634 + 2160 * 10,
                            "nn_itend": 152634 + 2160 * 17 - 1,
                            "nn_date0": 20141125,
                        }
                    },
                ),
            ],
            1,
        )
        m_btrd.return_value = (
            Path(str(p_run_dir)),
            Path(str(p_run_dir), "SalishSeaNEMO.sh"),
        )
        m_sj.side_effect = job_msgs
        with patch("salishsea_cmd.run.SYSTEM", system):
            submit_job_msg = salishsea_cmd.run.run(
                Path("SalishSea.yaml"), Path(str(p_results_dir))
            )
        assert m_wsdf.call_args_list[1][0][2] == Path("results_dir_1")

    @pytest.mark.parametrize(
        "sep_xios_server, xios_servers, system, queue_job_cmd, job_msgs, submit_job_msg",
        [
            (
                False,
                0,
                "beluga",
                "sbatch",
                ("Submitted batch job 43", "Submitted batch job 44"),
                "Submitted batch job 43",
            ),
            (
                True,
                4,
                "beluga",
                "sbatch",
                ("Submitted batch job 43", "Submitted batch job 44"),
                "Submitted batch job 43",
            ),
            (
                False,
                0,
                "cedar",
                "sbatch",
                ("Submitted batch job 43", "Submitted batch job 44"),
                "Submitted batch job 43",
            ),
            (
                True,
                4,
                "cedar",
                "sbatch",
                ("Submitted batch job 43", "Submitted batch job 44"),
                "Submitted batch job 43",
            ),
            (
                False,
                0,
                "delta",
                "qsub -q mpi",
                ("43.admin.default.domain", "44.admin.default.domain"),
                "43.admin.default.domain",
            ),
            (
                True,
                4,
                "delta",
                "qsub -q mpi",
                ("43.admin.default.domain", "44.admin.default.domain"),
                "43.admin.default.domain",
            ),
            (
                False,
                0,
                "graham",
                "sbatch",
                ("Submitted batch job 43", "Submitted batch job 44"),
                "Submitted batch job 43",
            ),
            (
                True,
                4,
                "graham",
                "sbatch",
                ("Submitted batch job 43", "Submitted batch job 44"),
                "Submitted batch job 43",
            ),
            (False, 0, "salish", "qsub", ("43.master", "44.master"), "43.master"),
            (True, 4, "salish", "qsub", ("43.master", "44.master"), "43.master"),
            (
                False,
                0,
                "sigma",
                "qsub -q mpi",
                ("43.admin.default.domain", "44.admin.default.domain"),
                "43.admin.default.domain",
            ),
            (
                True,
                4,
                "sigma",
                "qsub -q mpi",
                ("43.admin.default.domain", "44.admin.default.domain"),
                "43.admin.default.domain",
            ),
            (
                True,
                4,
                "sockeye",
                "qsub",
                ("43.pbsha.ib.sockeye", "44.pbsha.ib.sockeye"),
                "43.pbsha.ib.sockeye",
            ),
            (
                False,
                0,
                "orcinus",
                "qsub",
                ("43.orca2.ibb", "44.orca2.ibb"),
                "43.orca2.ibb",
            ),
            (
                False,
                0,
                "orcinus",
                "qsub",
                ("43.orca2.ibb", "44.orca2.ibb"),
                "43.orca2.ibb",
            ),
            (
                True,
                4,
                "orcinus",
                "qsub",
                ("43.orca2.ibb", "44.orca2.ibb"),
                "43.orca2.ibb",
            ),
        ],
    )
    def test_segmented_run_submits(
        self,
        m_wsdf,
        m_wsnn,
        m_crs,
        m_btrd,
        m_bds,
        m_sj,
        m_ssdj,
        sep_xios_server,
        xios_servers,
        system,
        queue_job_cmd,
        job_msgs,
        submit_job_msg,
        tmpdir,
    ):
        p_run_dir = tmpdir.ensure_dir("run_dir")
        p_results_dir = tmpdir.ensure_dir("results_dir")
        m_crs.return_value = (
            [
                (
                    yaml.safe_load(
                        StringIO(
                            """
                        run_id: 0_sensitivity
                        
                        segmented run:
                            start date: 2014-11-15
                            start time step: 152634
                            end date: 2014-12-02
                            days per segment: 10
                            first segment number: 0
                            segment walltime: 12:00:00
                            namelists:
                                namrun: ./namelist.time
                                namdom: $PROJECT/SS-run-sets/v201812/namelist.domain
                    """
                        )
                    ),
                    "SalishSea_0.yaml",
                    Path("results_dir_0"),
                    {
                        "namrun": {
                            "nn_it000": 152634,
                            "nn_itend": 152634 + 2160 * 10 - 1,
                            "nn_date0": 20141115,
                        }
                    },
                ),
                (
                    yaml.safe_load(
                        StringIO(
                            """
                        run_id: 1_sensitivity
    
                        segmented run:
                            start date: 2014-11-15
                            start time step: 152634
                            end date: 2014-12-02
                            days per segment: 10
                            first segment number: 0
                            segment walltime: 12:00:00
                            namelists:
                                namrun: ./namelist.time
                                namdom: $PROJECT/SS-run-sets/v201812/namelist.domain
                    """
                        )
                    ),
                    "SalishSea_1.yaml",
                    Path("results_dir_1"),
                    {
                        "namrun": {
                            "nn_it000": 152634 + 2160 * 10,
                            "nn_itend": 152634 + 2160 * 17 - 1,
                            "nn_date0": 20141125,
                        }
                    },
                ),
            ],
            0,
        )
        m_btrd.return_value = (
            Path(str(p_run_dir)),
            Path(str(p_run_dir), "SalishSeaNEMO.sh"),
        )
        m_sj.side_effect = job_msgs
        with patch("salishsea_cmd.run.SYSTEM", system):
            submit_job_msg = salishsea_cmd.run.run(
                Path("SalishSea.yaml"), Path(str(p_results_dir))
            )
        assert m_sj.call_args_list == [
            call(Path(str(p_run_dir), "SalishSeaNEMO.sh"), queue_job_cmd, waitjob="0"),
            call(
                Path(str(p_run_dir), "SalishSeaNEMO.sh"),
                queue_job_cmd,
                waitjob=job_msgs[0],
            ),
        ]
        expected = "Submitted jobs"
        for job_msg in job_msgs:
            expected = " ".join((expected, job_msg.split()[-1]))
        assert submit_job_msg == expected


@patch("salishsea_cmd.run.load_run_desc")
@patch("salishsea_cmd.run.f90nml.read", return_value={"namdom": {"rn_rdt": 40.0}})
class TestCalcRunSegments:
    """Unit tests for _calc_run_segments() function.
    """

    def test_not_segmented_run(self, m_f90nml_read, m_lrd):
        m_lrd.return_value = {}
        run_segments, first_seg_no = salishsea_cmd.run._calc_run_segments(
            Path("SalishSea.yaml"), Path("results_dir")
        )
        assert run_segments == [
            (m_lrd(), Path("SalishSea.yaml"), Path("results_dir"), {})
        ]
        assert first_seg_no == 0

    def test_no_run_id(self, m_f90nml_read, m_lrd):
        m_lrd.return_value = yaml.safe_load(
            StringIO(
                """
            segmented run:
                start date: 2014-11-15
                start time step: 152634
                end date: 2014-12-02
                days per segment: 10
                first segment number: 0
                segment walltime: 12:00:00
                namelists:
                    namrun: ./namelist.time
                    namdom: $PROJECT/SS-run-sets/v201812/namelist.domain
        """
            )
        )
        with pytest.raises(SystemExit):
            salishsea_cmd.run._calc_run_segments(
                Path("SalishSea.yaml"), Path("results_dir")
            )

    def test_no_start_date(self, m_f90nml_read, m_lrd):
        m_lrd.return_value = yaml.safe_load(
            StringIO(
                """
            run_id: sensitivity

            segmented run:

                start time step: 152634
                end date: 2014-12-02
                days per segment: 10
                first segment number: 0
                segment walltime: 12:00:00
                namelists:
                    namrun: ./namelist.time
                    namdom: $PROJECT/SS-run-sets/v201812/namelist.domain
        """
            )
        )
        with pytest.raises(SystemExit):
            salishsea_cmd.run._calc_run_segments(
                Path("SalishSea.yaml"), Path("results_dir")
            )

    def test_no_start_time_step(self, m_f90nml_read, m_lrd):
        m_lrd.return_value = yaml.safe_load(
            StringIO(
                """
            run_id: sensitivity

            segmented run:
                start date: 2014-11-15

                end date: 2014-12-02
                days per segment: 10
                first segment number: 0
                segment walltime: 12:00:00
                namelists:
                    namrun: ./namelist.time
                    namdom: $PROJECT/SS-run-sets/v201812/namelist.domain
        """
            )
        )
        with pytest.raises(SystemExit):
            salishsea_cmd.run._calc_run_segments(
                Path("SalishSea.yaml"), Path("results_dir")
            )

    def test_no_end_date(self, m_f90nml_read, m_lrd):
        m_lrd.return_value = yaml.safe_load(
            StringIO(
                """
            run_id: sensitivity

            segmented run:
                start date: 2014-11-15
                start time step: 152634

                days per segment: 10
                first segment number: 0
                segment walltime: 12:00:00
                namelists:
                    namrun: ./namelist.time
                    namdom: $PROJECT/SS-run-sets/v201812/namelist.domain
        """
            )
        )
        with pytest.raises(SystemExit):
            salishsea_cmd.run._calc_run_segments(
                Path("SalishSea.yaml"), Path("results_dir")
            )

    def test_no_days_per_segment(self, m_f90nml_read, m_lrd):
        m_lrd.return_value = yaml.safe_load(
            StringIO(
                """
            run_id: sensitivity

            segmented run:
                start date: 2014-11-15
                start time step: 152634
                end date: 2014-12-02
                
                first segment number: 0
                segment walltime: 12:00:00
                namelists:
                    namrun: ./namelist.time
                    namdom: $PROJECT/SS-run-sets/v201812/namelist.domain
        """
            )
        )
        with pytest.raises(SystemExit):
            salishsea_cmd.run._calc_run_segments(
                Path("SalishSea.yaml"), Path("results_dir")
            )

    def test_no_first_segment_number(self, m_f90nml_read, m_lrd):
        m_lrd.return_value = yaml.safe_load(
            StringIO(
                """
            run_id: sensitivity

            segmented run:
                start date: 2014-11-15
                start time step: 152634
                end date: 2014-12-02
                days per segment: 10
                
                segment walltime: 12:00:00
                namelists:
                    namrun: ./namelist.time
                    namdom: $PROJECT/SS-run-sets/v201812/namelist.domain
        """
            )
        )
        with pytest.raises(SystemExit):
            salishsea_cmd.run._calc_run_segments(
                Path("SalishSea.yaml"), Path("results_dir")
            )

    def test_no_namdom_namelist(self, m_f90nml_read, m_lrd):
        m_lrd.return_value = yaml.safe_load(
            StringIO(
                """
            run_id: sensitivity

            segmented run:
                start date: 2014-11-15
                start time step: 152634
                end date: 2014-12-02
                days per segment: 10
                first segment number: 0
                segment walltime: 12:00:00
                namelists:
                    namrun: ./namelist.time
                    
        """
            )
        )
        with pytest.raises(SystemExit):
            salishsea_cmd.run._calc_run_segments(
                Path("SalishSea.yaml"), Path("results_dir")
            )

    @pytest.mark.parametrize("first_seg_no", (0, 3))
    def test_run_segments(self, m_f90nml_read, m_lrd, first_seg_no):
        m_lrd.return_value = yaml.safe_load(
            StringIO(
                """
            run_id: sensitivity
            
            segmented run:
                start date: 2014-11-15
                start time step: 152634
                end date: 2014-12-02
                days per segment: 10
                first segment number: {first_seg_no}
                segment walltime: 12:00:00
                namelists:
                    namrun: ./namelist.time
                    namdom: $PROJECT/SS-run-sets/v201812/namelist.domain
        """.format(
                    first_seg_no=first_seg_no
                )
            )
        )
        run_segments, first_seg_no_ = salishsea_cmd.run._calc_run_segments(
            Path("SalishSea.yaml"), Path("results_dir")
        )
        expected = [
            (
                yaml.safe_load(
                    StringIO(
                        """
                    run_id: {seg_no}_sensitivity
                    
                    segmented run:
                        start date: 2014-11-15
                        start time step: 152634
                        end date: 2014-12-02
                        days per segment: 10
                        first segment number: {seg_no}
                        segment walltime: 12:00:00
                        namelists:
                            namrun: ./namelist.time
                            namdom: $PROJECT/SS-run-sets/v201812/namelist.domain
                """.format(
                            seg_no=first_seg_no
                        )
                    )
                ),
                "SalishSea_{seg_no}.yaml".format(seg_no=first_seg_no),
                Path("results_dir_{seg_no}".format(seg_no=first_seg_no)),
                {
                    "namrun": {
                        "nn_it000": 152634,
                        "nn_itend": 152634 + 2160 * 10 - 1,
                        "nn_date0": 20141115,
                    }
                },
            ),
            (
                yaml.safe_load(
                    StringIO(
                        """
                    run_id: {seg_no}_sensitivity

                    segmented run:
                        start date: 2014-11-15
                        start time step: 152634
                        end date: 2014-12-02
                        days per segment: 10
                        first segment number: {first_seg_no}
                        segment walltime: 12:00:00
                        namelists:
                            namrun: ./namelist.time
                            namdom: $PROJECT/SS-run-sets/v201812/namelist.domain
                """.format(
                            first_seg_no=first_seg_no, seg_no=first_seg_no + 1
                        )
                    )
                ),
                "SalishSea_{seg_no}.yaml".format(seg_no=first_seg_no + 1),
                Path("results_dir_{seg_no}".format(seg_no=first_seg_no + 1)),
                {
                    "namrun": {
                        "nn_it000": 152634 + 2160 * 10,
                        "nn_itend": 152634 + 2160 * 18 - 1,
                        "nn_date0": 20141125,
                    }
                },
            ),
        ]
        assert run_segments == expected
        assert first_seg_no_ == first_seg_no

    def test_final_run_segment(self, m_f90nml_read, m_lrd):
        m_lrd.return_value = yaml.safe_load(
            StringIO(
                textwrap.dedent(
                    """\
                run_id: SKOG_2016_BASE
                
                segmented run:
                  start date: 2016-04-30
                  start time step: 2730241
                  end date: 2016-12-31
                  days per segment: 30
                  first segment number: 0
                  segment walltime: 12:00:00
                  namelists:
                    namrun: ./namelist.time
                    namdom: $PROJECT/SalishSeaCast/hindcast-sys/SS-run-sets/v201812/namelist.domain
                """
                )
            )
        )
        run_segments, first_seg_no = salishsea_cmd.run._calc_run_segments(
            Path("BR5_12SKOG2016.yaml"), Path("SKOG_C")
        )
        expected = (
            yaml.safe_load(
                StringIO(
                    textwrap.dedent(
                        """\
                    run_id: 8_SKOG_2016_BASE

                    segmented run:
                      start date: 2016-04-30
                      start time step: 2730241
                      end date: 2016-12-31
                      days per segment: 30
                      first segment number: 0
                      segment walltime: 12:00:00
                      namelists:
                        namrun: ./namelist.time
                        namdom: $PROJECT/SalishSeaCast/hindcast-sys/SS-run-sets/v201812/namelist.domain
                    """
                    )
                )
            ),
            "BR5_12SKOG2016_8.yaml",
            Path("SKOG_C_8"),
            {
                "namrun": {
                    "nn_it000": 3248641,
                    "nn_itend": 3261600,
                    "nn_date0": 20161226,
                }
            },
        )
        assert run_segments[-1] == expected


class TestCalcNSegments:
    """Unit tests for _calc_n_segments() function.
    """

    @pytest.mark.parametrize(
        "run_desc, expected",
        [
            (
                {
                    "segmented run": {
                        "start date": "2014-11-21",
                        "end date": "2014-11-22",
                        "days per segment": 1,
                    }
                },
                2,
            ),
            (
                {
                    "segmented run": {
                        "start date": "2014-11-15",
                        "end date": "2014-11-16",
                        "days per segment": 10,
                    }
                },
                1,
            ),
            (
                {
                    "segmented run": {
                        "start date": "2014-11-15",
                        "end date": "2014-11-24",
                        "days per segment": 10,
                    }
                },
                1,
            ),
            (
                {
                    "segmented run": {
                        "start date": "2014-11-15",
                        "end date": "2014-11-25",
                        "days per segment": 10,
                    }
                },
                2,
            ),
            (
                {
                    "segmented run": {
                        "start date": "2014-11-15",
                        "end date": "2014-12-02",
                        "days per segment": 10,
                    }
                },
                2,
            ),
            (
                {
                    "segmented run": {
                        "start date": "2016-04-30",
                        "end date": "2016-12-31",
                        "days per segment": 30,
                    }
                },
                9,
            ),
        ],
    )
    def test_calc_n_segments(self, run_desc, expected):
        assert salishsea_cmd.run._calc_n_segments(run_desc) == expected

    @pytest.mark.parametrize(
        "run_desc",
        [
            {"segmented run": {"end date": "2014-11-16", "days per segment": 10}},
            {"segmented run": {"start date": "2014-11-15", "days per segment": 10}},
            {"segmented run": {"start date": "2014-11-15", "end date": "2014-11-25"}},
        ],
    )
    def test_bad_run_desc(self, run_desc):
        with pytest.raises(SystemExit):
            salishsea_cmd.run._calc_n_segments(run_desc)


class TestWriteSegmentNamerunNamelist:
    """Unit tests for _write_segment_namerun_namelist() function.
    """

    def test_no_namrun_namelist(self):
        run_desc = yaml.safe_load(
            StringIO(
                """
            run_id: sensitivity

            segmented run:
                start date: 2014-11-15
                start time step: 152634
                end date: 2014-12-02
                days per segment: 10
                walltime: 12:00:00
                namelists:

                    namdom: $PROJECT/SS-run-sets/v201812/namelist.domain
            """
            )
        )
        with tempfile.TemporaryDirectory() as tmp_run_desc_dir:
            with pytest.raises(SystemExit):
                salishsea_cmd.run._write_segment_namrun_namelist(
                    run_desc, {}, Path(tmp_run_desc_dir)
                )

    def test_write_segment_namrun_namelist(self, tmp_path):
        namelist_time = tmp_path / "namelist.time"
        namelist_time.write_text(
            """
            &namrun
                nn_it000 = 0
                nn_itend = 0
                nn_date0 = 0
            &end
            """
        )
        run_desc = yaml.safe_load(
            StringIO(
                """
            run_id: sensitivity

            segmented run:
                start date: 2014-11-15
                start time step: 152634
                end date: 2014-12-02
                days per segment: 10
                walltime: 12:00:00
                namelists:
                    namrun: ./namelist.time
                    namdom: $PROJECT/SS-run-sets/v201812/namelist.domain
        """
            )
        )
        run_desc["segmented run"]["namelists"]["namrun"] = os.fspath(namelist_time)
        namelist_namrun_patch = {
            "namrun": {
                "nn_it000": 152634,
                "nn_itend": 152634 + 2160 * 10 - 1,
                "nn_date0": 20141115,
            }
        }
        with tempfile.TemporaryDirectory() as tmp_run_desc_dir:
            segment_namrun = salishsea_cmd.run._write_segment_namrun_namelist(
                run_desc, namelist_namrun_patch, Path(tmp_run_desc_dir)
            )
            assert segment_namrun == Path(tmp_run_desc_dir, "namelist.time")
            nml = f90nml.read(segment_namrun)
            assert nml["namrun"]["nn_it000"] == 152634
            assert nml["namrun"]["nn_itend"] == 152634 + 2160 * 10 - 1
            assert nml["namrun"]["nn_date0"] == 20141115


class TestWriteSegmentDescFile:
    """Unit test for _write_segment_desc_file() function.
    """

    def test_run_desc_file(self, tmp_path):
        run_desc = yaml.safe_load(
            StringIO(
                """
            run_id: sensitivity
            walltime: 24:00:00

            segmented run:
                start date: 2014-11-15
                start time step: 152634
                end date: 2014-12-02
                days per segment: 10
                segment walltime: 12:00:00
                namelists:
                    namrun: ./namelist.time
                    namdom: $PROJECT/SS-run-sets/v201812/namelist.domain
                    
            namelists:
                namelist_cfg:
                    - ./namelist.time
                    
            restart:
                restart.nc: $PROJECT/$USER/MEOPAR/results/14nov14/SalishSea_00152633_restart.nc
                restart_trc.nc: $PROJECT/$USER/MEOPAR/results/14nov14/SalishSea_00152633_restart_trc.nc
        """
            )
        )

        with tempfile.TemporaryDirectory() as tmp_run_desc_dir:
            segment_namrun = Path(tmp_run_desc_dir, "namelist.time")
            segment_namrun.write_text(
                """
                &namrun
                    nn_it000 = 174234
                    nn_itend = 189353
                    nn_date0 = 20141125
                &end
                """
            )
            run_desc, segment_desc_file = salishsea_cmd.run._write_segment_desc_file(
                run_desc,
                "SalishSea_1.yaml",
                Path("results_dir_0"),
                segment_namrun,
                Path(tmp_run_desc_dir),
            )
            assert segment_desc_file == Path(tmp_run_desc_dir, "SalishSea_1.yaml")
            assert Path(tmp_run_desc_dir, "SalishSea_1.yaml").exists()

    def test_namrun_namelist_path(self, tmp_path):
        run_desc = yaml.safe_load(
            StringIO(
                """
            run_id: sensitivity
            walltime: 24:00:00

            segmented run:
                start date: 2014-11-15
                start time step: 152634
                end date: 2014-12-02
                days per segment: 10
                segment walltime: 12:00:00
                namelists:
                    namrun: ./namelist.time
                    namdom: $PROJECT/SS-run-sets/v201812/namelist.domain
                    
            namelists:
                namelist_cfg:
                    - ./namelist.time
                    
            restart:
                restart.nc: $PROJECT/$USER/MEOPAR/results/14nov14/SalishSea_00152633_restart.nc
                restart_trc.nc: $PROJECT/$USER/MEOPAR/results/14nov14/SalishSea_00152633_restart_trc.nc
        """
            )
        )

        with tempfile.TemporaryDirectory() as tmp_run_desc_dir:
            segment_namrun = Path(tmp_run_desc_dir, "namelist.time")
            segment_namrun.write_text(
                """
                &namrun
                    nn_it000 = 174234
                    nn_itend = 189353
                    nn_date0 = 20141125
                &end
                """
            )
            run_desc, segment_desc_file = salishsea_cmd.run._write_segment_desc_file(
                run_desc,
                "SalishSea_1.yaml",
                Path("results_dir_0"),
                segment_namrun,
                Path(tmp_run_desc_dir),
            )
            assert run_desc["namelists"]["namelist_cfg"][0] == os.fspath(segment_namrun)

    @pytest.mark.parametrize("nemo_exp", ("SalishSea", "SKOG"))
    def test_segment_0_restart_files_path(self, nemo_exp, tmp_path):
        run_desc = yaml.safe_load(
            StringIO(
                """
            run_id: sensitivity
            walltime: 24:00:00

            segmented run:
                start date: 2014-11-15
                start time step: 152634
                end date: 2014-12-02
                days per segment: 10
                segment walltime: 12:00:00
                namelists:
                    namrun: ./namelist.time
                    namdom: $PROJECT/SS-run-sets/v201812/namelist.domain
                    
            namelists:
                namelist_cfg:
                    - ./namelist.time
                    
            restart:
                restart.nc: $PROJECT/$USER/MEOPAR/results/14nov14/{nemo_exp}_00152633_restart.nc
                restart_trc.nc: $PROJECT/$USER/MEOPAR/results/14nov14/{nemo_exp}_00152633_restart_trc.nc
        """.format(
                    nemo_exp=nemo_exp
                )
            )
        )
        with tempfile.TemporaryDirectory() as tmp_run_desc_dir:
            segment_namrun = Path(tmp_run_desc_dir, "namelist.time")
            segment_namrun.write_text(
                """
                &namrun
                    nn_it000 = 174234
                    nn_itend = 189353
                    nn_date0 = 20141125
                &end
                """
            )
            run_desc, segment_desc_file = salishsea_cmd.run._write_segment_desc_file(
                run_desc,
                "SalishSea_1.yaml",
                None,
                segment_namrun,
                Path(tmp_run_desc_dir),
            )
        expected = "$PROJECT/$USER/MEOPAR/results/14nov14/{nemo_exp}_00152633_restart.nc".format(
            nemo_exp=nemo_exp
        )
        assert run_desc["restart"]["restart.nc"] == expected
        expected = "$PROJECT/$USER/MEOPAR/results/14nov14/{nemo_exp}_00152633_restart_trc.nc".format(
            nemo_exp=nemo_exp
        )
        assert run_desc["restart"]["restart_trc.nc"] == expected

    @pytest.mark.parametrize("nemo_exp", ("SalishSea", "SKOG"))
    def test_restart_files_path(self, nemo_exp, tmp_path):
        run_desc = yaml.safe_load(
            StringIO(
                """
            run_id: sensitivity
            walltime: 24:00:00

            segmented run:
                start date: 2014-11-15
                start time step: 152634
                end date: 2014-12-02
                days per segment: 10
                segment walltime: 12:00:00
                namelists:
                    namrun: ./namelist.time
                    namdom: $PROJECT/SS-run-sets/v201812/namelist.domain
                    
            namelists:
                namelist_cfg:
                    - ./namelist.time
                    
            restart:
                restart.nc: $PROJECT/$USER/MEOPAR/results/14nov14/{nemo_exp}_00152633_restart.nc
                restart_trc.nc: $PROJECT/$USER/MEOPAR/results/14nov14/{nemo_exp}_00152633_restart_trc.nc
        """.format(
                    nemo_exp=nemo_exp
                )
            )
        )
        with tempfile.TemporaryDirectory() as tmp_run_desc_dir:
            segment_namrun = Path(tmp_run_desc_dir, "namelist.time")
            segment_namrun.write_text(
                """
                &namrun
                    nn_it000 = 174234
                    nn_itend = 189353
                    nn_date0 = 20141125
                &end
                """
            )
            run_desc, segment_desc_file = salishsea_cmd.run._write_segment_desc_file(
                run_desc,
                "SalishSea_1.yaml",
                Path("$PROJECT/$USER/MEOPAR/results/results_dir_0"),
                segment_namrun,
                Path(tmp_run_desc_dir),
            )
        expected = "$PROJECT/$USER/MEOPAR/results/results_dir_0/{nemo_exp}_00174233_restart.nc".format(
            nemo_exp=nemo_exp
        )
        assert run_desc["restart"]["restart.nc"] == expected
        expected = "$PROJECT/$USER/MEOPAR/results/results_dir_0/{nemo_exp}_00174233_restart_trc.nc".format(
            nemo_exp=nemo_exp
        )
        assert run_desc["restart"]["restart_trc.nc"] == expected

    def test_no_segment_walltime(self, tmp_path):
        run_desc = yaml.safe_load(
            StringIO(
                """
            run_id: sensitivity
            walltime: 24:00:00

            segmented run:
                start date: 2014-11-15
                start time step: 152634
                end date: 2014-12-02
                days per segment: 10
                
                namelists:
                    namrun: ./namelist.time
                    namdom: $PROJECT/SS-run-sets/v201812/namelist.domain
                    
            namelists:
                namelist_cfg:
                    - ./namelist.time
                    
            restart:
                restart.nc: $PROJECT/$USER/MEOPAR/results/14nov14/SalishSea_00152633_restart.nc
                restart_trc.nc: $PROJECT/$USER/MEOPAR/results/14nov14/SalishSea_00152633_restart_trc.nc
        """
            )
        )
        with tempfile.TemporaryDirectory() as tmp_run_desc_dir:
            segment_namrun = Path(tmp_run_desc_dir, "namelist.time")
            segment_namrun.write_text(
                """
                &namrun
                    nn_it000 = 174234
                    nn_itend = 189353
                    nn_date0 = 20141125
                &end
                """
            )
            with pytest.raises(SystemExit):
                salishsea_cmd.run._write_segment_desc_file(
                    run_desc,
                    "SalishSea_1.yaml",
                    Path("$PROJECT/$USER/MEOPAR/results/results_dir_0"),
                    segment_namrun,
                    Path(tmp_run_desc_dir),
                )

    def test_segment_walltime(self, tmp_path):
        run_desc = yaml.safe_load(
            StringIO(
                """
            run_id: sensitivity
            walltime: 24:00:00

            segmented run:
                start date: 2014-11-15
                start time step: 152634
                end date: 2014-12-02
                days per segment: 10
                segment walltime: 12:00:00
                namelists:
                    namrun: ./namelist.time
                    namdom: $PROJECT/SS-run-sets/v201812/namelist.domain
                    
            namelists:
                namelist_cfg:
                    - ./namelist.time
                    
            restart:
                restart.nc: $PROJECT/$USER/MEOPAR/results/14nov14/SalishSea_00152633_restart.nc
                restart_trc.nc: $PROJECT/$USER/MEOPAR/results/14nov14/SalishSea_00152633_restart_trc.nc
        """
            )
        )
        with tempfile.TemporaryDirectory() as tmp_run_desc_dir:
            segment_namrun = Path(tmp_run_desc_dir, "namelist.time")
            segment_namrun.write_text(
                """
                &namrun
                    nn_it000 = 174234
                    nn_itend = 189353
                    nn_date0 = 20141125
                &end
                """
            )
            run_desc, segment_desc_file = salishsea_cmd.run._write_segment_desc_file(
                run_desc,
                "SalishSea_1.yaml",
                Path("$PROJECT/$USER/MEOPAR/results/results_dir_0"),
                segment_namrun,
                Path(tmp_run_desc_dir),
            )
        assert run_desc["walltime"] == 43200


@patch("salishsea_cmd.run.log", autospec=True)
@patch("salishsea_cmd.run._build_deflate_script", return_value="deflate script")
@patch("salishsea_cmd.run._build_batch_script", return_value="batch script")
@patch("salishsea_cmd.run.get_n_processors", return_value=144)
@patch("salishsea_cmd.run.api.prepare")
@pytest.mark.parametrize("sep_xios_server, xios_servers", [(False, 0), (True, 4)])
class TestBuildTmpRunDir:
    """Unit tests for _build_tmp_run_dir() function.
    """

    def test_build_tmp_run_dir(
        self,
        m_prepare,
        m_gnp,
        m_bbs,
        m_bds,
        m_log,
        sep_xios_server,
        xios_servers,
        tmpdir,
    ):
        p_run_dir = tmpdir.ensure_dir("run_dir")
        m_prepare.return_value = Path(str(p_run_dir))
        run_desc = {
            "output": {
                "separate XIOS server": sep_xios_server,
                "XIOS servers": xios_servers,
            }
        }
        run_dir, batch_file = salishsea_cmd.run._build_tmp_run_dir(
            run_desc,
            Path("SalishSea.yaml"),
            Path("results_dir"),
            cedar_broadwell=False,
            deflate=False,
            max_deflate_jobs=4,
            separate_deflate=False,
            nocheck_init=False,
            quiet=False,
        )
        assert p_run_dir.join("SalishSeaNEMO.sh").check(file=True)
        assert run_dir == Path(str(p_run_dir))
        assert batch_file == Path(str(p_run_dir)) / "SalishSeaNEMO.sh"

    def test_build_tmp_run_dir_quiet(
        self,
        m_prepare,
        m_gnp,
        m_bbs,
        m_bds,
        m_log,
        sep_xios_server,
        xios_servers,
        tmpdir,
    ):
        p_run_dir = tmpdir.ensure_dir("run_dir")
        m_prepare.return_value = Path(str(p_run_dir))
        run_desc = {
            "output": {
                "separate XIOS server": sep_xios_server,
                "XIOS servers": xios_servers,
            }
        }
        run_dir, batch_file = salishsea_cmd.run._build_tmp_run_dir(
            run_desc,
            Path("SalishSea.yaml"),
            Path("results_dir"),
            cedar_broadwell=False,
            deflate=False,
            max_deflate_jobs=4,
            separate_deflate=False,
            nocheck_init=False,
            quiet=True,
        )
        assert not m_log.info.called
        assert p_run_dir.join("SalishSeaNEMO.sh").check(file=True)
        assert run_dir == Path(str(p_run_dir))
        assert batch_file == Path(str(p_run_dir)) / "SalishSeaNEMO.sh"

    def test_build_tmp_run_dir_separate_deflate(
        self,
        m_prepare,
        m_gnp,
        m_bbs,
        m_bds,
        m_log,
        sep_xios_server,
        xios_servers,
        tmpdir,
    ):
        p_run_dir = tmpdir.ensure_dir("run_dir")
        m_prepare.return_value = Path(str(p_run_dir))
        run_desc = {
            "output": {
                "separate XIOS server": sep_xios_server,
                "XIOS servers": xios_servers,
            }
        }
        run_dir, batch_file = salishsea_cmd.run._build_tmp_run_dir(
            run_desc,
            Path("SalishSea.yaml"),
            Path("results_dir"),
            cedar_broadwell=False,
            deflate=False,
            max_deflate_jobs=4,
            separate_deflate=True,
            nocheck_init=False,
            quiet=False,
        )
        assert p_run_dir.join("SalishSeaNEMO.sh").check(file=True)
        assert p_run_dir.join("deflate_grid.sh").check(file=True)
        assert p_run_dir.join("deflate_ptrc.sh").check(file=True)
        assert p_run_dir.join("deflate_dia.sh").check(file=True)
        assert run_dir == Path(str(p_run_dir))
        assert batch_file == Path(str(p_run_dir)) / "SalishSeaNEMO.sh"


@patch("salishsea_cmd.run.subprocess.run")
@pytest.mark.parametrize(
    "queue_job_cmd, depend_flag, depend_option, submit_job_msg",
    [
        ("sbatch", "-d", "afterok", "Submitted batch job 43"),
        ("qsub", "-W", "depend=afterok", "43.orca2.ibb"),
        ("qsub -q mpi", "-W", "depend=afterok", "43.admin.default.domain"),
    ],
)
class TestSubmitJob:
    """Unit tests for _submit_job() function.
    """

    def test_submit_job(
        self, m_run, queue_job_cmd, depend_flag, depend_option, submit_job_msg
    ):
        submit_job_msg = salishsea_cmd.run._submit_job(
            Path("run_dir", "SalishSeaNEMO.sh"), queue_job_cmd, "0"
        )
        m_run.assert_called_once_with(
            shlex.split(
                "{queue_job_cmd} {run_dir}/SalishSeaNEMO.sh".format(
                    queue_job_cmd=queue_job_cmd, run_dir=Path("run_dir")
                )
            ),
            check=True,
            universal_newlines=True,
            stdout=subprocess.PIPE,
        )
        assert submit_job_msg == submit_job_msg

    def test_submit_job_w_waitjob(
        self, m_run, queue_job_cmd, depend_flag, depend_option, submit_job_msg
    ):
        submit_job_msg = salishsea_cmd.run._submit_job(
            Path("run_dir", "SalishSeaNEMO.sh"), queue_job_cmd, 42
        )
        m_run.assert_called_once_with(
            shlex.split(
                "{queue_job_cmd} {depend_flag} {depend_option}:42 {run_dir}/SalishSeaNEMO.sh".format(
                    queue_job_cmd=queue_job_cmd,
                    depend_flag=depend_flag,
                    depend_option=depend_option,
                    run_dir=Path("run_dir"),
                )
            ),
            check=True,
            universal_newlines=True,
            stdout=subprocess.PIPE,
        )
        assert submit_job_msg == submit_job_msg


@patch("salishsea_cmd.run.log", autospec=True)
@patch("salishsea_cmd.run.subprocess.run")
@pytest.mark.parametrize(
    "submit_job_msg, queue_job_cmd, depend_flag, depend_option",
    [
        ("Submitted batch job 43", "sbatch", "-d", "afterok"),
        ("43.orca2.ibb", "qsub", "-W", "depend=afterok"),
        ("43.admin.default.domain", "qsub -q mpi", "-W", "depend=afterok"),
    ],
)
class TestSubmitSeparateDeflateJobs:
    """Unit tests for _submit_separate_deflate_jobs() function.
    """

    def test_submit_separate_deflate_jobs(
        self,
        m_run,
        m_log,
        submit_job_msg,
        queue_job_cmd,
        depend_flag,
        depend_option,
        tmpdir,
    ):
        p_run_dir = tmpdir.ensure_dir("run_dir")
        salishsea_cmd.run._submit_separate_deflate_jobs(
            Path(str(p_run_dir)) / "SalishSeaNEMO.sh", submit_job_msg, queue_job_cmd
        )
        assert m_run.call_args_list == [
            call(
                shlex.split(
                    "{queue_job_cmd} {depend_flag} {depend_option}:{job_id} {run_dir}/deflate_grid.sh".format(
                        queue_job_cmd=queue_job_cmd,
                        depend_flag=depend_flag,
                        depend_option=depend_option,
                        job_id=submit_job_msg.split()[-1],
                        run_dir=str(p_run_dir),
                    )
                ),
                check=True,
                universal_newlines=True,
                stdout=subprocess.PIPE,
            ),
            call(
                shlex.split(
                    "{queue_job_cmd} {depend_flag} {depend_option}:{job_id} {run_dir}/deflate_ptrc.sh".format(
                        queue_job_cmd=queue_job_cmd,
                        depend_flag=depend_flag,
                        depend_option=depend_option,
                        job_id=submit_job_msg.split()[-1],
                        run_dir=str(p_run_dir),
                    )
                ),
                check=True,
                universal_newlines=True,
                stdout=subprocess.PIPE,
            ),
            call(
                shlex.split(
                    "{queue_job_cmd} {depend_flag} {depend_option}:{job_id} {run_dir}/deflate_dia.sh".format(
                        queue_job_cmd=queue_job_cmd,
                        depend_flag=depend_flag,
                        depend_option=depend_option,
                        job_id=submit_job_msg.split()[-1],
                        run_dir=str(p_run_dir),
                    )
                ),
                check=True,
                universal_newlines=True,
                stdout=subprocess.PIPE,
            ),
        ]


class TestBuildBatchScript:
    """Unit test for _build_batch_script() function.
    """

    @pytest.mark.parametrize(
        "account, deflate", [("rrg-allen", True), ("rrg-allen", False)]
    )
    def test_beluga(self, account, deflate):
        desc_file = StringIO(
            "run_id: foo\n" "walltime: 01:02:03\n" "email: me@example.com"
        )
        run_desc = yaml.safe_load(desc_file)
        with patch("salishsea_cmd.run.SYSTEM", "beluga"):
            script = salishsea_cmd.run._build_batch_script(
                run_desc,
                Path("SalishSea.yaml"),
                nemo_processors=42,
                xios_processors=1,
                max_deflate_jobs=4,
                results_dir=Path("results_dir"),
                run_dir=Path("tmp_run_dir"),
                deflate=deflate,
                separate_deflate=False,
                cedar_broadwell=False,
            )
        expected = textwrap.dedent(
            """\
            #!/bin/bash
            
            #SBATCH --job-name=foo
            #SBATCH --nodes=2
            #SBATCH --ntasks-per-node=40
            #SBATCH --mem=92G
            #SBATCH --time=1:02:03
            #SBATCH --mail-user=me@example.com
            #SBATCH --mail-type=ALL
            #SBATCH --account={account}
            # stdout and stderr file paths/names
            #SBATCH --output=results_dir/stdout
            #SBATCH --error=results_dir/stderr
            
            
            RUN_ID="foo"
            RUN_DESC="tmp_run_dir/SalishSea.yaml"
            WORK_DIR="tmp_run_dir"
            RESULTS_DIR="results_dir"
            COMBINE="${{HOME}}/.local/bin/salishsea combine"
            """.format(
                account=account
            )
        )
        if deflate:
            expected += textwrap.dedent(
                """\
                DEFLATE="${HOME}/.local/bin/salishsea deflate"
                """
            )
        expected += textwrap.dedent(
            """\
            GATHER="${HOME}/.local/bin/salishsea gather"
            
            module load netcdf-fortran-mpi/4.4.4
            module load python/3.7.0
            
            mkdir -p ${RESULTS_DIR}
            cd ${WORK_DIR}
            echo "working dir: $(pwd)"
            
            echo "Starting run at $(date)"
            mpirun -np 42 ./nemo.exe : -np 1 ./xios_server.exe
            MPIRUN_EXIT_CODE=$?
            echo "Ended run at $(date)"
            
            echo "Results combining started at $(date)"
            ${COMBINE} ${RUN_DESC} --debug
            echo "Results combining ended at $(date)"
            """
        )
        if deflate:
            expected += textwrap.dedent(
                """\
                
                echo "Results deflation started at $(date)"
                module load nco/4.6.6
                ${DEFLATE} *_ptrc_T*.nc *_prod_T*.nc *_carp_T*.nc *_grid_[TUVW]*.nc \\
                  *_turb_T*.nc *_dia[12n]_T*.nc FVCOM*.nc Slab_[UV]*.nc *_mtrc_T*.nc \\
                  --jobs 4 --debug
                echo "Results deflation ended at $(date)"
                """
            )
        expected += textwrap.dedent(
            """\
            
            echo "Results gathering started at $(date)"
            ${GATHER} ${RESULTS_DIR} --debug
            echo "Results gathering ended at $(date)"
            
            chmod go+rx ${RESULTS_DIR}
            chmod g+rw ${RESULTS_DIR}/*
            chmod o+r ${RESULTS_DIR}/*
            
            echo "Deleting run directory" >>${RESULTS_DIR}/stdout
            rmdir $(pwd)
            echo "Finished at $(date)" >>${RESULTS_DIR}/stdout
            exit ${MPIRUN_EXIT_CODE}
            """
        )
        assert script == expected

    @pytest.mark.parametrize(
        "cedar_broadwell, constraint, nodes, ntasks, mem, deflate",
        [(True, "broadwell", 2, 32, "0", True), (False, "skylake", 1, 48, "0", True)],
    )
    def test_cedar(self, cedar_broadwell, constraint, nodes, ntasks, mem, deflate):
        desc_file = StringIO(
            "run_id: foo\n" "walltime: 01:02:03\n" "email: me@example.com"
        )
        run_desc = yaml.safe_load(desc_file)
        with patch("salishsea_cmd.run.SYSTEM", "cedar"):
            script = salishsea_cmd.run._build_batch_script(
                run_desc,
                Path("SalishSea.yaml"),
                nemo_processors=42,
                xios_processors=1,
                max_deflate_jobs=4,
                results_dir=Path("results_dir"),
                run_dir=Path("tmp_run_dir"),
                deflate=deflate,
                separate_deflate=False,
                cedar_broadwell=cedar_broadwell,
            )
        expected = textwrap.dedent(
            """\
            #!/bin/bash
            
            #SBATCH --job-name=foo
            #SBATCH --constraint={constraint}
            #SBATCH --nodes={nodes}
            #SBATCH --ntasks-per-node={ntasks}
            #SBATCH --mem={mem}
            #SBATCH --time=1:02:03
            #SBATCH --mail-user=me@example.com
            #SBATCH --mail-type=ALL
            #SBATCH --account=rrg-allen
            # stdout and stderr file paths/names
            #SBATCH --output=results_dir/stdout
            #SBATCH --error=results_dir/stderr
            
            
            RUN_ID="foo"
            RUN_DESC="tmp_run_dir/SalishSea.yaml"
            WORK_DIR="tmp_run_dir"
            RESULTS_DIR="results_dir"
            COMBINE="${{HOME}}/.local/bin/salishsea combine"
            """.format(
                constraint=constraint, nodes=nodes, ntasks=ntasks, mem=mem
            )
        )
        if deflate:
            expected += textwrap.dedent(
                """\
                DEFLATE="${HOME}/.local/bin/salishsea deflate"
                """
            )
        expected += textwrap.dedent(
            """\
            GATHER="${HOME}/.local/bin/salishsea gather"
            
            module load netcdf-fortran-mpi/4.4.4
            module load python/3.7.0
            
            mkdir -p ${RESULTS_DIR}
            cd ${WORK_DIR}
            echo "working dir: $(pwd)"
            
            echo "Starting run at $(date)"
            mpirun -np 42 ./nemo.exe : -np 1 ./xios_server.exe
            MPIRUN_EXIT_CODE=$?
            echo "Ended run at $(date)"
            
            echo "Results combining started at $(date)"
            ${COMBINE} ${RUN_DESC} --debug
            echo "Results combining ended at $(date)"
            """
        )
        if deflate:
            expected += textwrap.dedent(
                """\
                
                echo "Results deflation started at $(date)"
                module load nco/4.6.6
                ${DEFLATE} *_ptrc_T*.nc *_prod_T*.nc *_carp_T*.nc *_grid_[TUVW]*.nc \\
                  *_turb_T*.nc *_dia[12n]_T*.nc FVCOM*.nc Slab_[UV]*.nc *_mtrc_T*.nc \\
                  --jobs 4 --debug
                echo "Results deflation ended at $(date)"
                """
            )
        expected += textwrap.dedent(
            """\
            
            echo "Results gathering started at $(date)"
            ${GATHER} ${RESULTS_DIR} --debug
            echo "Results gathering ended at $(date)"
            
            chmod go+rx ${RESULTS_DIR}
            chmod g+rw ${RESULTS_DIR}/*
            chmod o+r ${RESULTS_DIR}/*
            
            echo "Deleting run directory" >>${RESULTS_DIR}/stdout
            rmdir $(pwd)
            echo "Finished at $(date)" >>${RESULTS_DIR}/stdout
            exit ${MPIRUN_EXIT_CODE}
            """
        )
        assert script == expected

    @pytest.mark.parametrize(
        "account, deflate", [("def-allen", True), ("def-allen", False)]
    )
    def test_graham(self, account, deflate):
        desc_file = StringIO(
            "run_id: foo\n" "walltime: 01:02:03\n" "email: me@example.com"
        )
        run_desc = yaml.safe_load(desc_file)
        with patch("salishsea_cmd.run.SYSTEM", "graham"):
            script = salishsea_cmd.run._build_batch_script(
                run_desc,
                Path("SalishSea.yaml"),
                nemo_processors=42,
                xios_processors=1,
                max_deflate_jobs=4,
                results_dir=Path("results_dir"),
                run_dir=Path("tmp_run_dir"),
                deflate=deflate,
                separate_deflate=False,
                cedar_broadwell=False,
            )
        expected = textwrap.dedent(
            """\
            #!/bin/bash
            
            #SBATCH --job-name=foo
            #SBATCH --nodes=2
            #SBATCH --ntasks-per-node=32
            #SBATCH --mem=125G
            #SBATCH --time=1:02:03
            #SBATCH --mail-user=me@example.com
            #SBATCH --mail-type=ALL
            #SBATCH --account={account}
            # stdout and stderr file paths/names
            #SBATCH --output=results_dir/stdout
            #SBATCH --error=results_dir/stderr
            
            
            RUN_ID="foo"
            RUN_DESC="tmp_run_dir/SalishSea.yaml"
            WORK_DIR="tmp_run_dir"
            RESULTS_DIR="results_dir"
            COMBINE="${{HOME}}/.local/bin/salishsea combine"
            """.format(
                account=account
            )
        )
        if deflate:
            expected += textwrap.dedent(
                """\
                DEFLATE="${HOME}/.local/bin/salishsea deflate"
                """
            )
        expected += textwrap.dedent(
            """\
            GATHER="${HOME}/.local/bin/salishsea gather"
            
            module load netcdf-fortran-mpi/4.4.4
            module load python/3.7.0
            
            mkdir -p ${RESULTS_DIR}
            cd ${WORK_DIR}
            echo "working dir: $(pwd)"
            
            echo "Starting run at $(date)"
            mpirun -np 42 ./nemo.exe : -np 1 ./xios_server.exe
            MPIRUN_EXIT_CODE=$?
            echo "Ended run at $(date)"
            
            echo "Results combining started at $(date)"
            ${COMBINE} ${RUN_DESC} --debug
            echo "Results combining ended at $(date)"
            """
        )
        if deflate:
            expected += textwrap.dedent(
                """\
                
                echo "Results deflation started at $(date)"
                module load nco/4.6.6
                ${DEFLATE} *_ptrc_T*.nc *_prod_T*.nc *_carp_T*.nc *_grid_[TUVW]*.nc \\
                  *_turb_T*.nc *_dia[12n]_T*.nc FVCOM*.nc Slab_[UV]*.nc *_mtrc_T*.nc \\
                  --jobs 4 --debug
                echo "Results deflation ended at $(date)"
                """
            )
        expected += textwrap.dedent(
            """\
            
            echo "Results gathering started at $(date)"
            ${GATHER} ${RESULTS_DIR} --debug
            echo "Results gathering ended at $(date)"
            
            chmod go+rx ${RESULTS_DIR}
            chmod g+rw ${RESULTS_DIR}/*
            chmod o+r ${RESULTS_DIR}/*
            
            echo "Deleting run directory" >>${RESULTS_DIR}/stdout
            rmdir $(pwd)
            echo "Finished at $(date)" >>${RESULTS_DIR}/stdout
            exit ${MPIRUN_EXIT_CODE}
            """
        )
        assert script == expected

    @pytest.mark.parametrize(
        "system, deflate",
        [("delta", True), ("delta", False), ("sigma", True), ("sigma", False)],
    )
    def test_optimum(self, system, deflate):
        desc_file = StringIO(
            "run_id: foo\n" "walltime: 01:02:03\n" "email: me@example.com"
        )
        run_desc = yaml.safe_load(desc_file)
        with patch("salishsea_cmd.run.SYSTEM", system):
            script = salishsea_cmd.run._build_batch_script(
                run_desc,
                Path("SalishSea.yaml"),
                nemo_processors=278,
                xios_processors=1,
                max_deflate_jobs=4,
                results_dir=Path("results_dir"),
                run_dir=Path("tmp_run_dir"),
                deflate=deflate,
                separate_deflate=False,
                cedar_broadwell=False,
            )
        expected = textwrap.dedent(
            """\
            #!/bin/bash
            
            #PBS -N foo
            #PBS -S /bin/bash
            #PBS -l walltime=1:02:03
            # email when the job [b]egins and [e]nds, or is [a]borted
            #PBS -m bea
            #PBS -M me@example.com
            #PBS -l nodes=14:ppn=20
            # memory per processor
            #PBS -l pmem=2000mb
            # stdout and stderr file paths/names
            #PBS -o results_dir/stdout
            #PBS -e results_dir/stderr
            
            
            RUN_ID="foo"
            RUN_DESC="tmp_run_dir/SalishSea.yaml"
            WORK_DIR="tmp_run_dir"
            RESULTS_DIR="results_dir"
            COMBINE="${PBS_O_HOME}/bin/salishsea combine"
            """
        )
        if deflate:
            expected += textwrap.dedent(
                """\
                DEFLATE="${PBS_O_HOME}/bin/salishsea deflate"
                """
            )
        expected += textwrap.dedent(
            """\
            GATHER="${PBS_O_HOME}/bin/salishsea gather"
            
            module load OpenMPI/2.1.6/GCC/SYSTEM
            
            mkdir -p ${RESULTS_DIR}
            cd ${WORK_DIR}
            echo "working dir: $(pwd)"
            
            echo "Starting run at $(date)"
            mpiexec -hostfile $(openmpi_nodefile) -bind-to core -np 278 ./nemo.exe : -bind-to core -np 1 ./xios_server.exe
            MPIRUN_EXIT_CODE=$?
            echo "Ended run at $(date)"
            
            echo "Results combining started at $(date)"
            module load GCC/8.3
            module load OpenMPI/2.1.6/GCC/8.3
            module load ZLIB/1.2/11
            module load use.paustin
            module load HDF5/1.08/20
            module load NETCDF/4.6/1
            ${COMBINE} ${RUN_DESC} --debug
            echo "Results combining ended at $(date)"
            """
        )
        if deflate:
            expected += textwrap.dedent(
                """\
                
                echo "Results deflation started at $(date)"
                ${DEFLATE} *_ptrc_T*.nc *_prod_T*.nc *_carp_T*.nc *_grid_[TUVW]*.nc \\
                  *_turb_T*.nc *_dia[12n]_T*.nc FVCOM*.nc Slab_[UV]*.nc *_mtrc_T*.nc \\
                  --jobs 4 --debug
                echo "Results deflation ended at $(date)"
                """
            )
        expected += textwrap.dedent(
            """\
            
            echo "Results gathering started at $(date)"
            ${GATHER} ${RESULTS_DIR} --debug
            echo "Results gathering ended at $(date)"
            
            chmod go+rx ${RESULTS_DIR}
            chmod g+rw ${RESULTS_DIR}/*
            chmod o+r ${RESULTS_DIR}/*
            
            echo "Deleting run directory" >>${RESULTS_DIR}/stdout
            rmdir $(pwd)
            echo "Finished at $(date)" >>${RESULTS_DIR}/stdout
            exit ${MPIRUN_EXIT_CODE}
            """
        )
        assert script == expected

    @pytest.mark.parametrize("deflate", [True, False])
    def test_orcinus(self, deflate):
        desc_file = StringIO(
            "run_id: foo\n" "walltime: 01:02:03\n" "email: me@example.com"
        )
        run_desc = yaml.safe_load(desc_file)
        with patch("salishsea_cmd.run.SYSTEM", "orcinus"):
            script = salishsea_cmd.run._build_batch_script(
                run_desc,
                Path("SalishSea.yaml"),
                nemo_processors=42,
                xios_processors=1,
                max_deflate_jobs=4,
                results_dir=Path("results_dir"),
                run_dir=Path("tmp_run_dir"),
                deflate=deflate,
                separate_deflate=False,
                cedar_broadwell=False,
            )
        expected = textwrap.dedent(
            """\
            #!/bin/bash
            
            #PBS -N foo
            #PBS -S /bin/bash
            #PBS -l walltime=1:02:03
            # email when the job [b]egins and [e]nds, or is [a]borted
            #PBS -m bea
            #PBS -M me@example.com
            #PBS -l procs=43
            # memory per processor
            #PBS -l pmem=2000mb
            # stdout and stderr file paths/names
            #PBS -o results_dir/stdout
            #PBS -e results_dir/stderr
            
            #PBS -l partition=QDR
            
            RUN_ID="foo"
            RUN_DESC="tmp_run_dir/SalishSea.yaml"
            WORK_DIR="tmp_run_dir"
            RESULTS_DIR="results_dir"
            COMBINE="${PBS_O_HOME}/.local/bin/salishsea combine"
            """
        )
        if deflate:
            expected += textwrap.dedent(
                """\
                DEFLATE="${PBS_O_HOME}/.local/bin/salishsea deflate"
                """
            )
        expected += textwrap.dedent(
            """\
            GATHER="${PBS_O_HOME}/.local/bin/salishsea gather"
            
            module load intel
            module load intel/14.0/netcdf-4.3.3.1_mpi
            module load intel/14.0/netcdf-fortran-4.4.0_mpi
            module load intel/14.0/hdf5-1.8.15p1_mpi
            module load intel/14.0/nco-4.5.2
            module load python
            
            mkdir -p ${RESULTS_DIR}
            cd ${WORK_DIR}
            echo "working dir: $(pwd)"
            
            echo "Starting run at $(date)"
            mpirun -np 42 ./nemo.exe : -np 1 ./xios_server.exe
            MPIRUN_EXIT_CODE=$?
            echo "Ended run at $(date)"
            
            echo "Results combining started at $(date)"
            ${COMBINE} ${RUN_DESC} --debug
            echo "Results combining ended at $(date)"
            """
        )
        if deflate:
            expected += textwrap.dedent(
                """\
                
                echo "Results deflation started at $(date)"
                ${DEFLATE} *_ptrc_T*.nc *_prod_T*.nc *_carp_T*.nc *_grid_[TUVW]*.nc \\
                  *_turb_T*.nc *_dia[12n]_T*.nc FVCOM*.nc Slab_[UV]*.nc *_mtrc_T*.nc \\
                  --jobs 4 --debug
                echo "Results deflation ended at $(date)"
                """
            )
        expected += textwrap.dedent(
            """\
            
            echo "Results gathering started at $(date)"
            ${GATHER} ${RESULTS_DIR} --debug
            echo "Results gathering ended at $(date)"
            
            chmod go+rx ${RESULTS_DIR}
            chmod g+rw ${RESULTS_DIR}/*
            chmod o+r ${RESULTS_DIR}/*
            
            echo "Deleting run directory" >>${RESULTS_DIR}/stdout
            rmdir $(pwd)
            echo "Finished at $(date)" >>${RESULTS_DIR}/stdout
            exit ${MPIRUN_EXIT_CODE}
            """
        )
        assert script == expected

    @pytest.mark.parametrize("deflate", [True, False])
    def test_salish(self, deflate):
        desc_file = StringIO(
            "run_id: foo\n" "walltime: 01:02:03\n" "email: me@example.com"
        )
        run_desc = yaml.safe_load(desc_file)
        with patch("salishsea_cmd.run.SYSTEM", "salish"):
            script = salishsea_cmd.run._build_batch_script(
                run_desc,
                Path("SalishSea.yaml"),
                nemo_processors=6,
                xios_processors=1,
                max_deflate_jobs=4,
                results_dir=Path("results_dir"),
                run_dir=Path("tmp_run_dir"),
                deflate=deflate,
                separate_deflate=False,
                cedar_broadwell=False,
            )
        expected = textwrap.dedent(
            """\
            #!/bin/bash
            
            #PBS -N foo
            #PBS -S /bin/bash
            #PBS -l walltime=1:02:03
            # email when the job [b]egins and [e]nds, or is [a]borted
            #PBS -m bea
            #PBS -M me@example.com
            #PBS -l procs=7
            # memory per processor
            #PBS -l pmem=2000mb
            # stdout and stderr file paths/names
            #PBS -o results_dir/stdout
            #PBS -e results_dir/stderr
            
            
            RUN_ID="foo"
            RUN_DESC="tmp_run_dir/SalishSea.yaml"
            WORK_DIR="tmp_run_dir"
            RESULTS_DIR="results_dir"
            COMBINE="${HOME}/.local/bin/salishsea combine"
            """
        )
        if deflate:
            expected += textwrap.dedent(
                """\
                DEFLATE="${HOME}/.local/bin/salishsea deflate"
                """
            )
        expected += textwrap.dedent(
            """\
            GATHER="${HOME}/.local/bin/salishsea gather"
            
            
            mkdir -p ${RESULTS_DIR}
            cd ${WORK_DIR}
            echo "working dir: $(pwd)"
            
            echo "Starting run at $(date)"
            /usr/bin/mpirun -np 6 ./nemo.exe : -np 1 ./xios_server.exe
            MPIRUN_EXIT_CODE=$?
            echo "Ended run at $(date)"
            
            echo "Results combining started at $(date)"
            ${COMBINE} ${RUN_DESC} --debug
            echo "Results combining ended at $(date)"
            """
        )
        if deflate:
            expected += textwrap.dedent(
                """\
                
                echo "Results deflation started at $(date)"
                ${DEFLATE} *_ptrc_T*.nc *_prod_T*.nc *_carp_T*.nc *_grid_[TUVW]*.nc \\
                  *_turb_T*.nc *_dia[12n]_T*.nc FVCOM*.nc Slab_[UV]*.nc *_mtrc_T*.nc \\
                  --jobs 4 --debug
                echo "Results deflation ended at $(date)"
                """
            )
        expected += textwrap.dedent(
            """\
            
            echo "Results gathering started at $(date)"
            ${GATHER} ${RESULTS_DIR} --debug
            echo "Results gathering ended at $(date)"
            
            chmod go+rx ${RESULTS_DIR}
            chmod g+rw ${RESULTS_DIR}/*
            chmod o+r ${RESULTS_DIR}/*
            
            echo "Deleting run directory" >>${RESULTS_DIR}/stdout
            rmdir $(pwd)
            echo "Finished at $(date)" >>${RESULTS_DIR}/stdout
            exit ${MPIRUN_EXIT_CODE}
            """
        )
        assert script == expected

    @pytest.mark.parametrize("deflate", [True, False])
    def test_sockeye(self, deflate):
        desc_file = StringIO(
            "run_id: foo\n" "walltime: 01:02:03\n" "email: me@example.com"
        )
        run_desc = yaml.safe_load(desc_file)
        with patch("salishsea_cmd.run.SYSTEM", "sockeye"):
            script = salishsea_cmd.run._build_batch_script(
                run_desc,
                Path("SalishSea.yaml"),
                nemo_processors=42,
                xios_processors=1,
                max_deflate_jobs=4,
                results_dir=Path("results_dir"),
                run_dir=Path("tmp_run_dir"),
                deflate=deflate,
                separate_deflate=False,
                cedar_broadwell=False,
            )
        expected = textwrap.dedent(
            """\
            #!/bin/bash

            #PBS -N foo
            #PBS -S /bin/bash
            #PBS -l walltime=1:02:03
            # email when the job [b]egins and [e]nds, or is [a]borted
            #PBS -m bea
            #PBS -M me@example.com
            #PBS -A dri-allen
            #PBS -l select=2:ncpus=32:mpiprocs=32:mem=64gb
            # stdout and stderr file paths/names
            #PBS -o results_dir/stdout
            #PBS -e results_dir/stderr


            RUN_ID="foo"
            RUN_DESC="tmp_run_dir/SalishSea.yaml"
            WORK_DIR="tmp_run_dir"
            RESULTS_DIR="results_dir"
            COMBINE="${PBS_O_HOME}/.local/bin/salishsea combine"
            """
        )
        if deflate:
            expected += textwrap.dedent(
                """\
                DEFLATE="${PBS_O_HOME}/.local/bin/salishsea deflate"
                """
            )
        expected += textwrap.dedent(
            """\
            GATHER="${PBS_O_HOME}/.local/bin/salishsea gather"

            module load gcc/5.4.0
            module load openmpi/3.1.4
            module load netcdf-fortran/4.4.5
            module load hdf5/1.10.5
            module load python/3.7.3
            module load py-setuptools/41.0.1-py3.7.3

            mkdir -p ${RESULTS_DIR}
            cd ${WORK_DIR}
            echo "working dir: $(pwd)"

            echo "Starting run at $(date)"
            mpirun --bind-to core -np 42 ./nemo.exe : --bind-to core -np 1 ./xios_server.exe
            MPIRUN_EXIT_CODE=$?
            echo "Ended run at $(date)"

            echo "Results combining started at $(date)"
            ${COMBINE} ${RUN_DESC} --debug
            echo "Results combining ended at $(date)"
            """
        )
        if deflate:
            expected += textwrap.dedent(
                """\

                echo "Results deflation started at $(date)"
                ${DEFLATE} *_ptrc_T*.nc *_prod_T*.nc *_carp_T*.nc *_grid_[TUVW]*.nc \\
                  *_turb_T*.nc *_dia[12n]_T*.nc FVCOM*.nc Slab_[UV]*.nc *_mtrc_T*.nc \\
                  --jobs 4 --debug
                echo "Results deflation ended at $(date)"
                """
            )
        expected += textwrap.dedent(
            """\

            echo "Results gathering started at $(date)"
            ${GATHER} ${RESULTS_DIR} --debug
            echo "Results gathering ended at $(date)"

            chmod go+rx ${RESULTS_DIR}
            chmod g+rw ${RESULTS_DIR}/*
            chmod o+r ${RESULTS_DIR}/*

            echo "Deleting run directory" >>${RESULTS_DIR}/stdout
            rmdir $(pwd)
            echo "Finished at $(date)" >>${RESULTS_DIR}/stdout
            exit ${MPIRUN_EXIT_CODE}
            """
        )
        assert script == expected


@patch("salishsea_cmd.run.log", autospec=True)
class TestSbatchDirectives:
    """Unit tests for _sbatch_directives() function.
    """

    def test_unknown_system(self, m_logger):
        desc_file = StringIO(
            "run_id: foo\n" "walltime: 01:02:03\n" "account: def-sverdrup\n"
        )
        run_desc = yaml.safe_load(desc_file)
        with pytest.raises(SystemExit):
            salishsea_cmd.run._sbatch_directives(
                run_desc,
                43,
                cedar_broadwell=False,
                email="me@example.com",
                results_dir=Path("foo"),
            )
        assert m_logger.error.called

    def test_beluga_sbatch_directives(self, m_logger):
        desc_file = StringIO("run_id: foo\n" "walltime: 01:02:03\n")
        run_desc = yaml.safe_load(desc_file)
        with patch("salishsea_cmd.run.SYSTEM", "beluga"):
            slurm_directives = salishsea_cmd.run._sbatch_directives(
                run_desc,
                n_processors=43,
                cedar_broadwell=False,
                email="me@example.com",
                results_dir=Path("foo"),
            )
        expected = (
            "#SBATCH --job-name=foo\n"
            "#SBATCH --nodes=2\n"
            "#SBATCH --ntasks-per-node=40\n"
            "#SBATCH --mem=92G\n"
            "#SBATCH --time=1:02:03\n"
            "#SBATCH --mail-user=me@example.com\n"
            "#SBATCH --mail-type=ALL\n"
            "#SBATCH --account=rrg-allen\n"
            "# stdout and stderr file paths/names\n"
            "#SBATCH --output=foo/stdout\n"
            "#SBATCH --error=foo/stderr\n"
        )
        assert slurm_directives == expected
        assert m_logger.info.called

    @pytest.mark.parametrize(
        "system, account, cedar_broadwell, constraint, nodes, ntasks, mem",
        [
            ("cedar", "rrg-allen", True, "broadwell", 2, 32, "0"),
            ("cedar", "rrg-allen", False, "skylake", 1, 48, "0"),
        ],
    )
    def test_cedar_sbatch_directives(
        self, m_logger, system, account, cedar_broadwell, constraint, nodes, ntasks, mem
    ):
        desc_file = StringIO("run_id: foo\n" "walltime: 01:02:03\n")
        run_desc = yaml.safe_load(desc_file)
        with patch("salishsea_cmd.run.SYSTEM", "cedar"):
            slurm_directives = salishsea_cmd.run._sbatch_directives(
                run_desc, 43, cedar_broadwell, "me@example.com", Path("foo")
            )
        expected = (
            "#SBATCH --job-name=foo\n"
            "#SBATCH --constraint={constraint}\n"
            "#SBATCH --nodes={nodes}\n"
            "#SBATCH --ntasks-per-node={ntasks}\n"
            "#SBATCH --mem={mem}\n"
            "#SBATCH --time=1:02:03\n"
            "#SBATCH --mail-user=me@example.com\n"
            "#SBATCH --mail-type=ALL\n"
            "#SBATCH --account={account}\n"
            "# stdout and stderr file paths/names\n"
            "#SBATCH --output=foo/stdout\n"
            "#SBATCH --error=foo/stderr\n"
        ).format(
            constraint=constraint, nodes=nodes, ntasks=ntasks, mem=mem, account=account
        )
        assert slurm_directives == expected
        assert m_logger.info.called

    def test_graham_sbatch_directives(self, m_logger):
        desc_file = StringIO("run_id: foo\n" "walltime: 01:02:03\n")
        run_desc = yaml.safe_load(desc_file)
        with patch("salishsea_cmd.run.SYSTEM", "graham"):
            slurm_directives = salishsea_cmd.run._sbatch_directives(
                run_desc,
                n_processors=43,
                cedar_broadwell=False,
                email="me@example.com",
                results_dir=Path("foo"),
            )
        expected = (
            "#SBATCH --job-name=foo\n"
            "#SBATCH --nodes=2\n"
            "#SBATCH --ntasks-per-node=32\n"
            "#SBATCH --mem=125G\n"
            "#SBATCH --time=1:02:03\n"
            "#SBATCH --mail-user=me@example.com\n"
            "#SBATCH --mail-type=ALL\n"
            "#SBATCH --account=def-allen\n"
            "# stdout and stderr file paths/names\n"
            "#SBATCH --output=foo/stdout\n"
            "#SBATCH --error=foo/stderr\n"
        )
        assert slurm_directives == expected
        assert m_logger.info.called

    @pytest.mark.parametrize("system", ("beluga", "cedar", "graham"))
    def test_account_directive_from_yaml(self, m_logger, system):
        desc_file = StringIO(
            "run_id: foo\n" "walltime: 01:02:03\n" "account: def-sverdrup\n"
        )
        run_desc = yaml.safe_load(desc_file)
        with patch("salishsea_cmd.run.SYSTEM", system):
            slurm_directives = salishsea_cmd.run._sbatch_directives(
                run_desc,
                43,
                cedar_broadwell=False,
                email="me@example.com",
                results_dir=Path("foo"),
            )
        assert "#SBATCH --account=def-sverdrup\n" in slurm_directives
        assert not m_logger.info.called


class TestPbsDirectives:
    """Unit tests for `salishsea run` _pbs_directives() function.
    """

    @pytest.mark.parametrize(
        "system, procs_per_node, procs_directives",
        (
            (
                "delta",
                20,
                "#PBS -l nodes=3:ppn=20\n# memory per processor\n#PBS -l pmem=2000mb",
            ),
            (
                "orcinus",
                0,
                "#PBS -l procs=42\n# memory per processor\n#PBS -l pmem=2000mb",
            ),
            (
                "salish",
                0,
                "#PBS -l procs=42\n# memory per processor\n#PBS -l pmem=2000mb",
            ),
            (
                "sigma",
                20,
                "#PBS -l nodes=3:ppn=20\n# memory per processor\n#PBS -l pmem=2000mb",
            ),
            (
                "sockeye",
                32,
                "#PBS -A dri-allen\n#PBS -l select=2:ncpus=32:mpiprocs=32:mem=64gb",
            ),
        ),
    )
    def test_pbs_directives_run(self, system, procs_per_node, procs_directives):
        run_desc = yaml.safe_load(
            StringIO(
                textwrap.dedent(
                    """\
                    run_id: foo 
                    walltime: 01:02:03
                    """
                )
            )
        )
        with patch("salishsea_cmd.run.SYSTEM", system):
            pbs_directives = salishsea_cmd.run._pbs_directives(
                run_desc, 42, "me@example.com", Path("foo"), procs_per_node
            )
        expected = textwrap.dedent(
            """\
            #PBS -N foo
            #PBS -S /bin/bash
            #PBS -l walltime=1:02:03
            # email when the job [b]egins and [e]nds, or is [a]borted
            #PBS -m bea
            #PBS -M me@example.com
            {procs_directives}
            # stdout and stderr file paths/names
            #PBS -o foo/stdout
            #PBS -e foo/stderr
            """
        ).format(procs_directives=procs_directives)
        assert pbs_directives == expected

    @pytest.mark.parametrize(
        "system, procs_per_node, procs_directives",
        (
            (
                "delta",
                20,
                "#PBS -l nodes=3:ppn=20\n# memory per processor\n#PBS -l pmem=2000mb",
            ),
            (
                "orcinus",
                0,
                "#PBS -l procs=42\n# memory per processor\n#PBS -l pmem=2000mb",
            ),
            (
                "salish",
                0,
                "#PBS -l procs=42\n# memory per processor\n#PBS -l pmem=2000mb",
            ),
            (
                "sigma",
                20,
                "#PBS -l nodes=3:ppn=20\n# memory per processor\n#PBS -l pmem=2000mb",
            ),
            (
                "sockeye",
                32,
                "#PBS -A dri-allen\n#PBS -l select=2:ncpus=32:mpiprocs=32:mem=64gb",
            ),
        ),
    )
    def test_pbs_directives_run_no_stderr_stdout(
        self, system, procs_per_node, procs_directives
    ):
        run_desc = yaml.safe_load(
            StringIO(
                textwrap.dedent(
                    """\
                    run_id: foo 
                    walltime: 01:02:03
                    """
                )
            )
        )
        with patch("salishsea_cmd.run.SYSTEM", system):
            pbs_directives = salishsea_cmd.run._pbs_directives(
                run_desc,
                42,
                "me@example.com",
                Path("foo"),
                procs_per_node,
                stderr_stdout=False,
            )
        expected = textwrap.dedent(
            """\
            #PBS -N foo
            #PBS -S /bin/bash
            #PBS -l walltime=1:02:03
            # email when the job [b]egins and [e]nds, or is [a]borted
            #PBS -m bea
            #PBS -M me@example.com
            {procs_directives}
            """
        ).format(procs_directives=procs_directives)
        assert pbs_directives == expected

    def test_pbs_directives_deflate(self):
        run_desc = yaml.safe_load(
            StringIO(
                textwrap.dedent(
                    """\
                    run_id: foo 
                    walltime: 01:02:03
                    """
                )
            )
        )
        pbs_directives = salishsea_cmd.run._pbs_directives(
            run_desc,
            1,
            "me@example.com",
            Path("foo"),
            pmem="2500mb",
            deflate=True,
            result_type="ptrc",
        )
        expected = textwrap.dedent(
            """\
            #PBS -N ptrc_foo_deflate
            #PBS -S /bin/bash
            #PBS -l walltime=1:02:03
            # email when the job [b]egins and [e]nds, or is [a]borted
            #PBS -m bea
            #PBS -M me@example.com
            #PBS -l procs=1
            # memory per processor
            #PBS -l pmem=2500mb
            # stdout and stderr file paths/names
            #PBS -o foo/stdout_deflate_ptrc
            #PBS -e foo/stderr_deflate_ptrc
            """
        )
        assert pbs_directives == expected

    @pytest.mark.parametrize(
        "walltime, expected_walltime", [("01:02:03", "1:02:03"), ("1:02:03", "1:02:03")]
    )
    def test_walltime(self, walltime, expected_walltime):
        """Ensure correct handling of walltime w/ leading zero in YAML desc file

        re: issue#16
        """
        run_desc = yaml.safe_load(
            StringIO(
                textwrap.dedent(
                    """\
                    run_id: foo 
                    walltime: {walltime}
                    """
                ).format(walltime=walltime)
            )
        )
        pbs_directives = salishsea_cmd.run._pbs_directives(
            run_desc, 42, "me@example.com", Path("")
        )
        expected = "walltime={expected}".format(expected=expected_walltime)
        assert expected in pbs_directives

    def test_sockeye_account_directive(self):
        run_desc = yaml.safe_load(
            StringIO(
                textwrap.dedent(
                    """\
                    run_id: foo 
                    walltime: 01:02:03
                    """
                )
            )
        )
        with patch("salishsea_cmd.run.SYSTEM", "sockeye"):
            pbs_directives = salishsea_cmd.run._pbs_directives(
                run_desc, 43, email="me@example.com", results_dir=Path("foo")
            )
        assert "#PBS -A dri-allen\n" in pbs_directives

    @pytest.mark.parametrize("system", ("delta", "orcinus", "sigma", "salish"))
    def test_not_sockeye_no_account_directive_from_yaml(self, system):
        run_desc = yaml.safe_load(
            StringIO(
                textwrap.dedent(
                    """\
                    run_id: foo 
                    walltime: 01:02:03
                    """
                )
            )
        )
        with patch("salishsea_cmd.run.SYSTEM", system):
            pbs_directives = salishsea_cmd.run._pbs_directives(
                run_desc, 43, email="me@example.com", results_dir=Path("foo")
            )
        assert "#PBS -A" not in pbs_directives


class TestDefinitions:
    """Unit tests for _definitions function.
    """

    @pytest.mark.parametrize(
        "system, home, deflate",
        [
            ("beluga", "${HOME}/.local", True),
            ("beluga", "${HOME}/.local", False),
            ("cedar", "${HOME}/.local", True),
            ("cedar", "${HOME}/.local", False),
            ("delta", "${PBS_O_HOME}", True),
            ("delta", "${PBS_O_HOME}", False),
            ("graham", "${HOME}/.local", True),
            ("graham", "${HOME}/.local", False),
            ("orcinus", "${PBS_O_HOME}/.local", True),
            ("orcinus", "${PBS_O_HOME}/.local", False),
            ("salish", "${HOME}/.local", True),
            ("salish", "${HOME}/.local", False),
            ("sigma", "${PBS_O_HOME}", True),
            ("sigma", "${PBS_O_HOME}", False),
            ("sockeye", "${PBS_O_HOME}/.local", True),
            ("sockeye", "${PBS_O_HOME}/.local", False),
        ],
    )
    def test_definitions(self, system, home, deflate):
        desc_file = StringIO("run_id: foo\n")
        run_desc = yaml.safe_load(desc_file)
        with patch("salishsea_cmd.run.SYSTEM", system):
            defns = salishsea_cmd.run._definitions(
                run_desc,
                Path("SS-run-sets", "SalishSea.yaml"),
                Path("tmp_run_dir"),
                Path("results_dir"),
                deflate,
            )
        expected = (
            'RUN_ID="foo"\n'
            'RUN_DESC="tmp_run_dir/SalishSea.yaml"\n'
            'WORK_DIR="tmp_run_dir"\n'
            'RESULTS_DIR="results_dir"\n'
            'COMBINE="{home}/bin/salishsea combine"\n'
        ).format(home=home)
        if deflate:
            expected += 'DEFLATE="{home}/bin/salishsea deflate"\n'.format(home=home)
        expected += 'GATHER="{home}/bin/salishsea gather"\n'.format(home=home)
        assert defns == expected


class TestModules:
    """Unit tests for _modules function.
    """

    def test_unknown_system(self):
        modules = salishsea_cmd.run._modules()
        assert modules == ""

    @pytest.mark.parametrize("system", ["beluga", "cedar", "graham"])
    def test_beluga_cedar_graham(self, system):
        with patch("salishsea_cmd.run.SYSTEM", system):
            modules = salishsea_cmd.run._modules()
        expected = textwrap.dedent(
            """\
            module load netcdf-fortran-mpi/4.4.4
            module load python/3.7.0
            """
        )
        assert modules == expected

    def test_orcinus(self):
        with patch("salishsea_cmd.run.SYSTEM", "orcinus"):
            modules = salishsea_cmd.run._modules()
        expected = textwrap.dedent(
            """\
            module load intel
            module load intel/14.0/netcdf-4.3.3.1_mpi
            module load intel/14.0/netcdf-fortran-4.4.0_mpi
            module load intel/14.0/hdf5-1.8.15p1_mpi
            module load intel/14.0/nco-4.5.2
            module load python
            """
        )
        assert modules == expected

    @pytest.mark.parametrize("system", ["delta", "sigma"])
    def test_optimum(self, system):
        with patch("salishsea_cmd.run.SYSTEM", system):
            modules = salishsea_cmd.run._modules()
        expected = textwrap.dedent(
            """\
            module load OpenMPI/2.1.6/GCC/SYSTEM
            """
        )
        assert modules == expected

    def test_sockeye(self):
        with patch("salishsea_cmd.run.SYSTEM", "sockeye"):
            modules = salishsea_cmd.run._modules()
        expected = textwrap.dedent(
            """\
            module load gcc/5.4.0
            module load openmpi/3.1.4
            module load netcdf-fortran/4.4.5
            module load hdf5/1.10.5
            module load python/3.7.3
            module load py-setuptools/41.0.1-py3.7.3
            """
        )
        assert modules == expected


class TestExecute:
    """Unit test for _execute function.
    """

    @pytest.mark.parametrize(
        "system, mpirun_cmd",
        [
            ("beluga", "mpirun -np 42 ./nemo.exe : -np 1 ./xios_server.exe"),
            ("cedar", "mpirun -np 42 ./nemo.exe : -np 1 ./xios_server.exe"),
            (
                "delta",
                "mpiexec -hostfile $(openmpi_nodefile) -bind-to core -np 42 ./nemo.exe : -bind-to core -np 1 ./xios_server.exe",
            ),
            ("graham", "mpirun -np 42 ./nemo.exe : -np 1 ./xios_server.exe"),
            ("orcinus", "mpirun -np 42 ./nemo.exe : -np 1 ./xios_server.exe"),
            ("salish", "/usr/bin/mpirun -np 42 ./nemo.exe : -np 1 ./xios_server.exe"),
            (
                "sigma",
                "mpiexec -hostfile $(openmpi_nodefile) -bind-to core -np 42 ./nemo.exe : -bind-to core -np 1 ./xios_server.exe",
            ),
            (
                "sockeye",
                "mpirun --bind-to core -np 42 ./nemo.exe : --bind-to core -np 1 ./xios_server.exe",
            ),
        ],
    )
    def test_execute_with_deflate(self, system, mpirun_cmd):
        with patch("salishsea_cmd.run.SYSTEM", system):
            script = salishsea_cmd.run._execute(
                nemo_processors=42,
                xios_processors=1,
                deflate=True,
                max_deflate_jobs=4,
                separate_deflate=False,
            )
        expected = textwrap.dedent(
            """\
            mkdir -p ${{RESULTS_DIR}}
            cd ${{WORK_DIR}}
            echo "working dir: $(pwd)"

            echo "Starting run at $(date)"
            {mpirun_cmd}
            MPIRUN_EXIT_CODE=$?
            echo "Ended run at $(date)"
    
            echo "Results combining started at $(date)"
            """.format(
                mpirun_cmd=mpirun_cmd
            )
        )
        if system in {"delta", "sigma"}:
            expected += textwrap.dedent(
                """\
                module load GCC/8.3
                module load OpenMPI/2.1.6/GCC/8.3
                module load ZLIB/1.2/11
                module load use.paustin
                module load HDF5/1.08/20
                module load NETCDF/4.6/1
                """
            )
        expected += textwrap.dedent(
            """\
            ${COMBINE} ${RUN_DESC} --debug
            echo "Results combining ended at $(date)"
            
            echo "Results deflation started at $(date)"
            """
        )
        if system in {"beluga", "cedar", "graham"}:
            expected += textwrap.dedent(
                """\
                module load nco/4.6.6
                """
            )
        expected += textwrap.dedent(
            """\
            ${DEFLATE} *_ptrc_T*.nc *_prod_T*.nc *_carp_T*.nc *_grid_[TUVW]*.nc \\
              *_turb_T*.nc *_dia[12n]_T*.nc FVCOM*.nc Slab_[UV]*.nc *_mtrc_T*.nc \\
              --jobs 4 --debug
            echo "Results deflation ended at $(date)"
            """
        )
        expected += textwrap.dedent(
            """\
            
            echo "Results gathering started at $(date)"
            ${GATHER} ${RESULTS_DIR} --debug
            echo "Results gathering ended at $(date)"
            """
        )
        assert script == expected

    @pytest.mark.parametrize(
        "system, mpirun_cmd, deflate, separate_deflate",
        [
            (
                "beluga",
                "mpirun -np 42 ./nemo.exe : -np 1 ./xios_server.exe",
                False,
                True,
            ),
            (
                "beluga",
                "mpirun -np 42 ./nemo.exe : -np 1 ./xios_server.exe",
                False,
                False,
            ),
            (
                "beluga",
                "mpirun -np 42 ./nemo.exe : -np 1 ./xios_server.exe",
                True,
                True,
            ),
            (
                "cedar",
                "mpirun -np 42 ./nemo.exe : -np 1 ./xios_server.exe",
                False,
                True,
            ),
            (
                "cedar",
                "mpirun -np 42 ./nemo.exe : -np 1 ./xios_server.exe",
                False,
                False,
            ),
            ("cedar", "mpirun -np 42 ./nemo.exe : -np 1 ./xios_server.exe", True, True),
            (
                "delta",
                "mpiexec -hostfile $(openmpi_nodefile) -bind-to core -np 42 ./nemo.exe : -bind-to core -np 1 ./xios_server.exe",
                False,
                True,
            ),
            (
                "delta",
                "mpiexec -hostfile $(openmpi_nodefile) -bind-to core -np 42 ./nemo.exe : -bind-to core -np 1 ./xios_server.exe",
                False,
                False,
            ),
            (
                "delta",
                "mpiexec -hostfile $(openmpi_nodefile) -bind-to core -np 42 ./nemo.exe : -bind-to core -np 1 ./xios_server.exe",
                True,
                True,
            ),
            (
                "graham",
                "mpirun -np 42 ./nemo.exe : -np 1 ./xios_server.exe",
                False,
                True,
            ),
            (
                "graham",
                "mpirun -np 42 ./nemo.exe : -np 1 ./xios_server.exe",
                False,
                False,
            ),
            (
                "graham",
                "mpirun -np 42 ./nemo.exe : -np 1 ./xios_server.exe",
                True,
                True,
            ),
            (
                "orcinus",
                "mpirun -np 42 ./nemo.exe : -np 1 ./xios_server.exe",
                False,
                True,
            ),
            (
                "orcinus",
                "mpirun -np 42 ./nemo.exe : -np 1 ./xios_server.exe",
                False,
                False,
            ),
            (
                "orcinus",
                "mpirun -np 42 ./nemo.exe : -np 1 ./xios_server.exe",
                True,
                True,
            ),
            (
                "salish",
                "/usr/bin/mpirun -np 42 ./nemo.exe : -np 1 ./xios_server.exe",
                False,
                True,
            ),
            (
                "salish",
                "/usr/bin/mpirun -np 42 ./nemo.exe : -np 1 ./xios_server.exe",
                False,
                False,
            ),
            (
                "salish",
                "/usr/bin/mpirun -np 42 ./nemo.exe : -np 1 ./xios_server.exe",
                True,
                True,
            ),
            (
                "sigma",
                "mpiexec -hostfile $(openmpi_nodefile) -bind-to core -np 42 ./nemo.exe : -bind-to core -np 1 ./xios_server.exe",
                False,
                True,
            ),
            (
                "sigma",
                "mpiexec -hostfile $(openmpi_nodefile) -bind-to core -np 42 ./nemo.exe : -bind-to core -np 1 ./xios_server.exe",
                False,
                False,
            ),
            (
                "sigma",
                "mpiexec -hostfile $(openmpi_nodefile) -bind-to core -np 42 ./nemo.exe : -bind-to core -np 1 ./xios_server.exe",
                True,
                True,
            ),
            (
                "sockeye",
                "mpirun --bind-to core -np 42 ./nemo.exe : --bind-to core -np 1 ./xios_server.exe",
                False,
                True,
            ),
            (
                "sockeye",
                "mpirun --bind-to core -np 42 ./nemo.exe : --bind-to core -np 1 ./xios_server.exe",
                False,
                False,
            ),
            (
                "sockeye",
                "mpirun --bind-to core -np 42 ./nemo.exe : --bind-to core -np 1 ./xios_server.exe",
                True,
                True,
            ),
        ],
    )
    def test_execute_without_deflate(
        self, system, mpirun_cmd, deflate, separate_deflate
    ):
        with patch("salishsea_cmd.run.SYSTEM", system):
            script = salishsea_cmd.run._execute(
                nemo_processors=42,
                xios_processors=1,
                deflate=deflate,
                max_deflate_jobs=4,
                separate_deflate=separate_deflate,
            )
        expected = textwrap.dedent(
            """\
            mkdir -p ${{RESULTS_DIR}}
            cd ${{WORK_DIR}}
            echo "working dir: $(pwd)"
    
            echo "Starting run at $(date)"
            {mpirun_cmd}
            MPIRUN_EXIT_CODE=$?
            echo "Ended run at $(date)"
    
            echo "Results combining started at $(date)"
            """.format(
                mpirun_cmd=mpirun_cmd
            )
        )
        if system in {"delta", "sigma"}:
            expected += textwrap.dedent(
                """\
                module load GCC/8.3
                module load OpenMPI/2.1.6/GCC/8.3
                module load ZLIB/1.2/11
                module load use.paustin
                module load HDF5/1.08/20
                module load NETCDF/4.6/1
                """
            )
        expected += textwrap.dedent(
            """\
            ${COMBINE} ${RUN_DESC} --debug
            echo "Results combining ended at $(date)"
            
            echo "Results gathering started at $(date)"
            ${GATHER} ${RESULTS_DIR} --debug
            echo "Results gathering ended at $(date)"
            """
        )
        assert script == expected


class TestCleanup:
    """Unit test for _cleanup() function.
    """

    def test_cleanup(self):
        script = salishsea_cmd.run._cleanup()
        expected = textwrap.dedent(
            """\
            echo "Deleting run directory" >>${RESULTS_DIR}/stdout
            rmdir $(pwd)
            echo "Finished at $(date)" >>${RESULTS_DIR}/stdout
            exit ${MPIRUN_EXIT_CODE}
            """
        )
        assert script == expected


@pytest.mark.parametrize(
    "pattern, result_type, pmem",
    [
        ("*_grid_[TUVW]*.nc", "grid", "2000mb"),
        ("*_ptrc_T*.nc", "ptrc", "2500mb"),
        ("*_dia[12]_T.nc", "dia", "2000mb"),
    ],
)
class TestBuildDeflateScript:
    """Unit test for _build_deflate_script() function.
    """

    def test_build_deflate_script_orcinus(self, pattern, result_type, pmem, tmpdir):
        run_desc = {
            "run_id": "19sep14_hindcast",
            "walltime": "3:00:00",
            "email": "test@example.com",
        }
        p_results_dir = tmpdir.ensure_dir("results_dir")
        with patch("salishsea_cmd.run.SYSTEM", "orcinus"):
            script = salishsea_cmd.run._build_deflate_script(
                run_desc, pattern, result_type, Path(str(p_results_dir))
            )
        expected = """#!/bin/bash
        
        #PBS -N {result_type}_19sep14_hindcast_deflate
        #PBS -S /bin/bash
        #PBS -l walltime=3:00:00
        # email when the job [b]egins and [e]nds, or is [a]borted
        #PBS -m bea
        #PBS -M test@example.com
        #PBS -l procs=1
        # memory per processor
        #PBS -l pmem={pmem}
        # stdout and stderr file paths/names
        #PBS -o {results_dir}/stdout_deflate_{result_type}
        #PBS -e {results_dir}/stderr_deflate_{result_type}
        
        RESULTS_DIR="{results_dir}"
        DEFLATE="${{PBS_O_HOME}}/.local/bin/salishsea deflate"
        
        module load intel
        module load intel/14.0/netcdf-4.3.3.1_mpi
        module load intel/14.0/netcdf-fortran-4.4.0_mpi
        module load intel/14.0/hdf5-1.8.15p1_mpi
        module load intel/14.0/nco-4.5.2
        module load python

        cd ${{RESULTS_DIR}}
        echo "Results deflation started at $(date)"
        ${{DEFLATE}} {pattern} --jobs 1 --debug
        DEFLATE_EXIT_CODE=$?
        echo "Results deflation ended at $(date)"
        
        chmod g+rw ${{RESULTS_DIR}}/*
        chmod o+r ${{RESULTS_DIR}}/*
        
        exit ${{DEFLATE_EXIT_CODE}}
        """.format(
            result_type=result_type,
            results_dir=str(p_results_dir),
            pattern=pattern,
            pmem=pmem,
        )
        expected = expected.splitlines()
        for i, line in enumerate(script.splitlines()):
            assert line.strip() == expected[i].strip()

    def test_build_deflate_script_pmem(self, pattern, result_type, pmem, tmpdir):
        run_desc = {
            "run_id": "19sep14_hindcast",
            "walltime": "3:00:00",
            "email": "test@example.com",
        }
        p_results_dir = tmpdir.ensure_dir("results_dir")
        script = salishsea_cmd.run._build_deflate_script(
            run_desc, pattern, result_type, Path(str(p_results_dir))
        )
        if result_type == "ptrc":
            assert "#PBS -l pmem=2500mb" in script
        else:
            assert "#PBS -l pmem=2000mb" in script
