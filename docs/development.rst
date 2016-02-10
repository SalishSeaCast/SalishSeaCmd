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

.. note:: This section is work in progress.


.. _DevelopmentEnvironment:

Development Environment
=======================

The :kbd:`SalishSeaCmd` package is developed and tested using `Python`_ 3.4 or later.
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
