# Copyright 2013-2017 The Salish Sea MEOPAR Contributors
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
"""SalishSeaCmd prepare sub-command plug-in unit tests
"""
try:
    from pathlib import Path
except ImportError:
    # Python 2.7
    from pathlib2 import Path
try:
    from unittest.mock import call, Mock, patch
except ImportError:
    # Python 2.7
    from mock import call, Mock, patch

import arrow
import cliff.app
import nemo_cmd.prepare
import pytest

import salishsea_cmd.prepare


@pytest.fixture
def prepare_cmd():
    return salishsea_cmd.prepare.Prepare(Mock(spec=cliff.app.App), [])


class TestParser:
    """Unit tests for `salishsea prepare` sub-command command-line parser.
    """

    def test_get_parser(self, prepare_cmd):
        parser = prepare_cmd.get_parser('salishsea prepare')
        assert parser.prog == 'salishsea prepare'

    def test_parsed_args_defaults(self, prepare_cmd):
        parser = prepare_cmd.get_parser('salishsea prepare')
        parsed_args = parser.parse_args(['foo'])
        assert parsed_args.desc_file == Path('foo')
        assert not parsed_args.quiet

    @pytest.mark.parametrize(
        'flag, attr', [
            ('-q', 'quiet'),
            ('--quiet', 'quiet'),
        ]
    )
    def test_parsed_args_flags(self, flag, attr, prepare_cmd):
        parser = prepare_cmd.get_parser('salishsea prepare')
        parsed_args = parser.parse_args(['foo', flag])
        assert getattr(parsed_args, attr)


@patch('salishsea_cmd.prepare.lib.load_run_desc')
@patch('nemo_cmd.prepare.check_nemo_exec', return_value='nemo_bin_dir')
@patch('nemo_cmd.prepare.check_xios_exec', return_value='xios_bin_dir')
@patch('nemo_cmd.api.find_rebuild_nemo_script')
@patch('nemo_cmd.resolved_path')
@patch('nemo_cmd.prepare.make_run_dir')
@patch('nemo_cmd.prepare.make_namelists')
@patch('nemo_cmd.prepare.copy_run_set_files')
@patch('nemo_cmd.prepare.make_executable_links')
@patch('nemo_cmd.prepare.make_grid_links')
@patch('nemo_cmd.prepare.make_forcing_links')
@patch('nemo_cmd.prepare.make_restart_links')
@patch('salishsea_cmd.prepare._record_vcs_revisions')
@patch('salishsea_cmd.prepare._add_agrif_files')
class TestPrepare:
    """Unit tests for `salishsea prepare` prepare() function.
    """

    def test_prepare(
        self, m_aaf, m_rvr, m_mrl, m_mfl, m_mgl, m_mel, m_crsf, m_mnl, m_mrd,
        m_resolved_path, m_frns, m_cxe, m_cne, m_lrd
    ):
        run_dir = salishsea_cmd.prepare.prepare(
            Path('SalishSea.yaml'), nocheck_init=False
        )
        m_lrd.assert_called_once_with(Path('SalishSea.yaml'))
        m_cne.assert_called_once_with(m_lrd())
        m_cne.assert_called_once_with(m_lrd())
        m_frns.assert_called_once_with(m_lrd())
        m_resolved_path.assert_called_once_with(Path('SalishSea.yaml'))
        m_mrd.assert_called_once_with(m_lrd())
        m_mnl.assert_called_once_with(
            m_resolved_path().parent, m_lrd(), m_mrd()
        )
        m_crsf.assert_called_once_with(
            m_lrd(), Path('SalishSea.yaml'),
            m_resolved_path().parent, m_mrd()
        )
        m_mel.assert_called_once_with('nemo_bin_dir', m_mrd(), 'xios_bin_dir')
        m_mgl.assert_called_once_with(m_lrd(), m_mrd())
        m_mfl.assert_called_once_with(m_lrd(), m_mrd())
        m_mrl.assert_called_once_with(m_lrd(), m_mrd(), False)
        m_aaf.assert_called_once_with(
            m_lrd(), Path('SalishSea.yaml'),
            m_resolved_path().parent, m_mrd(), False
        )
        m_rvr.assert_called_once_with(m_lrd(), m_mrd())
        assert run_dir == m_mrd()


