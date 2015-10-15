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


.. _SalishSeaCmdSubcommands:

*********************************
:command:`salishsea` Sub-Commands
*********************************

The command :kbd:`salishsea --help` produces a list of the available :program:`salishsea` options and sub-commands:

.. code-block:: bash

    usage: salishsea [--version] [-v] [--log-file LOG_FILE] [-q] [-h] [--debug]

    Salish Sea NEMO Command Processor

    optional arguments:
      --version            show program's version number and exit
      -v, --verbose        Increase verbosity of output. Can be repeated.
      --log-file LOG_FILE  Specify a file to log output. Disabled by default.
      -q, --quiet          Suppress output except warnings and errors.
      -h, --help           Show this help message and exit.
      --debug              Show tracebacks on errors.

    Commands:
      combine        Combine per-processor files from an MPI NEMO run into single files
      complete       print bash completion command
      gather         Gather results from a NEMO run; includes combining MPI results files
      get_cgrf       Download and symlink CGRF atmospheric forcing files
      help           print detailed help for another command
      prepare        Prepare a Salish Sea NEMO run
      run            Prepare, execute, and gather results from a Salish Sea NEMO model run.

For details of the arguments and options for a sub-command use
:command:`salishsea help <sub-command>`.
For example:

.. code-block:: bash

    $ salishsea help run

    usage: salishsea run [-h] [--nemo3.4] [-q] [--compress] [--keep-proc-results]
                         [--compress-restart] [--delete-restart]
                         DESC_FILE IO_DEFS RESULTS_DIR

    Prepare, execute, and gather the results from a Salish Sea NEMO-3.6 run
    described in DESC_FILE and IO_DEFS. The results files from the run are
    gathered in RESULTS_DIR. If RESULTS_DIR does not exist it will be created.

    positional arguments:
      DESC_FILE            File path/name of run description YAML file
      IO_DEFS              File path/name of NEMO IOM server defs file for run
      RESULTS_DIR          directory to store results into

    optional arguments:
      -h, --help           show this help message and exit
      --nemo3.4            Do a NEMO-3.4 run; the default is to do a NEMO-3.6 run
      -q, --quiet          don't show the run directory path or job submission
                           message
      --compress           compress results files
      --keep-proc-results  don't delete per-processor results files
      --compress-restart   compress restart file(s)
      --delete-restart     delete restart file(s)

You can check what version of :program:`salishsea` you have installed with:

.. code-block:: bash

    salishsea --version


.. _salishsea-run:

:kbd:`run` Sub-command
======================

The :command:`salishsea run` command prepares,
executes,
and gathers the results from the Salish Sea NEMO run described in the specifed run description and IOM server definitions files.
The results are gathered in the specified results directory.

.. code-block:: bash

    usage: salishsea run [-h] [--nemo3.4] [-q] [--compress] [--keep-proc-results]
                         [--compress-restart] [--delete-restart]
                         DESC_FILE IO_DEFS RESULTS_DIR

    Prepare, execute, and gather the results from a Salish Sea NEMO-3.6 run
    described in DESC_FILE and IO_DEFS. The results files from the run are
    gathered in RESULTS_DIR. If RESULTS_DIR does not exist it will be created.

    positional arguments:
      DESC_FILE            File path/name of run description YAML file
      IO_DEFS              File path/name of NEMO IOM server defs file for run
      RESULTS_DIR          directory to store results into

    optional arguments:
      -h, --help           show this help message and exit
      --nemo3.4            Do a NEMO-3.4 run; the default is to do a NEMO-3.6 run
      -q, --quiet          don't show the run directory path or job submission
                           message
      --compress           compress results files
      --keep-proc-results  don't delete per-processor results files
      --compress-restart   compress restart file(s)
      --delete-restart     delete restart file(s)

The path to the run directory,
and the response from the job queue manager
(typically a job number)
are printed upon completion of the command.

The :command:`salishsea run` command does the following:

#. Execute the :ref:`salishsea-prepare` via the :ref:`SalishSeaCmdAPI` to set up a temporary run directory from which to execute the Salish Sea NEMO run.
#. Create a :file:`SalishSeaNEMO.sh` job script in the run directory.
   The job script runs NEMO and executes the :ref:`salishsea-gather` via the :ref:`SalishSeaCmdAPI` to collect the run results files into the results directory.
#. Submit the job script to the queue manager via :command:`qsub` on systems like :kbd:`salish.eos.ubc.ca`,
   :kbd:`jasper.westgrid.ca`,
   and :kbd:`orcinus.westgrid.ca` that use TORQUE/PBS schedulers.

See the :ref:`RunDescriptionFileStructure` section for details of the run description file.

The :command:`salishsea run` command concludes by printing the path to the run directory and the response from the job queue manager.
Example:

