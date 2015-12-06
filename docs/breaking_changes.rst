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

Version 2.1
===========

The following changes that were introduced in version 2.1 of the :kbd:`SalishSeaCmd` package are incompatible with earlier versions:

* For NEMO-3.6 the :kbd:`namelists` section of the run description YAML file is now a dict of lists.
  The dict keys are the names of the :file:`namelist*_cfg` files to create and the element(s) of the list under each key are the namelist section files to be concatenated to create the file named by the key.
  For example:

  .. code-block:: yaml

      namelists:
        namelist_cfg:
          - namelist.time
          - namelist.domain
          - namelist.surface
          - namelist.lateral
          - namelist.bottom
          - namelist.tracer
          - namelist.dynamics
          - namelist.vertical
          - namelist.compute
        namelist_top_cfg:
          - namelist_top_cfg
        namelist_pisces_cfg:
          - namelist_pisces_cfg

  The :kbd:`namelist_cfg` key is required to create the basic namelist for running NEMO-3.6.
  Other :kbd:`namelist*_cfg` keys are optional.
  At least 1 namelist section file is required for each :kbd:`namelist*_cfg` key that is used.

  See :ref:`NEMO-3.6-Namelists` for details.

  For NEMO-3.4 the :kbd:`namelists` section remains a simple list of namelist section files,
  and construction of namelists for tracers,
  biology,
  etc. is not supported.

* The :py:func:`SalishSeaCmd.api.run_description` and :py:func:`SalishSeaCmd.api.run_in_subprocess` functions now accept a ::kbd:`nemo34` argument that defaults to :py:obj:`False`.
  That means that those functions now assume that their objective is a NEMO-3.6 run.


Version 2.0
===========

The following changes that were introduced in version 2.0 of the :kbd:`SalishSeaCmd` package are incompatible with earlier versions:

* The :kbd:`gather` and :kbd:`combine` sub-commands now take a :option:`--compress` command-line option to cause the results files to be :program:`gzip` compressed.
  Previously,
  :program:`gzip` compression was the default and the :option:`--no-compress` option was required to prevent it.
  The :kbd:`run`,
  :kbd:`gather`,
  and :kbd:`combine` sub-commands are now all consistent in defaulting to no compression of the results files.

* The run description YAML file must now contain an :kbd:`MPI decomposition` key-value pair,
  for example:

  .. code-block:: yaml

      MPI decomposition: 8x18

  The value is used to write the correct MPI decomposition values into the :file:`namelist.compute` namelist section file.
  That means that it is no longer necessary to a collection of :file:`namelist.compute.*` files for different MPI decompositions.
  The value is also used to tell the :program:`REBUILD_NEMO` script how many results file sections to operate on.
