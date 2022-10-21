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

import json
import os
import shutil
import subprocess
import unittest

from file_hasher import FileHasher
from versions import ValidatorsVersions


class TestFileHasher(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.resource_path = os.path.join(os.environ['VIRTUAL_ENV'], 'tests/resources/file_hasher')
        for file in [
            'sdo_files_modification_hashes.json',
            'sdo_files_modification_hashes.json.lock',
            'versions.json',
            'correct.json',
            'incorrect.json',
        ]:
            try:
                os.remove(self.resource(file))
            except FileNotFoundError:
                pass
            self.create_hash_files()

    def create_hash_files(self):
        with open(self.resource('versions.json'), 'w') as f:
            json.dump(ValidatorsVersions().get_versions(), f)
        hash_dict = {
            self.resource('file.txt'): self.compute_hash('file.txt'),
            self.resource('other_file.txt'): self.compute_hash('other_file.txt'),
        }
        with open(self.resource('correct.json'), 'w') as f:
            json.dump(hash_dict, f)
        hash_dict[self.resource('file.txt')] = 64 * '0'
        with open(self.resource('incorrect.json'), 'w') as f:
            json.dump(hash_dict, f)

    def compute_hash(self, file):
        command = 'cat {} {} | sha256sum'.format(self.resource(file), self.resource('versions.json'))
        return subprocess.run(command, shell=True, capture_output=True).stdout.decode().split()[0]

    def resource(self, file):
        return os.path.join(self.resource_path, file)

    def test_hash_values(self):
        fh = FileHasher(dst_dir=self.resource_path, force_compilation=False)
        _, hash = fh.should_parse(self.resource('file.txt'))
        fh.updated_hashes[self.resource('file.txt')] = hash
        _, hash = fh.should_parse(self.resource('other_file.txt'))
        fh.updated_hashes[self.resource('other_file.txt')] = hash
        fh.dump_hashed_files_list(self.resource_path)

        with open(self.resource('correct.json')) as f:
            expected = json.load(f)
        with open(self.resource('sdo_files_modification_hashes.json')) as f:
            result = json.load(f)

        self.assertDictEqual(result, expected)

    def test_invalidate_hashes(self):
        shutil.copy(self.resource('incorrect.json'), self.resource('sdo_files_modification_hashes.json'))

        fh = FileHasher(dst_dir=self.resource_path, force_compilation=False)
        _, hash = fh.should_parse(self.resource('file.txt'))
        fh.updated_hashes[self.resource('file.txt')] = hash
        _, hash = fh.should_parse(self.resource('other_file.txt'))
        fh.updated_hashes[self.resource('other_file.txt')] = hash
        fh.dump_hashed_files_list(self.resource_path)

        with open(self.resource('correct.json')) as f:
            expected = json.load(f)
        with open(self.resource('sdo_files_modification_hashes.json')) as f:
            result = json.load(f)

        self.assertDictEqual(result, expected)

    def test_should_parse(self):
        shutil.copy(self.resource('incorrect.json'), self.resource('sdo_files_modification_hashes.json'))

        fh = FileHasher(dst_dir=self.resource_path, force_compilation=False)
        should_parse, _ = fh.should_parse(self.resource('file.txt'))
        self.assertEqual(should_parse, True)
        should_parse, _ = fh.should_parse(self.resource('other_file.txt'))
        self.assertEqual(should_parse, False)

    def test_force_compilation(self):
        shutil.copy(self.resource('correct.json'), self.resource('sdo_files_modification_hashes.json'))

        fh = FileHasher(dst_dir=self.resource_path, force_compilation=True)
        should_parse, _ = fh.should_parse(self.resource('file.txt'))
        self.assertEqual(should_parse, True)
        should_parse, _ = fh.should_parse(self.resource('other_file.txt'))
        self.assertEqual(should_parse, True)
