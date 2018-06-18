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
@patch('salishsea_cmd.prepare._make_run_dir')
@patch('salishsea_cmd.prepare._make_namelists')
@patch('salishsea_cmd.prepare._copy_run_set_files')
@patch('salishsea_cmd.prepare._make_executable_links')
@patch('salishsea_cmd.prepare._make_grid_links')
@patch('salishsea_cmd.prepare._make_forcing_links')
@patch('salishsea_cmd.prepare._make_restart_links')
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


class TestMakeRunDir:
    """Unit test for `salishsea prepare` _make_run_dir() function.
    """

    @patch(
        'salishsea_cmd.prepare.arrow.now',
        return_value=arrow.get('2017-10-01 18:23:55.555919-0700')
    )
    def test_make_run_dir(self, m_isoformat, tmpdir):
        p_runs_dir = tmpdir.ensure_dir('SalishSea')
        run_desc = {
            'run_id': 'foo',
            'paths': {
                'runs directory': str(p_runs_dir)
            },
        }
        run_dir = salishsea_cmd.prepare._make_run_dir(run_desc)
        expected = (
            Path(str(p_runs_dir)) / 'foo_2017-10-01T182355.555919-0700'
        )
        assert run_dir == expected


class TestRemoveRunDir:
    """Unit tests for `salishsea prepare` _remove_run_dir() function.
    """

    def test_remove_run_dir(self, tmpdir):
        p_run_dir = tmpdir.ensure_dir('run_dir')
        salishsea_cmd.prepare._remove_run_dir(Path(str(p_run_dir)))
        assert not p_run_dir.check()

    def test_remove_run_dir_file(self, tmpdir):
        p_run_dir = tmpdir.ensure_dir('run_dir')
        p_run_dir.ensure('namelist')
        salishsea_cmd.prepare._remove_run_dir(Path(str(p_run_dir)))
        assert not p_run_dir.join('namelist').check()
        assert not p_run_dir.check()

    @patch('salishsea_cmd.prepare.Path.rmdir')
    def test_remove_run_dir_no_run_dir(self, m_rmdir):
        salishsea_cmd.prepare._remove_run_dir(Path('run_dir'))
        assert not m_rmdir.called


