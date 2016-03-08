.. Copyright 2013-2016 The Salish Sea MEOPAR conttributors
.. and The University of British Columbia
..
.. Licensed under the Apache License, Version 2.0 (the "License");
.. you may not use this file except in compliance with the License.
.. You may obtain a copy of the License at
..
..    http://www.apache.org/licenses/LICENSE-2.0
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

.. _SalishSeaCmdPythonVersions:

Python Versions
===============

The :kbd:`SalishSeaCmd` package is developed and tested using `Python`_ 3.5 or later.
However,
the package must also run under `Python`_ 2.7 for use on the Westgrid HPC platform.


.. _SalishSeaCmdGettingTheCode:

Getting the Code
================

Clone the :ref:`tools-repo` code and documentation `repository`_ from Bitbucket with:

.. _repository: https://bitbucket.org/salishsea/tools/

.. code-block:: bash

    $ hg clone ssh://hg@bitbucket.org/salishsea/tools

or

.. code-block:: bash

    $ hg clone https://<your_userid>@bitbucket.org/salishsea/tools

if you don't have `ssh key authentication`_ set up on Bitbucket.

.. _ssh key authentication: https://confluence.atlassian.com/bitbucket/set-up-ssh-for-mercurial-728138122.html


.. _SalishSeaCmdDevelopmentEnvironment:

Development Environment
=======================

Setting up an isolated development environment using `Conda`_ is recommended.
Assuming that you have :ref:`AnacondaPythonDistro` or `Miniconda3`_ installed,
you can create and activate an environment called :kbd:`salishsea-cmd` that will have all of the Python packages necessary for development,
testing,
and building the documentation with the commands:

.. _Python: https://www.python.org/
.. _Conda: http://conda.pydata.org/docs/
.. _Miniconda3: http://conda.pydata.org/docs/install/quick.html

.. code-block:: bash

    $ cd tools
    $ conda env create -f SalishSeaCmd/environment.yaml
    $ source activate salishsea-cmd
    (salishsea-cmd)$ pip install --editable SalishSeaTools
    (salishsea-cmd)$ pip install --editable SalishSeaCmd

The :option:`--editable` option in the :command:`pip install` commands above installs the :kbd:`SalishSeaTools` and :kbd:`SalishSeaCmd` packaged from the :ref:`tools-repo` via symlinks so that :program:`salishsea` in the :kbd:`salishsea-cmd` environment will be automatically updated as the repo evolves.

To deactivate the environment use:

.. code-block:: bash

    (salishsea-cmd)$ source deactivate


.. _SalishSeaCmdBuildingTheDocumentation:

Building the Documentation
==========================

The documentation for the :kbd:`SalishSeaCmd` package is written in `reStructuredText`_ and converted to HTML using `Sphinx`_.
Creating a :ref:`SalishSeaCmdDevelopmentEnvironment` as described above includes the installation of Sphinx.
The documentation is integrated into the :ref:`tools-repo` docs.
Building the documentation is driven by :file:`tools/docs/Makefile`.
With your :kbd:`salishsea-cmd` development environment activated,
use:

.. _reStructuredText: http://sphinx-doc.org/rest.html
.. _Sphinx: http://sphinx-doc.org/

.. code-block:: bash

    (salishsea-cmd)$ cd tools
    (salishsea-cmd)$ (cd docs && make clean html)

to do a clean build of the documentation.
The output looks something like::

  rm -rf _build/*
  sphinx-build -b html -d _build/doctrees   . _build/html
  Running Sphinx v1.3.1
  making output directory...
  loading pickled environment... not yet created
  loading intersphinx inventory from http://salishsea-meopar-docs.readthedocs.org/en/latest/objects.inv...
  building [mo]: targets for 0 po files that are out of date
  building [html]: targets for 36 source files that are out of date
  updating environment: 36 added, 0 changed, 0 removed
  reading sources... [100%] results_server/nowcast-green
  looking for now-outdated files... none found
  pickling environment... done
  done
  preparing documents... done
  writing output... [100%] results_server/nowcast-green
  generating indices...
  highlighting module code... [100%] salishsea_tools.tidetools
  writing additional pages... search
  copying static files... done
  copying extra files... done
  dumping search index in English (code: en) ... done
  dumping object inventory... done
  build succeeded.

  Build finished. The HTML pages are in _build/html.

The HTML rendering of the docs ends up in :file:`tools/docs/_build/html/`.
You can open the :file:`SalishSeaCmd/index.html` file in that directory tree in your browser to preview the results of the build before committing and pushing your changes to Bitbucket.

Whenever you push changes to the :ref:`tools-repo` on Bitbucket the documentation is automatically re-built and rendered at https://salishsea-meopar-tools.readthedocs.org/en/latest/SalishSeaCmd/.


.. _SalishSeaCmdRuningTheUnitTests:

Running the Unit Tests
======================

The test suite for the :kbd:`SalishSeaCmd` package is in :file:`tools/SalishSeaCmd/tests/`.
The `pytest`_ tools is used for test fixtures and as the test runner for the suite.

.. _pytest: http://pytest.org/latest/

With your :kbd:`salishsea-cmd` development environment activated,
use:

.. _Mercurial: http://mercurial.selenic.com/

.. code-block:: bash

    (salishsea-cmd)$ cd tools/SalishSeaCmd/
    (salishsea-cmd)$ py.test

to run the test suite.
The output looks something like::

  ============================ test session starts =============================
  platform linux -- Python 3.5.1, pytest-2.8.1, py-1.4.30, pluggy-0.3.1
  rootdir: /home/doug/Documents/MEOPAR/tools/SalishSeaCmd, inifile:
  collected 116 items

  tests/test_api.py ................
  tests/test_combine.py .............
  tests/test_gather.py .
  tests/test_get_cgrf.py .............
  tests/test_prepare.py ......................................................
  tests/test_run.py ...................

  ========================= 116 passed in 1.37 seconds =========================

You can monitor what lines of code the test suite exercises using the `coverage.py`_ tool with the command:

.. _coverage.py: https://coverage.readthedocs.org/en/latest/

.. code-block:: bash

    (salishsea-cmd)$ cd tools/SalishSeaCmd/
    (salishsea-cmd)$ coverage run -m py.test

and generate a test coverage report with:

.. code-block:: bash

    (salishsea-cmd)$ coverage report

to produce a plain text report,
or

.. code-block:: bash

    (salishsea-cmd)$ coverage html

to produce an HTML report that you can view in your browser by opening :file:`tools/SalishSeaCmd/htmlcov/index.html`.

The run the test suite under Python 2.7,
create a Python 2.7 :ref:`SalishSeaCmdDevelopmentEnvironment`.


.. _SalishSeaCmdVersionControlRepository:

Version Control Repository
==========================

The :kbd:`SalishSeaCmd` package code and documentation source files are available as part of the :ref:`tools-repo` `Mercurial`_ repository at https://bitbucket.org/salishsea/tools.


.. _SalishSeaCmdIssueTracker:

Issue Tracker
=============

Development tasks,
bug reports,
and enhancement ideas are recorded and managed in the issue tracker at https://bitbucket.org/salishsea/tools/issues using the component tag :kbd:`SalishSeaCmd`.
