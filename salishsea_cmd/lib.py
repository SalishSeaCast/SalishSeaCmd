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
"""Utility functions for use by SalishSeaCmd command plug-ins.
"""
import logging

import yaml
from nemo_cmd import fspath
from nemo_cmd.prepare import get_run_desc_value

logger = logging.getLogger(__name__)


def load_run_desc(desc_file):
    """Load the run description file contents into a data structure.

    :param desc_file: File path/name of the YAML run description file.
    :type desc_file: :py:class:`pathlib.Path`

    :returns: Contents of run description file parsed from YAML into a dict.
    :rtype: dict
    """
    with open(fspath(desc_file), 'rt') as f:
        run_desc = yaml.load(f)
    return run_desc


def get_n_processors(run_desc, run_dir):
    """Return the total number of processors required for the run as
    specified by the MPI decomposition key in the run description.

    :param dict run_desc: Run description dictionary.

    :param run_dir: Path of the temporary run directory.
    :type run_dir: :py:class:`pathlib.Path`

    :returns: Number of processors required for the run.
    :rtype: int
    """
    jpni, jpnj = map(
        int, get_run_desc_value(run_desc, ('MPI decomposition',)).split('x')
    )
    try:
        mpi_lpe_mapping = get_run_desc_value(
            run_desc, ('grid', 'land processor elimination'), fatal=False
        )
    except KeyError:
        # Alternate key spelling for backward compatibility
        try:
            mpi_lpe_mapping = get_run_desc_value(
                run_desc, ('grid', 'Land processor elimination'), fatal=False
            )
        except KeyError:
            logger.warning(
                'No grid: land processor elimination: key found in run '
                'description YAML file, so proceeding on the assumption that '
                'you want to run without land processor elimination'
            )
            mpi_lpe_mapping = False
    if not mpi_lpe_mapping:
        return jpni * jpnj

    try:
        mpi_lpe_mapping = get_run_desc_value(
            run_desc, ('grid', 'land processor elimination'),
            expand_path=True,
            fatal=False,
            run_dir=run_dir
        )
    except KeyError:
        # Alternate key spelling for backward compatibility
        mpi_lpe_mapping = get_run_desc_value(
            run_desc, ('grid', 'Land processor elimination'),
            expand_path=True,
            run_dir=run_dir
        )
    if not mpi_lpe_mapping.is_absolute():
        nemo_forcing_dir = get_run_desc_value(
            run_desc, ('paths', 'forcing'), resolve_path=True, run_dir=run_dir
        )
        mpi_lpe_mapping = nemo_forcing_dir / 'grid' / mpi_lpe_mapping
    n_processors = _lookup_lpe_n_processors(mpi_lpe_mapping, jpni, jpnj)
    if n_processors is None:
        msg = (
            'No land processor elimination choice found for {jpni}x{jpnj} '
            'MPI decomposition'.format(jpni=jpni, jpnj=jpnj)
        )
        logger.error(msg)
        raise ValueError(msg)
    return n_processors


def _lookup_lpe_n_processors(mpi_lpe_mapping, jpni, jpnj):
    """Encapsulate file access to facilitate testability of get_n_processors().
    """
    with mpi_lpe_mapping.open('rt') as f:
        for line in f:
            cjpni, cjpnj, cnw = map(int, line.split(','))
            if jpni == cjpni and jpnj == cjpnj:
                return cnw