class TestMakeNamelists:
    """Unit tests for `salishsea prepare` _make_namelists() function.
    """

    def test_make_namelists(self, tmpdir):
        p_nemo_config_dir = tmpdir.ensure_dir('NEMO-3.6/NEMOGCM/CONFIG')
        p_run_set_dir = tmpdir.ensure_dir('run_set_dir')
        p_run_set_dir.join('namelist.time').write('&namrun\n&end\n')
        p_run_set_dir.join('namelist_top').write('&namtrc\n&end\n')
        p_run_set_dir.join('namelist_pisces').write('&nampisbio\n&end\n')
        run_desc = {
            'config name': 'SalishSea',
            'paths': {
                'NEMO code config': str(p_nemo_config_dir),
            },
            'namelists': {
                'namelist_cfg': [str(p_run_set_dir.join('namelist.time'))],
                'namelist_top_cfg': [str(p_run_set_dir.join('namelist_top'))],
                'namelist_pisces_cfg': [
                    str(p_run_set_dir.join('namelist_pisces')),
                ],
            }
        }
        p_run_dir = tmpdir.ensure_dir('run_dir')
        p_nemo_config_dir.ensure('SalishSea/EXP00/namelist_ref')
        p_nemo_config_dir.ensure('SalishSea/EXP00/namelist_top_ref')
        p_nemo_config_dir.ensure('SalishSea/EXP00/namelist_pisces_ref')
        p_set_mpi_decomp = patch(
            'salishsea_cmd.prepare._set_mpi_decomposition', autospec=True
        )
        with p_set_mpi_decomp:
            salishsea_cmd.prepare._make_namelists(
                Path(str(p_run_set_dir)), run_desc, Path(str(p_run_dir))
            )
        assert p_run_dir.join('namelist_cfg').check(file=True, link=False)
        assert p_run_dir.join('namelist_top_cfg').check(file=True, link=False)
        assert p_run_dir.join('namelist_pisces_cfg').check(
            file=True, link=False
        )
        assert p_run_dir.join('namelist_ref').check(file=True, link=False)
        assert p_run_dir.join('namelist_top_ref').check(file=True, link=False)
        assert p_run_dir.join('namelist_pisces_ref').check(
            file=True, link=False
        )

    def test_agrif_make_namelists(self, tmpdir):
        p_nemo_config_dir = tmpdir.ensure_dir('NEMO-3.6/NEMOGCM/CONFIG')
        p_run_set_dir = tmpdir.ensure_dir('run_set_dir')
        p_run_set_dir.join('1_namelist.time').write('&namrun\n&end\n')
        p_run_set_dir.join('1_namelist_top').write('&namtrc\n&end\n')
        p_run_set_dir.join('1_namelist_pisces').write('&nampisbio\n&end\n')
        run_desc = {
            'config name': 'SalishSea',
            'paths': {
                'NEMO code config': str(p_nemo_config_dir),
            },
            'namelists': {
                'AGRIF_1': {
                    'namelist_cfg':
                    [str(p_run_set_dir.join('1_namelist.time'))],
                    'namelist_top_cfg':
                    [str(p_run_set_dir.join('1_namelist_top'))],
                    'namelist_pisces_cfg': [
                        str(p_run_set_dir.join('1_namelist_pisces')),
                    ],
                }
            }
        }
        p_run_dir = tmpdir.ensure_dir('run_dir')
        p_nemo_config_dir.ensure('SalishSea/EXP00/namelist_ref')
        p_nemo_config_dir.ensure('SalishSea/EXP00/namelist_top_ref')
        p_nemo_config_dir.ensure('SalishSea/EXP00/namelist_pisces_ref')
        p_set_mpi_decomp = patch(
            'salishsea_cmd.prepare._set_mpi_decomposition', autospec=True
        )
        with p_set_mpi_decomp:
            salishsea_cmd.prepare._make_namelists(
                Path(str(p_run_set_dir)),
                run_desc,
                Path(str(p_run_dir)),
                agrif_n=1
            )
        assert p_run_dir.join('1_namelist_cfg').check(file=True, link=False)
        assert p_run_dir.join('1_namelist_top_cfg').check(
            file=True, link=False
        )
        assert p_run_dir.join('1_namelist_pisces_cfg').check(
            file=True, link=False
        )
        assert p_run_dir.join('1_namelist_ref').check(file=True, link=False)
        assert p_run_dir.join('1_namelist_top_ref').check(
            file=True, link=False
        )
        assert p_run_dir.join('1_namelist_pisces_ref').check(
            file=True, link=False
        )

    @patch('salishsea_cmd.prepare.logger', autospec=True)
    def test_namelist_file_not_found_error(self, m_logger, tmpdir):
        p_nemo_config_dir = tmpdir.ensure_dir('NEMO-3.6/NEMOGCM/CONFIG')
        p_run_set_dir = tmpdir.ensure_dir('run_set_dir')
        run_desc = {
            'config name': 'SalishSea',
            'paths': {
                'NEMO code config': str(p_nemo_config_dir),
            },
            'namelists': {
                'namelist_cfg': [str(p_run_set_dir.join('namelist.time'))],
            }
        }
        p_run_dir = tmpdir.ensure_dir('run_dir')
        with pytest.raises(SystemExit):
            salishsea_cmd.prepare._make_namelists(
                Path(str(p_run_set_dir)), run_desc, Path(str(p_run_dir))
            )

    def test_namelist_ref_not_shared(self, tmpdir):
        p_nemo_config_dir = tmpdir.ensure_dir('NEMO-3.6/NEMOGCM/CONFIG')
        p_run_set_dir = tmpdir.ensure_dir('run_set_dir')
        p_run_set_dir.join('namelist.time').write('&namrun\n&end\n')
        p_run_set_dir.join('namelist_top').write('&namtrc\n&end\n')
        p_run_set_dir.join('namelist_pisces').write('&nampisbio\n&end\n')
        p_run_set_dir.join('namelist_ref').write('&namrun\n&end\n')
        p_run_set_dir.join('namelist_top_ref').write('&namtrc\n&end\n')
        p_run_set_dir.join('namelist_pisces_ref').write('&nampisbio\n&end\n')
        run_desc = {
            'config name': 'SalishSea',
            'paths': {
                'NEMO code config': str(p_nemo_config_dir),
            },
            'namelists': {
                'namelist_cfg': [str(p_run_set_dir.join('namelist.time'))],
                'namelist_top_cfg': [str(p_run_set_dir.join('namelist_top'))],
                'namelist_pisces_cfg': [
                    str(p_run_set_dir.join('namelist_pisces')),
                ],
                'namelist_ref': [str(p_run_set_dir.join('namelist_ref'))],
                'namelist_top_ref':
                [str(p_run_set_dir.join('namelist_top_ref'))],
                'namelist_pisces_ref': [
                    str(p_run_set_dir.join('namelist_pisces_ref')),
                ],
            }
        }
        p_run_dir = tmpdir.ensure_dir('run_dir')
        p_set_mpi_decomp = patch(
            'salishsea_cmd.prepare._set_mpi_decomposition', autospec=True
        )
        with p_set_mpi_decomp:
            salishsea_cmd.prepare._make_namelists(
                Path(str(p_run_set_dir)), run_desc, Path(str(p_run_dir))
            )
        assert p_run_dir.join('namelist_ref').check(file=True, link=False)
        assert p_run_dir.join('namelist_top_ref').check(file=True, link=False)
        assert p_run_dir.join('namelist_pisces_ref').check(
            file=True, link=False
        )

    def test_agrif_namelist_ref_not_shared(self, tmpdir):
        p_nemo_config_dir = tmpdir.ensure_dir('NEMO-3.6/NEMOGCM/CONFIG')
        p_run_set_dir = tmpdir.ensure_dir('run_set_dir')
        p_run_set_dir.join('1_namelist.time').write('&namrun\n&end\n')
        p_run_set_dir.join('1_namelist_top').write('&namtrc\n&end\n')
        p_run_set_dir.join('1_namelist_pisces').write('&nampisbio\n&end\n')
        p_run_set_dir.join('1_namelist_ref').write('&namrun\n&end\n')
        p_run_set_dir.join('1_namelist_top_ref').write('&namtrc\n&end\n')
        p_run_set_dir.join('1_namelist_pisces_ref').write('&nampisbio\n&end\n')
        run_desc = {
            'config name': 'SalishSea',
            'paths': {
                'NEMO code config': str(p_nemo_config_dir),
            },
            'namelists': {
                'AGRIF_1': {
                    'namelist_cfg':
                    [str(p_run_set_dir.join('1_namelist.time'))],
                    'namelist_top_cfg':
                    [str(p_run_set_dir.join('1_namelist_top'))],
                    'namelist_pisces_cfg': [
                        str(p_run_set_dir.join('1_namelist_pisces')),
                    ],
                    'namelist_ref':
                    [str(p_run_set_dir.join('1_namelist_ref'))],
                    'namelist_top_ref': [
                        str(p_run_set_dir.join('1_namelist_top_ref'))
                    ],
                    'namelist_pisces_ref': [
                        str(p_run_set_dir.join('1_namelist_pisces_ref')),
                    ],
                }
            }
        }
        p_run_dir = tmpdir.ensure_dir('run_dir')
        p_set_mpi_decomp = patch(
            'salishsea_cmd.prepare._set_mpi_decomposition', autospec=True
        )
        with p_set_mpi_decomp:
            salishsea_cmd.prepare._make_namelists(
                Path(str(p_run_set_dir)),
                run_desc,
                Path(str(p_run_dir)),
                agrif_n=1
            )
        assert p_run_dir.join('1_namelist_ref').check(file=True, link=False)
        assert p_run_dir.join('1_namelist_top_ref').check(
            file=True, link=False
        )
        assert p_run_dir.join('1_namelist_pisces_ref').check(
            file=True, link=False
        )

    def test_namelist_cfg_set_mpi_decomposition(self, tmpdir):
        p_nemo_config_dir = tmpdir.ensure_dir('NEMO-3.6/NEMOGCM/CONFIG')
        p_run_set_dir = tmpdir.ensure_dir('run_set_dir')
        p_run_set_dir.join('namelist.time').write('&namrun\n&end\n')
        p_run_set_dir.join('namelist_top').write('&namtrc\n&end\n')
        run_desc = {
            'config name': 'SalishSea',
            'paths': {
                'NEMO code config': str(p_nemo_config_dir),
            },
            'namelists': {
                'namelist_cfg': [
                    str(p_run_set_dir.join('namelist.time')),
                ],
                'namelist_top_cfg': [
                    str(p_run_set_dir.join('namelist_top')),
                ],
            }
        }
        p_run_dir = tmpdir.ensure_dir('run_dir')
        p_nemo_config_dir.ensure('SalishSea/EXP00/namelist_ref')
        p_nemo_config_dir.ensure('SalishSea/EXP00/namelist_top_ref')
        p_nemo_config_dir.ensure('SalishSea/EXP00/namelist_pisces_ref')
        p_set_mpi_decomp = patch(
            'salishsea_cmd.prepare._set_mpi_decomposition', autospec=True
        )
        with p_set_mpi_decomp as m_set_mpi_decomp:
            salishsea_cmd.prepare._make_namelists(
                Path(str(p_run_set_dir)), run_desc, Path(str(p_run_dir))
            )
        m_set_mpi_decomp.assert_called_once_with(
            'namelist_cfg', run_desc, Path(str(p_run_dir))
        )

    @patch('salishsea_cmd.prepare.logger', autospec=True)
    def test_no_namelist_cfg_error(self, m_logger, tmpdir):
        p_nemo_config_dir = tmpdir.ensure_dir('NEMO-3.6/NEMOGCM/CONFIG')
        p_run_set_dir = tmpdir.ensure_dir('run_set_dir')
        p_run_set_dir.join('namelist_top').write('&namtrc\n&end\n')
        run_desc = {
            'config name': 'SalishSea',
            'paths': {
                'NEMO code config': str(p_nemo_config_dir),
            },
            'namelists': {
                'namelist_top_cfg': [
                    str(p_run_set_dir.join('namelist_top')),
                ],
            }
        }
        p_run_dir = tmpdir.ensure_dir('run_dir')
        p_nemo_config_dir.ensure('SalishSea/EXP00/namelist_ref')
        p_nemo_config_dir.ensure('SalishSea/EXP00/namelist_top_ref')
        p_nemo_config_dir.ensure('SalishSea/EXP00/namelist_pisces_ref')
        with pytest.raises(SystemExit):
            salishsea_cmd.prepare._make_namelists(
                Path(str(p_run_set_dir)), run_desc, Path(str(p_run_dir))
            )

    @patch('salishsea_cmd.prepare.logger', autospec=True)
    def test_agrif_no_namelist_cfg_error(self, m_logger, tmpdir):
        p_nemo_config_dir = tmpdir.ensure_dir('NEMO-3.6/NEMOGCM/CONFIG')
        p_run_set_dir = tmpdir.ensure_dir('run_set_dir')
        p_run_set_dir.join('1_namelist_top').write('&namtrc\n&end\n')
        run_desc = {
            'config name': 'SalishSea',
            'paths': {
                'NEMO code config': str(p_nemo_config_dir),
            },
            'namelists': {
                'AGRIF_1': {
                    'namelist_top_cfg': [
                        str(p_run_set_dir.join('namelist_top')),
                    ],
                }
            }
        }
        p_run_dir = tmpdir.ensure_dir('run_dir')
        p_nemo_config_dir.ensure('SalishSea/EXP00/1_namelist_ref')
        p_nemo_config_dir.ensure('SalishSea/EXP00/1_namelist_top_ref')
        p_nemo_config_dir.ensure('SalishSea/EXP00/1_namelist_pisces_ref')
        with pytest.raises(SystemExit):
            salishsea_cmd.prepare._make_namelists(
                Path(str(p_run_set_dir)),
                run_desc,
                Path(str(p_run_dir)),
                agrif_n=1
            )


