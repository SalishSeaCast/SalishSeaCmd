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
import os
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
        assert not parsed_args.nemo34
        assert not parsed_args.quiet

    @pytest.mark.parametrize(
        'flag, attr', [
            ('--nemo3.4', 'nemo34'),
            ('-q', 'quiet'),
            ('--quiet', 'quiet'),
        ]
    )
    def test_parsed_args_flags(self, flag, attr, prepare_cmd):
        parser = prepare_cmd.get_parser('salishsea prepare')
        parsed_args = parser.parse_args(['foo', flag])
        assert getattr(parsed_args, attr)


@patch('salishsea_cmd.prepare.lib.load_run_desc')
@patch('salishsea_cmd.prepare._check_nemo_exec')
@patch('salishsea_cmd.prepare._check_xios_exec')
@patch('nemo_cmd.resolved_path')
@patch('salishsea_cmd.prepare._make_run_dir')
@patch('salishsea_cmd.prepare._make_namelists')
@patch('salishsea_cmd.prepare._copy_run_set_files')
@patch('salishsea_cmd.prepare._make_executable_links')
@patch('salishsea_cmd.prepare._make_grid_links')
@patch('salishsea_cmd.prepare._make_forcing_links')
@patch('salishsea_cmd.prepare._make_restart_links')
@patch('salishsea_cmd.prepare._record_vcs_revisions')
class TestPrepare:
    """Unit tests for `salishsea prepare` prepare() function.
    """

    @pytest.mark.parametrize(
        'nemo34, m_cne_return, m_cxe_return', [
            (True, 'bin_dir', ''),
            (False, 'nemo_bin_dir', 'xios_bin_dir'),
        ]
    )
    def test_prepare(
        self, m_rvr, m_mrl, m_mfl, m_mgl, m_mel, m_crsf, m_mnl, m_mrd,
        m_resolved_path, m_cxe, m_cne, m_lrd, nemo34, m_cne_return,
        m_cxe_return
    ):
        m_cne.return_value = m_cne_return
        m_cxe.return_value = m_cxe_return
        run_dir = salishsea_cmd.prepare.prepare(
            Path('SalishSea.yaml'), nemo34, nocheck_init=False
        )
        m_lrd.assert_called_once_with(Path('SalishSea.yaml'))
        m_cne.assert_called_once_with(m_lrd(), nemo34)
        if nemo34:
            assert not m_cxe.called
        else:
            m_cne.assert_called_once_with(m_lrd(), nemo34)
        m_resolved_path.assert_called_once_with(Path('SalishSea.yaml'))
        m_mrd.assert_called_once_with(m_lrd())
        m_mnl.assert_called_once_with(
            m_resolved_path().parent, m_lrd(), m_mrd(), nemo34
        )
        m_crsf.assert_called_once_with(
            m_lrd(),
            Path('SalishSea.yaml'), m_resolved_path().parent, m_mrd(), nemo34
        )
        m_mel.assert_called_once_with(
            m_cne_return, m_mrd(), nemo34, m_cxe_return
        )
        m_mgl.assert_called_once_with(m_lrd(), m_mrd())
        m_mfl.assert_called_once_with(m_lrd(), m_mrd(), nemo34, False)
        if nemo34:
            assert not m_mrl.called
        else:
            m_mrl.assert_called_once_with(m_lrd(), m_mrd(), False)
        m_rvr.assert_called_once_with(m_lrd(), m_mrd())
        assert run_dir == m_mrd()


