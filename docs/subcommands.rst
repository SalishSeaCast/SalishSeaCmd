.. Copyright 2013-2017 The Salish Sea MEOPAR contributors
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

The command :kbd:`salishsea --help` produces a list of the available :program:`salishsea` options and sub-commands::

  usage: salishsea [--version] [-v | -q] [--log-file LOG_FILE] [-h] [--debug]

  Salish Sea NEMO Command Processor

  optional arguments:
    --version            show program's version number and exit
    -v, --verbose        Increase verbosity of output. Can be repeated.
    -q, --quiet          Suppress output except warnings and errors.
    --log-file LOG_FILE  Specify a file to log output. Disabled by default.
    -h, --help           Show help message and exit.
    --debug              Show tracebacks on errors.

  Commands:
    combine        Combine per-processor files from an MPI NEMO run into single files
    complete       print bash completion command
    deflate        Deflate variables in netCDF files using Lempel-Ziv compression.
    gather         Gather results from a NEMO run.
    help           print detailed help for another command
    prepare        Prepare a Salish Sea NEMO run.
    run            Prepare, execute, and gather results from a Salish Sea NEMO model run.

For details of the arguments and options for a sub-command use
:command:`salishsea help <sub-command>`.
For example:

.. code-block:: bash

    $ salishsea help run

::

    usage: salishsea run [-h] [--max-deflate-jobs MAX_DEFLATE_JOBS] [--nemo3.4]
                         [--nocheck-initial-conditions] [--no-deflate]
                         [--no-submit] [--separate-deflate] [--waitjob WAITJOB]
                         [-q]
                         DESC_FILE RESULTS_DIR

    Prepare, execute, and gather the results from a Salish Sea NEMO-3.6 run
    described in DESC_FILE. The results files from the run are gathered in
    RESULTS_DIR. If RESULTS_DIR does not exist it will be created.

    positional arguments:
      DESC_FILE             run description YAML file
      RESULTS_DIR           directory to store results into

    optional arguments:
      -h, --help            show this help message and exit
      --max-deflate-jobs MAX_DEFLATE_JOBS
                            Maximum number of concurrent sub-processes to use for
                            netCDF deflating. Defaults to 4.
      --nemo3.4             Do a NEMO-3.4 run; the default is to do a NEMO-3.6 run
      --nocheck-initial-conditions
                            Suppress checking of the initial conditions link.
                            Useful if you are submitting a job to wait on a
                            previous job
      --no-deflate          Do not include "salishsea deflate" command in the bash
                            script. Use this option if you are using on-the-fly
                            deflation in XIOS-2; i.e. you are using 1 XIOS-2
                            process and have the compression_level="4" attribute
                            set in all of the file_group definitions in your
                            file_def.xml file.
      --no-submit           Prepare the temporary run directory, and the bash
                            script to execute the NEMO run, but don't submit the
                            run to the queue. This is useful during development
                            runs when you want to hack on the bash script and/or
                            use the same temporary run directory more than once.
      --separate-deflate    Produce separate bash scripts to deflate the run
                            results and qsub them to run as serial jobs after the
                            NEMO run finishes via the `qsub -W depend=afterok`
                            feature.
      --waitjob WAITJOB     Use -W waitjob in call to qsub, to make current job
                            wait for on waitjob. WAITJOB is the queue job number.
      -q, --quiet           Don't show the run directory path or job submission
                            message.

You can check what version of :program:`salishsea` you have installed with:

.. code-block:: bash

    salishsea --version


.. _salishsea-run:

:kbd:`run` Sub-command
======================

The :command:`run` sub-command prepares,
executes,
and gathers the results from the Salish Sea NEMO run described in the specified run description file.
The results are gathered in the specified results directory.

