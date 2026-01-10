.. Copyright 2013 – present by the SalishSeaCast Project Contributors
.. and The University of British Columbia
..
.. Licensed under the Apache License, Version 2.0 (the "License");
.. you may not use this file except in compliance with the License.
.. You may obtain a copy of the License at
..
..    https://www.apache.org/licenses/LICENSE-2.0
..
.. Unless required by applicable law or agreed to in writing, software
.. distributed under the License is distributed on an "AS IS" BASIS,
.. WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
.. See the License for the specific language governing permissions and
.. limitations under the License.

.. SPDX-License-Identifier: Apache-2.0


.. _SalishSeaCmdPackageDevelopment:

***************************************
:kbd:`SalishSeaCmd` Package Development
***************************************

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
| **Documentation**          | .. image:: https://app.readthedocs.org/projects/salishseacmd/badge/?version=latest                                                                                                                   |
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
|                            |      :target: https://docs.python.org/3/                                                                                                                                                             |
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
|                            | .. image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/prefix-dev/pixi/main/assets/badge/v0.json                                                                           |
|                            |     :target: https://pixi.prefix.dev/latest/                                                                                                                                                         |
|                            |     :alt: Pixi                                                                                                                                                                                       |
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


.. _SalishSeaCmdPythonVersions:

Python Versions
===============

.. image:: https://img.shields.io/python/required-version-toml?tomlFilePath=https://raw.githubusercontent.com/SalishSeaCast/SalishSeaCmd/main/pyproject.toml&logo=Python&logoColor=gold&label=Python
    :target: https://docs.python.org/3/
    :alt: Python Version from PEP 621 TOML

The :py:obj:`SalishSeaCmd` package is developed using `Python`_ 3.14.
The minimum supported Python version is 3.12.
The :ref:`SalishSeaCmdContinuousIntegration` workflow on GitHub ensures that the package
is tested for all versions of Python>=3.12.
An old version of the package running under Python 3.5 is deployed on the
Westgrid ``orcinus`` HPC platform.
That version is tagged in the repository as ``orcinus-python-3.5``.

.. _Python: https://www.python.org/


.. _SalishSeaCmdGettingTheCode:

Getting the Code
================

.. image:: https://img.shields.io/badge/version%20control-git-blue.svg?logo=github
    :target: https://github.com/SalishSeaCast/SalishSeaCmd
    :alt: Git on GitHub

Clone the :ref:`SalishSeaCmd-repo` code and documentation `repository`_ from GitHub with:

.. _repository: https://github.com/SalishSeaCast/SalishSeaCmd

.. code-block:: bash

    git clone git@github.com:SalishSeaCast/SalishSeaCmd.git


.. _SalishSeaCmdDevelopmentEnvironment:

Development Environment
=======================

The :kbd:`SalishSeaCmd` package depends on the :kbd:`NEMO-Cmd` package,
so you need to clone its repo,
:ref:`NEMO-Cmd-repo`,
beside your clone of :ref:`SalishSeaCmd-repo`.

:py:obj:`SalishSeaCmd` uses Pixi_ for package and environment management.
If you don't already have Pixi_ installed,
please follow its `installation instructions`_ to do so.

.. _Pixi: https://pixi.prefix.dev/latest/
.. _`installation instructions`: https://pixi.prefix.dev/latest/installation/

Most commands are executed using :command:`pixi run` in the :file:`SalishSeaCmd/` directory
(or a sub-directory).
Dependencies will be downloaded and linked in to environments when you use :command:`pixi run`
for the first time.

* The ``default`` environment has the packages installed that are required to run the
  :py:obj:`SalishSeaCmd` command-line interface;
  e.g. :command:`pixi run salishsea help`

* Other environments used by commands in the sections below have addition packages for running
  the test suite,
  building and link checking the documentation,
  etc.

