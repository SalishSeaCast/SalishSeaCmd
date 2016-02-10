# Copyright 2015-2016 The Salish Sea MEOPAR Contributors
# and The University of British Columbia

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""SalishSeaCmd application

Salish Sea NEMO Command Processor

This module is connected to the `salishsea` command via a console_scripts
entry point in setup.py.
"""
import sys

import cliff.app
import cliff.commandmanager

from salishsea_cmd import __pkg_metadata__


__all__ = ['main', 'SalishSeaApp']


class SalishSeaApp(cliff.app.App):
    CONSOLE_MESSAGE_FORMAT = '%(name)s %(levelname)s: %(message)s'

    def __init__(self):
        super(SalishSeaApp, self).__init__(
            description=__pkg_metadata__.DESCRIPTION,
            version=__pkg_metadata__.VERSION,
            command_manager=cliff.commandmanager.CommandManager(
                'salishsea.app', convert_underscores=False),
            stderr=sys.stdout,
        )


def main(argv=sys.argv[1:]):
    app = SalishSeaApp()
    return app.run(argv)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
