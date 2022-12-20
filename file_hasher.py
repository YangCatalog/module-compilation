# Copyright The IETF Trust 2021, All Rights Reserved
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

"""
This file contains FileHasher class which defines the functionality
for hashing the contents of files. SHA256 hash is created from the content
of the file, and also versions of the validators which were used
for validation. Every time either content of the file or a version
of one of the validators used is changed - hash will be completely different.
Different hash means that the file needs to be re-validated.
"""

__author__ = 'Slavomir Mazur'
__copyright__ = 'Copyright The IETF Trust 2021, All Rights Reserved'
__license__ = 'Apache License, Version 2.0'
__email__ = 'slavomir.mazur@pantheon.tech'

import hashlib
import json
import os.path
from configparser import ConfigParser
from dataclasses import dataclass

import filelock

from create_config import create_config

BLOCK_SIZE = 65536  # The size of each read from the file


class FileHasher:
    def __init__(self, dst_dir: str = '', force_compilation: bool = False, config: ConfigParser = create_config()):
        self.cache_dir = config.get('Directory-Section', 'cache')
        self.force_compilation = force_compilation
        self.files_hashes = self._load_hashed_files_list(dst_dir)
        self.updated_hashes = {}

    def hash_file(self, path: str) -> str:
        """
        Create hash from content of the given file and validators versions.
        Each time either the content of the file or the validator version change,
        the resulting hash will be different.

        :param path     (str) Path fo file to be hashed
        :return         SHA256 hash of the content of the given file
        :rtype          str
        """
        file_hash = hashlib.sha256()
        with open(path, 'rb') as reader:
            file_block = reader.read(BLOCK_SIZE)
            while len(file_block) > 0:
                file_hash.update(file_block)
                file_block = reader.read(BLOCK_SIZE)
        return file_hash.hexdigest()

    def _load_hashed_files_list(self, dst_dir: str = '') -> dict:
        """
        Load dumped list of files content hashes from .json file.
        Several threads can access this file at once, so locking the file
        while accessing is necessary.
        """
        dst_dir = dst_dir or self.cache_dir

        with filelock.FileLock(os.path.join(dst_dir, 'sdo_files_modification_hashes.json.lock')):
            print('Lock acquired.')
            try:
                with open(os.path.join(dst_dir, 'sdo_files_modification_hashes.json'), 'r') as reader:
                    hashed_files_list = json.load(reader)
                    print(f'Dictionary of {len(hashed_files_list)} hashes loaded successfully')
            except FileNotFoundError:
                hashed_files_list = {}

        return hashed_files_list

    def dump_hashed_files_list(self, dst_dir: str = ''):
        """
        Dumped updated list of files content hashes into .json file.
        Several threads can access this file at once, so locking the file
        while accessing is necessary.
        """
        if not self.updated_hashes:
            return

        dst_dir = self.cache_dir if dst_dir == '' else dst_dir

        # Load existing hashes, merge with new one, then dump all to the .json file
        with filelock.FileLock(os.path.join(dst_dir, 'sdo_files_modification_hashes.json.lock')):
            try:
                with open(os.path.join(dst_dir, 'sdo_files_modification_hashes.json'), 'r') as reader:
                    hash_cache = json.load(reader)
                    print(f'Dictionary of {len(hash_cache)} hashes loaded successfully')
            except FileNotFoundError:
                hash_cache = {}

            hash_cache.update(self.updated_hashes)

            with open(os.path.join(dst_dir, 'sdo_files_modification_hashes.json'), 'w') as writer:
                json.dump(hash_cache, writer, indent=2, sort_keys=True)
            print(f'Dictionary of {len(hash_cache)} hashes successfully dumped into .json file')

    @dataclass
    class ModuleHashCheckForParsing:
        hash_changed: bool
        hash: str
        validator_versions: dict

        def get_changed_validator_versions(self, validators_to_check: dict) -> list[str]:
            changed_validators = []
            for validator, version in validators_to_check.items():
                if self.validator_versions.get(validator) == version:
                    continue
                changed_validators.append(validator)
            return changed_validators

    def should_parse(self, path: str) -> ModuleHashCheckForParsing:
        """
        Decide whether module at the given path should be parsed or not.
        Check whether file content hash has changed and keep it for the future use.

        Argument:
            :param path     (str) Full path to the file to be hashed
        """
        file_hash = self.hash_file(path)
        old_file_hash_info = self.files_hashes.get(path)
        if not old_file_hash_info or not isinstance(old_file_hash_info, dict):
            return self.ModuleHashCheckForParsing(hash_changed=True, hash=file_hash, validator_versions={})
        return self.ModuleHashCheckForParsing(
            hash_changed=self.force_compilation or old_file_hash_info['hash'] != file_hash,
            hash=file_hash,
            validator_versions=old_file_hash_info['validator_versions'],
        )