* If you are using an integrated development environment like VSCode or PyCharm
  where you need a Python interpreter to support coding assistance features,
  run development tasks,
  etc.,
  use the interpreter in the ``dev`` environment.
  You can get its full path with :command:`pixi run -e dev which python`

To get detailed information about the environments,
the packages installed in them,
`Pixi`_ tasks that are defined for them,
etc.,
:use command:`pixi info`.

:py:obj:`SalishSeaCmd` is installed in `editable install mode`_ in all of the environments that
`Pixi`_ creates.
That means that changes you make to the code are immediately reflected in the environments.

.. _editable install mode: https://pip.pypa.io/en/stable/topics/local-project-installs/#editable-installs


.. _SalishSeaCmdCodingStyle:

Coding Style
============

.. image:: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white
    :target: https://pre-commit.com
    :alt: pre-commit
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://black.readthedocs.io/en/stable/
    :alt: The uncompromising Python code formatter

The :py:obj:`SalishSeaCmd` package uses Git pre-commit hooks managed by `pre-commit`_ to
maintain consistent code style and and other aspects of code,
docs,
and repo QA.

.. _pre-commit: https://pre-commit.com/

To install the `pre-commit` hooks in a newly cloned repo,
run :command:`pre-commit install`:

.. code-block:: bash

    cd SalishSeaCmd
    pixi run -e dev pre-commit install

.. note::
    You only need to install the hooks once immediately after you make a new clone
    of the `SalishSeaCmd repository`_.

.. _SalishSeaCmd repository: https://github.com/SalishSeaCast/SalishSeaCmd


.. _SalishSeaCmdBuildingTheDocumentation:

Building the Documentation
==========================

.. image:: https://app.readthedocs.org/projects/salishseacmd/badge/?version=latest
    :target: https://salishseacmd.readthedocs.io/en/latest/
    :alt: Documentation Status

The documentation for the :py:obj:`SalishSeaCmd` package is written in `reStructuredText`_ and converted to HTML using `Sphinx`_.

.. _reStructuredText: https://www.sphinx-doc.org/en/master/usage/restructuredtext/index.html
.. _Sphinx: https://www.sphinx-doc.org/en/master/

If you have write access to the `repository`_ on GitHub,
whenever you push changes to GitHub the documentation is automatically re-built and rendered at https://salishseacmd.readthedocs.io/en/latest/.

Additions,
improvements,
and corrections to these docs are *always* welcome.

The quickest way to fix typos, etc. on existing pages is to use the :guilabel:`Edit on GitHub` link in the upper right corner of the page to get to the online editor for the page on `GitHub`_.

.. _GitHub: https://github.com/SalishSeaCast/SalishSeaCmd

For more substantial work,
and to add new pages,
follow the instructions in the :ref:`SalishSeaCmdDevelopmentEnvironment` section above.
In the development environment you can build the docs locally instead of having to push commits to GitHub to trigger a `build on readthedocs.org`_ and wait for it to complete.
Below are instructions that explain how to:

.. _build on readthedocs.org: https://app.readthedocs.org/projects/salishseacmd/builds/

* build the docs with your changes,
  and preview them in Firefox

* check the docs for broken links


.. _SalishSeaCmdBuildingAndPreviewingTheDocumentation:

Building and Previewing the Documentation
-----------------------------------------

Building the documentation is driven by :file:`docs/Makefile`.
To do a clean build of the documentation use:

.. code-block:: bash

    cd SalishSeaCmd/
    pixi run docs

The output looks something like:

