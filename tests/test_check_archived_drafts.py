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

__author__ = 'Bohdan Konovalenko'
__copyright__ = 'Copyright The IETF Trust 2022, All Rights Reserved'
__license__ = 'Apache License, Version 2.0'
__email__ = 'bohdan.konovalenko@pantheon.tech'

import json
import os
import shutil
import unittest
from configparser import ConfigParser
from unittest.mock import MagicMock

from check_archived_drafts import CheckArchivedDrafts
from create_config import create_config


class MessageFactoryMock(MagicMock):
    pass


class TestCheckArchivedDrafts(unittest.TestCase):
    config: ConfigParser
    backup_directory: str
    web_private_directory: str
    directory_to_store_backup_files: str

    @classmethod
    def setUpClass(cls):
        resources_path = os.path.join(os.environ['VIRTUAL_ENV'], 'tests/resources/check_archived_drafts')
        cls.config = create_config()
        cls.config.set('Directory-Section', 'var', os.path.join(resources_path, 'var'))
        cls.config.set('Directory-Section', 'temp', os.path.join(resources_path, 'tmp'))
        cls.config.set('Directory-Section', 'ietf-directory', os.path.join(resources_path, 'ietf'))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.directory_to_store_backup_files, ignore_errors=True)

    def setUp(self):
        self.get_stats_instance: CheckArchivedDrafts = CheckArchivedDrafts(
            config=self.config,
            message_factory=MessageFactoryMock(),
        )

    def tearDown(self):
        for filename in os.listdir(self.directory_to_store_backup_files):
            shutil.copy2(
                os.path.join(self.directory_to_store_backup_files, filename),
                os.path.join(self.backup_directory, filename),
            )
        for filename in os.listdir(self.stats_directory):
            if not (self._check_filename_contains_prefix(filename) and 'Stats' in filename):
                continue
            with open(os.path.join(self.stats_directory, filename), 'w') as f:
                json.dump({}, f)


if __name__ == '__main__':
    unittest.main()