class TestRecordVCSRevisions:
    """Unit tests for `salishsea prepare` _record_vcs_revisions() function.
    """

    def test_no_paths_forcing_key(self):
        run_desc = {}
        with pytest.raises(SystemExit):
            salishsea_cmd.prepare._record_vcs_revisions(
                run_desc, Path('run_dir')
            )

    @pytest.mark.parametrize(
        'config_name_key, nemo_code_config_key', [
            ('config name', 'NEMO code config'),
            ('config_name', 'NEMO-code-config'),
        ]
    )
    @patch('nemo_cmd.prepare.write_repo_rev_file')
    def test_write_repo_rev_file_default_calls(
        self, m_write, config_name_key, nemo_code_config_key, tmpdir
    ):
        nemo_code_repo = tmpdir.ensure_dir('NEMO-3.6-code')
        nemo_config = nemo_code_repo.ensure_dir('NEMOGCM', 'CONFIG')
        xios_code_repo = tmpdir.ensure_dir('XIOS')
        run_desc = {
            config_name_key: 'SalishSea',
            'paths': {
                nemo_code_config_key: str(nemo_config),
                'XIOS': str(xios_code_repo),
            }
        }
        salishsea_cmd.prepare._record_vcs_revisions(run_desc, Path('run_dir'))
        assert m_write.call_args_list == [
            call(
                Path(str(nemo_code_repo)), Path('run_dir'),
                nemo_cmd.prepare.get_hg_revision
            ),
            call(
                Path(str(xios_code_repo)), Path('run_dir'),
                nemo_cmd.prepare.get_hg_revision
            ),
        ]

    @pytest.mark.parametrize(
        'config_name_key, nemo_code_config_key', [
            ('config name', 'NEMO code config'),
            ('config_name', 'NEMO-code-config'),
        ]
    )
    @patch('nemo_cmd.prepare.write_repo_rev_file')
    def test_write_repo_rev_file_vcs_revisions_hg_call(
        self, m_write, config_name_key, nemo_code_config_key, tmpdir
    ):
        nemo_config = tmpdir.ensure_dir('NEMO-3.6-code', 'NEMOGCM', 'CONFIG')
        xios_code_repo = tmpdir.ensure_dir('XIOS')
        nemo_forcing = tmpdir.ensure_dir('NEMO-forcing')
        ss_run_sets = tmpdir.ensure_dir('SS-run-sets')
        run_desc = {
            config_name_key: 'SalishSea',
            'paths': {
                nemo_code_config_key: str(nemo_config),
                'XIOS': str(xios_code_repo),
                'forcing': str(nemo_forcing)
            },
            'vcs revisions': {
                'hg': [str(ss_run_sets)]
            }
        }
        salishsea_cmd.prepare._record_vcs_revisions(run_desc, Path('run_dir'))
        assert m_write.call_args_list[-1] == call(
            Path(str(ss_run_sets)), Path('run_dir'),
            nemo_cmd.prepare.get_hg_revision
        )


