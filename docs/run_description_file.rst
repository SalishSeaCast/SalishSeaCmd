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

NEMO-3.6 Run Description File
=============================

Example (from :file:`SS-run-sets/SalishSea/nemo3.6/SalishSea.yaml`):

.. literalinclude:: SalishSea.yaml.example-NEMO-3.6
   :language: yaml
