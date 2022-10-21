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

import extract_emails as ee


class TestExtractElem(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.resource_path = os.path.join(os.environ['VIRTUAL_ENV'], 'tests/resources/extract_emails')

    def test_extract_emails(self):
        result = ee.extract_email_string(os.path.join(self.resource_path, 'emails.txt'), 'foo.com')
        self.assertSetEqual(set(result.split(',')), {'foo@foo.com', 'bar@foo.com', 'foobar@foo.com'})

    def test_list_of_ietf_drafts(self):
        result = ee.list_of_ietf_drafts(os.path.join(self.resource_path, 'drafts'))
        self.assertSetEqual(set(result), {'draft-foo.txt', 'draft-bar.txt'})


if __name__ == '__main__':
    unittest.main()
