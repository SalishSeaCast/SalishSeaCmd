"""Salish Sea NEMO results combine sub-command processor

Combines per-processor files from an MPI Salish Sea NEMO run into single files
with the same name-root.


Copyright 2013 The Salish Sea MEOPAR Contributors
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
import glob
import gzip
import logging
import os
import subprocess
import sys
from . import utils


__all__ = ['main']


log = logging.getLogger('combine')
log.setLevel(logging.DEBUG)
log.addHandler(utils.make_stdout_logger())
log.addHandler(utils.make_stderr_logger())


def main(run_desc, args):
    """Run the NEMO `rebuild_nemo` tool for each set of per-processor
    results files.

    The output of `rebuild_nemo` for each file set is logged
    at the INFO level.
    The combined results files that `rebuild_nemo` produces are moved
    to the directory given by `args.results_dir`.

    :arg run_desc: Run description data structure.
    :type run_desc: dict

    :arg args: Command line arguments and option values
    :type args: :class:`argparse.Namespace`
    """
    rebuild_nemo_script = _find_rebuild_nemo_script(
        run_desc['paths']['NEMO-code'])
    name_roots, ncores = _get_results_files(args)
    _combine_results_files(rebuild_nemo_script, name_roots, ncores)
    os.remove('nam_rebuild')
    _move_results(name_roots, args.results_dir)
    _compress_results(name_roots, args)
    _delete_results_files(name_roots, args)


def _find_rebuild_nemo_script(nemo_code_path):
    rebuild_nemo_exec = os.path.join(
        nemo_code_path,
        'NEMOGCM/TOOLS/REBUILD_NEMO/rebuild_nemo.exe')
    if not os.path.lexists(rebuild_nemo_exec):
        log.error(
            'Error: {} not found - did you forget to build it?'
            .format(rebuild_nemo_exec))
        sys.exit(2)
    rebuild_nemo_script = os.path.splitext(rebuild_nemo_exec)[0]
    return rebuild_nemo_script


def _get_results_files(args):
    if args.delete_restart:
        restart_pattern = '*_restart_[0-9][0-9][0-9][0-9].nc'
        for fn in glob.glob(restart_pattern):
            os.remove(fn)
    result_pattern = '*_0000.nc'
    name_roots = [fn[:-8] for fn in glob.glob(result_pattern)]
    if not name_roots:
        log.error(
            'Error: no files found that match the {} pattern'
            .format(result_pattern))
        sys.exit(2)
    ncores = len(glob.glob(name_roots[0] + '_[0-9][0-9][0-9][0-9].nc'))
    return name_roots, ncores


def _combine_results_files(rebuild_nemo_script, name_roots, ncores):
    for fn in name_roots:
        result = subprocess.check_output(
            [rebuild_nemo_script, fn, str(ncores)],
            stderr=subprocess.STDOUT,
            universal_newlines=True)
        log.info(result)


def _move_results(name_roots, results_dir):
    abs_results_dir = os.path.abspath(results_dir)
    if os.path.exists(abs_results_dir):
        if os.path.samefile(os.getcwd(), abs_results_dir):
            return
    postfix = '' if results_dir.endswith('/') else '/'
    for fn in _results_files(name_roots):
        log.info('moving {} to {}{}'.format(fn, results_dir, postfix))
        os.renames(os.path.join('.', fn), os.path.join(abs_results_dir, fn))


def _results_files(name_roots):
    for fn in ('.'.join((n, 'nc')) for n in name_roots):
        yield fn


def _compress_results(name_roots, args):
    if args.no_compress:
        return
    log.info('Starting compression...')
    for fn in _results_files(name_roots):
        if 'restart' in fn and not args.compress_restart:
            continue
        fp = os.path.join(args.results_dir, fn)
        with open(fp, 'rb') as f_in:
            fpgz = '.'.join((fp, 'gz'))
            with gzip.open(fpgz, 'wb') as f_out:
                f_out.writelines(f_in)
        os.remove(fp)
        log.info('compressed {}'.format(fp))


def _delete_results_files(name_roots, args):
    if args.keep_proc_results:
        return
    log.info('Deleting per-processor files...')
    for name_root in name_roots:
        for fn in glob.glob(name_root + '_[0-9][0-9][0-9][0-9].nc'):
            os.remove(fn)
