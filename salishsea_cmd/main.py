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

This module is connected to the :command:`salishsea` command via a scripts and
entry-points configuration in :file:`pyproject.toml`.
"""
import importlib.metadata
import sys

import cliff.app
import cliff.commandmanager


class SalishSeaApp(cliff.app.App):
    CONSOLE_MESSAGE_FORMAT = "%(name)s %(levelname)s: %(message)s"

    def __init__(self):
        super().__init__(
            description="SalishSeaCast NEMO Command Processor",
            version=importlib.metadata.version("SalishSeaCmd"),
            command_manager=cliff.commandmanager.CommandManager(
                "salishsea", convert_underscores=False
            ),
            stderr=sys.stdout,
        )


def main(argv=sys.argv[1:]):
    salishsea = SalishSeaApp()
    return salishsea.run(argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
