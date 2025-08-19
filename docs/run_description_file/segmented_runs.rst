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


.. _SegmentedRuns:

**************
Segmented Runs
**************

Segmented runs is a feature that enables a single run description YAML file to be used to launch a sequence of linked runs for a date range
(e.g. a year) that is longer than can robustly executed in a single run.
It is available in :ref:`BreakingChangesVersion19.1` onward.

The segmented runs feature is activated by including a :kbd:`segmented run` section in the run description YAML file.
This section describes the :kbd:`segmented run` section.
Please see :ref:`NEMO-3.6-RunDescriptionFile` for other details of run description files.

.. warning::
    There are some restrictions imposed on the contents of run description YAML files when the segmented runs feature is in use.
    Please see :ref:`SegmentedRunsYAMLFileRestrictions` below for details.

An example of a :kbd:`segmented run` section is:

.. code-block:: yaml

    segmented run:
      start date: 2016-04-30
      start time step: 2730241
      end date: 2016-12-31
      days per segment: 30
      first segment number: 0
      segment walltime: 12:00:00
      namelists:
        namrun: $PROJECT/SalishSeaCast/hindcast-sys/SS-run-sets/v201812/namelist.time
        namdom: $PROJECT/SalishSeaCast/hindcast-sys/SS-run-sets/v201812/namelist.domain

.. note::
    The presence of a :kbd:`segmented run` section in a run description YAML file is what enables the feature.
    If you have a YAML file that contains a :kbd:`segmented run` section but you want to execute the run without segmentation,
    please be sure to delete or comment out the :kbd:`segmented run` section.

All key-value pairs in the :kbd:`segmented run` section are required;
:command:`salishsea run` will raise an error if any are missing.

:kbd:`start date`
  The start date for the first run in the sequence of linked runs,
  formatted as :kbd:`YYYY-MM-DD`.
  In the example above,
  the sequence of runs will start on :kbd:`2016-04-30`.

:kbd:`start time step`
  The time step number on which to start the first run in the sequence,
  formatted as an integer.
  If you are initializing the segmented run from restart file(s),
  the :kbd:`start time step` value is the time step number of the restart file(s) given in the :ref:`NEMO-3.6-Restart` plus 1.
  In the example above,
  the run will start with time step :kbd:`2730241`.

:kbd:`end date`
  The end date for the sequence of linked runs,
  formatted as :kbd:`YYYY-MM-DD`.
  In the example above,
  the sequence of runs will start on :kbd:`2016-12-31`.

:kbd:`days per segment`
  The number of days to use for each segment of the sequence of runs,
  formatted as an integer.
  In the example above,
  the run segments will be 30 days long.
  The length of the final segment in the sequence is adjusted to be the appropriate number of days required to bring the sequence to an end on :kbd:`end date`;
  i.e. it is *not* necessary for the value of :kbd:`days per segment` to divide evenly into the span of :kbd:`start date` to :kbd:`end date`.

:kbd:`first segment number`
  The 0-based index number of the first segment in the sequence to run.
  This value is normally :kbd:`0`.
  A non-zero value is used if you are restarting a segmented run after recovering from a failure of one of the run segments.
  Please see :ref:`SegmentedRunsAfterASegmentFailure` for details of how to restart a segmented run after failures such as running out of walltime.

:kbd:`segment walltime`
  The wall-clock time to request for the *each segment* of the run,
  formatted as :kbd:`HH:MM:SS`.
  The value of :kbd:`walltime` in the :ref:`NEMO-3.6-BasicRunConfiguration` section of the run description YAML file is ignored.
  In the example above,
  each segment of the run will have a walltime of :kbd:`12:00:00`.

The :kbd:`namelists` sub-section provides paths to the namelist files containing the :kbd:`namrun` and :kbd:`namdom` namelists that needed to calculate the :kbd:`namrun` values for each run segment.

