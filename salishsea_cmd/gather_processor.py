"""Salish Sea NEMO results gather sub-command processor

Gather results files from a Salish Sea NEMO run into a specified directory.


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
import logging
import os
import shutil
import tempfile
from . import (
    api,
    utils,
)


__all__ = ['main']


log = logging.getLogger('gather')
log.setLevel(logging.DEBUG)
log.addHandler(utils.make_stdout_logger())
log.addHandler(utils.make_stderr_logger())


def main(run_desc, args):
    """Gather the results files from a Salish Sea NEMO run into
    a results directory.

    The per-processor results files from an MPI run are combined via
    the `salishsea combine` command.
    The run description file,
    namelist,
    and other files that define the run are also gathered into the
    directory given by `args.results_dir`.

    :arg run_desc: Run description data structure.
    :type run_desc: dict

    :arg args: Command line arguments and option values
    :type args: :class:`argparse.Namespace`
    """
    api.combine(
        run_desc, args.results_dir, args.keep_proc_results, args.no_compress,
        args.compress_restart, args.delete_restart)
    _copy_run_description(args)
    _delete_symlinks()
    _move_results(args.results_dir)


def _copy_run_description(args):
    log.info('Copying run description file...')
    abs_results_dir = os.path.abspath(args.results_dir)
    if os.path.samefile(os.getcwd(), abs_results_dir):
        # Results are being gathered in-place so replace run description
        # file symlink with a copy of the file
        tmpfile_obj, tmpfile = tempfile.mkstemp(dir='.')
        shutil.copy2(args.desc_file.name, tmpfile)
        os.remove(args.desc_file.name)
        shutil.copy2(tmpfile, args.desc_file.name)
        os.remove(tmpfile)
        return
    shutil.copy2(args.desc_file.name, abs_results_dir)


def _delete_symlinks():
    log.info('Deleting symbolic links...')
    for fn in os.listdir('.'):
        if os.path.islink(fn):
            os.remove(fn)


def _move_results(results_dir):
    abs_results_dir = os.path.abspath(results_dir)
    if os.path.samefile(os.getcwd(), abs_results_dir):
        return
    log.info('Moving run definition and non-netCDF results files...')
    for fn in os.listdir('.'):
        os.rename(os.path.join('.', fn), os.path.join(abs_results_dir, fn))
