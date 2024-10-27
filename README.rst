************************************
SalishSeaCast NEMO Command Processor
************************************

+----------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| **Continuous Integration** | .. image:: https://github.com/SalishSeaCast/SalishSeaCmd/actions/workflows/pytest-with-coverage.yaml/badge.svg                                                                                       |
|                            |      :target: https://github.com/SalishSeaCast/SalishSeaCmd/actions?query=workflow:pytest-with-coverage                                                                                              |
|                            |      :alt: Pytest with Coverage Status                                                                                                                                                               |
|                            | .. image:: https://codecov.io/gh/SalishSeaCast/SalishSeaCmd/branch/main/graph/badge.svg                                                                                                              |
|                            |      :target: https://app.codecov.io/gh/SalishSeaCast/SalishSeaCmd                                                                                                                                   |
|                            |      :alt: Codecov Testing Coverage Report                                                                                                                                                           |
|                            | .. image:: https://github.com/SalishSeaCast/SalishSeaCmd/actions/workflows/codeql-analysis.yaml/badge.svg                                                                                            |
|                            |     :target: https://github.com/SalishSeaCast/SalishSeaCmd/actions?query=workflow:CodeQL                                                                                                             |
|                            |     :alt: CodeQL analysis                                                                                                                                                                            |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| **Documentation**          | .. image:: https://readthedocs.org/projects/salishseacmd/badge/?version=latest                                                                                                                       |
|                            |     :target: https://salishseacmd.readthedocs.io/en/latest/                                                                                                                                          |
|                            |     :alt: Documentation Status                                                                                                                                                                       |
|                            | .. image:: https://github.com/SalishSeaCast/SalishSeaCmd/actions/workflows/sphinx-linkcheck.yaml/badge.svg                                                                                           |
|                            |     :target: https://github.com/SalishSeaCast/SalishSeaCmd/actions?query=workflow:sphinx-linkcheck                                                                                                   |
|                            |     :alt: Sphinx linkcheck                                                                                                                                                                           |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| **Package**                | .. image:: https://img.shields.io/github/v/release/SalishSeaCast/SalishSeaCmd?logo=github                                                                                                            |
|                            |     :target: https://github.com/SalishSeaCast/SalishSeaCmd/releases                                                                                                                                  |
|                            |     :alt: Releases                                                                                                                                                                                   |
|                            | .. image:: https://img.shields.io/python/required-version-toml?tomlFilePath=https://raw.githubusercontent.com/SalishSeaCast/SalishSeaCmd/main/pyproject.toml&logo=Python&logoColor=gold&label=Python |
|                            |      :target: https://docs.python.org/3.13/                                                                                                                                                          |
|                            |      :alt: Python Version from PEP 621 TOML                                                                                                                                                          |
|                            | .. image:: https://img.shields.io/github/issues/SalishSeaCast/SalishSeaCmd?logo=github                                                                                                               |
|                            |     :target: https://github.com/SalishSeaCast/SalishSeaCmd/issues                                                                                                                                    |
|                            |     :alt: Issue Tracker                                                                                                                                                                              |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| **Meta**                   | .. image:: https://img.shields.io/badge/license-Apache%202-cb2533.svg                                                                                                                                |
|                            |     :target: https://www.apache.org/licenses/LICENSE-2.0                                                                                                                                             |
|                            |     :alt: Licensed under the Apache License, Version 2.0                                                                                                                                             |
|                            | .. image:: https://img.shields.io/badge/version%20control-git-blue.svg?logo=github                                                                                                                   |
|                            |     :target: https://github.com/SalishSeaCast/SalishSeaCmd                                                                                                                                           |
|                            |     :alt: Git on GitHub                                                                                                                                                                              |
|                            | .. image:: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white                                                                                              |
|                            |     :target: https://pre-commit.com                                                                                                                                                                  |
|                            |     :alt: pre-commit                                                                                                                                                                                 |
|                            | .. image:: https://img.shields.io/badge/code%20style-black-000000.svg                                                                                                                                |
|                            |     :target: https://black.readthedocs.io/en/stable/                                                                                                                                                 |
|                            |     :alt: The uncompromising Python code formatter                                                                                                                                                   |
|                            | .. image:: https://img.shields.io/badge/%F0%9F%A5%9A-Hatch-4051b5.svg                                                                                                                                |
|                            |     :target: https://github.com/pypa/hatch                                                                                                                                                           |
|                            |     :alt: Hatch project                                                                                                                                                                              |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

The SalishSeaCast NEMO command processor, ``salishsea``, is a command line tool
for doing various operations associated with the `SalishSeaCast NEMO model`_.

.. _SalishSeaCast NEMO model: https://salishsea-meopar-docs.readthedocs.io/en/latest/

Use ``salishsea --help`` to get a list of the sub-commands available for doing things
with and related to SalishSeaCast NEMO.
Use ``salishsea help <sub-command>`` to get a synopsis of what a sub-command does,
what its required arguments are,
and what options are available to control it.

Documentation for the command processor is in the ``docs/`` directory and is rendered
at https://salishseacmd.readthedocs.io/en/latest/.

.. image:: https://readthedocs.org/projects/salishseacmd/badge/?version=latest
    :target: https://salishseacmd.readthedocs.io/en/latest/
    :alt: Documentation Status

This an extensible tool built on the OpenStack ``cliff``
(`Command Line Interface Formulation Framework`_)
package.
It is a NEMO domain-specific command processor tool for the `SalishSeaCast NEMO model`_
that uses plug-ins from the `NEMO-Cmd`_ package.

.. _Command Line Interface Formulation Framework: http://docs.openstack.org/developer/cliff/
.. _NEMO-Cmd: https://github.com/SalishSeaCast/NEMO-Cmd


License
=======

.. image:: https://img.shields.io/badge/license-Apache%202-cb2533.svg
    :target: https://www.apache.org/licenses/LICENSE-2.0
    :alt: Licensed under the Apache License, Version 2.0

The SalishSeaCast NEMO command processor and documentation are copyright 2013 – present
by the `SalishSeaCast Project Contributors`_ and The University of British Columbia.

.. _SalishSeaCast Project Contributors: https://github.com/SalishSeaCast/docs/blob/main/CONTRIBUTORS.rst

They are licensed under the Apache License, Version 2.0.
https://www.apache.org/licenses/LICENSE-2.0
Please see the LICENSE file for details of the license.
