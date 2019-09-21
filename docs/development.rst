.. Copyright 2013-2019 The Salish Sea MEOPAR contributors
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


.. _SalishSeaCmdPackageDevelopment:

***************************************
:kbd:`SalishSeaCmd` Package Development
***************************************

.. image:: https://img.shields.io/badge/license-Apache%202-cb2533.svg
    :target: https://www.apache.org/licenses/LICENSE-2.0
    :alt: Licensed under the Apache License, Version 2.0
.. image:: https://img.shields.io/badge/python-3.5+-blue.svg
    :target: https://docs.python.org/3.7/
    :alt: Python Version
.. image:: https://img.shields.io/badge/version%20control-hg-blue.svg
    :target: https://bitbucket.org/salishsea/salishseacmd/
    :alt: Mercurial on Bitbucket
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://black.readthedocs.io/en/stable/
    :alt: The uncompromising Python code formatter
.. image:: https://readthedocs.org/projects/salishseacmd/badge/?version=latest
    :target: https://salishseacmd.readthedocs.io/en/latest/
    :alt: Documentation Status
.. image:: https://img.shields.io/bitbucket/issues/salishsea/salishseacmd.svg
    :target: https://bitbucket.org/salishsea/salishseacmd/issues?status=new&status=open
    :alt: Issue Tracker


.. _SalishSeaCmdPythonVersions:

Python Versions
===============

.. image:: https://img.shields.io/badge/python-3.5+-blue.svg
    :target: https://docs.python.org/3.7/
    :alt: Python Version

The :kbd:`SalishSeaCmd` package is developed and tested using `Python`_ 3.7 or later.
However,
the package must also run under `Python`_ 3.5 for use on the Westgrid :kbd:`orcinus` HPC platform.

.. _Python: https://www.python.org/


.. _SalishSeaCmdGettingTheCode:

Getting the Code
================

.. image:: https://img.shields.io/badge/version%20control-hg-blue.svg
    :target: https://bitbucket.org/salishsea/salishseacmd/
    :alt: Mercurial on Bitbucket

Clone the :ref:`SalishSeaCmd-repo` code and documentation `repository`_ from Bitbucket with:

.. _repository: https://bitbucket.org/salishsea/salishseacmd/

.. code-block:: bash

    $ hg clone ssh://hg@bitbucket.org/salishsea/salishseacmd SalishSeaCmd

or

.. code-block:: bash

    $ hg clone https://<your_userid>@bitbucket.org/salishsea/salishseacmd SalishSeaCmd

if you don't have `ssh key authentication`_ set up on Bitbucket.

.. _ssh key authentication: https://confluence.atlassian.com/bitbucket/set-up-ssh-for-mercurial-728138122.html


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

.. _Conda: http://conda.pydata.org/docs/
.. _Miniconda3: http://conda.pydata.org/docs/install/quick.html

.. code-block:: bash

    $ conda env create -f SalishSeaCmd/env/environment-dev.yaml
    $ source activate salishsea-cmd
    (salishsea-cmd)$ pip install --editable NEMO-Cmd
    (salishsea-cmd)$ pip install --editable SalishSeaCmd

The :kbd:`--editable` option in the :command:`pip install` commands above installs the :kbd:`NEMO-Cmd` package and the :kbd:`SalishSeaCmd` package via symlinks so that :program:`salishsea` in the :kbd:`salishsea-cmd` environment will be automatically updated as the repos evolve.

To deactivate the environment use:

.. code-block:: bash

    (salishsea-cmd)$ source deactivate


.. _SalishSeaCmdCodingStyle:

Coding Style
============

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://black.readthedocs.io/en/stable/
    :alt: The uncompromising Python code formatter

The :kbd:`SalishSeaCmd` package uses the `black`_ code formatting tool to maintain a coding style that is very close to `PEP 8`_.

.. _black: https://black.readthedocs.io/en/stable/
.. _PEP 8: https://www.python.org/dev/peps/pep-0008/

:command:`black` is installed as part of the :ref:`SalishSeaCmdDevelopmentEnvironment` setup.

To run :command:`black` on the entire code-base use:

.. code-block:: bash

    $ cd SalishSeaCmd
    $ conda activate salishsea-cmd
    (salishsea-cmd)$ black ./

in the repository root directory.
The output looks something like::

  reformatted /media/doug/warehouse/MEOPAR/SalishSeaCmd/salishsea_cmd/prepare.py
  reformatted /media/doug/warehouse/MEOPAR/SalishSeaCmd/tests/test_api.py
  reformatted /media/doug/warehouse/MEOPAR/SalishSeaCmd/salishsea_cmd/api.py
  reformatted /media/doug/warehouse/MEOPAR/SalishSeaCmd/tests/test_prepare.py
  reformatted /media/doug/warehouse/MEOPAR/SalishSeaCmd/salishsea_cmd/run.py
  reformatted /media/doug/warehouse/MEOPAR/SalishSeaCmd/tests/test_run.py
  All done! ✨ 🍰 ✨
  6 files reformatted, 5 files left unchanged.

.. _SalishSeaCmdBuildingTheDocumentation:

Building the Documentation
==========================

.. image:: https://readthedocs.org/projects/salishseacmd/badge/?version=latest
    :target: https://salishseacmd.readthedocs.io/en/latest/
    :alt: Documentation Status

The documentation for the :kbd:`SalishSeaCmd` package is written in `reStructuredText`_ and converted to HTML using `Sphinx`_.
Creating a :ref:`SalishSeaCmdDevelopmentEnvironment` as described above includes the installation of Sphinx.
Building the documentation is driven by :file:`docs/Makefile`.
With your :kbd:`salishsea-cmd` development environment activated,
use:

