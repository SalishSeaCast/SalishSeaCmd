Changelog
=========

* The ``SalishSeaCmd`` package now depend on the ``SalishSeaTools``
  package for its Mercurial commands interface.

* ``salishsea get_cgrf`` sub-command to download CGRF products
  atmospheric forcing files from Dalhousie rsync repository and symlink
  them with the file names that NEMO expects.
  See ``salishsea get_cgrf --help`` for details.

* ``salishsea prepare`` sub-command to set up a Salish Sea NEMO run
  directory that is described in a YAML file and print the path to the run
  directory.
  See ``salishsea prepare --help`` for details.

* ``salishsea combine`` sub-command to combine per-processor files
  from an MPI Salish Sea NEMO run into single files with the same name-root
  and store the results in a specified directory.
  See ``salishsea combine --help`` for details.

* Salish Sea NEMO command processor framework based on the Python argparse
  module for command line argument and option handling.
