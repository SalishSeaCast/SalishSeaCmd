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
|                            |      :target: https://docs.python.org/3.12/                                                                                                                                                          |
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


.. _SalishSeaCmdPythonVersions:

Python Versions
===============

.. image:: https://img.shields.io/python/required-version-toml?tomlFilePath=https://raw.githubusercontent.com/SalishSeaCast/SalishSeaCmd/main/pyproject.toml&logo=Python&logoColor=gold&label=Python
    :target: https://docs.python.org/3.12/
    :alt: Python Version from PEP 621 TOML

The :kbd:`SalishSeaCmd` package is developed using `Python`_ 3.12.
The minimum supported Python version is 3.11.
The :ref:`SalishSeaCmdContinuousIntegration` workflow on GitHub ensures that the package
is tested for all versions of Python>=3.11.
An old version of the package running under Python 3.5 is depoloyed on the
Westgrid :kbd:`orcinus` HPC platform.
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

    $ git clone git@github.com:SalishSeaCast/SalishSeaCmd.git


.. _SalishSeaCmdDevelopmentEnvironment:

Development Environment
=======================

The :kbd:`SalishSeaCmd` package depends on the :kbd:`NEMO-Cmd` package,
so you need to clone its repo,
:ref:`NEMO-Cmd-repo`,
beside your clone of :ref:`SalishSeaCmd-repo`.

Setting up an isolated development environment using `Conda`_ is recommended.
Assuming that you have :ref:`AnacondaPythonDistro` or `Miniconda3`_ installed,
you can create and activate an environment called :kbd:`salishsea-cmd` that will have all of the Python packages necessary for development,
testing,
and building the documentation with the commands:

.. _Conda: https://docs.conda.io/en/latest/
.. _Miniconda3: https://docs.conda.io/en/latest/miniconda.html

.. code-block:: bash

    $ conda env create -f SalishSeaCmd/envs/environment-dev.yaml
    $ conda activate salishsea-cmd
    (salishsea-cmd)$ pip install --editable NEMO-Cmd
    (salishsea-cmd)$ pip install --editable SalishSeaCmd

The :kbd:`--editable` option in the :command:`pip install` commands above installs the :kbd:`NEMO-Cmd` package and the :kbd:`SalishSeaCmd` packages via symlinks so that :program:`salishsea` in the :kbd:`salishsea-cmd` environment will be automatically updated as the repos evolve.

To deactivate the environment use:

.. code-block:: bash

    (salishsea-cmd)$ conda deactivate


.. _SalishSeaCmdCodingStyle:

Coding Style
============

.. image:: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white
    :target: https://pre-commit.com
    :alt: pre-commit
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://black.readthedocs.io/en/stable/
    :alt: The uncompromising Python code formatter

The ``SalishSeaCmd`` package uses Git pre-commit hooks managed by `pre-commit`_ to
maintain consistent code style and and other aspects of code,
docs,
and repo QA.

.. _pre-commit: https://pre-commit.com/

To install the `pre-commit` hooks in a newly cloned repo,
activate the conda development environment,
and run :command:`pre-commit install`:

.. code-block:: bash

    $ cd SalishSeaCmd
    $ conda activate nemo-cmd
    (nemo-cmd)$ pre-commit install

.. note::
    You only need to install the hooks once immediately after you make a new clone
    of the `SalishSeaCmd repository`_ and build your :ref:`SalishSeaCmdDevelopmentEnvironment`.

.. _SalishSeaCmd repository: https://github.com/SalishSeaCast/SalishSeaCmd


.. _SalishSeaCmdBuildingTheDocumentation:

Building the Documentation
==========================

.. image:: https://readthedocs.org/projects/salishseacmd/badge/?version=latest
    :target: https://salishseacmd.readthedocs.io/en/latest/
    :alt: Documentation Status

The documentation for the :kbd:`SalishSeaCmd` package is written in `reStructuredText`_ and converted to HTML using `Sphinx`_.

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

.. _build on readthedocs.org: https://readthedocs.org/projects/salishseacmd/builds/

* build the docs with your changes,
  and preview them in Firefox