.. code-block:: bash

    $ salishsea run SalishSea.yaml iodef.xml ../../SalishSea/myrun

    salishsea_cmd.run INFO: salishsea_cmd.prepare Created run directory ../../SalishSea/38e87e0c-472d-11e3-9c8e-0025909a8461
    salishsea_cmd.run INFO: 3330782.orca2.ibb

If the :command:`salishsea run` command prints an error message,
you can get a Python traceback containing more information about the error by re-running the command with the :kbd:`--debug` flag.

.. _salishsea-prepare:

:kbd:`prepare` Sub-command
==========================

The :command:`salishsea prepare` command sets up a run directory from which to execute the Salish Sea NEMO run described in the specifed run description,
and IOM server definitions files:

.. code-block:: bash

    usage: salishsea prepare [-h] [--nemo3.4] [-q] DESC_FILE IO_DEFS

    Set up the Salish Sea NEMO described in DESC_FILE and print the path to the
    run directory.

    positional arguments:
      DESC_FILE    run description YAML file
      IO_DEFS      For NEMO-3.6 runs, the XIOS IO server file and contained
                   variable definitions for the run. For NEMO-3.4 runs, the IOM
                   server definitions file for run.

    optional arguments:
      -h, --help   show this help message and exit
      --nemo3.4    Prepare a NEMO-3.4 run; the default is to prepare a NEMO-3.6
                   run
      -q, --quiet  don't show the run directory path on completion

See the :ref:`RunDescriptionFileStructure` section for details of the run description file.

The :command:`salishsea prepare` command concludes by printing the path to the run directory it created.
Example:

.. code-block:: bash

    $ salishsea prepare SalishSea.yaml iodef.xml

    salishsea_cmd.prepare INFO: Created run directory ../../runs/SalishSea/38e87e0c-472d-11e3-9c8e-0025909a8461

The name of the run directory created is a `Universally Unique Identifier`_
(UUID)
string because the directory is intended to be ephemerally used for a single run.

.. _Universally Unique Identifier: https://en.wikipedia.org/wiki/Universally_unique_identifier

If the :command:`salishsea prepare` command prints an error message,
you can get a Python traceback containing more information about the error by re-running the command with the :kbd:`--debug` flag.


Run Directory Contents for NEMO-3.6
-----------------------------------

For NEMO-3.6 runs,
(initiated by :command:`salishsea run ...` or :command:`salishsea prepare ...` commands)
the run directory contains:

* The run description file provided on the command line.

* The XIOS IO server definitions file provided on the command line copied to a file called :file:`iodefs.xml`
  (the file name required by NEMO).
  That file specifies the output files and variables they contain for the run;
  it is also someimtes known as the NEMO IOM defs file.

* A :file:`namelist_cfg`
  (the file name required by NEMO)
  file that is constructed by concatenating the namelist segments listed in the run description file
  (see :ref:`RunDescriptionFileStructure`).

* A symlink to the :file:`NEMOGCM/CONFIG/SHARED/namelist_ref` file in the :kbd:`NEMO-code` directory specified in the :kbd:`paths` section of the run description file is also created to provide default values to be used for any namelist variables not included in the namelist segments listed in the run description file.

* A symlink called :file:`bathy_meter.nc`
  (the file name required by NEMO)
  to the bathymetry file specified in the :kbd:`grid` section of the run description file.

* A symlink called :file:`coordinates.nc`
  (the file name required by NEMO)
  to the grid coordinates file specified in the :kbd:`grid` section of the run description file.

* A file called :file:`domain_def.xml`
  (the file name required by NEMO)
  that contains the XIOS IO server domain definitions for the run that are specified in the :kbd:`output` section of the run description file.

* A file called :file:`field_def.xml`
  (the file name required by NEMO)
  that contains the XIOS IO server field definitions for the run that are specified in the :kbd:`output` section of the run description file.

* The :file:`nemo.exe` executable found in the :file:`BLD/bin/` directory of the NEMO configuration given by the :kbd:`config_name` and :kbd:`NEMO-code` keys in the run description file.
  :command:`salishsea prepare` aborts with an error message and exit code 2 if the :file:`nemo.exe` file is not found.
  In that case the run directory is not created.

* The :file:`xios_server.exe` executable found in the :file:`bin/` sub-directory of the directory given by the :kbd:`XIOS` key in the :kbd:`paths` section of the run description file.
  :command:`salishsea prepare` aborts with an error message and exit code 2 if the :file:`xios_server.exe` file is not found.
  In that case the run directory is not created.

The run directory also contains symbolic links to:

* The initial conditions,
  atmospheric,
  open boundary conditions,
  and rivers run-off forcing directories given in the :kbd:`forcing` section of the run description file.
  The initial conditions may be specified from a restart file instead of a directory of netCDF files,
  in which case the restart file is symlinked as :file:`restart.nc`
  (the file name required by NEMO).

