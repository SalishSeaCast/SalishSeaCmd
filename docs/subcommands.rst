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


.. _SalishSeaCmdSubcommands:

*********************************
:command:`salishsea` Sub-Commands
*********************************

The command :kbd:`salishsea help` produces a list of the available :program:`salishsea`
options and sub-commands:

.. code-block:: text

  usage: salishsea [--version] [-v | -q] [--log-file LOG_FILE] [-h] [--debug]

  SalishSeaCast NEMO Command Processor

  optional arguments:
    --version            show program's version number and exit
    -v, --verbose        Increase verbosity of output. Can be repeated.
    -q, --quiet          Suppress output except warnings and errors.
    --log-file LOG_FILE  Specify a file to log output. Disabled by default.
    -h, --help           Show help message and exit.
    --debug              Show tracebacks on errors.

  Commands:
    combine        Combine per-processor files from an MPI NEMO run into single files (NEMO-Cmd)
    complete       print bash completion command (cliff)
    deflate        Deflate variables in netCDF files using Lempel-Ziv compression. (NEMO-Cmd)
    gather         Gather results from a NEMO run. (NEMO-Cmd)
    help           print detailed help for another command (cliff)
    prepare        Prepare a SalishSeaCast NEMO run.
    run            Prepare, execute, and gather results from a SalishSeaCast NEMO model run.
    split-results  Split the results of a multi-day SalishSeaCast NEMO model run
                   (e.g. a hindcast run) into daily results directories.

For details of the arguments and options for a sub-command use
:command:`salishsea help <sub-command>`.
For example:

.. code-block:: bash

    $ salishsea help run

.. code-block:: text

    usage: salishsea run [-h] [--cores-per-node CORES_PER_NODE] [--cpu-arch CPU_ARCH]
                         [--deflate] [--max-deflate-jobs MAX_DEFLATE_JOBS]
                         [--nocheck-initial-conditions] [--no-submit]
                         [--separate-deflate] [--waitjob WAITJOB] [-q]
                         DESC_FILE RESULTS_DIR

    Prepare, execute, and gather the results from a SalishSeaCast NEMO run
    described in DESC_FILE. The results files from the run are gathered in RESULTS_DIR.
    If RESULTS_DIR does not exist it will be created.

    positional arguments:
      DESC_FILE     run description YAML file
      RESULTS_DIR   directory to store results into

    options:
      -h, --help            show this help message and exit
      --cores-per-node CORES_PER_NODE
                            Number of cores/node to use in PBS or SBATCH directives.
                            Use this option to override the default cores/node that are
                            specified in the code for each HPC cluster.
      --cpu-arch CPU_ARCH
                            CPU architecture to use in PBS or SBATCH directives.
                            Use this to override the default CPU architecture on
                            HPC clusters that have more than one type of CPU;
                            e.g. sockeye (cascade is default, skylake is alternative)
                            or cedar (skylake is default, broadwell is alternative).
                            This option must be used in conjunction with --core-per-node.
      --deflate
                            Include "salishsea deflate" command in the bash script.
                            Use this option, or the --separate-deflate option
                            if you are *not* using on-the-fly deflation in XIOS-2;
                            i.e. you are using more than 1 XIOS-2 process and/or
                            do not have the compression_level="4" attribute set in all of
                            the file_group definitions in your file_def.xml file.
      --max-deflate-jobs MAX_DEFLATE_JOBS
                            Maximum number of concurrent sub-processes to
                            use for netCDF deflating. Defaults to 4.
      --nocheck-initial-conditions
                            Suppress checking of the initial conditions link.
                            Useful if you are submitting a job to wait on a
                            previous job
      --no-submit
                            Prepare the temporary run directory, and the bash script
                            to execute the NEMO run, but don't submit the run to the queue.
                            This is useful during development runs when you want to
                            hack on the bash script and/or use the same temporary run
                            directory more than once.
      --separate-deflate
                            Produce separate bash scripts to deflate the run results
                            and submit them to run as serial jobs after the NEMO run
                            finishes via the queue manager's job chaining feature.
      --waitjob WAITJOB
                            Make this job wait for to start until the successful
                            completion of WAITJOB. WAITJOB is the queue job number of
                            the job to wait for.
      -q, --quiet
                            Don't show the run directory path or job submission message.

You can check what version of :program:`salishsea` you have installed with:

.. code-block:: bash

    salishsea --version


.. _salishsea-run:

:kbd:`run` Sub-command
======================

The :command:`run` sub-command prepares,
executes,
and gathers the results from the SalishSeaCast NEMO run described in the specified run
description file.
The results are gathered in the specified results directory.

