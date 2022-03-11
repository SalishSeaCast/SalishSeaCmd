# Copyright 2013 – present by the SalishSeaCast Project Contributors
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

# SPDX-License-Identifier: Apache-2.0


"""SalishSeaCmd application

SalishSeaCast NEMO Command Processor

This module is connected to the `salishsea` command via a console_scripts
entry point in setup.py.
"""
import sys

import cliff.app
import cliff.commandmanager

import salishsea_cmd


class SalishSeaApp(cliff.app.App):
    CONSOLE_MESSAGE_FORMAT = "%(name)s %(levelname)s: %(message)s"

    def __init__(self):
        super(SalishSeaApp, self).__init__(
            description="SalishSeaCast NEMO Command Processor",
            version=salishsea_cmd.__version__,
            command_manager=cliff.commandmanager.CommandManager(
                "salishsea.app", convert_underscores=False
            ),
            stderr=sys.stdout,
        )


def main(argv=sys.argv[1:]):
    app = SalishSeaApp()
    return app.run(argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
