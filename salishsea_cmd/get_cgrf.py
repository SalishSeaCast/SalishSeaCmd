# Copyright 2013-2014 The Salish Sea MEOPAR Contributors
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

"""SalishSeaCmd command plug-in for get_cgrf sub-command.

Download CGRF products atmospheric forcing files from Dalhousie rsync
repository and symlink with the file names that NEMO expects.
"""
from __future__ import absolute_import

import argparse
import datetime
import getpass
import logging
import os
import stat
import subprocess
import tempfile

import arrow
import cliff.command
import netCDF4 as nc
import numpy as np

from salishsea_tools import nc_tools


__all__ = ['GetCGRF']


log = logging.getLogger(__name__)


SERVER = 'goapp.ocean.dal.ca::canadian_GDPS_reforecasts_v1'
PERM664 = (
    stat.S_IRUSR | stat.S_IWUSR |
    stat.S_IRGRP | stat.S_IWGRP |
    stat.S_IROTH)
PERM775 = PERM664 | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH

RSYNC_MIRROR_DIR = os.path.abspath('rsync-mirror')
NEMO_ATMOS_DIR = os.path.abspath('NEMO-atmos')
# Assume altitude_CGRF.nc is in NEMO-atmos
ALTITUDE_DIR = os.path.abspath('NEMO-atmos')


class GetCGRF(cliff.command.Command):
    """Download and symlink CGRF atmospheric forcing files
    """
    def get_parser(self, prog_name):
        parser = super(GetCGRF, self).get_parser(prog_name)
        parser.description = '''
            Download CGRF products atmospheric forcing files from
            Dalhousie rsync repository and symlink with the file names
            that NEMO expects.
        '''
        parser.add_argument(
            'start_date', metavar='START_DATE', type=self._date_string,
            help='1st date to download files for')
        parser.add_argument(
            '-d', '--days', type=int, default=1,
            help='Number of days to download; defaults to 1')
        parser.add_argument(
            '--user', dest='userid', metavar='USERID',
            help='User id for Dalhousie CGRF rsync repository')
        parser.add_argument(
            '--password', dest='passwd', metavar='PASSWD',
            help='Passowrd for Dalhousie CGRF rsync repository')
        return parser

    def take_action(self, parsed_args):
        """Download CGRF products atmospheric forcing files from
        Dalhousie rsync repository and symlink with the file names that
        NEMO expects.
        """
        userid = (
            parsed_args.userid if parsed_args.userid is not None
            else raw_input('User id: '))
        passwd = (
            parsed_args.passwd if parsed_args.passwd is not None
            else getpass.getpass())
        with tempfile.NamedTemporaryFile(mode='wt', delete=False) as f:
            f.write('{}\n'.format(passwd))
            passwd_file = f.name
        cgrf_dir = os.getcwd()
        try:
            os.mkdir(RSYNC_MIRROR_DIR)
        except OSError:
            pass
        start_date = parsed_args.start_date.replace(days=-1)
        end_date = parsed_args.start_date.replace(days=parsed_args.days - 1)
        for day in arrow.Arrow.range('day', start_date, end_date):
            os.chdir(RSYNC_MIRROR_DIR)
            _get_cgrf(day, userid, passwd_file)
            os.chdir(cgrf_dir)
        os.remove(passwd_file)
        for day in arrow.Arrow.range('day', parsed_args.start_date, end_date):
            _rebase_cgrf_time(day)
            _correct_pressure(day)
        os.remove('tmp1.nc')
        os.remove('tmp2.nc')
        for day in arrow.Arrow.range('day', start_date, end_date):
            rsync_dir = os.path.join(
                RSYNC_MIRROR_DIR, day.format('YYYY-MM-DD'))
            log.info('Deleting {} files'.format(rsync_dir))
            for f in os.listdir(rsync_dir):
                os.remove(os.path.join(rsync_dir, f))
            log.info('Deleting {} directory'.format(RSYNC_MIRROR_DIR))
            os.removedirs(rsync_dir)

    def _date_string(self, string):
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


def _get_cgrf(day, userid, passwd_file):
    dst_dir = day.format('YYYY-MM-DD')
    if os.path.exists(dst_dir) and len(os.listdir(dst_dir)) == 8:
        log.info('{} dataset already downloaded'.format(dst_dir))
        return
    src_dir = day.strftime('%Y%m%d00')
    src_path = os.path.join(SERVER, str(day.year), src_dir)
    cmd = [
        'rsync',
        '-rlt',
        '--password-file={}'.format(passwd_file),
        '{}@{}/'.format(userid, src_path),
        '{}/'.format(dst_dir),
    ]
    log.info('Downloading {}'.format(dst_dir))
    subprocess.check_call(cmd)
    os.chmod(dst_dir, PERM775)
    for f in os.listdir(dst_dir):
        fp = os.path.join(dst_dir, f)
        log.info('Uncompressing {}'.format(fp))
        os.chmod(fp, PERM664)
        subprocess.check_call(['gunzip', fp])


