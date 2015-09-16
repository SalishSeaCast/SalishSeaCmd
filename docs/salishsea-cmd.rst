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


.. _SalishSeaCmdProcessor:

*********************************
Salish Sea NEMO Command Processor
*********************************

The Salish Sea NEMO command processor,
:program:`salishsea`,
is a command line tool for doing various operations associated with the :ref:`SalishSeaNEMO` model.
It is provided by the :kbd:`SalishSeaCmd` package in the `tools repo`_.

.. _tools repo: https://bitbucket.org/salishsea/tools/

The :kbd:`SalishSeaCmd` package is a Python 3 package.
It was developed and tested under Python 3.4 and should work with that and later versions of Python.


Installation
============

These instructions assume that:

* You have an up to date clone of the `tools repo`_
* You have the :ref:`AnacondaPythonDistro` or `Miniconda`_ installed
* :file:`$HOME/anaconda3/bin` or :file:`$HOME/anaconda/bin` is included in your :envvar:`PATH` environment variable if your are using the :ref:`AnacondaPythonDistro`,
  or :file:`$HOME/miniconda3/bin` or :file:`$HOME/miniconda/bin` is included in your :envvar:`PATH` environment variable if your are using

.. _Miniconda: http://conda.pydata.org/miniconda.html

Use :program:`conda`
(the Miniconda/Anaconda package manager)
to create a :kbd:`salishsea-cmd` environment in which the :kbd:`SalishSeaCmd` package dependencies are installed:

.. code-block:: bash

    $ cd tools
    $ conda env create -f SalishSeaCmd/environment.yaml

Activate the :kbd:`salishsea-cmd` environment and install the :kbd:`SalishSeaTools` and :kbd:`SalishSeaCmd` packaged from the `tools repo`_ in editable mode so that :program:`salishsea` will be automatically updated as the repo evolves:

.. code-block:: bash

    $ source activate salishsea-cmd
    (salishsea-cmd)$ pip install --editable SalishSeaTools
    (salishsea-cmd)$ pip install --editable SalishSeaCmd


:kbd:`<TAB>` Completion
-----------------------

The :program:`salishsea` command line interface includes a sub-command that enables it to hook into the :program:`bash` :kbd:`<TAB>` completion machinery.
(:kbd:`<TAB>` completion or `command-line completion`_ is a shell feature whereby partially typed commands are filled out by the shell when the user presses the :kbd:`<TAB>` key.)
The :command:`salishsea complete` command prints a blob of :program:`bash` code that does the job,
so,
capturing that code in a file and then executing it with the :command:`source` command will enable completion for :program:`salishsea` in your current shell session.
You can do that with the compound command:

.. code-block:: bash

    salishsea complete > foo.sh && source foo.sh && rm -f foo.sh

Including that line in your :file:`~/.bashrc` file will ensure that completion for :program:`salishsea` is available in every shell you launch.

.. _command-line completion: http://en.wikipedia.org/wiki/Command-line_completion


Available Commands
==================

The command :kbd:`salishsea --help` produces a list of the available :program:`salishsea` options and sub-commands:

.. code-block:: bash

    usage: salishsea [--version] [-v] [--log-file LOG_FILE] [-q] [-h] [--debug]

    Salish Sea NEMO Command Processor

    optional arguments:
      --version            show program's version number and exit
      -v, --verbose        Increase verbosity of output. Can be repeated.
      --log-file LOG_FILE  Specify a file to log output. Disabled by default.
      -q, --quiet          suppress output except warnings and errors
      -h, --help           show this help message and exit
      --debug              show tracebacks on errors

    Commands:
      combine        Combine per-processor files from an MPI NEMO run into single files
      complete       print bash completion command
      gather         Gather results from a NEMO run; includes combining MPI results files
      get_cgrf       Download and symlink CGRF atmospheric forcing files
      help           print detailed help for another command
      prepare        Prepare a Salish Sea NEMO run
      run            Prepare, execute, and gather results from a Salish Sea NEMO model run

