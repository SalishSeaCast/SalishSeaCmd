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

.. image:: https://img.shields.io/badge/license-Apache%202-cb2533.svg
    :target: https://www.apache.org/licenses/LICENSE-2.0
    :alt: Licensed under the Apache License, Version 2.0
.. image:: https://img.shields.io/badge/Python-3.10%20%7C%203.11-blue?logo=python&label=Python&logoColor=gold
    :target: https://docs.python.org/3.11/
    :alt: Python Version
.. image:: https://img.shields.io/badge/version%20control-git-blue.svg?logo=github
    :target: https://github.com/SalishSeaCast/SalishSeaCmd
    :alt: Git on GitHub
.. image:: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white
    :target: https://github.com/pre-commit/pre-commit
    :alt: pre-commit
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://black.readthedocs.io/en/stable/
    :alt: The uncompromising Python code formatter
.. image:: https://readthedocs.org/projects/salishseacmd/badge/?version=latest
    :target: https://salishseacmd.readthedocs.io/en/latest/
    :alt: Documentation Status
.. image:: https://github.com/SalishSeaCast/SalishSeaCmd/workflows/sphinx-linkcheck/badge.svg
    :target: https://github.com/SalishSeaCast/SalishSeaCmd/actions?query=workflow%3Asphinx-linkcheck
    :alt: Sphinx linkcheck
.. image:: https://github.com/SalishSeaCast/SalishSeaCmd/workflows/pytest-with-coverage/badge.svg
    :target: https://github.com/SalishSeaCast/SalishSeaCmd/actions?query=workflow%3Apytest-with-coverage
    :alt: Pytest with Coverage Status
.. image:: https://codecov.io/gh/SalishSeaCast/SalishSeaCmd/branch/main/graph/badge.svg
    :target: https://app.codecov.io/gh/SalishSeaCast/SalishSeaCmd
    :alt: Codecov Testing Coverage Report
.. image:: https://github.com/SalishSeaCast/SalishSeaCmd/actions/workflows/codeql-analysis.yaml/badge.svg
      :target: https://github.com/SalishSeaCast/SalishSeaCmd/actions?query=workflow:codeql-analysis
      :alt: CodeQL analysis
.. image:: https://img.shields.io/github/issues/SalishSeaCast/SalishSeaCmd?logo=github
    :target: https://github.com/SalishSeaCast/SalishSeaCmd/issues
    :alt: Issue Tracker


.. _SalishSeaCmdPythonVersions:

Python Versions
===============

.. image:: https://img.shields.io/badge/Python-3.10%20%7C%203.11-blue?logo=python&label=Python&logoColor=gold
    :target: https://docs.python.org/3.11/
    :alt: Python Version

The :kbd:`SalishSeaCmd` package is developed using `Python`_ 3.11.
The minimum supported Python version is 3.10.
The :ref:`SalishSeaCmdContinuousIntegration` workflow on GitHub ensures that the package
is tested for all versions of Python>=3.10.
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

.. _Conda: https://conda.io/en/latest/
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
    :target: https://github.com/pre-commit/pre-commit
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
The output looks something like::

  Removing everything under '_build'...
  Running Sphinx v3.0.0
  making output directory... done
  loading intersphinx inventory from https://docs.python.org/3/objects.inv...
  loading intersphinx inventory from http://salishsea-meopar-docs.readthedocs.io/en/latest/objects.inv...
  loading intersphinx inventory from http://nemo-cmd.readthedocs.io/en/latest/objects.inv...
  intersphinx inventory has moved: http://nemo-cmd.readthedocs.io/en/latest/objects.inv -> https://nemo-cmd.readthedocs.io/en/latest/objects.inv
  intersphinx inventory has moved: http://salishsea-meopar-docs.readthedocs.io/en/latest/objects.inv -> https://salishsea-meopar-docs.readthedocs.io/en/latest/objects.inv
  building [mo]: targets for 0 po files that are out of date
  building [html]: targets for 10 source files that are out of date
  updating environment: [new config] 10 added, 0 changed, 0 removed
  reading sources... [100%] subcommands
  looking for now-outdated files... none found
  pickling environment... done
  checking consistency... done
  preparing documents... done
  writing output... [100%] subcommands
  generating indices...  genindexdone
  highlighting module code... [100%] salishsea_cmd.api
  writing additional pages...  searchdone
  copying static files... ... done
  copying extra files... done
  dumping search index in English (code: en)... done
  dumping object inventory... done
  build succeeded.

  Build finished. The HTML pages are in _build/html.