.. code-block:: text

    ✨ Pixi task (docs in docs): make clean html
    Removing everything under '_build'...
    Running Sphinx v8.1.3
    loading translations [en]... done
    making output directory... done
    loading intersphinx inventory 'python' from https://docs.python.org/3/objects.inv ...
    loading intersphinx inventory 'salishseadocs' from https://salishsea-meopar-docs.readthedocs.io/en/latest/objects.inv ...
    loading intersphinx inventory 'nemocmd' from https://nemo-cmd.readthedocs.io/en/latest/objects.inv ...
    building [mo]: targets for 0 po files that are out of date
    writing output...
    building [html]: targets for 10 source files that are out of date
    updating environment: [new config] 10 added, 0 changed, 0 removed
    reading sources... [100%] subcommands
    looking for now-outdated files... none found
    pickling environment... done
    checking consistency... done
    preparing documents... done
    copying assets...
    copying static files...
    Writing evaluated template result to /media/doug/warehouse/MEOPAR/SalishSeaCmd/docs/_build/html/_static/language_data.js
    Writing evaluated template result to /media/doug/warehouse/MEOPAR/SalishSeaCmd/docs/_build/html/_static/documentation_options.js
    Writing evaluated template result to /media/doug/warehouse/MEOPAR/SalishSeaCmd/docs/_build/html/_static/basic.css
    Writing evaluated template result to /media/doug/warehouse/MEOPAR/SalishSeaCmd/docs/_build/html/_static/js/versions.js
    copying static files: done
    copying extra files...
    copying extra files: done
    copying assets: done
    writing output... [100%] subcommands
    generating indices... genindex done
    highlighting module code... [100%] salishsea_cmd.api
    writing additional pages... search done
    dumping search index in English (code: en)... done
    dumping object inventory... done
    build succeeded.

    The HTML pages are in _build/html.

The HTML rendering of the docs ends up in :file:`docs/_build/html/`.
You can open the :file:`index.html` file in that directory tree in your browser to preview the results of the build before committing and pushing your changes to GitHub.

Whenever you push changes to the :ref:`SalishSeaCmd-repo` on GitHub the documentation is automatically re-built and rendered at https://salishseacmd.readthedocs.io/en/latest/.


.. _SalishSeaCmdLinkCheckingTheDocumentation:

Link Checking the Documentation
-------------------------------

.. image:: https://github.com/SalishSeaCast/SalishSeaCmd/workflows/sphinx-linkcheck/badge.svg
    :target: https://github.com/SalishSeaCast/SalishSeaCmd/actions?query=workflow:sphinx-linkcheck
    :alt: Sphinx linkcheck

Sphinx also provides a link checker utility which can be run to find broken or redirected links in the docs.
Run the link checker with:

.. code-block:: bash

    cd SalishSeaCmd/
    pixi run linkcheck

The output looks something like:

