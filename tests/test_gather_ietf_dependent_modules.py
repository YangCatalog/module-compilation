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


__author__ = 'Slavomir Mazur'
__copyright__ = 'Copyright The IETF Trust 2022, All Rights Reserved'
__license__ = 'Apache License, Version 2.0'
__email__ = 'slavomir.mazur@pantheon.tech'

import json
import os
import shutil
import unittest
from unittest import mock

from create_config import create_config
from gather_ietf_dependent_modules import copy_modules


class TestGatherIetfDependentModules(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        config = create_config()
        self.resource_path = os.path.join(os.environ['VIRTUAL_ENV'], 'tests/resources/gather_ietf_dependent_modules')
        self.yangcatalog_api_prefix = config.get('Web-Section', 'yangcatalog-api-prefix')
        self.ietf_dependencies_dir = os.path.join(self.resource_path, 'dependencies')
        self.payloads_file = os.path.join(self.resource_path, 'payloads.json')

    def setUp(self) -> None:
        shutil.rmtree(self.ietf_dependencies_dir, ignore_errors=True)

    @mock.patch('requests.post')
    def test_copy_modules(self, mock_post: mock.MagicMock) -> None:
        """ Test whether the yang files have been copied to the destination directory. """
        with open(self.payloads_file, 'r', encoding='utf-8') as reader:
            content = json.load(reader)
        mock_post.return_value.json.return_value = content['search-filter-ietf']
        src_dir = os.path.join(self.resource_path, 'all_modules')
        copied_modules = copy_modules(self.yangcatalog_api_prefix, src_dir, self.ietf_dependencies_dir)

        self.assertIn('ietf-test@2022-08-01.yang', copied_modules)
        copied_files = os.listdir(self.ietf_dependencies_dir)
        self.assertNotEqual(copied_files, [])
        copied_file = copied_files[0]
        self.assertEqual('ietf-test@2022-08-01.yang', copied_file)

    @mock.patch('requests.post')
    def test_copy_modules_no_src_dir(self, mock_post: mock.MagicMock) -> None:
        """ Destination directory should be empty if the source directory does not exist. """
        with open(self.payloads_file, 'r', encoding='utf-8') as reader:
            content = json.load(reader)
        mock_post.return_value.json.return_value = content['search-filter-ietf']
        src_dir = os.path.join(self.resource_path, 'non_existing_dir')
        copied_modules = copy_modules(self.yangcatalog_api_prefix, src_dir, self.ietf_dependencies_dir)

        self.assertEqual(copied_modules, set())
        copied_files = os.listdir(self.ietf_dependencies_dir)
        self.assertEqual(copied_files, [])

    @mock.patch('requests.post')
    def test_copy_modules_400_response(self, mock_post: mock.MagicMock) -> None:
        """ Destination directory should be empty if server responded with 400/404 error message. """
        with open(self.payloads_file, 'r', encoding='utf-8') as reader:
            content = json.load(reader)
        mock_post.return_value.json.return_value = content['search-filter-ietf-400-response']
        src_dir = os.path.join(self.resource_path, 'all_modules')
        copied_modules = copy_modules(self.yangcatalog_api_prefix, src_dir, self.ietf_dependencies_dir)

        self.assertEqual(copied_modules, set())
        copied_files = os.listdir(self.ietf_dependencies_dir)
        self.assertEqual(copied_files, [])


if __name__ == '__main__':
    unittest.main()