class TestCheckNemoExec:
    """Unit tests for `salishsea prepare` _check_nemo_exec() function.
    """

    @pytest.mark.parametrize(
        'config_name_key, nemo_code_config_key', [
            ('config name', 'NEMO code config'),
            ('config_name', 'NEMO-code-config'),
        ]
    )
    def test_nemo_bin_dir_path(
        self, config_name_key, nemo_code_config_key, tmpdir
    ):
        p_config = tmpdir.ensure_dir('NEMO-3.6-code', 'NEMOGCM', 'CONFIG')
        run_desc = {
            config_name_key: 'SalishSea',
            'paths': {
                nemo_code_config_key: str(p_config)
            },
        }
        p_bin_dir = p_config.ensure_dir('SalishSea', 'BLD', 'bin')
        p_bin_dir.ensure('nemo.exe')
        nemo_bin_dir = salishsea_cmd.prepare._check_nemo_exec(
            run_desc, nemo34=False
        )
        assert nemo_bin_dir == Path(str(p_bin_dir))

    @pytest.mark.parametrize(
        'config_name_key, nemo_code_config_key', [
            ('config name', 'NEMO code config'),
            ('config_name', 'NEMO-code-config'),
        ]
    )
    @patch('salishsea_cmd.prepare.logger')
    def test_nemo_exec_not_found(
        self, m_logger, config_name_key, nemo_code_config_key, tmpdir
    ):
        p_code = tmpdir.ensure_dir('NEMO-3.6-code')
        run_desc = {
            config_name_key: 'SalishSea',
            'paths': {
                nemo_code_config_key: str(p_code)
            },
        }
        with pytest.raises(SystemExit):
            salishsea_cmd.prepare._check_nemo_exec(run_desc, nemo34=False)

    @pytest.mark.parametrize(
        'config_name_key, nemo_code_config_key', [
            ('config name', 'NEMO code config'),
            ('config_name', 'NEMO-code-config'),
        ]
    )
    @patch('salishsea_cmd.prepare.logger')
    @patch('salishsea_cmd.prepare.get_run_desc_value')
    def test_iom_server_exec_not_found(
        self, m_get_run_desc_value, m_logger, config_name_key,
        nemo_code_config_key, tmpdir
    ):
        p_config = tmpdir.ensure_dir('NEMO-3.6-code', 'NEMOGCM', 'CONFIG')
        run_desc = {
            config_name_key: 'SalishSea',
            'paths': {
                nemo_code_config_key: str(p_config)
            },
        }
        p_bin_dir = p_config.ensure_dir('SalishSea', 'BLD', 'bin')
        m_get_run_desc_value.side_effect = (Path(str(p_config)), 'SalishSea')
        p_exists = patch(
            'salishsea_cmd.prepare.Path.exists', side_effect=[True, False]
        )
        with p_exists:
            salishsea_cmd.prepare._check_nemo_exec(run_desc, nemo34=True)
        m_logger.warning.assert_called_once_with(
            '{}/server.exe not found - are you running without key_iomput?'
            .format(p_bin_dir)
        )

    @pytest.mark.parametrize(
        'config_name_key, nemo_code_config_key', [
            ('config name', 'NEMO code config'),
            ('config_name', 'NEMO-code-config'),
        ]
    )
    @patch('salishsea_cmd.prepare.get_run_desc_value')
    def test_nemo36_no_iom_server_check(
        self, m_get_run_desc_value, config_name_key, nemo_code_config_key,
        tmpdir
    ):
        p_config = tmpdir.ensure_dir('NEMO-3.6-code', 'NEMOGCM', 'CONFIG')
        run_desc = {
            config_name_key: 'SalishSea',
            'paths': {
                nemo_code_config_key: str(p_config)
            },
        }
        p_config.ensure_dir('SalishSea', 'BLD', 'bin')
        m_get_run_desc_value.side_effect = (Path(str(p_config)), 'SalishSea')
        with patch('salishsea_cmd.prepare.Path.exists') as m_exists:
            salishsea_cmd.prepare._check_nemo_exec(run_desc, nemo34=False)
        assert m_exists.call_count == 1


@patch('salishsea_cmd.prepare.logger')
class TestCheckXiosExec:
    """Unit tests for `salishsea prepare` _check_xios_exec() function.
    """

    def test_xios_bin_dir_path(self, m_logger, tmpdir):
        p_xios = tmpdir.ensure_dir('XIOS')
        run_desc = {'paths': {'XIOS': str(p_xios)}}
        p_bin_dir = p_xios.ensure_dir('bin')
        p_bin_dir.ensure('xios_server.exe')
        xios_bin_dir = salishsea_cmd.prepare._check_xios_exec(run_desc)
        assert xios_bin_dir == Path(str(p_bin_dir))

    def test_xios_exec_not_found(self, m_logger, tmpdir):
        p_xios = tmpdir.ensure_dir('XIOS')
        run_desc = {
            'paths': {
                'XIOS': str(p_xios)
            },
        }
        with pytest.raises(SystemExit):
            salishsea_cmd.prepare._check_xios_exec(run_desc)


