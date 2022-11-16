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


import argparse
import datetime
import json
import os
import shutil
import time
import typing as t
from configparser import ConfigParser

import requests
from create_config import create_config
from extractors.draft_extractor import DraftExtractor
from job_log import job_log
from message_factory.message_factory import MessageFactory
from remove_directory_content import remove_directory_content

file_basename = os.path.basename(__file__)


class CheckArchivedDrafts:
    def __init__(
        self,
        config: ConfigParser = create_config(),
        debug: int = 0,
        message_factory: t.Optional[MessageFactory] = None,
    ):
        self.debug = debug
        self.message_factory = message_factory

        self.yangcatalog_api_prefix = config.get('Web-Section', 'yangcatalog-api-prefix')
        self.temp_dir = config.get('Directory-Section', 'temp')
        self.all_yang_drafts_strict = os.path.join(self.temp_dir, 'draft-with-YANG-strict')
        self.missing_modules_directory = os.path.join(self.temp_dir, 'drafts-missing-modules')
        self.extracted_missing_modules_directory = os.path.join(
            self.missing_modules_directory,
            'yangmodels/yang/experimental/ietf-extracted-YANG-modules',
        )
        self.all_yang_path = os.path.join(self.temp_dir, 'YANG-ALL')
        self.var_path = config.get('Directory-Section', 'var')
        ietf_directory = config.get('Directory-Section', 'ietf-directory')
        self.archived_draft_path = os.path.join(ietf_directory, 'my-id-archive-mirror')
        self.yang_path = os.path.join(ietf_directory, 'archived-drafts-modules')
        os.makedirs(self.all_yang_path, exist_ok=True)

        self.draft_extractor_paths = {
            'draft_path': self.archived_draft_path,
            'yang_path': self.yang_path,
            'draft_path_strict': self.all_yang_drafts_strict,
            'all_yang_path': self.all_yang_path,
        }
        self.draft_extractor = DraftExtractor(
            self.draft_extractor_paths,
            self.debug,
            extract_elements=False,
            extract_examples=False,
            copy_drafts=False,
        )

        self.all_modules_keys: list[str] = []
        self.modules_to_skip: tuple[str] = ()
        self.missing_modules: list[str] = []
        self.incorrect_revision_modules: list[str] = []

    def start_process(self):
        start = int(time.time())
        self._custom_print(f'Starting {file_basename} script')
        try:
            self._extract_drafts()
        except Exception as err:
            self._custom_print('Error occurred while extracting modules')
            end = int(time.time())
            job_log(start, end, self.temp_dir, file_basename, error=repr(err), status='Fail')
            return
        self._get_all_modules()
        self._get_incorrect_and_missing_modules()
        shutil.rmtree(self.yang_path)
        shutil.rmtree(self.all_yang_drafts_strict)
        if self.missing_modules:
            mf = self.message_factory or MessageFactory()
            mf.send_missing_modules(self.missing_modules, self.incorrect_revision_modules)
        message = {'label': 'Number of missing modules', 'message': len(self.missing_modules)}
        end = int(time.time())
        job_log(start, end, self.temp_dir, file_basename, messages=[message], status='Success')
        self._custom_print(f'end of {file_basename} job')
        shutil.rmtree(self.all_yang_path, ignore_errors=True)  # Cleaning created directory

    def _extract_drafts(self):
        remove_directory_content(self.yang_path, self.debug)
        remove_directory_content(self.missing_modules_directory, self.debug)
        remove_directory_content(self.all_yang_drafts_strict, self.debug)

        self._custom_print(f'Extracting modules from drafts stored in {self.archived_draft_path}')
        self.draft_extractor.extract()

    def _get_all_modules(self):
        self._custom_print('Loading all modules data from API')
        all_modules = requests.get(f'{self.yangcatalog_api_prefix}/search/modules').json()
        if all_modules:
            all_modules = all_modules.get('module', [])
            self.all_modules_keys = [f'{m.get("name")}@{m.get("revision")}' for m in all_modules]
        try:
            resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')
            with open(os.path.join(resources_dir, 'old-rfcs.json'), 'r') as f:
                old_modules = json.load(f)
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            old_modules = []
        try:
            with open(os.path.join(self.var_path, 'unparsable-modules.json'), 'r') as f:
                unparsable_modules = json.load(f)
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            unparsable_modules = []
        self.modules_to_skip = (*old_modules, *unparsable_modules)

    def _get_incorrect_and_missing_modules(self):
        os.makedirs(self.extracted_missing_modules_directory, exist_ok=True)
        for yang_file in self.draft_extractor.inverted_draft_yang_dict:
            if (
                yang_file.startswith('example')
                or yang_file.startswith('@')
                or any(yang_file in module for module in self.modules_to_skip)
            ):
                continue
            name_revision = yang_file.split('.yang')[0]
            if '@' in name_revision:
                revision = name_revision.split('@')[-1]
                _, month, day = revision.split('-')
                if len(month) != 2 or len(day) != 2:
                    self.incorrect_revision_modules.append(yang_file)
                    continue
            else:
                name_revision += '@1970-01-01'
            if name_revision in self.all_modules_keys:
                continue
            self.missing_modules.append(yang_file)
            shutil.copy2(
                os.path.join(self.yang_path, yang_file),
                os.path.join(self.extracted_missing_modules_directory, yang_file),
            )

    def _custom_print(self, message: str):
        timestamp = f'{datetime.datetime.now().time()} ({os.getpid()}):'
        print(f'{timestamp} {message}', flush=True)


def main():
    parser = argparse.ArgumentParser(description='Check if modules from all the Drafts are populated in YANG Catalog')
    parser.add_argument('--debug', help='Debug level - default is 0', type=int, default=0)
    args = parser.parse_args()
    CheckArchivedDrafts(debug=args.debug).start_process()


if __name__ == '__main__':
    main()