def _rebase_cgrf_time(day):
    log.info('Rebasing {} dataset'.format(day.format('YYYY-MM-DD')))
    vars = (
        ('precip', 'liquid precipitation'),
        ('q2', '2m specific humidity'),
        ('qlw', 'long-wave radiation'),
        ('qsw', 'short-wave radiation'),
        ('slp', 'sea-level atmospheric pressure'),
        ('t2', '2m temperature'),
        ('u10', 'u-component 10m wind'),
        ('v10', 'v-component 10m wind'),
    )
    prev_day = day.replace(days=-1)
    for var, description in vars:
        log.info('Gathering {} values'.format(var))
        _get_cgrf_hyperslab(prev_day, var, 18, 23, 'tmp1.nc')
        _get_cgrf_hyperslab(day, var, 0, 17, 'tmp2.nc')
        _merge_cgrf_hyperslabs(day, var, 'tmp1.nc', 'tmp2.nc')
        tmp2 = nc.Dataset('tmp2.nc')
        _improve_cgrf_file(var, description, day, tmp2.history)


def _get_cgrf_hyperslab(day, var, start_hr, end_hr, result_filename):
    src_dir = os.path.join(RSYNC_MIRROR_DIR, day.format('YYYY-MM-DD'))
    cgrf_filename = '{}_{}.nc'.format(day.format('YYYYMMDD00'), var)
    cmd = [
        'ncks',
        '-4', '-L4', '-O',
        '-d', 'time_counter,{},{}'.format(start_hr, end_hr),
        os.path.join(src_dir, cgrf_filename),
        result_filename,
    ]
    subprocess.check_call(cmd)


def _merge_cgrf_hyperslabs(day, var, part1_filename, part2_filename):
        nemo_filename = '{}_{}.nc'.format(var, day.strftime('y%Ym%md%d'))
        cmd = [
            'ncrcat',
            '-O',
            part1_filename,
            part2_filename,
            os.path.join(NEMO_ATMOS_DIR, nemo_filename),
        ]
        output = subprocess.check_output(
            cmd, stderr=subprocess.STDOUT, universal_newlines=True)
        if output.strip() and not output.startswith('ncrcat: INFO/WARNING'):
            log.info(output)


def _improve_cgrf_file(var, description, day, tmp2_history):
    nemo_filename = '{}_{}.nc'.format(var, day.strftime('y%Ym%md%d'))
    dataset = nc.Dataset(os.path.join(NEMO_ATMOS_DIR, nemo_filename), 'r+')
    nc_tools.init_dataset_attrs(
        dataset,
        title=(
            'CGRF {} forcing dataset for {}'
            .format(description, day.format('YYYY-MM-DD'))),
        notebook_name='',
        nc_filepath='',
        comment=(
            'Processed from '
            'goapp.ocean.dal.ca::canadian_GDPS_reforecasts_v1 files.'),
        quiet=True,
    )
    dataset.source = (
        'https://bitbucket.org/salishsea/tools/raw/tip/SalishSeaCmd/'
        'salishsea_cmd/get_cgrf.py')
    dataset.references = os.path.join(NEMO_ATMOS_DIR, nemo_filename)
    time_counter = dataset.variables['time_counter']
    time_counter.units = (
        'hours since {} 00:00:00'.format(day.format('YYYY-MM-DD')))
    time_counter.time_origin = '{} 00:00:00'.format(day.format('YYYY-MMM-DD'))
    time_counter[:] = np.arange(24)
    time_counter.valid_range = np.array((0, 23))
    history = dataset.history.split('\n')
    history.reverse()
    dataset.history = (
        '{}\n'
        '{:%c}: Adjust time_counter values and clean up metadata.'
        .format('\n'.join(history), datetime.datetime.now())
    )
    dataset.close()


def _correct_pressure(day):
    log.info('Correcting pressure for {} '.format(day.format('YYYY-MM-DD')))
    pres_filename = '{}_{}.nc'.format('slp', day.strftime('y%Ym%md%d'))
    tmp_filename = '{}_{}.nc'.format('t2', day.strftime('y%Ym%md%d'))
    alt_filename = '{}.nc'.format('altitude_CGRF')
    # Load pressure, temperature, lat,lon, altitude
    f_pres = os.path.join(NEMO_ATMOS_DIR, pres_filename)
    f_temp = os.path.join(NEMO_ATMOS_DIR, tmp_filename)
    f_alt = os.path.join(ALTITUDE_DIR, alt_filename)
    # Build corrected pressure file
    slpcorr_filename = '{}_{}.nc'.format('slp_corr', day.strftime('y%Ym%md%d'))
    f_slp = os.path.join(NEMO_ATMOS_DIR, slpcorr_filename)
    nc_tools.generate_pressure_file(f_slp, f_pres, f_temp, f_alt, day)
