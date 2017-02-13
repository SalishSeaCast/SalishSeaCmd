# Copyright 2013-2016 The Salish Sea MEOPAR Contributors
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
"""Define the :func:`fspath` function that returns the string representation
of a file system path.
This provides a uniform interface for working with :class:`Path` objects in
Python versions both before and after Python 3.6 in which the PEP 519 file
system protocol appeared.
"""
import os


def fspath(path):
    """ Return the string representation of a file system path.

    This function provides a uniform interface for working with
    :class:`pathlib.Path` objects in Python versions both before and after
    Python 3.6 in which the PEP 519 file system protocol appeared.

    :param path:
    :type path: :class:`pathlib.Path` or str

    :return: String representation of path.
    :rtype: str
    """
    return os.fspath(path) if hasattr(os, 'fspath') else str(path)
