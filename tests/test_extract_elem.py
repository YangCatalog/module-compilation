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

import filecmp
import os
import unittest

import extract_elem as ee


class TestExtractElem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.resource_path = os.path.join(os.environ['VIRTUAL_ENV'], 'tests/resources/extract_elem')

    def test_extract_elem_grouping(self):
        groupings = [
            'grouping-catalog-module-metadata.txt',
            'grouping-online-source-file.txt',
            'grouping-organization-specific-metadata.txt',
            'grouping-shared-implementation-leafs.txt',
            'grouping-shared-module-leafs.txt',
            'grouping-yang-lib-common-leafs.txt',
            'grouping-yang-lib-implementation-leafs.txt',
            'grouping-yang-lib-schema-leaf.txt',
        ]

        ee.extract_elem(
            os.path.join(self.resource_path, 'yang-catalog@2018-04-03.yang'),
            os.path.join(self.resource_path, 'extracted'),
            'grouping',
        )
        match, mismatch, errors = filecmp.cmpfiles(
            os.path.join(self.resource_path, 'extracted'),
            os.path.join(self.resource_path, 'expected'),
            groupings,
        )
        self.assertFalse(mismatch or errors)

    def test_extract_elem_identity(self):
        identities = ['identity-netconf.txt', 'identity-protocol.txt', 'identity-restconf.txt']

        ee.extract_elem(
            os.path.join(self.resource_path, 'yang-catalog@2018-04-03.yang'),
            os.path.join(self.resource_path, 'extracted'),
            'identity',
        )
        match, mismatch, errors = filecmp.cmpfiles(
            os.path.join(self.resource_path, 'extracted'),
            os.path.join(self.resource_path, 'expected'),
            identities,
        )
        self.assertFalse(mismatch or errors)

    def test_extract_elem_typedef(self):
        typedefs = ['typedef-email-address.txt', 'typedef-path.txt', 'typedef-semver.txt']

        ee.extract_elem(
            os.path.join(self.resource_path, 'yang-catalog@2018-04-03.yang'),
            os.path.join(self.resource_path, 'extracted'),
            'typedef',
        )
        match, mismatch, errors = filecmp.cmpfiles(
            os.path.join(self.resource_path, 'extracted'),
            os.path.join(self.resource_path, 'expected'),
            typedefs,
        )
        self.assertFalse(mismatch or errors)


if __name__ == '__main__':
    unittest.main()