For details of the arguments and options for a sub-command use
:command:`salishsea help <sub-command>`.
For example:

.. code-block:: bash

    salishsea help run

    usage: salishsea run [-h] [-q] [--compress] [--keep-proc-results]
                         [--compress-restart] [--delete-restart]
                         DESC_FILE IO_DEFS RESULTS_DIR

    Prepare, execute, and gather the results from a Salish Sea NEMO run described
    in DESC_FILE and IO_DEFS. The results files from the run are gathered in
    RESULTS_DIR. If RESULTS_DIR does not exist it will be created.

    positional arguments:
      DESC_FILE            run description YAML file
      IO_DEFS              NEMO IOM server defs file for run
      RESULTS_DIR          directory to store results into

    optional arguments:
      -h, --help           show this help message and exit
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
----------------------

The :command:`salishsea run` command prepares,
executes,
and gathers the results from the Salish Sea NEMO run described in the specifed run description and IOM server definitions files.
The results are gathered in the specified results directory.

.. code-block:: bash

    usage: salishsea run [-h] [-q] [--compress] [--keep-proc-results]
                         [--compress-restart] [--delete-restart]
                         DESC_FILE IO_DEFS RESULTS_DIR

    Prepare, execute, and gather the results from a Salish Sea NEMO run described
    in DESC_FILE and IO_DEFS. The results files from the run are gathered in
    RESULTS_DIR. If RESULTS_DIR does not exist it will be created.

    positional arguments:
      DESC_FILE            run description YAML file
      IO_DEFS              NEMO IOM server defs file for run
      RESULTS_DIR          directory to store results into

    optional arguments:
      -h, --help           show this help message and exit
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

#. Execute the :ref:`salishsea-prepare` via the :ref:`salishsea-api` to sets up a temporary run directory from which to execute the Salish Sea NEMO run.
#. Create a :file:`SalishSeaNEMO.sh` job script in the run directory.
   The job script runs NEMO and executes the :ref:`salishsea-gather` via the :ref:`salishsea-api` to collect the run results files into the results directory.
#. Submit the job script to the queue manager via :command:`qsub` on systems like :kbd:`jasper.westgrid.ca` and :kbd:`orcinus.westgrid.ca` that use TORQUE/PBS schedulers,
   or via :command:`at` on other systems.

See the :ref:`RunDescriptionFileStructure` section for details of the run description file.

The :command:`salishsea run` command concludes by printing the path to the run directory and the response from the job queue manager.
Example:

.. code-block:: bash

    salishsea run SalishSea.yaml iodef.xml ../../SalishSea/myrun

    salishsea_cmd.prepare Created run directory ../../SalishSea/38e87e0c-472d-11e3-9c8e-0025909a8461
    salishsea_cmd.run INFO: 3330782.orca2.ibb

If the :command:`salishsea run` command prints an error message,
you can get a Python traceback containing more information about the error by re-running the command with the :kbd:`--debug` flag.

.. _salishsea-prepare:

:kbd:`prepare` Sub-command
--------------------------

The :command:`salishsea prepare` command sets up a run directory from which to execute the Salish Sea NEMO run described in the specifed run description,
and IOM server definitions files:

.. code-block:: bash

    usage: salishsea prepare [-h] [-q] DESC_FILE IO_DEFS

    Set up the Salish Sea NEMO run described in DESC_FILE and print the path to
    the run directory.

    positional arguments:
      DESC_FILE    run description YAML file
      IO_DEFS      NEMO IOM server defs file for run

    optional arguments:
      -h, --help   show this help message and exit
      -q, --quiet  don't show the run directory path on completion

The path to the run directory is printed upon completion of the command.

The name of the run directory created is a Universally Unique Identifier
(UUID)
string because the directory is intended to be ephemerally used for a single run.

The run directory contains a :file:`namelist`
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

See the :ref:`RunDescriptionFileStructure` section for details of the run description file.

The :command:`salishsea prepare` command concludes by printing the path to the run directory it created.
Example:

