"""Salish Sea NEMO get_cgrf sub-command processor

Download CGRF products atmospheric forcing files from Dalhousie rsync
repository and symlink with the file names that NEMO expects.

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
from __future__ import absolute_import
import getpass
import logging
import os
import stat
import subprocess
import tempfile
import arrow
from . import utils


__all__ = ['main']


SERVER = 'goapp.ocean.dal.ca::canadian_GDPS_reforecasts_v1'
PERM664 = (
    stat.S_IRUSR | stat.S_IWUSR |
    stat.S_IRGRP | stat.S_IWGRP |
    stat.S_IROTH)
PERM775 = PERM664 | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH


log = logging.getLogger('get_cgrf')
log.setLevel(logging.DEBUG)
log.addHandler(utils.make_stdout_logger())
log.addHandler(utils.make_stderr_logger())


RSYNC_MIRROR_DIR = os.path.abspath('rsync-mirror-new')
NEMO_ATMOS_DIR = os.path.abspath('NEMO-atmos-new')


def main(args):
    """Download CGRF products atmospheric forcing files from Dalhousie rsync
    repository and symlink with the file names that NEMO expects.

    :arg args: Command line arguments and option values
    :type args: :class:`argparse.Namespace`
    """
    userid = args.userid if args.userid is not None else raw_input('User id: ')
    passwd = args.passwd if args.passwd is not None else getpass.getpass()
    with tempfile.NamedTemporaryFile(mode='wt', delete=False) as f:
        f.write('{}\n'.format(passwd))
        passwd_file = f.name
    start_date = args.start_date.replace(days=-1)
    end_date = args.start_date.replace(days=args.days - 1)
    for day in arrow.Arrow.range('day', start_date, end_date):
        os.chdir(RSYNC_MIRROR_DIR)
        _get_cgrf(day, userid, passwd_file)
        os.chdir(NEMO_ATMOS_DIR)
        _link_cgrf(day)
    os.remove(passwd_file)


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


def _link_cgrf(day):
    link_src_dir = os.path.join('..', 'rsync-mirror', day.format('YYYY-MM-DD'))
    for f in os.listdir(link_src_dir):
        root, ext = os.path.splitext(f)
        var = root.rsplit('_', 1)[1]
        link_name = '{}_{}.nc'.format(var, day.strftime('y%Ym%md%d'))
        log.info('Symlinking {}'.format(link_name))
        os.symlink(os.path.join(link_src_dir, f), link_name)
