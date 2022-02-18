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

__author__ = 'Slavomir Mazur'
__copyright__ = 'Copyright The IETF Trust 2021, All Rights Reserved'
__license__ = 'Apache License, Version 2.0'
__email__ = 'slavomir.mazur@pantheon.tech'

import hashlib
import json

from filelock import FileLock

from create_config import create_config
from versions import ValidatorsVersions


class FileHasher:
    def __init__(self, forcecompilation: bool = False):
        config = create_config()
        self.cache_dir = config.get('Directory-Section', 'cache')

        self.forcecompilation = forcecompilation
        self.validators_versions_bytes = self.get_versions()
        self.files_hashes = self.load_hashed_files_list()
        self.updated_hashes = {}

    def hash_file(self, path: str):
        """ Create hash from content of the given file and validators versions.
        Each time either the content of the file or the validator version change,
        the resulting hash will be different.

        :param path     (str) Path fo file to be hashed
        :return         SHA256 hash of the content of the given file
        :rtype          str
        """
        BLOCK_SIZE = 65536  # The size of each read from the file

        file_hash = hashlib.sha256()
        with open(path, 'rb') as f:
            fb = f.read(BLOCK_SIZE)
            while len(fb) > 0:
                file_hash.update(fb)
                fb = f.read(BLOCK_SIZE)

        file_hash.update(self.validators_versions_bytes)

        return file_hash.hexdigest()

    def load_hashed_files_list(self, dst_dir: str = ''):
        """ Load dumped list of files content hashes from .json file.
        Several threads can access this file at once, so locking the file while accessing is necessary.
        """
        dst_dir = self.cache_dir if dst_dir == '' else dst_dir

        with FileLock('{}/sdo_files_modification_hashes.json.lock'.format(dst_dir)):
            print('Lock acquired.')
            try:
                with open('{}/sdo_files_modification_hashes.json'.format(dst_dir), 'r') as f:
                    hashed_files_list = json.load(f)
                    print('Dictionary of {} hashes loaded successfully'.format(len(hashed_files_list)))
            except FileNotFoundError as e:
                hashed_files_list = {}

        return hashed_files_list

    def dump_hashed_files_list(self, files_hashes: dict, dst_dir: str = ''):
        """ Dumped updated list of files content hashes into .json file.
        Several threads can access this file at once, so locking the file while accessing is necessary.
        """
        dst_dir = self.cache_dir if dst_dir == '' else dst_dir

        # Load existing hashes, merge with new one, then dump all to the .json file
        with FileLock('{}/sdo_files_modification_hashes.json.lock'.format(dst_dir)):
            try:
                with open('{}/sdo_files_modification_hashes.json'.format(dst_dir), 'r') as f:
                    hashes_in_file = json.load(f)
                    print('Dictionary of {} hashes loaded successfully'.format(len(hashes_in_file)))
            except FileNotFoundError as e:
                hashes_in_file = {}

            merged_files_hashes = {**hashes_in_file, **files_hashes}

            with open('{}/sdo_files_modification_hashes.json'.format(dst_dir), 'w') as f:
                json.dump(merged_files_hashes, f, indent=2, sort_keys=True)
            print('Dictionary of {} hashes successfully dumped into .json file'.format(len(merged_files_hashes)))

    def get_versions(self):
        """ Return encoded validators versions dictionary.
        """
        validators_versions = ValidatorsVersions()
        actual_versions = validators_versions.get_versions()
        return json.dumps(actual_versions).encode('utf-8')

    def should_parse(self, path: str):
        """ Decide whether module at the given path should be parsed or not.
        Check whether file content hash has changed and keep it for the future use.

        Argument:
            :param path     (str) Full path to the file to be hashed
        """
        hash_changed = False
        file_hash = self.hash_file(path)
        old_file_hash = self.files_hashes.get(path, None)
        if old_file_hash is None or old_file_hash != file_hash:
            hash_changed = True

        return [self.forcecompilation or hash_changed, file_hash]
