.. Copyright 2013-2015 The Salish Sea MEOPAR conttributors
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


.. _SalishSeaCmdChangesThatBreakBackwardCompatibility:

*************************************************************
:kbd:`SalishSeaCmd` Changes That Break Backward Compatibility
*************************************************************

Version 2.0
===========

The following changes that were introduced in version 2.0 of the :kbd:`SalishSeaCmd` package are incompatible with earlier versions:

* The :kbd:`gather` and :kbd:`combine` sub-commands now take a :option:`--compress` command-line option to cause the results files to be :program:`gzip` compressed.
  Previously,
  :program:`gzip` compression was the default and the :option:`--no-compress` option was required to prevent it.
  The :kbd:`run`,
  :kbd:`gather`,
  and :kbd:`combine` sub-commands are now all consistent in defaulting to no compression of the results files.

* The run description file must now contain an :kbd:`MPI decomposition` key-value pair,
  for example:

  .. code-block:: yaml

      MPI decomposition: 8x18

  The value is used to write the correct MPI decomposition values into the :file:`namelist.compute` namelist section file.
  That means that it is no longer necessary to a collection of :file:`namelist.compute.*` files for different MPI decompositions.
  The value is also used to tell the :program:`REBUILD_NEMO` script how many results file sections to operate on.