.. code-block:: text

    usage: salishsea run [-h] [--cores-per-node CORES_PER_NODE] [--cpu-arch CPU_ARCH]
                         [--deflate] [--max-deflate-jobs MAX_DEFLATE_JOBS]
                         [--nocheck-initial-conditions] [--no-submit]
                         [--separate-deflate] [--waitjob WAITJOB] [-q]
                         DESC_FILE RESULTS_DIR

    Prepare, execute, and gather the results from a SalishSeaCast NEMO run
    described in DESC_FILE. The results files from the run are gathered in RESULTS_DIR.
    If RESULTS_DIR does not exist it will be created.

    positional arguments:
      DESC_FILE     run description YAML file
      RESULTS_DIR   directory to store results into

    options:
      -h, --help            show this help message and exit
      --cores-per-node CORES_PER_NODE
                            Number of cores/node to use in PBS or SBATCH directives.
                            Use this option to override the default cores/node that are
                            specified in the code for each HPC cluster.
      --cpu-arch CPU_ARCH
                            CPU architecture to use in PBS or SBATCH directives.
                            Use this to override the default CPU architecture on
                            HPC clusters that have more than one type of CPU;
                            e.g. sockeye (cascade is default, skylake is alternative)
                            or cedar (skylake is default, broadwell is alternative).
                            This option must be used in conjunction with --core-per-node.
      --deflate
                            Include "salishsea deflate" command in the bash script.
                            Use this option, or the --separate-deflate option
                            if you are *not* using on-the-fly deflation in XIOS-2;
                            i.e. you are using more than 1 XIOS-2 process and/or
                            do not have the compression_level="4" attribute set in all of
                            the file_group definitions in your file_def.xml file.
      --max-deflate-jobs MAX_DEFLATE_JOBS
                            Maximum number of concurrent sub-processes to
                            use for netCDF deflating. Defaults to 4.
      --nocheck-initial-conditions
                            Suppress checking of the initial conditions link.
                            Useful if you are submitting a job to wait on a
                            previous job
      --no-submit
                            Prepare the temporary run directory, and the bash script
                            to execute the NEMO run, but don't submit the run to the queue.
                            This is useful during development runs when you want to
                            hack on the bash script and/or use the same temporary run
                            directory more than once.
      --separate-deflate
                            Produce separate bash scripts to deflate the run results
                            and submit them to run as serial jobs after the NEMO run
                            finishes via the queue manager's job chaining feature.
      --waitjob WAITJOB
                            Make this job wait for to start until the successful
                            completion of WAITJOB. WAITJOB is the queue job number of
                            the job to wait for.
      -q, --quiet
                            Don't show the run directory path or job submission message.

The path to the run directory,
and the response from the job queue manager
(typically a job number)
are printed upon completion of the command.

The :command:`run` sub-command does the following:

#. Execute the :ref:`salishsea-prepare` via the :ref:`SalishSeaCmdAPI` to set up a temporary run directory from which to execute the SalishSeaCast NEMO run.
#. Create a :file:`SalishSeaNEMO.sh` job script in the run directory.
   The job script:

   * runs NEMO
   * executes the :ref:`salishsea-combine` to combine the per-processor restart and/or results files
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

If you are *not* using on-the-fly deflation in :program:`XIOS-2`;
i.e. you are using more than 1 :program:`XIOS-2` process and/or do not have the :kbd:`compression_level="4"` attribute set in all of the :kbd:`file_group` definitions in your :file:`file_def.xml` file;
you should use the :kbd:`--deflate` option to include :ref:`nemo-deflate` in the :file:`SalishSeaNEMO.sh` job script,
or :kbd:`--separate-deflate` to produce separate bash scripts to deflate the run results and submit them to run as serial jobs after the NEMO run finishes via the queue manager's job chaining feature.


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

The :command:`prepare` sub-command sets up a run directory from which to execute the
SalishSeaCast NEMO run described in the specified run description,
and IOM server definitions files:

.. code-block:: text

    usage: salishsea prepare [-h] [--nemo3.4] [-q] DESC_FILE

    Set up the SalishSeaCast NEMO described in DESC_FILE and print the path to the
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


Run Directory Contents
----------------------

For runs initiated by :command:`salishsea run ...` or :command:`salishsea prepare ...` commands
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

.. _NEMO-Cmd: https://github.com/SalishSeaCast/NEMO-Cmd/

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

If the :command:`gather` sub-command prints an error message,
you can get a Python traceback containing more information about the error by re-running the command with the :kbd:`--debug` flag.


.. _salishsea-split-results:

:kbd:`split-results` Sub-command
================================

The :command:`split-results` sub-command splits the results of a multi-day SalishSeaCast NEMO model run
(e.g. a hindcast run)
into daily results directories.
It is assumed that the multi-day run output has been split into 1-day files by way of the :kbd:`split_freq="1d"` attribute in the :kbd:`file_group` elements of the run's :file:`file_def.xml` file
(see `file_def_dailysplit.xml`_ for example).
The results files are renamed so that they look like they came from a
single day run so that ERDDAP will accept them
(i.e. SalishSea_*_yyyymmdd_yyyymmdd_*.nc).
The run description files are left in the first run day's directory.
The restart files are moved to the last run day's directory.

.. _file_def_dailysplit.xml: https://github.com/SalishSeaCast/SS-run-sets/blob/main/v201905/hindcast/file_def_dailysplit.xml

.. code-block:: text

    usage: salishsea split-results [-h] [-q] SOURCE_DIR

    Split the results of the multi-day SalishSeaCast NEMO model run in SOURCE_DIR
    into daily results directories.

    positional arguments:
      SOURCE_DIR   Multi-day results directory to split into daily directories

    optional arguments:
      -h, --help   show this help message and exit
      -q, --quiet  Don't show progess messages.

If the :command:`split-results` sub-command prints an error message,
you can get a Python traceback containing more information about the error by re-running
the command with the :kbd:`--debug` flag.