class TestCopyRunSetFiles:
    """Unit tests for `salishsea prepare` _copy_run_set_files() function.
    """

    @pytest.mark.parametrize(
        'iodefs_key, domains_key, fields_key',
        [
            ('iodefs', 'domaindefs', 'fielddefs'),  # recommended
            ('files', 'domain', 'fields'),  # backward compatibility
        ]
    )
    @patch('salishsea_cmd.prepare.shutil.copy2')
    @patch('salishsea_cmd.prepare._set_xios_server_mode')
    @patch('salishsea_cmd.prepare.get_run_desc_value')
    def test_copy_run_set_files_no_path(
        self, m_get_run_desc_value, m_sxsm, m_copy, iodefs_key, domains_key,
        fields_key
    ):
        run_desc = {
            'output': {
                iodefs_key: 'iodef.xml',
                domains_key: 'domain_def.xml',
                fields_key: 'field_def.xml',
                'AGRIF_1': {
                    domains_key: '1_domain_def.xml',
                },
            },
        }
        desc_file = Path('foo.yaml')
        pwd = Path.cwd()
        m_get_run_desc_value.side_effect = (
            pwd / 'iodef.xml', pwd / 'domain_def.xml', pwd / 'field_def.xml',
            KeyError
        )
        salishsea_cmd.prepare._copy_run_set_files(
            run_desc, desc_file, pwd, Path('run_dir')
        )
        expected = [
            call(str(pwd / 'iodef.xml'), str(Path('run_dir') / 'iodef.xml')),
            call(str(pwd / 'foo.yaml'), str(Path('run_dir') / 'foo.yaml')),
            call(
                str(pwd / 'domain_def.xml'),
                str(Path('run_dir') / 'domain_def.xml')
            ),
            call(
                str(pwd / 'field_def.xml'),
                str(Path('run_dir') / 'field_def.xml')
            ),
        ]
        assert m_copy.call_args_list == expected

    @pytest.mark.parametrize(
        'iodefs_key, domains_key, fields_key',
        [
            ('iodefs', '1_domaindefs', 'fielddefs'),  # recommended
            ('files', '1_domain', 'fields'),  # backward compatibility
        ]
    )
    @patch('salishsea_cmd.prepare.shutil.copy2')
    @patch('salishsea_cmd.prepare._set_xios_server_mode')
    @patch('salishsea_cmd.prepare.get_run_desc_value')
    def test_copy_agrif_run_set_files_no_path(
        self, m_get_run_desc_value, m_sxsm, m_copy, iodefs_key, domains_key,
        fields_key
    ):
        run_desc = {
            'output': {
                iodefs_key: 'iodef.xml',
                domains_key: 'domain_def.xml',
                fields_key: 'field_def.xml',
                'AGRIF_1': {
                    domains_key: '1_domain_def.xml',
                },
            },
        }
        desc_file = Path('foo.yaml')
        pwd = Path.cwd()
        m_get_run_desc_value.side_effect = (
            pwd / 'iodef.xml', pwd / '1_domain_def.xml', pwd / 'field_def.xml',
            KeyError
        )
        salishsea_cmd.prepare._copy_run_set_files(
            run_desc, desc_file, pwd, Path('run_dir'), agrif_n=1
        )
        expected = [
            call(str(pwd / 'iodef.xml'), str(Path('run_dir') / 'iodef.xml')),
            call(str(pwd / 'foo.yaml'), str(Path('run_dir') / 'foo.yaml')),
            call(
                str(pwd / '1_domain_def.xml'),
                str(Path('run_dir') / '1_domain_def.xml')
            ),
            call(
                str(pwd / 'field_def.xml'),
                str(Path('run_dir') / 'field_def.xml')
            ),
        ]
        assert m_copy.call_args_list == expected

    @pytest.mark.parametrize(
        'iodefs_key, domains_key, fields_key',
        [
            ('iodefs', 'domaindefs', 'fielddefs'),  # recommended
            ('files', 'domain', 'fields'),  # backward compatibility
        ]
    )
    @patch('salishsea_cmd.prepare.shutil.copy2')
    @patch('salishsea_cmd.prepare._set_xios_server_mode')
    @patch('salishsea_cmd.prepare.get_run_desc_value')
    def test_copy_run_set_files_relative_path(
        self, m_get_run_desc_value, m_sxsm, m_copy, iodefs_key, domains_key,
        fields_key
    ):
        run_desc = {
            'output': {
                iodefs_key: '../iodef.xml',
                domains_key: '../domain_def.xml',
                fields_key: '../field_def.xml',
                'AGRIF_1': {
                    domains_key: '1_domain_def.xml',
                },
            },
        }
        desc_file = Path('foo.yaml')
        pwd = Path.cwd()
        m_get_run_desc_value.side_effect = ((pwd / '../iodef.xml').resolve(), (
            pwd / '../domain_def.xml'
        ).resolve(), (pwd / '../field_def.xml').resolve(), KeyError)
        salishsea_cmd.prepare._copy_run_set_files(
            run_desc, desc_file, pwd, Path('run_dir')
        )
        expected = [
            call(
                str(pwd.parent / 'iodef.xml'),
                str(Path('run_dir') / 'iodef.xml')
            ),
            call(str(pwd / 'foo.yaml'), str(Path('run_dir') / 'foo.yaml')),
            call(
                str(pwd.parent / 'domain_def.xml'),
                str(Path('run_dir') / 'domain_def.xml')
            ),
            call(
                str(pwd.parent / 'field_def.xml'),
                str(Path('run_dir') / 'field_def.xml')
            ),
        ]
        assert m_copy.call_args_list == expected

    @pytest.mark.parametrize(
        'iodefs_key, domains_key, fields_key',
        [
            ('iodefs', 'domaindefs', 'fielddefs'),  # recommended
            ('files', 'domain', 'fields'),  # backward compatibility
        ]
    )
    @patch('salishsea_cmd.prepare.shutil.copy2')
    @patch('salishsea_cmd.prepare._set_xios_server_mode')
    @patch('salishsea_cmd.prepare.get_run_desc_value')
    def test_copy_agrif_run_set_files_relative_path(
        self, m_get_run_desc_value, m_sxsm, m_copy, iodefs_key, domains_key,
        fields_key
    ):
        run_desc = {
            'output': {
                iodefs_key: '../iodef.xml',
                domains_key: '../domain_def.xml',
                fields_key: '../field_def.xml',
                'AGRIF_1': {
                    domains_key: '1_domain_def.xml',
                },
            },
        }
        desc_file = Path('foo.yaml')
        pwd = Path.cwd()
        m_get_run_desc_value.side_effect = ((pwd / '../iodef.xml').resolve(), (
            pwd / '../1_domain_def.xml'
        ).resolve(), (pwd / '../field_def.xml').resolve(), KeyError)
        salishsea_cmd.prepare._copy_run_set_files(
            run_desc, desc_file, pwd, Path('run_dir'), agrif_n=1
        )
        expected = [
            call(
                str(pwd.parent / 'iodef.xml'),
                str(Path('run_dir') / 'iodef.xml')
            ),
            call(str(pwd / 'foo.yaml'), str(Path('run_dir') / 'foo.yaml')),
            call(
                str(pwd.parent / '1_domain_def.xml'),
                str(Path('run_dir') / '1_domain_def.xml')
            ),
            call(
                str(pwd.parent / 'field_def.xml'),
                str(Path('run_dir') / 'field_def.xml')
            ),
        ]
        assert m_copy.call_args_list == expected

    @patch('salishsea_cmd.prepare.shutil.copy2')
    @patch('salishsea_cmd.prepare._set_xios_server_mode')
    @patch('salishsea_cmd.prepare.get_run_desc_value')
    def test_files_def(self, m_get_run_desc_value, m_sxsm, m_copy):
        run_desc = {
            'output': {
                'iodefs': '../iodef.xml',
                'filedefs': '../file_def.xml',
                'domaindefs': '../domain_def.xml',
                'fielddefs': '../field_def.xml',
                'AGRIF_1': {
                    'domaindefs': '../1_domain_def.xml',
                    'filedefs': '../1_file_def.xml',
                },
            },
        }
        desc_file = Path('foo.yaml')
        pwd = Path.cwd()
        m_get_run_desc_value.side_effect = (
            (pwd / '../iodef.xml').resolve(),
            (pwd / '../domain_def.xml').resolve(),
            (pwd / '../field_def.xml').resolve(),
            (pwd / '../file_def.xml').resolve()
        )
        salishsea_cmd.prepare._copy_run_set_files(
            run_desc, desc_file, pwd, Path('run_dir')
        )
        assert m_copy.call_args_list[-1] == call(
            str(pwd.parent / 'file_def.xml'),
            str(Path('run_dir') / 'file_def.xml')
        )

    @patch('salishsea_cmd.prepare.shutil.copy2')
    @patch('salishsea_cmd.prepare._set_xios_server_mode')
    @patch('salishsea_cmd.prepare.get_run_desc_value')
    def test_agrif_files_def(self, m_get_run_desc_value, m_sxsm, m_copy):
        run_desc = {
            'output': {
                'iodefs': '../iodef.xml',
                'filedefs': '../file_def.xml',
                'domaindefs': '../domain_def.xml',
                'fielddefs': '../field_def.xml',
                'AGRIF_1': {
                    'domaindefs': '../1_domain_def.xml',
                    'filedefs': '../1_file_def.xml',
                },
            },
        }
        desc_file = Path('foo.yaml')
        pwd = Path.cwd()
        m_get_run_desc_value.side_effect = (
            (pwd / '../iodef.xml').resolve(),
            (pwd / '../1_domain_def.xml').resolve(),
            (pwd / '../field_def.xml').resolve(),
            (pwd / '../1_file_def.xml').resolve()
        )
        salishsea_cmd.prepare._copy_run_set_files(
            run_desc, desc_file, pwd, Path('run_dir'), agrif_n=1
        )
        assert m_copy.call_args_list[-1] == call(
            str(pwd.parent / '1_file_def.xml'),
            str(Path('run_dir') / '1_file_def.xml')
        )


