*********************************
Salish Sea NEMO Command Processor
*********************************

The Salish Sea NEMO command processor, ``salishsea``, is a command line tool for doing various operations associated with the `Salish Sea NEMO model`_.

.. _Salish Sea NEMO model: https://salishsea-meopar-docs.readthedocs.io/en/latest/

Use ``salishsea --help`` to get a list of the sub-commands available for doing things with and related to Salish Sea NEMO.
Use ``salishsea help <sub-command>`` to get a synopsis of what a sub-command does,
what its required arguments are,
and what options are available to control it.

Documentation for the command processor is in the ``docs/`` directory and is rendered at https://salishseacmd.readthedocs.io/en/latest/.

.. image:: https://readthedocs.org/projects/salishseacmd/badge/?version=latest
    :target: https://salishseacmd.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

This an extensible tool built on the OpenStack :kbd:``cliff``
(`Command Line Interface Formulation Framework`_)
package.
It is a NEMO domain-specific command processor tool for the `Salish Sea NEMO model`_ that uses plug-ins from the `NEMO-Cmd`_ package.

.. _Command Line Interface Formulation Framework: http://docs.openstack.org/developer/cliff/
.. _NEMO-Cmd: https://bitbucket.org/salishsea/nemo-cmd


License
=======

The Salish Sea NEMO command processor and documentation are copyright 2013-2017 by the Salish Sea MEOPAR Project Contributors and The University of British Columbia.

They are licensed under the Apache License, Version 2.0.
https://www.apache.org/licenses/LICENSE-2.0
Please see the LICENSE file for details of the license.