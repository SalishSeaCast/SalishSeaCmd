# Copyright 2013-2019 The Salish Sea MEOPAR Contributors
# and The University of British Columbia
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""SalishSeaCmd -- SalishSeaCast NEMO command processor
"""
import setuptools


setuptools.setup(
    entry_points={
        # The salishsea command:
        "console_scripts": ["salishsea = salishsea_cmd.main:main"],
        # Sub-command plug-ins:
        "salishsea.app": [
            "combine = nemo_cmd.combine:Combine",
            "deflate = nemo_cmd.deflate:Deflate",
            "gather = nemo_cmd.gather:Gather",
            "prepare = salishsea_cmd.prepare:Prepare",
            "run = salishsea_cmd.run:Run",
        ],
    }
)