Finally,
the run directory contains 3 files,
:file:`NEMO-code_rev.txt`,
:file:`NEMO-forcing_rev.txt`,
and :file:`XIOS-code_rev.txt` that contain the output of the :command:`hg parents` command executed in the directories given by the :kbd:`NEMO-code`,
:kbd:`forcing`,
and :kbd:`XIOS` keys in the :kbd:`paths` section of the run description file,
respectively.
Those file provide a record of the last committed changesets in each of those directories,
which is important reproducibility information for the run.


Run Directory Contents for NEMO-3.4
-----------------------------------

For NEMO-3.4 runs,
(initiated by :command:`salishsea run --nemo3.4 ...` or :command:`salishsea prepare --nemo3.4 ...` commands)
the run directory contains a :file:`namelist`
(the file name expected by NEMO)
file that is constructed by concatenating the namelist segments listed in the run description file
(see :ref:`RunDescriptionFileStructure`).
That constructed namelist is concluded with empty instances of all of the namelists that NEMO requires so that default values will be used for any namelist variables not included in the namelist segments listed in the run description file.

The run directory also contains symbolic links to:

* The run description file provided on the command line

* The :file:`namelist` file constructed from the namelists provided in the run description file

* The IOM server definitions files provided on the command line,
  aliased to :file:`iodefs.xml`,
  the file name expected by NEMO

* The :file:`xmlio_server.def` file found in the run-set directory where the run description file resides

* The :file:`nemo.exe` and :file:`server.exe` executables found in the :file:`BLD/bin/` directory of the NEMO configuration given by the :kbd:`config_name` and :kbd:`NEMO-code` keys in the run description file.
  :command:`salishsea prepare` aborts with an error message and exit code 2 if the :file:`nemo.exe` file is not found.
  In that case the run directory is not created.
  :command:`salishsea prepare` also check to confirm that :file:`server.exe` exists but only issues a warning if it is not found becuase that is a valid situation if you are not using :kbd:`key_iomput` in your configuration.

* The coordinates and bathymetry files given in the :kbd:`grid` section of the run description file

* The initial conditions,
  open boundary conditions,
  and rivers run-off forcing directories given in the :kbd:`forcing` section of the run description file.
  The initial conditions may be specified from a restart file instead of a directory of netCDF files,
  in which case the restart file is symlinked as :file:`restart.nc`,
  the file name expected by NEMO.


.. _salishsea-gather:

:kbd:`gather` Sub-command
=========================

The :command:`salishsea gather` command gather results from a Salish Sea NEMO run into a results directory.
Its operation includes running the :command:`salishsea combine` command to combine the pre-processor MPI results files.

.. code-block:: bash

    usage: salishsea gather [-h] [--compress] [--keep-proc-results]
                            [--compress-restart] [--delete-restart]
                            DESC_FILE RESULTS_DIR

    Gather the results files from a Salish Sea NEMO run described in DESC_FILE
    into files in RESULTS_DIR. The gathering process includes combining the per-
    processor results files, and deleting the per-processor files. If RESULTS_DIR
    does not exist it will be created.

    positional arguments:
      DESC_FILE            file path/name of run description YAML file
      RESULTS_DIR          directory to store results into

    optional arguments:
      -h, --help           show this help message and exit
      --compress           compress results files
      --keep-proc-results  don't delete per-processor results files
      --compress-restart   compress restart file(s)
      --delete-restart     delete restart file(s)

If the :command:`salishsea gather` command prints an error message,
you can get a Python traceback containing more information about the error by re-running the command with the :kbd:`--debug` flag.


.. _salishsea-get_cgrf:

:kbd:`get_cgrf` Sub-command
===========================

The :command:`salishsea get_cgrf` command downloads CGRF products atmospheric forcing files from Dalhousie rsync repository and symlinks them with the file names that NEMO expects:

.. code-block:: bash

    usage: salishsea get_cgrf [-h] [-d DAYS] [--user USERID] [--password PASSWD]
                              START_DATE

    Download CGRF products atmospheric forcing files from Dalhousie rsync
    repository and symlink with the file names that NEMO expects.

    positional arguments:
      START_DATE            1st date to download files for

    optional arguments:
      -h, --help            show this help message and exit
      -d DAYS, --days DAYS  Number of days to download; defaults to 1
      --user USERID         User id for Dalhousie CGRF rsync repository
      --password PASSWD     Passowrd for Dalhousie CGRF rsync repository

The command *must* be run in the :file:`/ocean/dlatorne/CGRF/` directory.

If the :command:`salishsea get_cgrf` command prints an error message,
you can get a Python traceback containing more information about the error by re-running the command with the :kbd:`--debug` flag.


.. _salishsea-combine:

:kbd:`combine` Sub-command
==========================

The :command:`salishsea combine` command is a legacy command that combines the per-processor results files from an MPI Salish Sea NEMO run.
Its operation is included in the :command:`salishsea gather` command.
