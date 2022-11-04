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

import private_page as pp


class TestPrivatePage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.resources = os.path.join(os.environ['VIRTUAL_ENV'], 'tests/resources/private_page')

    def resource(self, file: str):
        return os.path.join(self.resources, file)

    def test_get_vendor_context(self):
        result = pp.get_vendor_context(
            self.resource('vendor'),
            lambda os_name, os_specific_dir: pp.alnum(f'{os_name}{os_specific_dir}'),
            lambda os_name, os_specific_dir: f'{os_name}{os_specific_dir}',
        )

        expected = [{'allCharacters': i, 'alphaNumeric': pp.alnum(i)} for i in ['bar1.0', 'foo1.0', 'foo1.1', 'foo1.2']]
        self.assertEqual(result, expected)

    def test_get_vendor_context_separate(self):
        result = pp.get_vendor_context(
            self.resource('vendor'),
            lambda os_name, os_specific_dir: pp.alnum(f'{os_name}{os_specific_dir}'),
            lambda os_name, os_specific_dir: f'{os_name}{os_specific_dir}',
            separate=True,
        )

        expected = {
            'BAR': [{'allCharacters': i, 'alphaNumeric': pp.alnum(i)} for i in ['bar1.0']],
            'FOO': [{'allCharacters': i, 'alphaNumeric': pp.alnum(i)} for i in ['foo1.0', 'foo1.1', 'foo1.2']],
        }
        assert isinstance(result, dict)
        self.assertDictEqual(result, expected)

    def test_get_etsi_context(self):
        result = pp.get_etsi_context(self.resource('etsi'))

        expected = [
            {'allCharacters': i.strip('NFV-SOL006-v'), 'alphaNumeric': pp.alnum(i.strip('NFV-SOL006-v'))}
            for i in ['NFV-SOL006-v2.6.1', 'NFV-SOL006-v2.7.1', 'NFV-SOL006-v2.8.1']
        ]
        self.assertEqual(result, expected)

    def test_get_openroadm_context(self):
        result = pp.get_openroadm_context(['bar1.0', 'foo1.0', 'foo1.1', 'foo1.2'])

        expected = [{'alphaNumeric': i, 'allCharacters': i} for i in ['bar1.0', 'foo1.0', 'foo1.1', 'foo1.2']]
        self.assertEqual(result, expected)
