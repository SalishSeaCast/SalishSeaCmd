"""Salish Sea NEMO command processor utility functions


Copyright 2013 Doug Latornell and The University of British Columbia

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
import sys


__all__ = ['make_stderr_logger', 'make_stdout_logger']


def make_stderr_logger():
    stderr = logging.StreamHandler(sys.stderr)
    stderr.setLevel(logging.ERROR)
    formatter = logging.Formatter('%(message)s')
    stderr.setFormatter(formatter)
    return stderr


def make_stdout_logger():
    stdout = logging.StreamHandler(sys.stdout)
    stdout.setLevel(logging.INFO)
    formatter = logging.Formatter('%(message)s')
    stdout.setFormatter(formatter)
    return stdout