class TestMakeExecutableLinks:
    """Unit tests for `salishsea prepare` _make_executable_links() function.
    """

    def test_nemo_exe_symlink(self, tmpdir):
        p_nemo_bin_dir = tmpdir.ensure_dir(
            'NEMO-code/NEMOGCM/CONFIG/SalishSea/BLD/bin'
        )
        p_nemo_bin_dir.ensure('nemo.exe')
        p_xios_bin_dir = tmpdir.ensure_dir('XIOS/bin')
        p_run_dir = tmpdir.ensure_dir('run_dir')
        salishsea_cmd.prepare._make_executable_links(
            Path(str(p_nemo_bin_dir)), Path(str(p_run_dir)),
            Path(str(p_xios_bin_dir))
        )
        assert p_run_dir.join('nemo.exe').check(file=True, link=True)

    def test_server_exe_symlink(self, tmpdir):
        p_nemo_bin_dir = tmpdir.ensure_dir(
            'NEMO-code/NEMOGCM/CONFIG/SalishSea/BLD/bin'
        )
        p_nemo_bin_dir.ensure('nemo.exe')
        p_xios_bin_dir = tmpdir.ensure_dir('XIOS/bin')
        p_run_dir = tmpdir.ensure_dir('run_dir')
        salishsea_cmd.prepare._make_executable_links(
            Path(str(p_nemo_bin_dir)), Path(str(p_run_dir)),
            Path(str(p_xios_bin_dir))
        )
        assert not p_run_dir.join('server.exe').check(file=True, link=True)

    def test_xios_server_exe_symlink(self, tmpdir):
        p_nemo_bin_dir = tmpdir.ensure_dir(
            'NEMO-code/NEMOGCM/CONFIG/SalishSea/BLD/bin'
        )
        p_nemo_bin_dir.ensure('nemo.exe')
        p_xios_bin_dir = tmpdir.ensure_dir('XIOS/bin')
        p_xios_bin_dir.ensure('xios_server.exe')
        p_run_dir = tmpdir.ensure_dir('run_dir')
        salishsea_cmd.prepare._make_executable_links(
            Path(str(p_nemo_bin_dir)), Path(str(p_run_dir)),
            Path(str(p_xios_bin_dir))
        )
        assert p_run_dir.join('xios_server.exe').check(file=True, link=True)


