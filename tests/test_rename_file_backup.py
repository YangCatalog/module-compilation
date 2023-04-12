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

import os
import shutil
import subprocess
import unittest
from datetime import datetime

import rename_file_backup as rfb


class TestRenameFileBackup(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.resource_path = os.path.join(os.environ['TESTS_RESOURCES_DIR'], 'rename_file_backup')
        cls.script_path = os.path.join(os.environ['VIRTUAL_ENV'], 'rename_file_backup.py')
        cls.private_directory = os.path.join(cls.resource_path, 'private')
        cls.backup_directory = os.path.join(cls.resource_path, 'backup')
        cls.filename = 'IETFYANGPageMain.html'
        cls.backup_filename = 'IETFYANGPageMain_{}.html'

    def setUp(self):
        shutil.rmtree(self.backup_directory, ignore_errors=True)

    def test_rename_file_backup(self) -> None:
        """
        Create a backup of the file with timestamp as suffix
        and test if the file exists and has the correct name.
        """
        rfb.rename_file_backup(self.private_directory, self.backup_directory, 1)

        file_to_backup = os.path.join(self.private_directory, self.filename)
        modified_time = os.path.getmtime(file_to_backup)
        timestamp = datetime.fromtimestamp(modified_time).strftime('%Y_%m_%d')

        backup_files = os.listdir(self.backup_directory)
        self.assertNotEqual(backup_files, [])

        backup_file = backup_files[0]
        self.assertEqual(backup_file, self.backup_filename.format(timestamp))

    def test_rename_file_backup_source_not_exists(self) -> None:
        """Method should not fail even if the source directory does not exist."""
        src_dir = os.path.join(os.environ['VIRTUAL_ENV'], 'tests/resources/non-existing-dir')
        result = rfb.rename_file_backup(src_dir, self.backup_directory, 1)

        self.assertEqual(result, None)

    def test_rename_file_backup_destination_missing(self) -> None:
        """Method should not fail even if the destination directory does not exist."""
        result = rfb.rename_file_backup(self.private_directory, '', 1)

        self.assertEqual(result, None)

    def test_rename_file_backup_from_console(self) -> None:
        """Run the script from the console by passing the arguments."""
        bash_command = (
            f'python {self.script_path} --srcdir {self.private_directory} --backupdir {self.backup_directory} --debug 1'
        )
        subprocess.run(bash_command, shell=True, capture_output=True, check=False).stdout.decode()

        file_to_backup = os.path.join(self.private_directory, self.filename)
        modified_time = os.path.getmtime(file_to_backup)
        timestamp = datetime.fromtimestamp(modified_time).strftime('%Y_%m_%d')

        backup_files = os.listdir(self.backup_directory)
        self.assertNotEqual(backup_files, [])

        backup_file = backup_files[0]
        self.assertEqual(backup_file, self.backup_filename.format(timestamp))


if __name__ == '__main__':
    unittest.main()