* check the docs for broken links


.. _SalishSeaCmdBuildingAndPreviewingTheDocumentation:

Building and Previewing the Documentation
-----------------------------------------

Building the documentation is driven by :file:`docs/Makefile`.
With your :kbd:`salishsea-cmd` development environment activated,
use:

.. code-block:: bash

    (salishsea-cmd)$ (cd docs && make clean html)

to do a clean build of the documentation.
The output looks something like:

.. code-block:: text

    Removing everything under '_build'...
    Running Sphinx v8.1.3
    loading translations [en]... done
    making output directory... done
    Converting `source_suffix = '.rst'` to `source_suffix = {'.rst': 'restructuredtext'}`.
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
With your :kbd:`salishsea-cmd` environment activated,
use:

.. code-block:: bash

    (salishsea-cmd)$ cd SalishSeaCmd/docs/
    (salishsea-cmd) docs$ make linkcheck

The output looks something like:

.. code-block:: text

    Removing everything under '_build'...
    Running Sphinx v8.1.3
    loading translations [en]... done
    making output directory... done
    Converting `source_suffix = '.rst'` to `source_suffix = {'.rst': 'restructuredtext'}`.
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

    (     development: line   23) ok        https://black.readthedocs.io/en/stable/
    (     development: line   29) ok        https://codecov.io/gh/SalishSeaCast/SalishSeaCmd/branch/main/graph/badge.svg
    (     development: line  462) ok        https://coverage.readthedocs.io/en/latest/
    (     development: line   23) ok        https://app.codecov.io/gh/SalishSeaCast/SalishSeaCmd
    (     development: line  510) ok        https://docs.github.com/en/actions
    (     development: line  119) ok        https://docs.conda.io/en/latest/miniconda.html
    (     development: line  119) ok        https://docs.conda.io/en/latest/
    (breaking_changes: line  102) ok        https://calver.org/
    (     development: line   23) ok        https://docs.python.org/3.12/
    (             api: line   23) ok        https://docs.python.org/3/library/constants.html#None
    (breaking_changes: line  153) ok        https://docs.python.org/3/library/constants.html#False
    (run_description_file/3.6_yaml_file: line  446) ok        https://docs.python.org/3/library/constants.html#True
    (     development: line  429) ok        https://docs.pytest.org/en/latest/
    (             api: line   23) ok        https://docs.python.org/3/library/functions.html#int
    (             api: line   23) ok        https://docs.python.org/3/library/pathlib.html#pathlib.Path
    (           index: line   33) ok        https://docs.openstack.org/cliff/latest/
    (run_description_file/3.6_agrif_yaml_file: line   26) ok        https://agrif.imag.fr/
    (     subcommands: line  303) ok        https://en.wikipedia.org/wiki/Universally_unique_identifier
    (             api: line   23) ok        https://docs.python.org/3/library/stdtypes.html#str
    (             api: line   23) ok        https://docs.python.org/3/library/stdtypes.html#dict
    (breaking_changes: line   93) ok        https://f90nml.readthedocs.io/en/latest/
    (     development: line  525) ok        https://git-scm.com/
    (     subcommands: line  384) ok        https://github.com/SalishSeaCast/NEMO-Cmd/
    (           index: line   33) ok        https://github.com/SalishSeaCast/NEMO-Cmd
    (     subcommands: line  446) ok        https://github.com/SalishSeaCast/SS-run-sets/blob/main/v201905/hindcast/file_def_dailysplit.xml
    (     development: line   23) ok        https://github.com/SalishSeaCast/SalishSeaCmd
    (     development: line   32) ok        https://github.com/SalishSeaCast/SalishSeaCmd/actions/workflows/codeql-analysis.yaml/badge.svg
    (     development: line   39) ok        https://github.com/SalishSeaCast/SalishSeaCmd/actions/workflows/sphinx-linkcheck.yaml/badge.svg
    (     development: line   26) ok        https://github.com/SalishSeaCast/SalishSeaCmd/actions/workflows/pytest-with-coverage.yaml/badge.svg
    (     development: line  497) ok        https://github.com/SalishSeaCast/SalishSeaCmd/actions
    (     development: line   23) ok        https://github.com/SalishSeaCast/SalishSeaCmd/actions?query=workflow:CodeQL
    (     development: line  497) ok        https://github.com/SalishSeaCast/SalishSeaCmd/commits/main
    (     development: line   23) ok        https://github.com/SalishSeaCast/SalishSeaCmd/actions?query=workflow:sphinx-linkcheck
    (     development: line  419) ok        https://github.com/SalishSeaCast/SalishSeaCmd/actions?query=workflow%3Asphinx-linkcheck
    (     development: line   23) ok        https://github.com/SalishSeaCast/SalishSeaCmd/actions?query=workflow:pytest-with-coverage
    (     development: line  490) ok        https://github.com/SalishSeaCast/SalishSeaCmd/workflows/pytest-with-coverage/badge.svg
    (     development: line  285) ok        https://github.com/SalishSeaCast/SalishSeaCmd/workflows/sphinx-linkcheck/badge.svg
    (     development: line   23) ok        https://github.com/SalishSeaCast/SalishSeaCmd/issues
    (     development: line  551) ok        https://github.com/SalishSeaCast/docs/blob/main/CONTRIBUTORS.rst
    (breaking_changes: line   76) ok        https://gitpython.readthedocs.io/en/stable/
    (     development: line   65) ok        https://img.shields.io/badge/%F0%9F%A5%9A-Hatch-4051b5.svg
    (     development: line   53) ok        https://img.shields.io/badge/license-Apache%202-cb2533.svg
    (     development: line   59) ok        https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white
    (     development: line   62) ok        https://img.shields.io/badge/code%20style-black-000000.svg
    (     development: line   23) ok        https://github.com/SalishSeaCast/SalishSeaCmd/releases
    (     development: line   49) ok        https://img.shields.io/github/issues/SalishSeaCast/SalishSeaCmd?logo=github
    (     development: line   56) ok        https://img.shields.io/badge/version%20control-git-blue.svg?logo=github
    (     development: line   46) ok        https://img.shields.io/python/required-version-toml?tomlFilePath=https://raw.githubusercontent.com/SalishSeaCast/SalishSeaCmd/main/pyproject.toml&logo=Python&logoColor=gold&label=Python
    (     development: line   43) ok        https://img.shields.io/github/v/release/SalishSeaCast/SalishSeaCmd?logo=github
    (    installation: line   35) ok        https://github.com/conda-forge/miniforge
    (     development: line   23) ok        https://github.com/pypa/hatch
    (     subcommands: line  392) ok        https://nemo-cmd.readthedocs.io/en/latest/subcommands.html#nemo-combine
    (     subcommands: line  233) ok        https://nemo-cmd.readthedocs.io/en/latest/subcommands.html#nemo-deflate
    (     subcommands: line  434) ok        https://nemo-cmd.readthedocs.io/en/latest/subcommands.html#nemo-gather
    (run_description_file/index: line   25) ok        https://pyyaml.org/wiki/PyYAMLDocumentation
    (     development: line   23) ok        https://pre-commit.com
    (     development: line  462) ok        https://pytest-cov.readthedocs.io/en/latest/
    (           index: line   25) ok        https://salishsea-meopar-docs.readthedocs.io/en/latest/code-notes/salishsea-nemo/index.html#salishseanemo
    (     development: line  156) ok        https://pre-commit.com/
    (breaking_changes: line  145) ok        https://salishsea-meopar-docs.readthedocs.io/en/latest/code-notes/salishsea-nemo/land-processor-elimination/index.html#landprocessorelimination
    (     development: line   36) ok        https://readthedocs.org/projects/salishseacmd/badge/?version=latest
    (run_description_file/3.6_yaml_file: line  173) ok        https://salishsea-meopar-docs.readthedocs.io/en/latest/code-notes/salishsea-nemo/land-processor-elimination/index.html#preferred-mpi-lpe-decompositions
    (run_description_file/3.6_yaml_file: line   91) ok        https://salishsea-meopar-docs.readthedocs.io/en/latest/repos_organization.html#nemo-3-6-code-repo
    (     development: line  100) ok        https://salishsea-meopar-docs.readthedocs.io/en/latest/repos_organization.html#salishseacmd-repo
    (run_description_file/index: line   30) ok        https://salishsea-meopar-docs.readthedocs.io/en/latest/repos_organization.html#ss-run-sets-repo
    (     development: line  205) ok        https://readthedocs.org/projects/salishseacmd/builds/
    (run_description_file/3.6_yaml_file: line   76) ok        https://slurm.schedmd.com/
    (     development: line  119) ok        https://salishsea-meopar-docs.readthedocs.io/en/latest/work_env/anaconda_python.html#anacondapythondistro
    (     development: line   23) ok        https://www.apache.org/licenses/LICENSE-2.0
    (     development: line   80) ok        https://www.python.org/
    (     development: line   23) ok        https://salishseacmd.readthedocs.io/en/latest/
    (     development: line  189) ok        https://www.sphinx-doc.org/en/master/usage/restructuredtext/index.html
    (run_description_file/3.6_yaml_file: line  102) ok        https://salishsea-meopar-docs.readthedocs.io/en/latest/repos_organization.html#xios-repo
    (     development: line  114) ok        https://salishsea-meopar-docs.readthedocs.io/en/latest/repos_organization.html#nemo-cmd-repo
    (     development: line  189) ok        https://www.sphinx-doc.org/en/master/
    build succeeded.

    Look for any errors in the above output or in _build/linkcheck/output.txt