::

    usage: salishsea run [-h] [--max-deflate-jobs MAX_DEFLATE_JOBS] [--nemo3.4]
                         [--nocheck-initial-conditions] [--no-deflate]
                         [--no-submit] [--separate-deflate] [--waitjob WAITJOB]
                         [-q]
                         DESC_FILE RESULTS_DIR

    Prepare, execute, and gather the results from a Salish Sea NEMO-3.6 run
    described in DESC_FILE. The results files from the run are gathered in
    RESULTS_DIR. If RESULTS_DIR does not exist it will be created.

    positional arguments:
      DESC_FILE             run description YAML file
      RESULTS_DIR           directory to store results into

    optional arguments:
      -h, --help            show this help message and exit
      --max-deflate-jobs MAX_DEFLATE_JOBS
                            Maximum number of concurrent sub-processes to use for
                            netCDF deflating. Defaults to 4.
      --nemo3.4             Do a NEMO-3.4 run; the default is to do a NEMO-3.6 run
      --nocheck-initial-conditions
                            Suppress checking of the initial conditions link.
                            Useful if you are submitting a job to wait on a
                            previous job
      --no-deflate          Do not include "salishsea deflate" command in the bash
                            script. Use this option if you are using on-the-fly
                            deflation in XIOS-2; i.e. you are using 1 XIOS-2
                            process and have the compression_level="4" attribute
                            set in all of the file_group definitions in your
                            file_def.xml file.
      --no-submit           Prepare the temporary run directory, and the bash
                            script to execute the NEMO run, but don't submit the
                            run to the queue. This is useful during development
                            runs when you want to hack on the bash script and/or
                            use the same temporary run directory more than once.
      --separate-deflate    Produce separate bash scripts to deflate the run
                            results and qsub them to run as serial jobs after the
                            NEMO run finishes via the `qsub -W depend=afterok`
                            feature.
      --waitjob WAITJOB     Use -W waitjob in call to qsub, to make current job
                            wait for on waitjob. WAITJOB is the queue job number.
      -q, --quiet           Don't show the run directory path or job submission
                            message.

The path to the run directory,
and the response from the job queue manager
(typically a job number)
are printed upon completion of the command.

The :command:`run` sub-command does the following:

#. Execute the :ref:`salishsea-prepare` via the :ref:`SalishSeaCmdAPI` to set up a temporary run directory from which to execute the Salish Sea NEMO run.
#. Create a :file:`SalishSeaNEMO.sh` job script in the run directory.
   The job script:

   * runs NEMO
   * executes the :ref:`salishsea-combine` to combine the per-processor restart and/or results files
   * executes the :ref:`salishsea-deflate` to deflate the variables in the large netCDF results files using the Lempel-Ziv compression algorithm to reduce the size of the file on disk
   * executes the :ref:`salishsea-gather` to collect the run description and results files into the results directory

#. Submit the job script to the queue manager via the appropriate command
   (:command:`qsub` for systems that use TORQUE/MOAB; e.g. :kbd:`bugaboo`, :kbd:`orcinus`, and :kbd:`salish`,
   or :command:`sbatch` for systems that use slurm; e.g. :kbd:`cedar` and :kbd:`graham`).

See the :ref:`RunDescriptionFileStructure` section for details of the run description YAML file.

The :command:`run` sub-command concludes by printing the path to the run directory and the response from the job queue manager.
Example:

.. code-block:: bash

    $ salishsea run SalishSea.yaml $HOME/MEOPAR/SalishSea/myrun

    salishsea_cmd.run INFO: salishsea_cmd.prepare Created run directory /global/scratch/sallen/20mar17hindcast_2017-10-01T183841.082501-0700
    salishsea_cmd.run INFO: 3330782.orca2.ibb

If the :command:`run` sub-command prints an error message,
you can get a Python traceback containing more information about the error by re-running the command with the :kbd:`--debug` flag.


:kbd:`--separate-deflate` Option
--------------------------------

The :kbd:`--separate-deflate` command-line option is provided to facilitate runs that produce very large results files;
for example the :kbd:`ptrc` files produced by 10-day long runs of the SMELT configuration.
Deflation of such files is both time-consuming and memory-hungry.
The memory demand can cause jobs to fail during deflation with memory allocation (malloc) errors.
This option addresses the memory demand problem by producing separate bash scripts to deflate the run results and submitting them to the queue manager to run as serial jobs after the NEMO run finishes via the :command:`qsub -W depend=afterok` feature.

Deflation of the results files is separated into 3 serial jobs by results file type:
:kbd:`grid_[TUVW]`,
:kbd:`ptrc_T`,
and :kbd:`dia[12]_T`.

The output of a :command:`run --separate-deflate` sub-command includes information from the job queue manager about the NEMO job and the 3 deflate jobs.
Example:

