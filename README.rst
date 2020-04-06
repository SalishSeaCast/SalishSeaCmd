************************************
SalishSeaCast NEMO Command Processor
************************************

.. image:: https://img.shields.io/badge/license-Apache%202-cb2533.svg
    :target: https://www.apache.org/licenses/LICENSE-2.0
    :alt: Licensed under the Apache License, Version 2.0
.. image:: https://img.shields.io/badge/python-3.5+-blue.svg
    :target: https://docs.python.org/3.8/
    :alt: Python Version
.. image:: https://img.shields.io/badge/version%20control-hg-blue.svg
    :target: https://bitbucket.org/salishsea/salishseacmd/
    :alt: Mercurial on Bitbucket
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://black.readthedocs.io/en/stable/
    :alt: The uncompromising Python code formatter
.. image:: https://readthedocs.org/projects/salishseacmd/badge/?version=latest
    :target: https://salishseacmd.readthedocs.io/en/latest/
    :alt: Documentation Status
.. image:: https://img.shields.io/bitbucket/issues/salishsea/salishseacmd.svg
    :target: https://bitbucket.org/salishsea/salishseacmd/issues?status=new&status=open
    :alt: Issue Tracker

The SalishSeaCast NEMO command processor, ``salishsea``, is a command line tool for doing various operations associated with the `Salish Sea NEMO model`_.

.. _Salish Sea NEMO model: https://salishsea-meopar-docs.readthedocs.io/en/latest/

Use ``salishsea --help`` to get a list of the sub-commands available for doing things with and related to Salish Sea NEMO.
Use ``salishsea help <sub-command>`` to get a synopsis of what a sub-command does,
what its required arguments are,
and what options are available to control it.

Documentation for the command processor is in the ``docs/`` directory and is rendered at https://salishseacmd.readthedocs.io/en/latest/.

.. image:: https://readthedocs.org/projects/salishseacmd/badge/?version=latest
    :target: https://salishseacmd.readthedocs.io/en/latest/
    :alt: Documentation Status

This an extensible tool built on the OpenStack ``cliff``
(`Command Line Interface Formulation Framework`_)
package.
It is a NEMO domain-specific command processor tool for the `Salish Sea NEMO model`_ that uses plug-ins from the `NEMO-Cmd`_ package.

.. _Command Line Interface Formulation Framework: http://docs.openstack.org/developer/cliff/
.. _NEMO-Cmd: https://bitbucket.org/salishsea/nemo-cmd


License
=======

.. image:: https://img.shields.io/badge/license-Apache%202-cb2533.svg
    :target: https://www.apache.org/licenses/LICENSE-2.0
    :alt: Licensed under the Apache License, Version 2.0

The SalishSeaCast NEMO command processor and documentation are copyright 2013-2020 by the Salish Sea MEOPAR Project Contributors and The University of British Columbia.

They are licensed under the Apache License, Version 2.0.
https://www.apache.org/licenses/LICENSE-2.0
Please see the LICENSE file for details of the license.