The HTML rendering of the docs ends up in :file:`docs/_build/html/`.
You can open the :file:`index.html` file in that directory tree in your browser to preview the results of the build before committing and pushing your changes to GitHub.

Whenever you push changes to the :ref:`SalishSeaCmd-repo` on GitHub the documentation is automatically re-built and rendered at https://salishseacmd.readthedocs.io/en/latest/.


.. _SalishSeaCmdLinkCheckingTheDocumentation:

Link Checking the Documentation
-------------------------------

.. image:: https://github.com/SalishSeaCast/SalishSeaCmd/workflows/sphinx-linkcheck/badge.svg
    :target: https://github.com/SalishSeaCast/SalishSeaCmd/actions?query=workflow%3Asphinx-linkcheck
    :alt: Sphinx linkcheck

Sphinx also provides a link checker utility which can be run to find broken or redirected links in the docs.
With your :kbd:`salishsea-cmd` environment activated,
use:

.. code-block:: bash

    (salishsea-cmd)$ cd SalishSeaCmd/docs/
    (salishsea-cmd) docs$ make linkcheck

The output looks something like::

  Removing everything under '_build'...
  Running Sphinx v3.3.1
  making output directory... done
  loading intersphinx inventory from https://docs.python.org/3/objects.inv...
  loading intersphinx inventory from https://salishsea-meopar-docs.readthedocs.io/en/latest/objects.inv...
  loading intersphinx inventory from https://nemo-cmd.readthedocs.io/en/latest/objects.inv...
  building [mo]: targets for 0 po files that are out of date
  building [linkcheck]: targets for 10 source files that are out of date
  updating environment: [new config] 10 added, 0 changed, 0 removed
  reading sources... [100%] subcommands
  looking for now-outdated files... none found
  pickling environment... done
  checking consistency... done
  preparing documents... done
  writing output... [ 10%] api
  (line   21) ok        https://docs.python.org/3/library/pathlib.html#pathlib.Path
  (line   21) ok        https://docs.python.org/3/library/pathlib.html#pathlib.Path
  (line   21) ok        https://docs.python.org/3/library/functions.html#int
  (line   21) ok        https://docs.python.org/3/library/pathlib.html#pathlib.Path
  (line   21) ok        https://docs.python.org/3/library/stdtypes.html#str
  (line   21) ok        https://docs.python.org/3/library/stdtypes.html#str
  (line   21) ok        https://docs.python.org/3/library/stdtypes.html#str
  (line   21) ok        https://docs.python.org/3/library/stdtypes.html#str
  (line   21) ok        https://docs.python.org/3/library/stdtypes.html#str
  (line   21) ok        https://docs.python.org/3/library/constants.html#None
  (line   21) ok        https://docs.python.org/3/library/constants.html#None
  (line   21) ok        https://docs.python.org/3/library/constants.html#None
  (line   21) ok        https://docs.python.org/3/library/stdtypes.html#dict
  (line   21) ok        https://docs.python.org/3/library/stdtypes.html#dict
  (line   21) ok        https://docs.python.org/3/library/stdtypes.html#dict
  writing output... [ 20%] breaking_changes
  (line   97) ok        https://docs.python.org/3/library/constants.html#False
  (line   45) ok        https://f90nml.readthedocs.io/en/latest/
  (line   30) ok        https://gitpython.readthedocs.io/en/stable/
  (line   91) ok        https://salishsea-meopar-docs.readthedocs.io/en/latest/code-notes/salishsea-nemo/land-processor-elimination/index.html#landprocessorelimination
  (line   53) ok        https://calver.org/
  writing output... [ 30%] development
  (line   21) ok        https://docs.python.org/3.11/
  (line   21) ok        https://black.readthedocs.io/en/stable/
  (line   21) ok        https://salishseacmd.readthedocs.io/en/latest/
  (line   21) ok        https://codecov.io/gh/SalishSeaCast/SalishSeaCmd
  (line   21) ok        https://github.com/SalishSeaCast/NEMO-Cmd/issues
  (line   58) ok        https://www.python.org/
  (line   58) ok        https://www.python.org/
  (line   21) ok        https://www.apache.org/licenses/LICENSE-2.0
  (line   58) ok        https://nemo-cmd.readthedocs.io/en/latest/development.html#nemo-cmdcontinuousintegration
  (line   80) ok        https://salishsea-meopar-docs.readthedocs.io/en/latest/repos_organization.html#salishseacmd-repo
  (line   21) ok        https://github.com/SalishSeaCast/SalishSeaCmd
  (line   94) ok        https://docs.github.com/en/free-pro-team@latest/github/authenticating-to-github/connecting-to-github-with-ssh
  (line  104) ok        https://salishsea-meopar-docs.readthedocs.io/en/latest/repos_organization.html#nemo-cmd-repo
  (line   74) ok        https://github.com/SalishSeaCast/SalishSeaCmd
  (line  109) ok        https://salishsea-meopar-docs.readthedocs.io/en/latest/work_env/anaconda_python.html#anacondapythondistro
  (line   80) ok        https://github.com/SalishSeaCast/SalishSeaCmd
  (line  143) ok        https://www.python.org/dev/peps/pep-0008/
  (line  179) ok        https://www.sphinx-doc.org/en/master/usage/restructuredtext/index.html
  (line  179) ok        https://www.sphinx-doc.org/en/master/
  (line  391) ok        https://docs.pytest.org/en/latest/
  (line  109) ok        https://conda.io/en/latest/
  (line  109) ok        https://docs.conda.io/en/latest/miniconda.html
  (line   21) ok        https://github.com/SalishSeaCast/SalishSeaCmd/actions?query=workflow%3Apytest-with-coverage
  (line  424) ok        https://pytest-cov.readthedocs.io/en/latest/
  (line  424) ok        https://coverage.readthedocs.io/en/latest/
  (line  469) ok        https://docs.github.com/en/free-pro-team@latest/actions
  (line  483) ok        https://git-scm.com/
  (line  449) ok        https://github.com/SalishSeaCast/SalishSeaCmd/actions?query=workflow%3Apytest-with-coverage
  (line  195) ok        https://readthedocs.org/projects/salishseacmd/builds/
  (line  458) ok        https://github.com/SalishSeaCast/SalishSeaCmd/actions
  (line  497) ok        https://github.com/SalishSeaCast/SalishSeaCmd/issues
  (line  491) ok        https://github.com/SalishSeaCast/SalishSeaCmd/issues
  (line   21) ok        https://img.shields.io/badge/license-Apache%202-cb2533.svg
  (line   21) ok        https://img.shields.io/badge/Python-3.10%20%7C%203.11-blue?logo=python&label=Python&logoColor=gold
  (line   21) ok        https://img.shields.io/badge/version%20control-git-blue.svg?logo=github
  (line   21) ok        https://img.shields.io/badge/code%20style-black-000000.svg
  (line   21) ok        https://codecov.io/gh/SalishSeaCast/SalishSeaCmd/branch/main/graph/badge.svg
  (line  509) ok        https://github.com/SalishSeaCast/docs/blob/main/CONTRIBUTORS.rst
  (line   21) ok        https://github.com/SalishSeaCast/SalishSeaCmd/workflows/pytest-with-coverage/badge.svg
  (line  458) ok        https://github.com/SalishSeaCast/SalishSeaCmd/commits/main
  (line   21) ok        https://readthedocs.org/projects/salishseacmd/badge/?version=latest
  (line  173) ok        https://readthedocs.org/projects/salishseacmd/badge/?version=latest
  (line   21) ok        https://img.shields.io/github/issues/SalishSeaCast/SalishSeaCmd?logo=github
  (line  491) ok        https://img.shields.io/github/issues/SalishSeaCast/SalishSeaCmd?logo=github
  writing output... [ 40%] index
  (line   23) ok        https://salishsea-meopar-docs.readthedocs.io/en/latest/code-notes/salishsea-nemo/index.html#salishseanemo
  (line   30) ok        https://salishsea-meopar-docs.readthedocs.io/en/latest/code-notes/salishsea-nemo/index.html#salishseanemo
  (line   30) ok        https://docs.openstack.org/cliff/latest/
  (line   30) ok        https://github.com/SalishSeaCast/NEMO-Cmd
  (line   67) ok        http://www.apache.org/licenses/LICENSE-2.0
  writing output... [ 50%] installation
  (line   63) ok        https://en.wikipedia.org/wiki/Command-line_completion
  writing output... [ 60%] run_description_file/3.6_agrif_yaml_file
  (line   24) ok        https://www-ljk.imag.fr/MOISE/AGRIF/index.html
  (line   27) ok        https://www-ljk.imag.fr/MOISE/AGRIF/index.html
  writing output... [ 70%] run_description_file/3.6_yaml_file
  (line  444) ok        https://docs.python.org/3/library/constants.html#True
  (line   89) ok        https://salishsea-meopar-docs.readthedocs.io/en/latest/repos_organization.html#nemo-3-6-code-repo
  (line  171) ok        https://salishsea-meopar-docs.readthedocs.io/en/latest/code-notes/salishsea-nemo/land-processor-elimination/index.html#preferred-mpi-lpe-decompositions
  (line  100) ok        https://salishsea-meopar-docs.readthedocs.io/en/latest/repos_organization.html#xios-repo
  (line   74) ok        https://slurm.schedmd.com/
  writing output... [ 80%] run_description_file/index
  (line   23) ok        https://pyyaml.org/wiki/PyYAMLDocumentation
  (line   28) ok        https://salishsea-meopar-docs.readthedocs.io/en/latest/repos_organization.html#ss-run-sets-repo
  writing output... [ 90%] run_description_file/segmented_runs
  writing output... [100%] subcommands
  (line  374) ok        https://nemo-cmd.readthedocs.io/en/latest/subcommands.html#nemo-combine
  (line  285) ok        https://en.wikipedia.org/wiki/Universally_unique_identifier
  (line  218) ok        https://nemo-cmd.readthedocs.io/en/latest/subcommands.html#nemo-deflate
  (line  396) ok        https://nemo-cmd.readthedocs.io/en/latest/subcommands.html#nemo-deflate
  (line  416) ok        https://nemo-cmd.readthedocs.io/en/latest/subcommands.html#nemo-gather
  (line  388) ok        https://github.com/SalishSeaCast/NEMO-Cmd/
  (line  408) ok        https://github.com/SalishSeaCast/NEMO-Cmd/
  (line  366) ok        https://github.com/SalishSeaCast/NEMO-Cmd/
  (line  428) ok        https://github.com/SalishSeaCast/SS-run-sets/blob/main/v201905/hindcast/file_def_dailysplit.xml

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
The output looks something like::

  ============================ test session starts =============================
  platform linux -- Python 3.8.2, pytest-5.4.1, py-1.8.1, pluggy-0.13.1
  Using --randomly-seed=1586216909
  rootdir: /media/doug/warehouse/MEOPAR/SalishSeaCmd
  plugins: randomly-3.2.1, cov-2.8.1
  collected 279 items

  tests/test_run.py ............................................................
  ..............................................................................
  ..............................................................................
  .............................                                           [ 87%]
  tests/test_api.py ......                                                [ 89%]
  tests/test_split_results.py ................                            [ 95%]
  tests/test_prepare.py ............                                      [100%]

  ============================ 279 passed in 1.96s =============================

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
    :target: https://github.com/SalishSeaCast/SalishSeaCmd/actions?query=workflow%3Apytest-with-coverage
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