class TestMakeRunDir:
    """Unit test for `salishsea prepare` _make_run_dir() function.
    """

    @patch('salishsea_cmd.prepare.uuid.uuid1', return_value='uuid')
    def test_make_run_dir(self, m_uuid1, tmpdir):
        """_make_run_dir() creates directory w/ UUID v1 name
        """
        p_runs_dir = tmpdir.ensure_dir('SalishSea')
        run_desc = {
            'paths': {
                'runs directory': str(p_runs_dir)
            },
        }
        run_dir = salishsea_cmd.prepare._make_run_dir(run_desc)
        assert run_dir == os.path.join(str(p_runs_dir), m_uuid1())


class TestRemoveRunDir:
    """Unit tests for `salishsea prepare` _remove_run_dir() function.
    """

    def test_remove_run_dir(self, tmpdir):
        p_run_dir = tmpdir.ensure_dir('run_dir')
        salishsea_cmd.prepare._remove_run_dir(str(p_run_dir))
        assert not p_run_dir.check()

    def test_remove_run_dir_file(self, tmpdir):
        p_run_dir = tmpdir.ensure_dir('run_dir')
        p_run_dir.ensure('namelist')
        salishsea_cmd.prepare._remove_run_dir(str(p_run_dir))
        assert not p_run_dir.join('namelist').check()
        assert not p_run_dir.check()

    @patch('salishsea_cmd.prepare.os.rmdir')
    def test_remove_run_dir_no_run_dir(self, m_rmdir):
        salishsea_cmd.prepare._remove_run_dir('run_dir')
        assert not m_rmdir.called


class TestMakeNamelists:
    """Unit tests for `salishsea prepare` _make_namelists() function.
    """

    def test_nemo34(self):
        with patch('salishsea_cmd.prepare._make_namelist_nemo34') as m_mn34:
            salishsea_cmd.prepare._make_namelists(
                'run_set_dir', 'run_desc', 'run_dir', nemo34=True
            )
        m_mn34.assert_called_once_with('run_set_dir', 'run_desc', 'run_dir')

    def test_nemo36(self):
        with patch('salishsea_cmd.prepare._make_namelists_nemo36') as m_mn36:
            salishsea_cmd.prepare._make_namelists(
                'run_set_dir', 'run_desc', 'run_dir', nemo34=False
            )
        m_mn36.assert_called_once_with('run_set_dir', 'run_desc', 'run_dir')


class TestMakeNamelistNEMO34:
    """Unit tests for `salishsea prepare` _make_namelist_nemo34() function.
    """

    def test_make_namelist_nemo34(self, tmpdir):
        p_run_set_dir = tmpdir.ensure_dir('run_set_dir')
        p_run_set_dir.join('namelist.time').write('&namrun\n&end\n')
        run_desc = {'namelists': [str(p_run_set_dir.join('namelist.time'))]}
        p_run_dir = tmpdir.ensure_dir('run_dir')
        with patch('salishsea_cmd.prepare._set_mpi_decomposition'):
            salishsea_cmd.prepare._make_namelist_nemo34(
                Path(str(p_run_set_dir)), run_desc, str(p_run_dir)
            )
        assert p_run_dir.join('namelist').check()

    @patch('salishsea_cmd.prepare.logger')
    def test_namelist_file_not_found_error(self, m_logger, tmpdir):
        p_run_set_dir = tmpdir.ensure_dir('run_set_dir')
        run_desc = {'namelists': [str(p_run_set_dir.join('namelist.time'))]}
        p_run_dir = tmpdir.ensure_dir('run_dir')
        with pytest.raises(SystemExit):
            salishsea_cmd.prepare._make_namelist_nemo34(
                Path(str(p_run_set_dir)), run_desc, str(p_run_dir)
            )

    def test_namelist_ends_with_empty_namelists(self, tmpdir):
        p_run_set_dir = tmpdir.ensure_dir('run_set_dir')
        p_run_set_dir.join('namelist.time').write('&namrun\n&end\n')
        run_desc = {'namelists': [str(p_run_set_dir.join('namelist.time'))]}
        p_run_dir = tmpdir.ensure_dir('run_dir')
        with patch('salishsea_cmd.prepare._set_mpi_decomposition'):
            salishsea_cmd.prepare._make_namelist_nemo34(
                Path(str(p_run_set_dir)), run_desc, str(p_run_dir)
            )
        namelist = p_run_dir.join('namelist').read()
        assert namelist.endswith(salishsea_cmd.prepare.EMPTY_NAMELISTS)