class TestMakeGridLinks:
    """Unit tests for `nemo prepare` _make_grid_links() function.
    """

    @patch('nemo_cmd.prepare._remove_run_dir')
    def test_no_grid_coordinates_key(self, m_rm_run_dir):
        run_desc = {}
        with pytest.raises(SystemExit):
            salishsea_cmd.prepare._make_grid_links(run_desc, Path('run_dir'))
        m_rm_run_dir.assert_called_once_with(Path('run_dir'))

    @patch('nemo_cmd.prepare._remove_run_dir')
    def test_no_grid_bathymetry_key(self, m_rm_run_dir):
        run_desc = {'grid': {'coordinates': 'coords.nc'}}
        with pytest.raises(SystemExit):
            salishsea_cmd.prepare._make_grid_links(run_desc, Path('run_dir'))
        m_rm_run_dir.assert_called_once_with(Path('run_dir'))

    @patch('nemo_cmd.prepare._remove_run_dir')
    def test_no_forcing_key(self, m_rm_run_dir):
        run_desc = {
            'grid': {
                'coordinates': 'coords.nc',
                'bathymetry': 'bathy.nc'
            }
        }
        with pytest.raises(SystemExit):
            salishsea_cmd.prepare._make_grid_links(run_desc, Path('run_dir'))
        m_rm_run_dir.assert_called_once_with(Path('run_dir'))

    @patch('salishsea_cmd.prepare._remove_run_dir')
    @patch('salishsea_cmd.prepare.logger')
    def test_no_link_path_absolute_coords_bathy(self, m_logger, m_rm_run_dir):
        run_desc = {
            'grid': {
                'coordinates': '/coords.nc',
                'bathymetry': '/bathy.nc'
            },
        }
        with pytest.raises(SystemExit):
            salishsea_cmd.prepare._make_grid_links(run_desc, Path('run_dir'))
        m_logger.error.assert_called_once_with(
            '/coords.nc not found; cannot create symlink - '
            'please check the forcing path and grid file names '
            'in your run description file'
        )
        m_rm_run_dir.assert_called_once_with(Path('run_dir'))

    @patch('salishsea_cmd.prepare._remove_run_dir')
    @patch('salishsea_cmd.prepare.logger')
    def test_no_link_path_relative_coords_bathy(
        self, m_logger, m_rm_run_dir, tmpdir
    ):
        forcing_dir = tmpdir.ensure_dir('foo')
        grid_dir = forcing_dir.ensure_dir('grid')
        run_dir = tmpdir.ensure_dir('runs')
        run_desc = {
            'paths': {
                'forcing': str(forcing_dir)
            },
            'grid': {
                'coordinates': 'coords.nc',
                'bathymetry': 'bathy.nc'
            },
        }
        with pytest.raises(SystemExit):
            salishsea_cmd.prepare._make_grid_links(
                run_desc, Path(str(run_dir))
            )
        m_logger.error.assert_called_once_with(
            '{}/coords.nc not found; cannot create symlink - '
            'please check the forcing path and grid file names '
            'in your run description file'.format(grid_dir)
        )
        m_rm_run_dir.assert_called_once_with(Path(str(run_dir)))

    @patch('salishsea_cmd.prepare._remove_run_dir')
    @patch('salishsea_cmd.prepare.logger')
    def test_link_paths(self, m_logger, m_rm_run_dir, tmpdir):
        forcing_dir = tmpdir.ensure_dir('foo')
        grid_dir = forcing_dir.ensure_dir('grid')
        grid_dir.ensure('coords.nc')
        grid_dir.ensure('bathy.nc')
        run_dir = tmpdir.ensure_dir('runs')
        run_desc = {
            'paths': {
                'forcing': str(forcing_dir)
            },
            'grid': {
                'coordinates': 'coords.nc',
                'bathymetry': 'bathy.nc'
            },
        }
        salishsea_cmd.prepare._make_grid_links(run_desc, Path(str(run_dir)))
        assert Path(str(run_dir), 'coordinates.nc').is_symlink()
        assert Path(str(run_dir), 'coordinates.nc').samefile(
            str(grid_dir.join('coords.nc'))
        )
        assert Path(str(run_dir), 'bathy_meter.nc').is_symlink()
        assert Path(str(run_dir),
                    'bathy_meter.nc').samefile(str(grid_dir.join('bathy.nc')))

    @patch('salishsea_cmd.prepare._remove_run_dir')
    @patch('salishsea_cmd.prepare.logger')
    def test_agrif_link_paths(self, m_logger, m_rm_run_dir, tmpdir):
        forcing_dir = tmpdir.ensure_dir('foo')
        grid_dir = forcing_dir.ensure_dir('grid')
        grid_dir.ensure('coords.nc')
        grid_dir.ensure('bathy.nc')
        run_dir = tmpdir.ensure_dir('runs')
        run_desc = {
            'paths': {
                'forcing': str(forcing_dir)
            },
            'grid': {
                'AGRIF_1': {
                    'coordinates': 'coords.nc',
                    'bathymetry': 'bathy.nc'
                }
            }
        }
        salishsea_cmd.prepare._make_grid_links(
            run_desc, Path(str(run_dir)), agrif_n=1
        )
        assert Path(str(run_dir), '1_coordinates.nc').is_symlink()
        assert Path(str(run_dir), '1_coordinates.nc').samefile(
            str(grid_dir.join('coords.nc'))
        )
        assert Path(str(run_dir), '1_bathy_meter.nc').is_symlink()
        assert Path(str(run_dir), '1_bathy_meter.nc').samefile(
            str(grid_dir.join('bathy.nc'))
        )


