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
import unittest

from exclude_bad_drafts import (list_lines_from_file, remove_drafts,
                                replace_draft_versions_by_asterisk)


class TestExcludeBadDrafts(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.resource_path = os.path.join(os.environ['VIRTUAL_ENV'], 'tests/resources/exclude_bad_drafts')
        self.exclude_filename = 'IETF-drafts-list-with-no-YANG-models.txt'
        self.draft_name = 'draft-cel-nfsv4-federated-fs-nce-01.txt'
        self.dst_dir = os.path.join(self.resource_path, 'my-id-mirror')
        self.debug_level = 1

    def setUp(self) -> None:
        shutil.rmtree(self.dst_dir, ignore_errors=True)
        os.makedirs(self.dst_dir, exist_ok=True)
        open(self.draft_name, 'w', encoding='utf-8').close()

    def test_list_lines_from_file(self) -> None:
        """ Try to get a list of lines from a file. """
        path = os.path.join(self.resource_path, self.exclude_filename)
        lines = list_lines_from_file(path, self.debug_level)

        self.assertIn(self.draft_name, lines)

    def test_list_lines_from_file_non_existing_file(self) -> None:
        """ Try to get a list of lines from non existing file - should be empty.  """
        path = os.path.join(self.resource_path, 'non-existing-file.txt')
        lines = list_lines_from_file(path, self.debug_level)

        self.assertEqual(lines, [])

    def test_replace_draft_versions_by_asterisk(self) -> None:
        """ Try to get a list of lines with versions replaced by asterisk. """
        lines = [self.draft_name]
        expected = 'draft-cel-nfsv4-federated-fs-nce*'
        list_of_lines_asterisk = replace_draft_versions_by_asterisk(lines, self.debug_level)

        self.assertIn(expected, list_of_lines_asterisk)

    def test_replace_draft_versions_by_asterisk_empty_list(self) -> None:
        """ Try to get a list of replaces versions, but use empty list. """
        list_of_lines_asterisk = replace_draft_versions_by_asterisk([], self.debug_level)

        self.assertEqual(list_of_lines_asterisk, [])

    def test_remove_drafts(self) -> None:
        """ Test if the file was successfully removed from the directory. """
        list_of_lines_asterisk = ['draft-cel-nfsv4-federated-fs-nce*']
        remove_drafts(list_of_lines_asterisk, self.dst_dir, self.debug_level)

        draft_files = os.listdir(self.dst_dir)
        self.assertNotIn(self.draft_name, draft_files)


if __name__ == '__main__':
    unittest.main()