:kbd:`namrun`
  *Absolute* path to the namelist file containing the :kbd:`namrun` namelist.
  If you follow the recommended pattern of breaking :file:`namelist_cfg` into different files (see :file:`SS-run-sets/v201905/`),
  the name of this file is :file:`namelist.time`.
  If you use a monolithic :file:`namelist_cfg` file,
  the name of this file is probably :file:`namelist_cfg`

  .. warning::
      This path must appear *identically* in the :kbd:`namelist_cfg` sub-section of the :ref:`NEMO-3.6-Namelists` of the run description YAML file.

:kbd:`namdom`
  *Absolute* path to the namelist file containing the :kbd:`namdom` namelist.
  If you follow the recommended pattern of breaking :file:`namelist_cfg` into different files (see :file:`SS-run-sets/v201905/`),
  the name of this file is :file:`namelist.domain`.
  If you use a monolithic :file:`namelist_cfg` file,
  the name of this file is probably :file:`namelist_cfg`


.. _SegmentedRunsYAMLFileRestrictions:

Segmented Runs YAML File Restrictions
=====================================

There are a few restrictions on how your run description YAML file must be structured for it to be usable for a segmented run in contrast to a single job run.
These restrictions arise due to the processing that :command:`salishsea run` has to do to construct run description and namelist files for each segment of a segmented run.

* All paths *must be absolute*;
  i.e. start with a :kbd:`/` or with a environment variable value that starts with a :kbd:`/`.
  That means
  (for example)
  you should use :file:`$PROJECT/SalishSeaCast/hindcast-sys/SS-run-sets/v201812/namelist.time` instead of :file:`./namelist.time`.
  Paths may contain :kbd:`~` or :envvar:`$HOME` as alternative spellings of the your home directory,
  and :envvar:`$USER` as an alternative spelling of your userid.
  You can also use system-defined environment variable values like :envvar:`$PROJECT` and :envvar:`$SCRATCH`.

* The path associated with the :kbd:`namerun` key in the :kbd:`namelists` sub-section under :kbd:`segmented run` must appear *identially* in the :kbd:`namelist_cfg` sub-section of the :ref:`NEMO-3.6-Namelists` of the run description YAML file.


.. _How Segmented Runs Work:

How Segmented Runs Work
=======================

This section describes how the :command:`salishsea run` command prepares and queues the sequence of linked runs that is generated when the :kbd:`segmented run` section is included in a run description YAML file.

The process begins by calculating several pieces of information for each segment of the sequence:

* the segment run description :py:obj:`dict`;
  that is a copy of the run description :py:obj:`dict` read from the run description YAML file given in the :command:`salishsea run` command with values calculated for the particular run segment

* the file name in which the segment run description :py:obj:`dict` will be stored as YAML;
  that is the name of the run description YAML file given in the :command:`salishsea run` command with the 0-based index of the segment appended to the name.
  For example,
  if the command-line YAML file is :file:`BR5_12SKOG2016.yaml`,
  the first segment's YAML file will be :file:`BR5_12SKOG2016_0.yaml`,
  the second will be :file:`BR5_12SKOG2016_1.yaml`,
  etc.
  Those are the names of the run description YAML files that will be stored in the segment results directories.

* the directory name in which the segment run results will be stored;
  that is the results directory name given in the :command:`salishsea run` command with the 0-based index of the segment appended to it.
  For example,
  if the command-line results directory is :file:`$SCRATCH/SKOG_nibi_BASERUN/BR_2016/`,
  the first segment's results will be stored in :file:`$SCRATCH/SKOG_nibi_BASERUN/BR_2016_0/`,
  the second will be in :file:`$SCRATCH/SKOG_nibi_BASERUN/BR_2016_1/`,
  etc.

* the `f90nml`_ patch :py:obj:`dict` that will be applied to the :kbd:`namrun` namelist to set the values of :kbd:`nn_it000`,
  :kbd:`nn_itend`,
  and :kbd:`nn_date0` for the segment

  .. _f90nml: https://f90nml.readthedocs.io/en/latest/

Next,
in temporary storage directories
(one for each segment)
that exists only while the :command:`salishsea run` command is being executed,
the namelist files containing the :kbd:`namrun` namelist for the segments,
and the segment run description YAML files are written.
Each segment's :kbd:`namrun` namelist file is created by using the value associated with the :kbd:`namrun` key as a template namelist file to which the `f90nml`_ patches calculated above are applied.
The segment run descriptions calculated above are updated with:

