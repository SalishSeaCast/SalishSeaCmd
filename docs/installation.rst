.. Copyright 2013 – present by the SalishSeaCast Project Contributors
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

.. SPDX-License-Identifier: Apache-2.0


.. _SalishSeaCmdPackageInstallation:

*******************************************
:py:obj:`SalishSeaCmd` Package Installation
*******************************************

:py:obj:`SalishSeaCmd` is a Python package that provides the :program:`salishsea`
command-line tool for doing various operations associated with the
:ref:`SalishSeaNEMO` model.
It is an extension of the :py:obj`NEMO-Cmd` package customized for working with
the SalishSeaCast NEMO model.

These instructions assume that:

* You have an up to date clone of the :ref:`SalishSeaCmd-repo` repository.

* You have installed the Pixi_ package and environments manager
  (`installation instructions`_).

  .. _Pixi: https://pixi.prefix.dev/latest/
  .. _`installation instructions`: https://pixi.prefix.dev/latest/installation/

The packages that are required by :py:obj:`SalishSeaCmd` will be downloaded and linked into
a working environment the first time that you use a `Pixi`_ command in the :file:`SalishSeaCmd/` directory
(or a sub-directory).
Example:

.. code-block:: bash

    cd SalishSeaCmd
    pixi run salishsea help

For doing so it development,
testing,
and documentation of the :py:obj:`SalishSeaCmd` package,
please see the :ref:`SalishSeaCmdPackageDevelopment` section.