.. code-block:: text

    ✨ Pixi task (linkcheck in docs): make clean linkcheck
    Removing everything under '_build'...
    Running Sphinx v8.1.3
    loading translations [en]... done
    making output directory... done
    loading intersphinx inventory 'python' from https://docs.python.org/3/objects.inv ...
    loading intersphinx inventory 'salishseadocs' from https://salishsea-meopar-docs.readthedocs.io/en/latest/objects.inv ...
    loading intersphinx inventory 'nemocmd' from https://nemo-cmd.readthedocs.io/en/latest/objects.inv ...
    building [mo]: targets for 0 po files that are out of date
    writing output...
    building [linkcheck]: targets for 10 source files that are out of date
    updating environment: [new config] 10 added, 0 changed, 0 removed
    reading sources... [100%] subcommands
    looking for now-outdated files... none found
    pickling environment... done
    checking consistency... done
    preparing documents... done
    copying assets...
    copying assets: done
    writing output... [100%] subcommands

    ( pkg_development: line   36) ok        https://app.readthedocs.org/projects/salishseacmd/badge/?version=latest
    ( pkg_development: line   23) ok        https://black.readthedocs.io/en/stable/
    ( pkg_development: line   23) ok        https://app.codecov.io/gh/SalishSeaCast/SalishSeaCmd
    ( pkg_development: line   29) ok        https://codecov.io/gh/SalishSeaCast/SalishSeaCmd/branch/main/graph/badge.svg
    ( pkg_development: line  460) ok        https://coverage.readthedocs.io/en/latest/
    (breaking_changes: line  132) ok        https://calver.org/
    (    installation: line   35) ok        https://docs.conda.io/en/latest/
    (    installation: line   35) ok        https://docs.conda.io/en/latest/miniconda.html
    ( pkg_development: line  426) ok        https://docs.pytest.org/en/latest/
    ( pkg_development: line  219) ok        https://app.readthedocs.org/projects/salishseacmd/builds/
    ( pkg_development: line   23) ok        https://docs.python.org/3/
    (breaking_changes: line  183) ok        https://docs.python.org/3/library/constants.html#False
    (             api: line   23) ok        https://docs.python.org/3/library/constants.html#None
    (run_description_file/3.6_agrif_yaml_file: line   26) ok        https://agrif.imag.fr/
    (           index: line   33) ok        https://docs.openstack.org/cliff/latest/
    (             api: line   23) ok        https://docs.python.org/3/library/functions.html#int
    (run_description_file/3.6_yaml_file: line  446) ok        https://docs.python.org/3/library/constants.html#True
    (             api: line   23) ok        https://docs.python.org/3/library/stdtypes.html#dict
    (             api: line   23) ok        https://docs.python.org/3/library/pathlib.html#pathlib.Path
    ( pkg_development: line  509) ok        https://docs.github.com/en/actions
    (             api: line   23) ok        https://docs.python.org/3/library/stdtypes.html#str
    (     subcommands: line  301) ok        https://en.wikipedia.org/wiki/Universally_unique_identifier
    ( pkg_development: line  524) ok        https://git-scm.com/
    (breaking_changes: line  123) ok        https://f90nml.readthedocs.io/en/latest/
    (           index: line   33) ok        https://github.com/SalishSeaCast/NEMO-Cmd
    (     subcommands: line  382) ok        https://github.com/SalishSeaCast/NEMO-Cmd/
    (     subcommands: line  444) ok        https://github.com/SalishSeaCast/SS-run-sets/blob/main/v201905/hindcast/file_def_dailysplit.xml
    ( pkg_development: line   23) ok        https://github.com/SalishSeaCast/SalishSeaCmd
    ( pkg_development: line   32) ok        https://github.com/SalishSeaCast/SalishSeaCmd/actions/workflows/codeql-analysis.yaml/badge.svg
    ( pkg_development: line   26) ok        https://github.com/SalishSeaCast/SalishSeaCmd/actions/workflows/pytest-with-coverage.yaml/badge.svg
    ( pkg_development: line   39) ok        https://github.com/SalishSeaCast/SalishSeaCmd/actions/workflows/sphinx-linkcheck.yaml/badge.svg
    ( pkg_development: line  496) ok        https://github.com/SalishSeaCast/SalishSeaCmd/actions
    ( pkg_development: line   23) ok        https://github.com/SalishSeaCast/SalishSeaCmd/actions?query=workflow:CodeQL
    ( pkg_development: line   23) ok        https://github.com/SalishSeaCast/SalishSeaCmd/actions?query=workflow:sphinx-linkcheck
    ( pkg_development: line  496) ok        https://github.com/SalishSeaCast/SalishSeaCmd/commits/main
    ( pkg_development: line  416) ok        https://github.com/SalishSeaCast/SalishSeaCmd/actions?query=workflow%3Asphinx-linkcheck
    ( pkg_development: line  489) ok        https://github.com/SalishSeaCast/SalishSeaCmd/workflows/pytest-with-coverage/badge.svg
    ( pkg_development: line  298) ok        https://github.com/SalishSeaCast/SalishSeaCmd/workflows/sphinx-linkcheck/badge.svg
    ( pkg_development: line   23) ok        https://github.com/SalishSeaCast/SalishSeaCmd/actions?query=workflow:pytest-with-coverage
    ( pkg_development: line   23) ok        https://github.com/SalishSeaCast/SalishSeaCmd/issues
    ( pkg_development: line   23) ok        https://github.com/SalishSeaCast/SalishSeaCmd/releases
    (breaking_changes: line  106) ok        https://gitpython.readthedocs.io/en/stable/
    (           index: line   67) ok        https://github.com/SalishSeaCast/docs/blob/main/CONTRIBUTORS.rst
    ( pkg_development: line   65) ok        https://img.shields.io/badge/%F0%9F%A5%9A-Hatch-4051b5.svg
    ( pkg_development: line   62) ok        https://img.shields.io/badge/code%20style-black-000000.svg
    ( pkg_development: line   53) ok        https://img.shields.io/badge/license-Apache%202-cb2533.svg
    ( pkg_development: line   59) ok        https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white
    ( pkg_development: line   49) ok        https://img.shields.io/github/issues/SalishSeaCast/SalishSeaCmd?logo=github
    ( pkg_development: line   56) ok        https://img.shields.io/badge/version%20control-git-blue.svg?logo=github
    ( pkg_development: line   43) ok        https://img.shields.io/github/v/release/SalishSeaCast/SalishSeaCmd?logo=github
    ( pkg_development: line   46) ok        https://img.shields.io/python/required-version-toml?tomlFilePath=https://raw.githubusercontent.com/SalishSeaCast/SalishSeaCmd/main/pyproject.toml&logo=Python&logoColor=gold&label=Python
    (    installation: line   35) ok        https://github.com/conda-forge/miniforge
    (     subcommands: line  390) ok        https://nemo-cmd.readthedocs.io/en/latest/subcommands.html#nemo-combine
    (     subcommands: line  231) ok        https://nemo-cmd.readthedocs.io/en/latest/subcommands.html#nemo-deflate
    ( pkg_development: line   23) ok        https://github.com/pypa/hatch
    (     subcommands: line  432) ok        https://nemo-cmd.readthedocs.io/en/latest/subcommands.html#nemo-gather
    ( pkg_development: line  119) ok        https://pixi.prefix.dev/latest/installation/
    ( pkg_development: line  119) ok        https://pixi.prefix.dev/latest/
    ( pkg_development: line  153) ok        https://pip.pypa.io/en/stable/topics/local-project-installs/#editable-installs
    ( pkg_development: line  460) ok        https://pytest-cov.readthedocs.io/en/latest/
    (breaking_changes: line  175) ok        https://salishsea-meopar-docs.readthedocs.io/en/latest/code-notes/salishsea-nemo/land-processor-elimination/index.html#landprocessorelimination
    (           index: line   25) ok        https://salishsea-meopar-docs.readthedocs.io/en/latest/code-notes/salishsea-nemo/index.html#salishseanemo
    ( pkg_development: line   23) ok        https://pre-commit.com
    ( pkg_development: line  172) ok        https://pre-commit.com/
    (run_description_file/index: line   25) ok        https://pyyaml.org/wiki/PyYAMLDocumentation
    (    installation: line   33) ok        https://salishsea-meopar-docs.readthedocs.io/en/latest/repos_organization.html#nemo-cmd-repo
    (run_description_file/3.6_yaml_file: line   91) ok        https://salishsea-meopar-docs.readthedocs.io/en/latest/repos_organization.html#nemo-3-6-code-repo
    (run_description_file/3.6_yaml_file: line  173) ok        https://salishsea-meopar-docs.readthedocs.io/en/latest/code-notes/salishsea-nemo/land-processor-elimination/index.html#preferred-mpi-lpe-decompositions
    (    installation: line   33) ok        https://salishsea-meopar-docs.readthedocs.io/en/latest/repos_organization.html#salishseacmd-repo
    (run_description_file/index: line   30) ok        https://salishsea-meopar-docs.readthedocs.io/en/latest/repos_organization.html#ss-run-sets-repo
    ( pkg_development: line   80) ok        https://www.python.org/
    (run_description_file/3.6_yaml_file: line  102) ok        https://salishsea-meopar-docs.readthedocs.io/en/latest/repos_organization.html#xios-repo
    ( pkg_development: line   23) ok        https://salishseacmd.readthedocs.io/en/latest/
    ( pkg_development: line  203) ok        https://www.sphinx-doc.org/en/master/usage/restructuredtext/index.html
    (           index: line   72) ok        https://www.apache.org/licenses/LICENSE-2.0
    (run_description_file/3.6_yaml_file: line   76) ok        https://slurm.schedmd.com/
    ( pkg_development: line  203) ok        https://www.sphinx-doc.org/en/master/
    build succeeded.

    Look for any errors in the above output or in _build/linkcheck/output.txt

