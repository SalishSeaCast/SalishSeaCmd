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


.. _RunDescriptionFileStructure:

******************************
Run Description File Structure
******************************

:program:`salishsea` run description files are written in YAML_.
They contain key-value pairs that define the names and locations of files and directories that :program:`salishsea` uses to manage Salish Sea NEMO runs and their results.

.. _YAML: http://pyyaml.org/wiki/PyYAMLDocumentation

Run description files are typically stored in a sub-directory of your clone of the :ref:`SS-run-sets-repo`.


NEMO-3.6 Run Description File
=============================

Example (from :file:`SS-run-sets/SalishSea/nemo3.6/SalishSea.yaml`):

.. literalinclude:: SalishSea.yaml.example-NEMO-3.6
   :language: yaml

The meanings of the key-value pairs are:

:kbd:`config_name`
  The name of the NEMO configuration to use for runs.
  It is the name of a directory in :file:`NEMOGCM/CONFIG/` in the :kbd:`NEMO-3.6` code directory given by the :kbd:`NEMO` key in the :ref:`NEMO-3.6-Paths`.

:kbd:`MPI decomposition`
  Specify how the domain is to be distributed over the processors in the :kbd:`i` (longitude) and :kbd:`j` (latitude) directions;
  e.g. :kbd:`8x18`.
  Those values are used to set the :kbd:`namelist.compute nammpp` namelist :kbd:`jpni` and :kbd:`jpnj` values,
  to set the number of processors and nodes in the PBS script,
  and to tell the :program:`REBUILD_NEMO` tool how many files to process.

:kbd:`run_id`
   The job identifier that appears in the :command:`qstat` listing.

:kbd:`walltime`
  The wall-clock time requested for the run.
  It limits the time that the job will run for on all machines,
  and it also affects queue priority for runs on Westgrid machines.
  It is important to allow some buffer time when calculating your walltime limits to allow for indeterminancy of the NEMO run itself,
  as well as the time required to combine the per-processor results files into run results files at the end of the run.

:kbd:`email`
  The email address at which you want to receive notification of the beginning and end of execution of the run,
  as well as notification of abnormal abort messages.
  The email key is only required if the address is different than would be constructed by combining your user id on the machine that the job runs on with :kbd:`@eos.ubc.ca`.


.. _NEMO-3.6-Paths:

:kbd:`paths` Section
--------------------

The :kbd:`paths` section of the run description file is a collection of directory paths that :program:`salishsea` uses to find files in other repos that it needs.
The paths may be either absolute or relative.

:kbd:`NEMO-code`
  The path to the :ref:`NEMO-3.6-code-repo` clone where the NEMO executable for the run is to be found.

:kbd:`XIOS`
  The path to the :ref:`XIOS-repo` clone where the XIOS executable for the run is to be found.

:kbd:`forcing`
  The path to the :ref:`NEMO-forcing-repo` clone where the netCDF files for the grid coordinates,
  bathymetry,
  initial conditions,
  open boundary conditions,
  etc. are to be found.

:kbd:`runs directory`
  The path to the directory where run directories will be created by the :command:`salishsea run` (or :command:`salishsea prepare`) sub-command.


.. _NEMO-3.6-Grid:

:kbd:`grid` Section
-------------------

The :kbd:`grid` section of the run description file contains 2 key-value pairs that provide the names of the coordinates and bathymetry files to use for the run.
Those file are presumed to be in the :file:`grid/` directory of the :ref:`NEMO-forcing-repo` clone pointed to by the :kbd:`forcing` key in the :ref:`NEMO-3.6-Paths`.
If relative paths are given,
they are appended to the :file:`grid/` directory of the :kbd:`forcing` path.

:kbd:`coordinates`
  The name of the coordinates file to use for the run,
  typically :file:`coordinates_seagrid_SalishSea.nc`.

:kbd:`bathymetry`
  The name of the bathymetry file to use for the run,
  typically :file:`bathy_meter_SalishSea2.nc`.


.. _NEMO-3.6-Forcing:

:kbd:`forcing` Section
----------------------