class TestResolveForcingPath:
    """Unit tests for `salishsea prepare` _resolve_forcing_path() function.
    """

    @pytest.mark.parametrize(
        'keys, forcing_dict', [
            (('atmospheric',), {
                'atmospheric': '/foo'
            }),
            (('atmospheric', 'link to'), {
                'atmospheric': {
                    'link to': '/foo'
                }
            }),
        ]
    )
    def test_absolute_path(self, keys, forcing_dict):
        run_desc = {'forcing': forcing_dict}
        path = salishsea_cmd.prepare._resolve_forcing_path(
            run_desc, keys, Path('run_dir')
        )
        assert path == Path('/foo')

    @pytest.mark.parametrize(
        'keys, forcing_dict', [
            (('atmospheric',), {
                'atmospheric': 'foo'
            }),
            (('atmospheric', 'link to'), {
                'atmospheric': {
                    'link to': 'foo'
                }
            }),
        ]
    )
    @patch('salishsea_cmd.prepare.get_run_desc_value')
    def test_relative_path(self, m_get_run_desc_value, keys, forcing_dict):
        run_desc = {'paths': {'forcing': '/foo'}, 'forcing': forcing_dict}
        m_get_run_desc_value.side_effect = (Path('bar'), Path('/foo'))
        path = salishsea_cmd.prepare._resolve_forcing_path(
            run_desc, keys, Path('run_dir')
        )
        assert path == Path('/foo/bar')