:command:`linkcheck` is run monthly via a `scheduled GitHub Actions workflow`_.

.. _scheduled GitHub Actions workflow: https://github.com/SalishSeaCast/SalishSeaCmd/actions?query=workflow%3Asphinx-linkcheck


.. _SalishSeaCmdRuningTheUnitTests:

Running the Unit Tests
======================

The test suite for the :py:obj:`SalishSeaCmd` package is in :file:`SalishSeaCmd/tests/`.
The `pytest`_ tool is used for test fixtures and as the test runner for the suite.

.. _pytest: https://docs.pytest.org/en/latest/

To run the test suite in the most recent supported version of Python use:

.. code-block:: bash

    cd SalishSeaCmd/
    pixi run -e test pytest

to run the test suite.
The output looks something like:

.. code-block:: text

    ================================= test session starts ===================================
    platform linux -- Python 3.14.2, pytest-9.0.2, pluggy-1.6.0
    Using --randomly-seed=3689377719
    rootdir: /media/doug/warehouse/MEOPAR/SalishSeaCmd
    configfile: pytest.ini
    plugins: cov-7.0.0, randomly-3.15.0
    collected 268 items

    tests/test_api.py ......                                                          [  2%]
    tests/test_run.py ......................................................................
    ........................................................................................
    ..........................................................................        [ 88%]
    tests/test_prepare.py ..............                                              [ 94%]
    tests/test_split_results.py ................                                      [100%]

    ================================= 268 passed in 0.68s ===================================

