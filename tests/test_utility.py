# Copyright The IETF Trust 2022, All Rights Reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


__author__ = 'Richard Zilincik'
__copyright__ = 'Copyright The IETF Trust 2022, All Rights Reserved'
__license__ = 'Apache License, Version 2.0'
__email__ = 'richard.zilincik@pantheon.tech'

import os
import unittest

import utility.utility as u
from create_config import create_config


class TestUtility(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.resource_path = os.path.join(os.environ['VIRTUAL_ENV'], 'tests/resources/utility')
        cls.config = create_config(os.path.join(os.path.dirname(cls.resource_path), 'test.conf'))

    def test_module_or_submodule(self):
        result = u.module_or_submodule(os.path.join(self.resource_path, 'module_or_submodule/module.yang'))
        self.assertEqual(result, 'module')

        result = u.module_or_submodule(os.path.join(self.resource_path, 'module_or_submodule/submodule.yang'))
        self.assertEqual(result, 'submodule')

        result = u.module_or_submodule(os.path.join(self.resource_path, 'module_or_submodule/neither.yang'))
        self.assertEqual(result, 'wrong file')