class TestMakeForcingLinks:
    """Unit tests for `salishsea prepare` _make_forcing_links() function.
    """

    def test_abs_path_link(self, tmpdir):
        p_nemo_forcing = tmpdir.ensure_dir('NEMO-forcing')
        p_atmos_ops = tmpdir.ensure_dir(
            'results/forcing/atmospheric/GEM2.5/operational'
        )
        run_desc = {
            'paths': {
                'forcing': str(p_nemo_forcing),
            },
            'forcing': {
                'NEMO-atmos': {
                    'link to': str(p_atmos_ops),
                }
            }
        }
        patch_symlink_to = patch('salishsea_cmd.prepare.Path.symlink_to')
        with patch_symlink_to as m_symlink_to:
            salishsea_cmd.prepare._make_forcing_links(
                run_desc, Path('run_dir')
            )
        m_symlink_to.assert_called_once_with(Path(str(p_atmos_ops)))

    def test_rel_path_link(self, tmpdir):
        p_nemo_forcing = tmpdir.ensure_dir('NEMO-forcing')
        p_nemo_forcing.ensure_dir('rivers')
        run_desc = {
            'paths': {
                'forcing': str(p_nemo_forcing),
            },
            'forcing': {
                'rivers': {
                    'link to': 'rivers',
                }
            }
        }
        patch_symlink_to = patch('salishsea_cmd.prepare.Path.symlink_to')
        with patch_symlink_to as m_symlink_to:
            salishsea_cmd.prepare._make_forcing_links(
                run_desc, Path('run_dir')
            )
        m_symlink_to.assert_called_once_with(
            Path(str(p_nemo_forcing.join('rivers')))
        )

    @patch('salishsea_cmd.prepare.logger')
    @patch('salishsea_cmd.prepare._remove_run_dir')
    def test_no_link_path(self, m_rm_run_dir, m_logger, tmpdir):
        p_nemo_forcing = tmpdir.ensure_dir('NEMO-forcing')
        run_desc = {
            'paths': {
                'forcing': str(p_nemo_forcing),
            },
            'forcing': {
                'rivers': {
                    'link to': 'rivers',
                }
            }
        }
        with pytest.raises(SystemExit):
            salishsea_cmd.prepare._make_forcing_links(
                run_desc, Path('run_dir')
            )
        m_logger.error.assert_called_once_with(
            '{} not found; cannot create symlink - '
            'please check the forcing paths and file names '
            'in your run description file'
            .format(p_nemo_forcing.join('rivers'))
        )
        m_rm_run_dir.assert_called_once_with(Path('run_dir'))

    @patch('salishsea_cmd.prepare._check_atmospheric_forcing_link')
    def test_link_checker(self, m_chk_atmos_frc_link, tmpdir):
        p_nemo_forcing = tmpdir.ensure_dir('NEMO-forcing')
        p_atmos_ops = tmpdir.ensure_dir(
            'results/forcing/atmospheric/GEM2.5/operational'
        )
        run_desc = {
            'paths': {
                'forcing': str(p_nemo_forcing),
            },
            'forcing': {
                'NEMO-atmos': {
                    'link to': str(p_atmos_ops),
                    'check link': {
                        'type': 'atmospheric',
                        'namelist filename': 'namelist_cfg',
                    }
                }
            }
        }
        patch_symlink_to = patch('salishsea_cmd.prepare.Path.symlink_to')
        with patch_symlink_to as m_symlink_to:
            salishsea_cmd.prepare._make_forcing_links(
                run_desc, Path('run_dir')
            )
        m_chk_atmos_frc_link.assert_called_once_with(
            Path('run_dir'), Path(str(p_atmos_ops)), 'namelist_cfg'
        )

    @patch('salishsea_cmd.prepare.logger')
    def test_unknown_link_checker(self, m_logger, tmpdir):
        p_nemo_forcing = tmpdir.ensure_dir('NEMO-forcing')
        p_atmos_ops = tmpdir.ensure_dir(
            'results/forcing/atmospheric/GEM2.5/operational'
        )
        run_desc = {
            'paths': {
                'forcing': str(p_nemo_forcing),
            },
            'forcing': {
                'NEMO-atmos': {
                    'link to': str(p_atmos_ops),
                    'check link': {
                        'type': 'bogus',
                        'namelist filename': 'namelist_cfg',
                    }
                }
            }
        }
        patch_symlink_to = patch('salishsea_cmd.prepare.Path.symlink_to')
        salishsea_cmd.prepare._remove_run_dir = Mock()
        with patch_symlink_to as m_symlink_to:
            with pytest.raises(SystemExit):
                salishsea_cmd.prepare._make_forcing_links(
                    run_desc, Path('run_dir')
                )