* the path of the :kbd:`namrun` namelist for the segments
* the path(s) of the restart file(s) that will be produced by the previous run segment
* the :kbd:`segment walltime` value

The segment run descriptions are stored with the YAML file names calculated above.

With all of that preparation completed,
temporary run directories for each segment are created in the directory given by the :kbd:`runs directory` key in the :ref:`NEMO-3.6-Paths` section of the run description YAML file from the command-line.
Then the run segments are submitted in order,
each with a :kbd:`--waitjob` dependency on successful completion of the previous segment.

The run ids of the segments are the value associated with the :kbd:`run_id` key in the YAML file from the command-line,
prefixed with the 0-based index of the run segment.
For example,
if the :kbd:`run_id` value is :kbd:`SKOG_2016_BASE`,
the run id of the first queued segment will be :kbd:`0_SKOG_2016_BASE`,
the second will be :kbd:`1_SKOG_2016_BASE`,
etc.
The run ids are prefixed with their segment number
(in contrast to YAML files and results directories which are suffixed)
so that the segment numbers are easily visible in the output of :command:`squeue` or :command:`qstat` even if the base run id is long.

The :command:`salishsea run` command returns a space-separated list of job ids of the queued run segments.


.. _SegmentedRunsAfterASegmentFailure:

Restarting After a Segment Failure
==================================

If a segmented run fails part way through,
you can restart it from the last restart file(s) it produced.
To do so,
you need update your run description YAML file,
or create a new one,
with the following changes:

* Set the value of :kbd:`start date` to the date
  (:kbd:`YYYY-MM-DD`)
  on which your want the run to resume.

* Set the value of :kbd:`start time step` to the time step of the restart file(s) plus 1.

* Set the value(s) in the :ref:`NEMO-3.6-Restart` section to the to the path(s) that you want the run to restart from.

* Set the value of :kbd:`first segment number` to the segment number in which the restart files were produced plus 1.

So,
for example,
let's say you started a segmented run with a YAML file that contained:

.. code-block:: yaml

    segmented run:
      start date: 2016-04-30
      start time step: 2730241
      end date: 2016-12-31
      days per segment: 30
      first segment number: 0
      segment walltime: 12:00:00
      namelists:
        namrun: $PROJECT/SalishSeaCast/hindcast-sys/SS-run-sets/v201812/namelist.time
        namdom: $PROJECT/SalishSeaCast/hindcast-sys/SS-run-sets/v201812/namelist.domain

    ...

      restart:
        restart.nc: $SCRATCHDIR/SKOG/SKOG_02730240_restart.nc
        restart_trc.nc: $SCRATCHDIR/SKOG/SKOG_02730240_restart_trc.nc

Now let's say it fails
(perhaps due to exceeding walltime)
during segment 2 so that you have restart files:

* :file:`$SCRATCHDIR/SKOG_2/SKOG_02892240_restart.nc`
* :file:`$SCRATCHDIR/SKOG_2/SKOG_02892240_restart_trc.nc`

corresponding to a run date of :kbd:`2016-07-14`.
You can restart the run by editing your YAML file to:

.. code-block:: yaml
   :emphasize-lines: 2,3,6,15,16

    segmented run:
      start date: 2016-07-15
      start time step: 2892241
      end date: 2016-12-31
      days per segment: 30
      first segment number: 3
      segment walltime: 12:00:00
      namelists:
        namrun: $PROJECT/SalishSeaCast/hindcast-sys/SS-run-sets/v201812/namelist.time
        namdom: $PROJECT/SalishSeaCast/hindcast-sys/SS-run-sets/v201812/namelist.domain

    ...

      restart:
        restart.nc: $SCRATCHDIR/SKOG_2/SKOG_02892240_restart.nc
        restart_trc.nc: $SCRATCHDIR/SKOG_2/SKOG_02892240_restart_trc.nc