.. _reStructuredText: http://sphinx-doc.org/rest.html
.. _Sphinx: http://sphinx-doc.org/

.. code-block:: bash

    (salishsea-cmd)$ (cd docs && make clean html)

to do a clean build of the documentation.
The output looks something like::

  rm -rf _build/*
  sphinx-build -b html -d _build/doctrees   . _build/html
  Running Sphinx v1.6.3
  making output directory...
  loading pickled environment... not yet created
  loading intersphinx inventory from https://docs.python.org/3/objects.inv...
  loading intersphinx inventory from http://salishsea-meopar-docs.readthedocs.io/en/latest/objects.inv...
  loading intersphinx inventory from http://nemo-cmd.readthedocs.io/en/latest/objects.inv...
  building [mo]: targets for 0 po files that are out of date
  building [html]: targets for 10 source files that are out of date
  updating environment: 10 added, 0 changed, 0 removed
  reading sources... [100%] subcommands
  looking for now-outdated files... none found
  pickling environment... done
  checking consistency... done
  preparing documents... done
  writing output... [100%] subcommands
  generating indices... genindex
  highlighting module code... [100%] salishsea_cmd.api
  writing additional pages... search
  copying static files... done
  copying extra files... done
  dumping search index in English (code: en) ... done
  dumping object inventory... done
  build succeeded.

  Build finished. The HTML pages are in _build/html.


The HTML rendering of the docs ends up in :file:`docs/_build/html/`.
You can open the :file:`index.html` file in that directory tree in your browser to preview the results of the build before committing and pushing your changes to Bitbucket.

Whenever you push changes to the :ref:`SalishSeaCmd-repo` on Bitbucket the documentation is automatically re-built and rendered at https://salishseacmd.readthedocs.org/en/latest/.


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
    (salishsea-cmd)$ py.test

to run the test suite.
The output looks something like::

  ============================ test session starts =============================
  platform linux -- Python 3.6.2, pytest-3.2.1, py-1.4.34, pluggy-0.4.0
  rootdir: /media/doug/warehouse/MEOPAR/SalishSeaCmd, inifile:
  collected 182 items

  tests/test_api.py ........
  tests/test_lib.py .........
  tests/test_prepare.py ...............................................................................................
  tests/test_run.py ......................................................................

  ========================= 182 passed in 1.61 seconds =========================

You can monitor what lines of code the test suite exercises using the `coverage.py`_ tool with the command:

.. _coverage.py: https://coverage.readthedocs.org/en/latest/

.. code-block:: bash

    (salishsea-cmd)$ cd SalishSeaCmd/
    (salishsea-cmd)$ coverage run -m py.test

and generate a test coverage report with:

.. code-block:: bash

    (salishsea-cmd)$ coverage report

to produce a plain text report,
or

.. code-block:: bash

    (salishsea-cmd)$ coverage html

to produce an HTML report that you can view in your browser by opening :file:`SalishSeaCmd/htmlcov/index.html`.


Continuous Integration
----------------------

The :kbd:`SalishSeaCmd` package unit test suite is run and a coverage report is generated whenever changes are pushed to Bitbucket.
The results are visible on the `repo pipelines page`_,
from the :guilabel:`Builds` column on the `repo commits page`_,
or from a link in the build status area on the right side of the `repo summary page`_ .

.. _repo pipelines page: https://bitbucket.org/salishsea/salishseacmd/addon/pipelines/home
.. _repo commits page: https://bitbucket.org/salishsea/salishseacmd/commits/all
.. _repo summary page: https://bitbucket.org/salishsea/salishseacmd/


Pipelines Container Image
^^^^^^^^^^^^^^^^^^^^^^^^^

The Bitbucket pipelines configuration in :file:`bitbucket-pipelines.yml` uses a custom image that includes a :command:`conda` environment for running the test wuite with coverage analysis.
The image is defined and maintained using the :file:`Dockerfile` and :file:`environment-test.yaml` files in the :file:`pipelines-test-env/` directory.

To build or update the image and push it to Docker Hub use:

.. code-block:: bash

    docker build -t salishsea-cmd-test pipelines-test-env/
    docker tag salishsea-cmd-test:latest douglatornell/salishsea:salishsea-cmd-test
    docker push douglatornell/salishsea:salishsea-cmd-test


.. _SalishSeaCmdVersionControlRepository:

Version Control Repository
==========================

.. image:: https://img.shields.io/badge/version%20control-hg-blue.svg
    :target: https://bitbucket.org/salishsea/salishseacmd/
    :alt: Mercurial on Bitbucket

The :kbd:`SalishSeaCmd` package code and documentation source files are available in the :ref:`SalishSeaCmd-repo` `Mercurial`_ repository at https://bitbucket.org/salishsea/salishseacmd.

.. _Mercurial: https://www.mercurial-scm.org/


.. _SalishSeaCmdIssueTracker:

Issue Tracker
=============

.. image:: https://img.shields.io/bitbucket/issues/salishsea/salishseacmd.svg
    :target: https://bitbucket.org/salishsea/salishseacmd/issues?status=new&status=open
    :alt: Issue Tracker

Development tasks,
bug reports,
and enhancement ideas are recorded and managed in the issue tracker at https://bitbucket.org/salishsea/salishseacmd/issues.


License
=======

.. image:: https://img.shields.io/badge/license-Apache%202-cb2533.svg
    :target: https://www.apache.org/licenses/LICENSE-2.0
    :alt: Licensed under the Apache License, Version 2.0

The SalishSeaCast NEMO command processor and documentation are copyright 2013-2019 by the Salish Sea MEOPAR Project Contributors and The University of British Columbia.

They are licensed under the Apache License, Version 2.0.
https://www.apache.org/licenses/LICENSE-2.0
Please see the LICENSE file for details of the license.