class TestMakeRestartLinks:
    """Unit tests for `salishsea prepare` _make_restart_links() function.
    """

    @patch('salishsea_cmd.prepare.logger')
    def test_no_restart_key(self, m_logger):
        run_desc = {}
        salishsea_cmd.prepare._make_restart_links(
            run_desc, Path('run_dir'), nocheck_init=False
        )
        m_logger.warning.assert_called_once_with(
            'No restart section found in run description YAML file, '
            'so proceeding on the assumption that initial conditions '
            'have been provided'
        )

    def test_link(self, tmpdir):
        p_results = tmpdir.ensure(
            'results/SalishSea/nowcast/SalishSea_00475200_restart.nc'
        )
        p_agrif_results = tmpdir.ensure(
            'results/SalishSea/nowcast/1_SalishSea_00475200_restart.nc'
        )
        run_desc = {
            'restart': {
                'restart.nc': str(p_results),
                'AGRIF_1': {
                    'restart.nc': str(p_agrif_results)
                },
            },
        }
        patch_symlink_to = patch('salishsea_cmd.prepare.Path.symlink_to')
        with patch_symlink_to as m_symlink_to:
            salishsea_cmd.prepare._make_restart_links(
                run_desc, Path('run_dir'), nocheck_init=False
            )
        m_symlink_to.assert_called_once_with(Path(str(p_results)))

    def test_agrif_link(self, tmpdir):
        p_results = tmpdir.ensure(
            'results/SalishSea/nowcast/SalishSea_00475200_restart.nc'
        )
        p_agrif_results = tmpdir.ensure(
            'results/SalishSea/nowcast/1_SalishSea_00475200_restart.nc'
        )
        run_desc = {
            'restart': {
                'restart.nc': str(p_results),
                'AGRIF_1': {
                    'restart.nc': str(p_agrif_results)
                },
            },
        }
        patch_symlink_to = patch('salishsea_cmd.prepare.Path.symlink_to')
        with patch_symlink_to as m_symlink_to:
            salishsea_cmd.prepare._make_restart_links(
                run_desc,
                Path('run_dir'),
                nocheck_init=False,
                agrif_n=1,
            )
        m_symlink_to.assert_called_once_with(Path(str(p_agrif_results)))

    @patch('salishsea_cmd.prepare.logger')
    @patch('salishsea_cmd.prepare._remove_run_dir')
    def test_no_link_path(self, m_rm_run_dir, m_logger):
        run_desc = {
            'restart': {
                'restart.nc': 'SalishSea/nowcast/SalishSea_00475200_restart.nc'
            }
        }
        with pytest.raises(SystemExit):
            salishsea_cmd.prepare._make_restart_links(
                run_desc, Path('run_dir'), nocheck_init=False
            )
        m_logger.error.assert_called_once_with(
            '{} not found; cannot create symlink - '
            'please check the restart file paths and file names '
            'in your run description file'
            .format('SalishSea/nowcast/SalishSea_00475200_restart.nc')
        )
        m_rm_run_dir.assert_called_once_with(Path('run_dir'))

    def test_nocheck_init(self):
        run_desc = {
            'restart': {
                'restart.nc': 'SalishSea/nowcast/SalishSea_00475200_restart.nc'
            }
        }
        patch_symlink_to = patch('salishsea_cmd.prepare.Path.symlink_to')
        with patch_symlink_to as m_symlink_to:
            salishsea_cmd.prepare._make_restart_links(
                run_desc, Path('run_dir'), nocheck_init=True
            )
        m_symlink_to.assert_called_once_with(
            Path('SalishSea/nowcast/SalishSea_00475200_restart.nc')
        )


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
@patch('salishsea_cmd.prepare._make_grid_links', autospec=True)
@patch('salishsea_cmd.prepare._make_restart_links', autospec=True)
@patch('salishsea_cmd.prepare._copy_run_set_files', autospec=True)
@patch('salishsea_cmd.prepare._make_namelists', autospec=True)
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
    def test_make_namelists_nemo36(
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
        assert m_mk_nl_36.call_args_list == [
            call(Path('run_set_dir'), run_desc, Path('run_dir'), agrif_n=1),
            call(Path('run_set_dir'), run_desc, Path('run_dir'), agrif_n=2),
        ]

    @patch('salishsea_cmd.prepare.shutil.copy2', autospec=True)
    def test_namelist_sub_grids_mismatch(
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