@patch('salishsea_cmd.prepare.logger', autospec=True)
@patch('nemo_cmd.prepare.make_grid_links', autospec=True)
@patch('nemo_cmd.prepare.make_restart_links', autospec=True)
@patch('nemo_cmd.prepare.copy_run_set_files', autospec=True)
@patch('nemo_cmd.prepare.make_namelists', autospec=True)
class TestAddAgrifFiles:
    """Unit tests for `salishsea prepare` _add_agrid_files() function.
    """

    @patch(
        'salishsea_cmd.prepare.get_run_desc_value',
        side_effect=KeyError,
        autospec=True
    )
    def test_no_agrif(
        self, m_get_run_desc_value, m_mk_nl_36, m_cp_run_set_files,
        mk_restart_links, m_mk_grid_links, m_logger
    ):
        run_desc = {}
        salishsea_cmd.prepare._add_agrif_files(
            run_desc,
            Path('foo.yaml'),
            Path('run_set_dir'),
            Path('run_dir'),
            nocheck_init=False
        )
        assert m_get_run_desc_value.call_args_list == [
            call(run_desc, ('AGRIF',), fatal=False)
        ]

    def test_no_fixed_grids_file(
        self, m_mk_nl_36, m_cp_run_set_files, mk_restart_links,
        m_mk_grid_links, m_logger
    ):
        run_desc = {'AGRIF': {}}
        with pytest.raises(SystemExit):
            salishsea_cmd.prepare._add_agrif_files(
                run_desc,
                Path('foo.yaml'),
                Path('run_set_dir'),
                Path('run_dir'),
                nocheck_init=False
            )

    def test_fixed_grids_file(
        self, m_mk_nl_36, m_cp_run_set_files, mk_restart_links,
        m_mk_grid_links, m_logger, tmpdir
    ):
        p_run_dir = tmpdir.ensure_dir('run_dir')
        p_fixed_grids = tmpdir.ensure('AGRIF_FixedGrids.in')
        run_desc = {
            'AGRIF': {
                'fixed grids': str(p_fixed_grids)
            },
            'grid': {
                'AGRIF_1': {}
            },
            'restart': {
                'AGRIF_1': {}
            },
            'namelists': {
                'AGRIF_1': {}
            },
            'output': {
                'AGRIF_1': {},
            },
        }
        p_open = patch('salishsea_cmd.prepare.Path.open')
        with p_open as m_open:
            m_open().__enter__.return_value = (
                '1\n# Byanes Sound\n40 70 2 30 3 3 3 43 \n'.splitlines()
            )
            salishsea_cmd.prepare._add_agrif_files(
                run_desc,
                Path('foo.yaml'),
                Path('run_set_dir'),
                Path(str(p_run_dir)),
                nocheck_init=False
            )
        assert p_run_dir.join('AGRIF_FixedGrids.in').check(file=True)

    @patch('salishsea_cmd.prepare.shutil.copy2', autospec=True)
    def test_make_grid_links(
        self, m_copy2, m_mk_nl_36, m_cp_run_set_files, mk_restart_links,
        m_mk_grid_links, m_logger, tmpdir
    ):
        p_fixed_grids = tmpdir.ensure('AGRIF_FixedGrids.in')
        run_desc = {
            'AGRIF': {
                'fixed grids': str(p_fixed_grids)
            },
            'grid': {
                'coordinates': 'coords.nc',
                'bathymetry': 'bathy.nc',
                'AGRIF_1': {},
                'AGRIF_2': {},
            },
            'restart': {
                'AGRIF_1': {},
                'AGRIF_2': {},
            },
            'namelists': {
                'AGRIF_1': {},
                'AGRIF_2': {},
            },
            'output': {
                'AGRIF_1': {},
                'AGRIF_2': {},
            },
        }
        p_open = patch('salishsea_cmd.prepare.Path.open')
        with p_open as m_open:
            m_open().__enter__.return_value = (
                '2\n# Byanes Sound\n40 70 2 30 3 3 3 43 \n'
                '110 130 50 80 3 3 3 42\n'.splitlines()
            )
            salishsea_cmd.prepare._add_agrif_files(
                run_desc,
                Path('foo.yaml'),
                Path('run_set_dir'),
                Path('run_dir'),
                nocheck_init=False
            )
        assert m_mk_grid_links.call_args_list == [
            call(run_desc, Path('run_dir'), agrif_n=1),
            call(run_desc, Path('run_dir'), agrif_n=2),
        ]

    @patch('salishsea_cmd.prepare.shutil.copy2', autospec=True)
    def test_grid_sub_grids_mismatch(
        self, m_copy2, m_mk_nl_36, m_cp_run_set_files, m_mk_restart_links,
        m_mk_grid_links, m_logger, tmpdir
    ):
        p_fixed_grids = tmpdir.ensure('AGRIF_FixedGrids.in')
        run_desc = {
            'AGRIF': {
                'fixed grids': str(p_fixed_grids)
            },
            'grid': {
                'coordinates': 'coords.nc',
                'bathymetry': 'bathy.nc',
                'AGRIF_1': {},
            },
            'restart': {
                'AGRIF_1': {},
            },
            'namelists': {
                'AGRIF_1': {},
                'AGRIF_2': {},
            },
            'output': {
                'AGRIF_1': {},
                'AGRIF_2': {},
            },
        }
        p_open = patch('salishsea_cmd.prepare.Path.open')
        with p_open as m_open:
            m_open().__enter__.return_value = (
                '2\n40 70 2 30 3 3 3 43 \n110 130 50 80 3 3 3 42\n'.splitlines(
                )
            )
            with pytest.raises(SystemExit):
                salishsea_cmd.prepare._add_agrif_files(
                    run_desc,
                    Path('foo.yaml'),
                    Path('run_set_dir'),
                    Path('run_dir'),
                    nocheck_init=False
                )

    @patch('salishsea_cmd.prepare.shutil.copy2', autospec=True)
    def test_make_restart_links(
        self, m_copy2, m_mk_nl_36, m_cp_run_set_files, m_mk_restart_links,
        m_mk_grid_links, m_logger, tmpdir
    ):
        p_fixed_grids = tmpdir.ensure('AGRIF_FixedGrids.in')
        run_desc = {
            'AGRIF': {
                'fixed grids': str(p_fixed_grids)
            },
            'grid': {
                'coordinates': 'coords.nc',
                'bathymetry': 'bathy.nc',
                'AGRIF_1': {},
                'AGRIF_2': {},
            },
            'restart': {
                'AGRIF_1': {},
                'AGRIF_2': {},
            },
            'namelists': {
                'AGRIF_1': {},
                'AGRIF_2': {},
            },
            'output': {
                'AGRIF_1': {},
                'AGRIF_2': {},
            },
        }
        p_open = patch('salishsea_cmd.prepare.Path.open')
        with p_open as m_open:
            m_open().__enter__.return_value = (
                '2\n40 70 2 30 3 3 3 43 \n110 130 50 80 3 3 3 42\n'.splitlines(
                )
            )
            salishsea_cmd.prepare._add_agrif_files(
                run_desc,
                Path('foo.yaml'),
                Path('run_set_dir'),
                Path('run_dir'),
                nocheck_init=False
            )
        assert m_mk_restart_links.call_args_list == [
            call(run_desc, Path('run_dir'), False, agrif_n=1),
            call(run_desc, Path('run_dir'), False, agrif_n=2),
        ]

    @patch('salishsea_cmd.prepare.shutil.copy2', autospec=True)
    def test_restart_sub_grids_mismatch(
        self, m_copy2, m_mk_nl_36, m_cp_run_set_files, m_mk_restart_links,
        m_mk_grid_links, m_logger, tmpdir
    ):
        p_fixed_grids = tmpdir.ensure('AGRIF_FixedGrids.in')
        run_desc = {
            'AGRIF': {
                'fixed grids': str(p_fixed_grids)
            },
            'grid': {
                'coordinates': 'coords.nc',
                'bathymetry': 'bathy.nc',
                'AGRIF_1': {},
                'AGRIF_2': {},
            },
            'restart': {
                'AGRIF_1': {},
            },
            'namelists': {
                'AGRIF_1': {},
                'AGRIF_2': {},
            },
            'output': {
                'AGRIF_1': {},
                'AGRIF_2': {},
            },
        }
        p_open = patch('salishsea_cmd.prepare.Path.open')
        with p_open as m_open:
            m_open().__enter__.return_value = (
                '2\n40 70 2 30 3 3 3 43 \n110 130 50 80 3 3 3 42\n'.splitlines(
                )
            )
            with pytest.raises(SystemExit):
                salishsea_cmd.prepare._add_agrif_files(
                    run_desc,
                    Path('foo.yaml'),
                    Path('run_set_dir'),
                    Path('run_dir'),
                    nocheck_init=False
                )

    @patch('salishsea_cmd.prepare.shutil.copy2', autospec=True)
    def test_no_restart(
        self, m_copy2, m_mk_nl_36, m_cp_run_set_files, m_mk_restart_links,
        m_mk_grid_links, m_logger, tmpdir
    ):
        p_fixed_grids = tmpdir.ensure('AGRIF_FixedGrids.in')
        run_desc = {
            'AGRIF': {
                'fixed grids': str(p_fixed_grids)
            },
            'grid': {
                'coordinates': 'coords.nc',
                'bathymetry': 'bathy.nc',
                'AGRIF_1': {},
                'AGRIF_2': {},
            },
            'namelists': {
                'AGRIF_1': {},
                'AGRIF_2': {},
            },
            'output': {
                'AGRIF_1': {},
                'AGRIF_2': {},
            },
        }
        p_open = patch('salishsea_cmd.prepare.Path.open')
        with p_open as m_open:
            m_open().__enter__.return_value = (
                '2\n40 70 2 30 3 3 3 43 \n110 130 50 80 3 3 3 42\n'.splitlines(
                )
            )
            salishsea_cmd.prepare._add_agrif_files(
                run_desc,
                Path('foo.yaml'),
                Path('run_set_dir'),
                Path('run_dir'),
                nocheck_init=False
            )
        assert m_mk_restart_links.call_args_list == []

    @patch('salishsea_cmd.prepare.shutil.copy2', autospec=True)
    def test_make_namelists(
        self, m_copy2, m_mk_nl, m_cp_run_set_files, m_mk_restart_links,
        m_mk_grid_links, m_logger, tmpdir
    ):
        p_fixed_grids = tmpdir.ensure('AGRIF_FixedGrids.in')
        run_desc = {
            'AGRIF': {
                'fixed grids': str(p_fixed_grids)
            },
            'grid': {
                'coordinates': 'coords.nc',
                'bathymetry': 'bathy.nc',
                'AGRIF_1': {},
                'AGRIF_2': {},
            },
            'restart': {
                'AGRIF_1': {},
                'AGRIF_2': {},
            },
            'namelists': {
                'AGRIF_1': {},
                'AGRIF_2': {},
            },
            'output': {
                'AGRIF_1': {},
                'AGRIF_2': {},
            },
        }
        p_open = patch('salishsea_cmd.prepare.Path.open')
        with p_open as m_open:
            m_open().__enter__.return_value = (
                '2\n40 70 2 30 3 3 3 43 \n110 130 50 80 3 3 3 42\n'.splitlines(
                )
            )
            salishsea_cmd.prepare._add_agrif_files(
                run_desc,
                Path('foo.yaml'),
                Path('run_set_dir'),
                Path('run_dir'),
                nocheck_init=False
            )
        assert m_mk_nl.call_args_list == [
            call(Path('run_set_dir'), run_desc, Path('run_dir'), agrif_n=1),
            call(Path('run_set_dir'), run_desc, Path('run_dir'), agrif_n=2),
        ]

    @patch('salishsea_cmd.prepare.shutil.copy2', autospec=True)
    def test_namelist_sub_grids_mismatch(
        self, m_copy2, m_mk_nl, m_cp_run_set_files, m_mk_restart_links,
        m_mk_grid_links, m_logger, tmpdir
    ):
        p_fixed_grids = tmpdir.ensure('AGRIF_FixedGrids.in')
        run_desc = {
            'AGRIF': {
                'fixed grids': str(p_fixed_grids)
            },
            'grid': {
                'coordinates': 'coords.nc',
                'bathymetry': 'bathy.nc',
                'AGRIF_1': {},
                'AGRIF_2': {},
            },
            'restart': {
                'AGRIF_1': {},
                'AGRIF_2': {},
            },
            'namelists': {
                'AGRIF_1': {},
            },
            'output': {
                'AGRIF_1': {},
                'AGRIF_2': {},
            },
        }
        p_open = patch('salishsea_cmd.prepare.Path.open')
        with p_open as m_open:
            m_open().__enter__.return_value = (
                '2\n40 70 2 30 3 3 3 43 \n110 130 50 80 3 3 3 42\n'.splitlines(
                )
            )
            with pytest.raises(SystemExit):
                salishsea_cmd.prepare._add_agrif_files(
                    run_desc,
                    Path('foo.yaml'),
                    Path('run_set_dir'),
                    Path('run_dir'),
                    nocheck_init=False
                )

    @patch('salishsea_cmd.prepare.shutil.copy2', autospec=True)
    def test_copy_run_set_files(
        self, m_copy2, m_mk_nl, m_cp_run_set_files, m_mk_restart_links,
        m_mk_grid_links, m_logger, tmpdir
    ):
        p_fixed_grids = tmpdir.ensure('AGRIF_FixedGrids.in')
        run_desc = {
            'AGRIF': {
                'fixed grids': str(p_fixed_grids)
            },
            'grid': {
                'coordinates': 'coords.nc',
                'bathymetry': 'bathy.nc',
                'AGRIF_1': {},
                'AGRIF_2': {},
            },
            'restart': {
                'AGRIF_1': {},
                'AGRIF_2': {},
            },
            'namelists': {
                'AGRIF_1': {},
                'AGRIF_2': {},
            },
            'output': {
                'AGRIF_1': {},
                'AGRIF_2': {},
            },
        }
        p_open = patch('salishsea_cmd.prepare.Path.open')
        with p_open as m_open:
            m_open().__enter__.return_value = (
                '2\n40 70 2 30 3 3 3 43 \n110 130 50 80 3 3 3 42\n'.splitlines(
                )
            )
            salishsea_cmd.prepare._add_agrif_files(
                run_desc,
                Path('foo.yaml'),
                Path('run_set_dir'),
                Path('run_dir'),
                nocheck_init=False
            )
        assert m_cp_run_set_files.call_args_list == [
            call(
                run_desc,
                Path('foo.yaml'),
                Path('run_set_dir'),
                Path('run_dir'),
                agrif_n=1
            ),
            call(
                run_desc,
                Path('foo.yaml'),
                Path('run_set_dir'),
                Path('run_dir'),
                agrif_n=2
            ),
        ]

    @patch('salishsea_cmd.prepare.shutil.copy2', autospec=True)
    def test_output_sub_grids_mismatch(
        self, m_copy2, m_mk_nl, m_cp_run_set_files, m_mk_restart_links,
        m_mk_grid_links, m_logger, tmpdir
    ):
        p_fixed_grids = tmpdir.ensure('AGRIF_FixedGrids.in')
        run_desc = {
            'AGRIF': {
                'fixed grids': str(p_fixed_grids)
            },
            'grid': {
                'coordinates': 'coords.nc',
                'bathymetry': 'bathy.nc',
                'AGRIF_1': {},
                'AGRIF_2': {},
            },
            'restart': {
                'AGRIF_1': {},
                'AGRIF_2': {},
            },
            'namelists': {
                'AGRIF_1': {},
                'AGRIF_2': {},
            },
            'output': {
                'AGRIF_1': {},
            },
        }
        p_open = patch('salishsea_cmd.prepare.Path.open')
        with p_open as m_open:
            m_open().__enter__.return_value = (
                '2\n40 70 2 30 3 3 3 43 \n110 130 50 80 3 3 3 42\n'.splitlines(
                )
            )
            with pytest.raises(SystemExit):
                salishsea_cmd.prepare._add_agrif_files(
                    run_desc,
                    Path('foo.yaml'),
                    Path('run_set_dir'),
                    Path('run_dir'),
                    nocheck_init=False
                )