class TestMakeNamelistNEMO36:
    """Unit tests for `salishsea prepare` _make_namelist_nemo36() function.
    """

    def test_make_namelists_nemo36(self, tmpdir):
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
        with patch('salishsea_cmd.prepare._set_mpi_decomposition'):
            salishsea_cmd.prepare._make_namelists_nemo36(
                Path(str(p_run_set_dir)), run_desc, str(p_run_dir)
            )
        assert p_run_dir.join('namelist_cfg').check()
        assert p_run_dir.join('namelist_top_cfg').check()
        assert p_run_dir.join('namelist_pisces_cfg').check()

    @patch('salishsea_cmd.prepare.logger')
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
            salishsea_cmd.prepare._make_namelists_nemo36(
                Path(str(p_run_set_dir)), run_desc, str(p_run_dir)
            )

    def test_namelist_ref_symlinks(self, tmpdir):
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
        with patch('salishsea_cmd.prepare._set_mpi_decomposition'):
            salishsea_cmd.prepare._make_namelists_nemo36(
                Path(str(p_run_set_dir)), run_desc, str(p_run_dir)
            )
        assert p_run_dir.join('namelist_ref').check(file=True, link=True)
        assert p_run_dir.join('namelist_top_ref').check(file=True, link=True)
        assert p_run_dir.join('namelist_pisces_ref').check(
            file=True, link=True
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
        with patch('salishsea_cmd.prepare._set_mpi_decomposition') as m_smd:
            salishsea_cmd.prepare._make_namelists_nemo36(
                Path(str(p_run_set_dir)), run_desc, str(p_run_dir)
            )
        m_smd.assert_called_once_with('namelist_cfg', run_desc, str(p_run_dir))

    @patch('salishsea_cmd.prepare.logger')
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
        with pytest.raises(SystemExit):
            salishsea_cmd.prepare._make_namelists_nemo36(
                Path(str(p_run_set_dir)), run_desc, str(p_run_dir)
            )


class TestCopyRunSetFiles:
    """Unit tests for `salishsea prepare` _copy_run_set_files() function.
    """

    @pytest.mark.parametrize(
        'iodefs_key',
        [
            'iodefs',  # recommended
            'files',  # backward compatibility
        ]
    )
    @patch('salishsea_cmd.prepare.shutil.copy2')
    @patch('salishsea_cmd.prepare._set_xios_server_mode')
    @patch('salishsea_cmd.prepare.get_run_desc_value')
    def test_nemo34_copy_run_set_files_no_path(
        self, m_get_run_desc_value, m_sxsm, m_copy, iodefs_key
    ):
        run_desc = {'output': {iodefs_key: 'iodef.xml'}}
        desc_file = Path('foo.yaml')
        pwd = Path.cwd()
        m_get_run_desc_value.return_value = pwd / 'iodef.xml'
        salishsea_cmd.prepare._copy_run_set_files(
            run_desc, desc_file, pwd, 'run_dir', nemo34=True
        )
        expected = [
            call(str(pwd / 'iodef.xml'), str(Path('run_dir') / 'iodef.xml')),
            call(str(pwd / 'foo.yaml'), str(Path('run_dir') / 'foo.yaml')),
            call(
                str(pwd / 'xmlio_server.def'),
                str(Path('run_dir') / 'xmlio_server.def')
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
    def test_nemo36_copy_run_set_files_no_path(
        self, m_get_run_desc_value, m_sxsm, m_copy, iodefs_key, domains_key,
        fields_key
    ):
        run_desc = {
            'output': {
                iodefs_key: 'iodef.xml',
                domains_key: 'domain_def.xml',
                fields_key: 'field_def.xml',
            },
        }
        desc_file = Path('foo.yaml')
        pwd = Path.cwd()
        m_get_run_desc_value.side_effect = (
            pwd / 'iodef.xml', pwd / 'domain_def.xml', pwd / 'field_def.xml',
            KeyError
        )
        salishsea_cmd.prepare._copy_run_set_files(
            run_desc, desc_file, pwd, 'run_dir', nemo34=False
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
        'iodefs_key',
        [
            'iodefs',  # recommended
            'files',  # backward compatibility
        ]
    )
    @patch('salishsea_cmd.prepare.shutil.copy2')
    @patch('salishsea_cmd.prepare._set_xios_server_mode')
    @patch('salishsea_cmd.prepare.get_run_desc_value')
    def test_nemo34_copy_run_set_files_relative_path(
        self, m_get_run_desc_value, m_sxsm, m_copy, iodefs_key
    ):
        run_desc = {'output': {iodefs_key: '../iodef.xml'}}
        desc_file = Path('foo.yaml')
        pwd = Path.cwd()
        m_get_run_desc_value.return_value = (pwd / '../iodef.xml').resolve()
        salishsea_cmd.prepare._copy_run_set_files(
            run_desc, desc_file, pwd, 'run_dir', nemo34=True
        )
        expected = [
            call(
                str(pwd.parent / 'iodef.xml'),
                str(Path('run_dir') / 'iodef.xml')
            ),
            call(str(pwd / 'foo.yaml'), str(Path('run_dir') / 'foo.yaml')),
            call(
                str(pwd / 'xmlio_server.def'),
                str(Path('run_dir') / 'xmlio_server.def')
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
    def test_nemo36_copy_run_set_files_relative_path(
        self, m_get_run_desc_value, m_sxsm, m_copy, iodefs_key, domains_key,
        fields_key
    ):
        run_desc = {
            'output': {
                iodefs_key: '../iodef.xml',
                domains_key: '../domain_def.xml',
                fields_key: '../field_def.xml',
            },
        }
        desc_file = Path('foo.yaml')
        pwd = Path.cwd()
        m_get_run_desc_value.side_effect = (
            (pwd / '../iodef.xml').resolve(),
            (pwd / '../domain_def.xml').resolve(),
            (pwd / '../field_def.xml').resolve(), KeyError
        )
        salishsea_cmd.prepare._copy_run_set_files(
            run_desc, desc_file, pwd, 'run_dir', nemo34=False
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

    @patch('salishsea_cmd.prepare.shutil.copy2')
    @patch('salishsea_cmd.prepare._set_xios_server_mode')
    @patch('salishsea_cmd.prepare.get_run_desc_value')
    def test_nemo36_files_def(self, m_get_run_desc_value, m_sxsm, m_copy):
        run_desc = {
            'output': {
                'iodefs': '../iodef.xml',
                'filedefs': '../file_def.xml',
                'domaindefs': '../domain_def.xml',
                'fielddefs': '../field_def.xml',
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
            run_desc, desc_file, pwd, 'run_dir', nemo34=False
        )
        assert m_copy.call_args_list[-1] == call(
            str(pwd.parent / 'file_def.xml'),
            str(Path('run_dir') / 'file_def.xml')
        )


class TestMakeExecutableLinks:
    """Unit tests for `salishsea prepare` _make_executable_links() function.
    """

    @pytest.mark.parametrize('nemo34', [True, False])
    def test_nemo_exe_symlink(self, nemo34, tmpdir):
        p_nemo_bin_dir = tmpdir.ensure_dir(
            'NEMO-code/NEMOGCM/CONFIG/SalishSea/BLD/bin'
        )
        p_nemo_bin_dir.ensure('nemo.exe')
        p_xios_bin_dir = tmpdir.ensure_dir('XIOS/bin')
        p_run_dir = tmpdir.ensure_dir('run_dir')
        salishsea_cmd.prepare._make_executable_links(
            Path(str(p_nemo_bin_dir)),
            str(p_run_dir), nemo34, Path(str(p_xios_bin_dir))
        )
        assert p_run_dir.join('nemo.exe').check(file=True, link=True)

    @pytest.mark.parametrize('nemo34', [True, False])
    def test_server_exe_symlink(self, nemo34, tmpdir):
        p_nemo_bin_dir = tmpdir.ensure_dir(
            'NEMO-code/NEMOGCM/CONFIG/SalishSea/BLD/bin'
        )
        p_nemo_bin_dir.ensure('nemo.exe')
        p_xios_bin_dir = tmpdir.ensure_dir('XIOS/bin')
        if nemo34:
            p_nemo_bin_dir.ensure('server.exe')
        p_run_dir = tmpdir.ensure_dir('run_dir')
        salishsea_cmd.prepare._make_executable_links(
            Path(str(p_nemo_bin_dir)),
            str(p_run_dir), nemo34, Path(str(p_xios_bin_dir))
        )
        if nemo34:
            assert p_run_dir.join('server.exe').check(file=True, link=True)
        else:
            assert not p_run_dir.join('server.exe').check(file=True, link=True)

    @pytest.mark.parametrize(
        'nemo34, xios_code_repo', [
            (True, None),
            (False, 'xios_code_repo'),
        ]
    )
    def test_xios_server_exe_symlink(
        self,
        nemo34,
        xios_code_repo,
        tmpdir,
    ):
        p_nemo_bin_dir = tmpdir.ensure_dir(
            'NEMO-code/NEMOGCM/CONFIG/SalishSea/BLD/bin'
        )
        p_nemo_bin_dir.ensure('nemo.exe')
        p_xios_bin_dir = tmpdir.ensure_dir('XIOS/bin')
        if not nemo34:
            p_xios_bin_dir.ensure('xios_server.exe')
        p_run_dir = tmpdir.ensure_dir('run_dir')
        salishsea_cmd.prepare._make_executable_links(
            Path(str(p_nemo_bin_dir)),
            str(p_run_dir), nemo34, Path(str(p_xios_bin_dir))
        )
        if nemo34:
            assert not p_run_dir.join('xios_server.exe').check(
                file=True, link=True
            )
        else:
            assert p_run_dir.join('xios_server.exe').check(
                file=True, link=True
            )


class TestMakeGridLinks:
    """Unit tests for `nemo prepare` _make_grid_links() function.
    """

    @patch('nemo_cmd.prepare._remove_run_dir')
    def test_no_grid_coordinates_key(self, m_rm_run_dir):
        run_desc = {}
        with pytest.raises(SystemExit):
            salishsea_cmd.prepare._make_grid_links(run_desc, 'run_dir')
        m_rm_run_dir.assert_called_once_with('run_dir')

    @patch('nemo_cmd.prepare._remove_run_dir')
    def test_no_grid_bathymetry_key(self, m_rm_run_dir):
        run_desc = {'grid': {'coordinates': 'coords.nc'}}
        with pytest.raises(SystemExit):
            salishsea_cmd.prepare._make_grid_links(run_desc, 'run_dir')
        m_rm_run_dir.assert_called_once_with('run_dir')

    @patch('nemo_cmd.prepare._remove_run_dir')
    def test_no_forcing_key(self, m_rm_run_dir):
        run_desc = {
            'grid': {
                'coordinates': 'coords.nc',
                'bathymetry': 'bathy.nc'
            }
        }
        with pytest.raises(SystemExit):
            salishsea_cmd.prepare._make_grid_links(run_desc, 'run_dir')
        m_rm_run_dir.assert_called_once_with('run_dir')

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
            salishsea_cmd.prepare._make_grid_links(run_desc, 'run_dir')
        m_logger.error.assert_called_once_with(
            '/coords.nc not found; cannot create symlink - '
            'please check the forcing path and grid file names '
            'in your run description file'
        )
        m_rm_run_dir.assert_called_once_with('run_dir')

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
            salishsea_cmd.prepare._make_grid_links(run_desc, str(run_dir))
        m_logger.error.assert_called_once_with(
            '{}/coords.nc not found; cannot create symlink - '
            'please check the forcing path and grid file names '
            'in your run description file'.format(grid_dir)
        )
        m_rm_run_dir.assert_called_once_with(run_dir)

    @patch('salishsea_cmd.prepare._remove_run_dir')
    @patch('salishsea_cmd.prepare.logger')
    def test_link_path(self, m_logger, m_rm_run_dir, tmpdir):
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
        salishsea_cmd.prepare._make_grid_links(run_desc, str(run_dir))
        assert Path(str(run_dir), 'coordinates.nc').is_symlink()
        assert Path(str(run_dir), 'coordinates.nc'
                    ).samefile(str(grid_dir.join('coords.nc')))
        assert Path(str(run_dir), 'bathy_meter.nc').is_symlink()
        assert Path(str(run_dir),
                    'bathy_meter.nc').samefile(str(grid_dir.join('bathy.nc')))


class TestMakeForcingLinks:
    """Unit tests for `salishsea prepare` _make_forcing_links() function.
    """

    def test_nemo34(self, tmpdir):
        p_run_dir = tmpdir.ensure_dir('run_dir')
        run_desc = {'paths': {'forcing': 'nemo_forcing_dir'}}
        patch_mfl34 = patch('salishsea_cmd.prepare._make_forcing_links_nemo34')
        with patch_mfl34 as m_mfl34:
            salishsea_cmd.prepare._make_forcing_links(
                run_desc, str(p_run_dir), nemo34=True, nocheck_init=False
            )
        m_mfl34.assert_called_once_with(run_desc, str(p_run_dir), False)

    def test_nemo36(self, tmpdir):
        p_run_dir = tmpdir.ensure_dir('run_dir')
        run_desc = {'paths': {'forcing': 'nemo_forcing_dir'}}
        patch_mfl36 = patch('salishsea_cmd.prepare._make_forcing_links_nemo36')
        with patch_mfl36 as m_mfl36:
            salishsea_cmd.prepare._make_forcing_links(
                run_desc, str(p_run_dir), nemo34=False, nocheck_init=False
            )
        m_mfl36.assert_called_once_with(run_desc, str(p_run_dir))


class TestMakeForcingLinksNEMO34:
    """Unit tests for `salishsea prepare` _make_forcing_links_nemo34() function.
    """

    @pytest.mark.parametrize(
        'link_path, expected',
        [
            ('SalishSea_00475200_restart.nc', 'SalishSea_00475200_restart.nc'),
            ('initial_strat/', 'initial_strat/'),
        ],
    )
    @patch('salishsea_cmd.prepare._check_atmos_files')
    @patch('salishsea_cmd.prepare.logger')
    def test_make_forcing_links_no_restart_path(
        self, m_logger, m_caf, link_path, expected, tmpdir
    ):
        forcing_dir = tmpdir.ensure_dir('foo')
        run_desc = {
            'paths': {
                'forcing': str(forcing_dir),
            },
            'forcing': {
                'atmospheric': 'bar',
                'initial conditions': link_path,
                'open boundaries': 'open_boundaries/',
                'rivers': 'rivers/',
            },
        }
        salishsea_cmd.prepare._remove_run_dir = Mock()
        with pytest.raises(SystemExit):
            salishsea_cmd.prepare._make_forcing_links_nemo34(
                run_desc, 'run_dir', nocheck_init=False
            )
        m_logger.error.assert_called_once_with(
            '{} not found; cannot create symlink - '
            'please check the forcing path and initial conditions file names '
            'in your run description file'.format(forcing_dir.join(expected))
        )
        salishsea_cmd.prepare._remove_run_dir.assert_called_once_with(
            'run_dir'
        )

    @patch('salishsea_cmd.prepare._check_atmos_files')
    @patch('salishsea_cmd.prepare.logger')
    def test_make_forcing_links_no_forcing_path(self, m_logger, m_caf):
        run_desc = {
            'paths': {
                'forcing': 'foo',
            },
            'forcing': {
                'atmospheric': 'bar',
                'initial conditions': 'initial_strat/',
                'open boundaries': 'open_boundaries/',
                'rivers': 'rivers/',
            },
        }
        with pytest.raises(SystemExit):
            salishsea_cmd.prepare._make_forcing_links_nemo34(
                run_desc, 'run_dir', nocheck_init=False
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
            run_desc, keys, 'run_dir'
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
            run_desc, keys, 'run_dir'
        )
        assert path == Path('/foo/bar')


class TestMakeForcingLinksNEMO36:
    """Unit tests for `salishsea prepare` _make_forcing_links_nemo36() function.
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
            salishsea_cmd.prepare._make_forcing_links_nemo36(
                run_desc, 'run_dir'
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
            salishsea_cmd.prepare._make_forcing_links_nemo36(
                run_desc, 'run_dir'
            )
        m_symlink_to.assert_called_once_with(
            Path(str(p_nemo_forcing.join('rivers')))
        )

    @patch('salishsea_cmd.prepare.logger')
    def test_no_link_path(self, m_logger, tmpdir):
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
        salishsea_cmd.prepare._remove_run_dir = Mock()
        with pytest.raises(SystemExit):
            salishsea_cmd.prepare._make_forcing_links_nemo36(
                run_desc, 'run_dir'
            )
        m_logger.error.assert_called_once_with(
            '{} not found; cannot create symlink - '
            'please check the forcing paths and file names '
            'in your run description file'
            .format(p_nemo_forcing.join('rivers'))
        )
        salishsea_cmd.prepare._remove_run_dir.assert_called_once_with(
            'run_dir'
        )

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
            salishsea_cmd.prepare._make_forcing_links_nemo36(
                run_desc, 'run_dir'
            )
        m_chk_atmos_frc_link.assert_called_once_with(
            run_desc, 'run_dir', Path(str(p_atmos_ops)), 'namelist_cfg'
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
                salishsea_cmd.prepare._make_forcing_links_nemo36(
                    run_desc, 'run_dir'
                )


class TestMakeRestartLinks:
    """Unit tests for `salishsea prepare` _make_restart_links() function.
    """

    @patch('salishsea_cmd.prepare.logger')
    def test_no_restart_key(self, m_logger):
        run_desc = {}
        salishsea_cmd.prepare._make_restart_links(
            run_desc, 'run_dir', nocheck_init=False
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
        run_desc = {'restart': {'restart.nc': str(p_results)}}
        patch_symlink_to = patch('salishsea_cmd.prepare.Path.symlink_to')
        with patch_symlink_to as m_symlink_to:
            salishsea_cmd.prepare._make_restart_links(
                run_desc, 'run_dir', nocheck_init=False
            )
        m_symlink_to.assert_called_once_with(Path(str(p_results)))

    @patch('salishsea_cmd.prepare.logger')
    def test_no_link_path(self, m_logger, tmpdir):
        run_desc = {
            'restart': {
                'restart.nc': 'SalishSea/nowcast/SalishSea_00475200_restart.nc'
            }
        }
        salishsea_cmd.prepare._remove_run_dir = Mock()
        with pytest.raises(SystemExit):
            salishsea_cmd.prepare._make_restart_links(
                run_desc, 'run_dir', nocheck_init=False
            )
        m_logger.error.assert_called_once_with(
            '{} not found; cannot create symlink - '
            'please check the restart file paths and file names '
            'in your run description file'
            .format('SalishSea/nowcast/SalishSea_00475200_restart.nc')
        )
        salishsea_cmd.prepare._remove_run_dir.assert_called_once_with(
            'run_dir'
        )

    def test_nocheck_init(self, tmpdir):
        run_desc = {
            'restart': {
                'restart.nc': 'SalishSea/nowcast/SalishSea_00475200_restart.nc'
            }
        }
        patch_symlink_to = patch('salishsea_cmd.prepare.Path.symlink_to')
        with patch_symlink_to as m_symlink_to:
            salishsea_cmd.prepare._make_restart_links(
                run_desc, 'run_dir', nocheck_init=True
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
            salishsea_cmd.prepare._record_vcs_revisions(run_desc, 'run_dir')

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
        nemo_forcing = tmpdir.ensure_dir('NEMO-forcing')
        run_desc = {
            config_name_key: 'SalishSea',
            'paths': {
                nemo_code_config_key: str(nemo_config),
                'XIOS': str(xios_code_repo),
                'forcing': str(nemo_forcing)
            }
        }
        salishsea_cmd.prepare._record_vcs_revisions(run_desc, 'run_dir')
        assert m_write.call_args_list == [
            call(
                Path(str(nemo_code_repo)), 'run_dir',
                nemo_cmd.prepare.get_hg_revision
            ),
            call(
                Path(str(xios_code_repo)), 'run_dir',
                nemo_cmd.prepare.get_hg_revision
            ),
            call(
                Path(str(nemo_forcing)), 'run_dir',
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
        salishsea_cmd.prepare._record_vcs_revisions(run_desc, 'run_dir')
        assert m_write.call_args_list[-1] == call(
            Path(str(ss_run_sets)), 'run_dir', nemo_cmd.prepare.get_hg_revision
        )