.. code-block:: bash

    $ salishsea run SalishSea.yaml $HOME/MEOPAR/SalishSea/myrun

    salishsea_cmd.run INFO: salishsea_cmd.prepare Created run directory ../../SalishSea/38e87e0c-472d-11e3-9c8e-0025909a8461
    salishsea_cmd.run INFO: SalishSeaNEMO.sh queued as 3330782.orca2.ibb
    salishsea_cmd.run INFO: deflate_grid.sh queued after 3330782.orca2.ibb as 3330783.orca2.ibb
    salishsea_cmd.run INFO: deflate_ptrc.sh queued after 3330782.orca2.ibb as 3330784.orca2.ibb
    salishsea_cmd.run INFO: deflate_dia.sh queued after 3330782.orca2.ibb as 3330785.orca2.ibb


.. _salishsea-prepare:

:kbd:`prepare` Sub-command
==========================

The :command:`prepare` sub-command sets up a run directory from which to execute the Salish Sea NEMO run described in the specifed run description,
and IOM server definitions files::

  usage: salishsea prepare [-h] [--nemo3.4] [-q] DESC_FILE

  Set up the Salish Sea NEMO described in DESC_FILE and print the path to the
  run directory.

  positional arguments:
    DESC_FILE    run description YAML file

  optional arguments:
    -h, --help   show this help message and exit
    --nemo3.4    Prepare a NEMO-3.4 run; the default is to prepare a NEMO-3.6
                 run
    -q, --quiet  don't show the run directory path on completion

See the :ref:`RunDescriptionFileStructure` section for details of the run description file.

The :command:`prepare` sub-command concludes by printing the path to the run directory it created.
Example:

.. code-block:: bash

    $ salishsea prepare SalishSea.yaml iodef.xml

    salishsea_cmd.prepare INFO: Created run directory ../../runs/SalishSea/38e87e0c-472d-11e3-9c8e-0025909a8461

The name of the run directory created is a `Universally Unique Identifier`_
(UUID)
string because the directory is intended to be ephemerally used for a single run.

.. _Universally Unique Identifier: https://en.wikipedia.org/wiki/Universally_unique_identifier

If the :command:`prepare` sub-command prints an error message,
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

* A symlink to the :file:`EXP00/namelist_ref` file in the directory of the NEMO configuration given by the :kbd:`config name` and :kbd:`NEMO code config` keys in the run description file is also created to provide default values to be used for any namelist variables not included in the namelist segments listed in the run description file.

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


.. _salishsea-combine:

:kbd:`combine` Sub-command
==========================

The :command:`combine` sub-command combines the per-processor results and/or restart files from an MPI NEMO run described in DESC_FILE using the the NEMO :command:`rebuild_nemo` tool.
It is provided by the `NEMO-Cmd`_ package.
Please use:

.. code-block:: bash

    $ salishsea help combine

to see its usage,
and see :ref:`nemocmd:nemo-combine` for more details.

.. _NEMO-Cmd: https://bitbucket.org/salishsea/nemo-cmd

If the :command:`combine` sub-command prints an error message,
you can get a Python traceback containing more information about the error by re-running the command with the :kbd:`--debug` flag.


.. _salishsea-deflate:

:kbd:`deflate` Sub-command
==========================

The :command:`deflate` sub-command deflates the variables in netCDF files using the Lempel-Ziv compression algorithm to reduce the size of the file on disk.
It is provided by the `NEMO-Cmd`_ package.
Please use:

.. code-block:: bash

    $ salishsea help deflate

to see its usage,
and see :ref:`nemocmd:nemo-deflate` for more details.

.. _NEMO-Cmd: https://bitbucket.org/salishsea/nemo-cmd

If the :command:`deflate` sub-command prints an error message,
you can get a Python traceback containing more information about the error by re-running the command with the :kbd:`--debug` flag.


.. _salishsea-gather:

:kbd:`gather` Sub-command
=========================

The :command:`gather` sub-command moves results from a NEMO run into a results directory.
It is provided by the `NEMO-Cmd`_ package.
Please use:

.. code-block:: bash

    $ salishsea help gather

to see its usage,
and see :ref:`nemocmd:nemo-gather` for more details.

.. _NEMO-Cmd: https://bitbucket.org/salishsea/nemo-cmd

If the :command:`gather` sub-command prints an error message,
you can get a Python traceback containing more information about the error by re-running the command with the :kbd:`--debug` flag.
