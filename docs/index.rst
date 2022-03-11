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


.. _SalishSeaCmdProcessor:

************************************
SalishSeaCast NEMO Command Processor
************************************

The SalishSeaCast NEMO command processor,
:program:`salishsea`,
is a command-line tool for doing various operations associated with the :ref:`SalishSeaNEMO` model.

The :kbd:`SalishSeaCmd` package is a Python 3 package.
It is developed and tested under Python 3.7 and should work with Python 3.5 and later.

This an extensible tool built on the OpenStack ``cliff``
(`Command Line Interface Formulation Framework`_)
package.
It is a NEMO domain-specific command processor tool for the :ref:`SalishSeaNEMO` that uses plug-ins from the `NEMO-Cmd`_ package.

.. _Command Line Interface Formulation Framework: https://docs.openstack.org/cliff/latest/
.. _NEMO-Cmd: https://github.com/SalishSeaCast/NEMO-Cmd


Contents
========

.. toctree::
   :maxdepth: 2

   installation
   breaking_changes
   subcommands
   run_description_file/index
   api
   development


Indices and Tables
------------------

* :ref:`genindex`
* :ref:`modindex`


License
=======

The SalishSeaCmd command processor code and documentation are copyright 2013 – present by the `SalishSeaCast Project Contributors`_ and The University of British Columbia.

.. _SalishSeaCast Project Contributors: https://github.com/SalishSeaCast/docs/blob/master/CONTRIBUTORS.rst

They are licensed under the Apache License, Version 2.0.
http://www.apache.org/licenses/LICENSE-2.0
Please see the LICENSE file for details of the license.