The :kbd:`forcing` section of the run description file contains key-value pairss that provide the names of directories in the :ref:`NEMO-forcing-repo` pointed to by the :kbd:`forcing` key in the :ref:`NEMO-3.6-Paths` where initial conditions and forcing files are found.
Those directory names are expected to appear in the appropriate places in the namelists.
The paths may be either absolute or relative.
If relative,
the paths are appended to the :kbd:`forcing` path given in the :ref:`NEMO-3.6-Paths`.

:kbd:`atmospheric`
  The path to the :ref:`AtmosphericForcing` files.
  It is symlinked as :file:`NEMO-atmos/` in the run directory,
  and that directory name must be used in the :kbd:`namelist.surface namsbc_core` and :kbd:`namesbc_apr` namelist.

:kbd:`initial conditions`
  The path to the :ref:`NEMO-forcing` files.
  It is symlinked as :file:`initial_strat/` in the run directory,
  and that directory name must be used in the :kbd:`namlist.domain namtsd` namelist.

  The :kbd:`initial conditions` key can,
  alternatively,
  be used to give the path to and name of a restart file,
  e.g.:

  .. code-block:: yaml

      initial conditions: ../../SalishSea/results/50s_22-25Sep/SalishSea_00019008_restart.nc

  which will be symlinked in the run directory as :file:`restart.nc`.

:kbd:`open boundaries`
  The path to the :ref:`OBC` files.
  It is symlinked as :file:`open_boundaries/` in the run directory,
  and that directory name must be used in the :kbd:`namelist.lateral nambdy_dat` namelists.

:kbd:`rivers`
  The path to the :ref:`RiverInput` files.
  It is symlinked as :file:`rivers/` in the run directory,
  and that directory name must be used in the :kbd:`namlist.domain namsbc_rnf` namelist.


.. _NEMO-3.6-Namelists:

:kbd:`namelists` Section
------------------------

The :kbd:`namelists` section of the run description file contains a list of NEMO namelist section files that will be concatenated to construct the :file:`namelist_cfg`
(the file name required by NEMO)
file for the run.
The paths may be either absolute or relative.
If relative paths are given,
they are appended to the directory containing the run description file.

Namelist sections that are specific to the run such as :file:`namelist.time` where the starting and ending timesteps and the restart configuration are defined are typically stored in the same directory as the run description file.
That mean that they are simply listed by name in the :kbd:`namelists` section:

.. code-block:: yaml

    namelists:
      - namelist.time

On the other hand,
when you want to use a namelist section that contains the group's current consensus best values,
list it as a relative path from the location of your run description file to the "standard" nameslist section files in :file:`SS-run-sets/SalishSea/nemo3.6/`:

.. code-block:: yaml

    namlists:
      - ../../nemo3.6/namelist.bottom

The :file:`NEMOGCM/CONFIG/SHARED/namelist_ref` file is symlinked into the run directory to provide default values that will be used for any namelist variables not included in the namelist section files listed in the :kbd:`namelists` section.


.. _NEMO-3.6-Output:

:kbd:`output` Section
---------------------

The :kbd:`output` section of the run description file contains 2 key-value pairs that provide the names of the output domains and fields definitions files to be used by the XIOS server for the run.
The paths may be either absolute or relative.
If relative paths are given,
they are appended to the directory containing the run description file.

:kbd:`domain`
  The path and name of the :file:`domain_def.xml` output domains definitions file to use for the run.
  It is copied into the run directory as :file:`domain_def.xml`
  (the file name required by XIOS).
  The value is typically either:

  * a relative or absolute path to :file:`SS-run-sets/SalishSea/nemo3.6/domain_def.xml`
  * a relative or absolute run-specific output domains definitions file

:kbd:`fields`
  The path and name of the :file:`field_def.xml` output fields definitions file to use for the run.
  It is copied into the run directory as :file:`field_def.xml`
  (the file name required by XIOS).
  The value is typically a relative or absolute path to :file:`NEMO-3.6-code/NEMOGCM/CONFIG/SHARED/field_def.xml`.