.. code-block:: bash

    salishsea prepare SalishSea.yaml iodef.xml
    salishsea_cmd.prepare INFO: Created run directory ../../runs/SalishSea/38e87e0c-472d-11e3-9c8e-0025909a8461

If the :command:`salishsea prepare` command prints an error message,
you can get a Python traceback containing more information about the error by re-running the command with the :kbd:`--debug` flag.


.. _salishsea-gather:

:kbd:`gather` Sub-command
-------------------------

The :command:`salishsea gather` command gather results from a Salish Sea NEMO run into a results directory.
Its operation includes running the :command:`salishsea combine` command to combine the pre-processor MPI results files.

.. code-block:: bash

    usage: salishsea gather [-h] [--keep-proc-results] [--no-compress]
                            [--compress-restart] [--delete-restart]
                            DESC_FILE RESULTS_DIR

    Gather the results files from a Salish Sea NEMO run described in DESC_FILE
    into files in RESULTS_DIR. The gathering process includes combining the per-
    processor results files, compressing them using gzip and deleting the per-
    processor files. If RESULTS_DIR does not exist it will be created.

    positional arguments:
      DESC_FILE            run description YAML file
      RESULTS_DIR          directory to store results into

    optional arguments:
      -h, --help           show this help message and exit
      --keep-proc-results  don't delete per-processor results files
      --no-compress        don't compress results files
      --compress-restart   compress restart file(s)
      --delete-restart     delete restart file(s)

If the :command:`salishsea gather` command prints an error message,
you can get a Python traceback containing more information about the error by re-running the command with the :kbd:`--debug` flag.


.. _salishsea-get_cgrf:

:kbd:`get_cgrf` Sub-command
---------------------------

The :command:`salishsea get_cgrf` command downloads CGRF products atmospheric forcing files from Dalhousie rsync
repository and symlink with the file names that NEMO expects:

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
--------------------------

The :command:`salishsea combine` command is a legacy command that combines the per-processor results files from an MPI Salish Sea NEMO run.
Its operation is included in the :command:`salishsea gather` command.


.. _RunDescriptionFileStructure:

Run Description File Structure
==============================

:program:`salishsea` run description files are written in YAML_.
They contain key-value pairs that define the names and locations of files and directories that :program:`salishsea` uses to manage Salish Sea NEMO runs and their results.

.. _YAML: http://pyyaml.org/wiki/PyYAMLDocumentation

Example:

.. literalinclude:: SalishSea.yaml.example
   :language: yaml

The value associated with the :kbd:`config_name` key is the name of the NEMO configuration to use for runs.
It is the name of a directory in :file:`NEMO-code/NEMOGCM/CONFIG/`.

The values associated with the :kbd:`run_id`,
:kbd:`walltime`,
and :kbd:`email` keys are used by the :command:`salishsea run` command in the :file:`SalishSeaNEMO.sh` TORQUE/PBS job scripts that it creates and submits to the job scheduler via :command:`qsub`.

* The :kbd:`run_id` value is the job identifier that appears in the :command:`qstat` listing.

* The :kbd:`walltime` value is the wall-clock time requested for the run.
  It limits the time that the job will run for on all machines,
  and it also affects queue priority for runs on Westgrid machines.
  On :kbd:`salish` with 4x4 = 16 cores
  (i.e. :file:`namelist.compute.4x4`)
  about 22 minutes of compute time are required per hour of model time.
  `Benchmark tests`_ on :kbd:`jasper.westgrid.ca` and :kbd:`orcinus.westgrid.ca` in Jun-2014 indicate that 12x27 = 324 processors
  (i.e. :file:`namelist.compute.12x27`)
  produces optimal processor use and about 1 minute of compute time is required per hour of model time.
  It is recommended to allow some buffer time when calculating your walltime limits to allow for indeterminancy,
  and the time required to combine the per-processor results files into run results files at the end of the run.
  Examples of recommended walltime values are:

  ============  ============================  ===============
  Run Duration  :kbd:`jasper`/:kbd:`orcinus`  :kbd:`salish`
  ============  ============================  ===============
  6 hours       :kbd:`0:15:00`                :kbd:`2:30:00`
  1 day         :kbd:`1:00:00`                :kbd:`10:00:00`
  5 days        :kbd:`3:00:00`                :kbd:`48:00:00`
  10 days       :kbd:`6:00:00`                :kbd:`90:00:00`
  ============  ============================  ===============

  .. _Benchmark tests: http://nbviewer.ipython.org/gist/douglatornell/9e140cb555c07344b2e4

