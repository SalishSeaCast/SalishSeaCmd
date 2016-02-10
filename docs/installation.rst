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


.. _SalishSeaCmdPackageInstallation:

****************************************
:kbd:`SalishSeaCmd` Package Installation
****************************************

:kbd:`SalishSeaCmd` is a Python 3 package that provides the :program:`salishsea` command-line tool for doing various operations associated with the :ref:`SalishSeaNEMO` model.

These instructions assume that:

* You have an up to date clone of the :ref:`tools-repo` repo
* You have the Python 3 version of :ref:`AnacondaPythonDistro` or `Miniconda`_ installed
* :file:`$HOME/anaconda3/bin` is included in your :envvar:`PATH` environment variable if your are using the :ref:`AnacondaPythonDistro`,
  or :file:`$HOME/miniconda3/bin` is included in your :envvar:`PATH` environment variable if your are using `Miniconda`_

.. _Miniconda: http://conda.pydata.org/miniconda.html

To install the :kbd:`SalishSeaCmd` package in your :kbd:`root` Anaconda or Miniconda environment use:

.. code-block:: bash

    $ cd tools
    $ pip install --editable SalishSeaTools
    $ pip install --editable SalishSeaCmd

The :option:`--editable` option in the :command:`pip install` commands installs the packages via symlinks so that :program:`salishsea` will be automatically updated as the repo evolves.

The :kbd:`SalishSeaCmd` package can also be installed in an isolated :program:`conda` environment.
The common use case for doing so it development,
testing,
and documentation of the package;
please see the :ref:`SalishSeaCmdPackageDevelopment` section for details.


.. _salishseaTabCompletion:

:kbd:`<TAB>` Completion
=======================

.. note::

    :kbd:`<TAB>` completion is only available in recent versions of :command:`bash`.
    The instructions below are only useful if you are working on Ubuntu 14.04 or later.

The :program:`salishsea` command line interface includes a sub-command that enables it to hook into the :program:`bash` :kbd:`<TAB>` completion machinery.
(:kbd:`<TAB>` completion or `command-line completion`_ is a shell feature whereby partially typed commands are filled out by the shell when the user presses the :kbd:`<TAB>` key.)
The :command:`salishsea complete` command prints a blob of :program:`bash` code that does the job,
so,
capturing that code and executing it with the :command:`eval` command will enable completion for :program:`salishsea` in your current shell session.
You can do that with the compound command:

.. code-block:: bash

    eval "$(salishsea complete)"

Including that line in your :file:`~/.bashrc` file will ensure that completion for :program:`salishsea` is available in every shell you launch.

.. _command-line completion: http://en.wikipedia.org/wiki/Command-line_completion