:command:`make linkcheck` is run monthly via a `scheduled GitHub Actions workflow`_

.. _scheduled GitHub Actions workflow: https://github.com/SalishSeaCast/SalishSeaCmd/actions?query=workflow%3Asphinx-linkcheck


.. _SalishSeaCmdRuningTheUnitTests:

Running the Unit Tests
======================

The test suite for the :kbd:`SalishSeaCmd` package is in :file:`SalishSeaCmd/tests/`.
The `pytest`_ tool is used for test fixtures and as the test runner for the suite.

.. _pytest: https://docs.pytest.org/en/latest/

With your :kbd:`salishsea-cmd` development environment activated,
use:

.. code-block:: bash

    (salishsea-cmd)$ cd SalishSeaCmd/
    (salishsea-cmd)$ pytest

to run the test suite.
The output looks something like:

.. code-block:: text

    =============================== test session starts ================================
    platform linux -- Python 3.12.7, pytest-8.3.3, pluggy-1.5.0
    Using --randomly-seed=363797280
    rootdir: /media/doug/warehouse/MEOPAR/SalishSeaCmd
    configfile: pytest.ini
    plugins: cov-5.0.0, anyio-4.6.2.post1, randomly-3.15.0
    collected 327 items

    tests/test_split_results.py ................                                   [  4%]
    tests/test_prepare.py ..............                                           [  9%]
    tests/test_api.py ......                                                       [ 11%]
    tests/test_run.py ...................................................................
    .....................................................................................
    .....................................................................................
    ...............................                                                [ 92%]
    .......................                                                        [100%]

    =============================== 327 passed in 2.53s ================================

You can monitor what lines of code the test suite exercises using the `coverage.py`_ and `pytest-cov`_ tools with the command:

.. _coverage.py: https://coverage.readthedocs.io/en/latest/
.. _pytest-cov: https://pytest-cov.readthedocs.io/en/latest/

.. code-block:: bash

    (salishsea-cmd)$ cd SalishSeaCmd/
    (salishsea-cmd)$ cpytest --cov=./

The test coverage report will be displayed below the test suite run output.

Alternatively,
you can use

.. code-block:: bash

    (salishsea-cmd)$ pytest --cov=./ --cov-report html

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

The :kbd:`SalishSeaCmd` package unit test suite is run and a coverage report is generated
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

The :kbd:`SalishSeaCmd` package code and documentation source files are available in the :ref:`SalishSeaCmd-repo` `Git`_ repository at https://github.com/SalishSeaCast/SalishSeaCmd.

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
   editing the auto-generated release notes as necessary

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