You can monitor what lines of code the test suite exercises using the `coverage.py`_ and `pytest-cov`_ tools with the command:

.. _coverage.py: https://coverage.readthedocs.io/en/latest/
.. _pytest-cov: https://pytest-cov.readthedocs.io/en/latest/

.. code-block:: bash

    cd SalishSeaCmd/
    pixi run -e test pytest-cov

The test coverage report will be displayed below the test suite run output.

Alternatively,
you can use

.. code-block:: bash

    cd SalishSeaCmd/
    pixi run -e test pytest-cov-html

to produce an HTML report that you can view in your browser by opening
:file:`SalishSeaCmd/htmlcov/index.html`.


.. _SalishSeaCmdContinuousIntegration:

Continuous Integration
----------------------

.. image:: https://github.com/SalishSeaCast/SalishSeaCmd/workflows/pytest-with-coverage/badge.svg
    :target: https://github.com/SalishSeaCast/SalishSeaCmd/actions?query=workflow:pytest-with-coverage
    :alt: Pytest with Coverage Status
.. image:: https://codecov.io/gh/SalishSeaCast/SalishSeaCmd/branch/main/graph/badge.svg
    :target: https://app.codecov.io/gh/SalishSeaCast/SalishSeaCmd
    :alt: Codecov Testing Coverage Report

The :py:obj:`SalishSeaCmd` package unit test suite is run and a coverage report is generated
whenever changes are pushed to GitHub.
The results are visible on the `repo actions page`_,
from the green checkmarks beside commits on the `repo commits page`_,
or from the green checkmark to the left of the "Latest commit" message on the
`repo code overview page`_ .
The testing coverage report is uploaded to `codecov.io`_