* The :kbd:`nodes` and :kbd:`processors_per_node` values are the number of nodes and number of processors per node to use on :kbd:`jasper.westgrid.ca` where preference is given to jobs that use entire nodes.
  For 12x27 = 324 processors
  (i.e. :file:`namelist.compute.12x27`)
  runs the appropriate values are:

  .. code-block:: yaml

      nodes: 27
      processors_per_node: 12

* The :kbd:`email`: value is the email address at which you want to receive notification of the beginning and end of execution of the run,
  as well as notification of abnormal abort messages.
  The email key is only required if the address is different than would be constructed by combining your user id on the machine that the job runs on with :kbd:`@eos.ubc.ca`.

All other values for the :file:`SalishSeaNEMO.sh` job scripts that :command:`salishsea run` creates are read from the namelist or otherwise calculated.

The :kbd:`paths` section of the run description file is a collection of directory paths that :program:`salishsea` uses to find files in other repos that it needs.
The paths may be either absolute or relative.

* The value associated with the :kbd:`NEMO-code` key is the path to the :ref:`NEMO-code-repo` clone where the NEMO executable,
  etc. for the run are to be found.

* The :kbd:`forcing` key value is the path to the :ref:`NEMO-forcing-repo` clone where the netCDF files for the grid coordinates,
  bathymetry,
  initial conditions,
  open boundary conditions,
  etc. are found.

* The :kbd:`runs directory` key gives the path to the directory where run directories will be created by the :command:`salishsea run` (or :command:`salishsea prepare`) sub-command.

The :kbd:`grid` section of the file contains 2 keys that provide the names of the coordinates and bathymetry files to use for the run.
Those file are presumed to be in the :file:`grid/` directory of the :ref:`NEMO-forcing-repo` clone pointed to by the :kbd:`forcing` key in the :kbd:`paths` section.

The :kbd:`forcing` section of the run description file contains 3 keys that provide the names of directories in the :ref:`NEMO-forcing-repo` where initial conditions and forcing files are found.
Those directory names are used in the appropriate places in the namelist.

The value associated with the :kbd:`atmospheric` key is the path to the :ref:`AtmosphericForcing` files.
It is symlinked as :file:`NEMO-atmos/` in the run directory,
and that directory name is used on the :kbd:`namsbc_core` namelist.

The :kbd:`initial conditions` key can,
alternatively,
be used to give the path to and name of a restart file,
e.g.:

.. code-block:: yaml

    initial conditions: ../../SalishSea/results/50s_22-25Sep/SalishSea_00019008_restart.nc

which will be symlinked in the run directory as :file:`restart.nc`.

The :kbd:`namelists` section of the run description file contains a list of NEMO namelist segments that will be concatenated to construct the :file:`namelist` file for the run.
That constructed :file:`namelist` is concluded with empty instances of all of the namelists that NEMO requires so that default values will be used for any namelist variables not included in the namelist segments listed in the run description file.
The blob of empty namelist instances is defined as a constant in the :py:mod:`salishsea_cmd.prepare_processor` module in the :py:mod:`SalishSeaCmd` package.


.. _salishsea-api:

API
===

This section documents the Salish Sea Nemo command processor Application Programming Interface (API).
The API provides Python function interfaces to command processor sub-commands for use in other sub-command processor modules,
and by other software.

.. autofunction:: api.combine

.. autofunction:: api.prepare

.. autofunction:: api.run_description

.. autofunction:: api.run_in_subprocess