.. _repo actions page: https://github.com/SalishSeaCast/SalishSeaCmd/actions
.. _repo commits page: https://github.com/SalishSeaCast/SalishSeaCmd/commits/main
.. _repo code overview page: https://github.com/SalishSeaCast/SalishSeaCmd
.. _codecov.io: https://app.codecov.io/gh/SalishSeaCast/SalishSeaCmd

The `GitHub Actions`_ workflow configuration that defines the continuous integration
tasks is in the :file:`.github/workflows/pytest-with-coverage.yaml` file.

.. _GitHub Actions: https://docs.github.com/en/actions


.. _SalishSeaCmdVersionControlRepository:

Version Control Repository
==========================

.. image:: https://img.shields.io/badge/version%20control-git-blue.svg?logo=github
    :target: https://github.com/SalishSeaCast/SalishSeaCmd
    :alt: Git on GitHub

The :py:obj:`SalishSeaCmd` package code and documentation source files are available in the
:ref:`SalishSeaCmd-repo` `Git`_ repository at https://github.com/SalishSeaCast/SalishSeaCmd.

.. _Git: https://git-scm.com/


.. _SalishSeaCmdIssueTracker:

Issue Tracker
=============

.. image:: https://img.shields.io/github/issues/SalishSeaCast/SalishSeaCmd?logo=github
    :target: https://github.com/SalishSeaCast/SalishSeaCmd/issues
    :alt: Issue Tracker

Development tasks,
bug reports,
and enhancement ideas are recorded and managed in the issue tracker at https://github.com/SalishSeaCast/SalishSeaCmd/issues.


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


Release Process
===============

.. image:: https://img.shields.io/github/v/release/SalishSeaCast/SalishSeaCmd?logo=github
    :target: https://github.com/SalishSeaCast/SalishSeaCmd/releases
    :alt: Releases
.. image:: https://img.shields.io/badge/%F0%9F%A5%9A-Hatch-4051b5.svg
    :target: https://github.com/pypa/hatch
    :alt: Hatch project

Releases are done at Doug's discretion when significant pieces of development work have been
completed.

The release process steps are:

#. Use :command:`hatch version release` to bump the version from ``.devn`` to the next release
   version identifier

#. Confirm that :file:`docs/breaking_changes.rst` includes any relevant notes for the
   version being released

#. Commit the version bump and breaking changes log update

#. Create an annotated tag for the release with :guilabel:`Git -> New Tag...` in PyCharm
   or :command:`git tag -e -a vyy.n`

#. Push the version bump commit and tag to GitHub

#. Use the GitHub web interface to create a release,
   editing the auto-generated release notes into sections:

   * Features
   * Bug Fixes
   * Documentation
   * Maintenance
   * Dependency Updates

#. Use the GitHub :guilabel:`Issues -> Milestones` web interface to edit the release
   milestone:

   * Change the :guilabel:`Due date` to the release date
   * Delete the "when it's ready" comment in the :guilabel:`Description`

#. Use the GitHub :guilabel:`Issues -> Milestones` web interface to create a milestone for
   the next release:

   * Set the :guilabel:`Title` to the next release version,
     prepended with a ``v``;
     e.g. ``v23.1``
   * Set the :guilabel:`Due date` to the end of the year of the next release
   * Set the :guilabel:`Description` to something like
     ``v23.1 release - when it's ready :-)``
   * Create the next release milestone

#. Review the open issues,
   especially any that are associated with the milestone for the just released version,
   and update their milestone.

#. Close the milestone for the just released version.

#. Use :command:`hatch version minor,dev` to bump the version for the next development cycle,
   or use :command:`hatch version major,minor,dev` for a year rollover version bump

#. Commit the version bump

#. Push the version bump commit to GitHub
