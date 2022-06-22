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

from create_config import create_config
from fileHasher import FileHasher
from utility.utility import (check_yangcatalog_data, module_or_submodule,
                             push_to_confd)
from versions import ValidatorsVersions


class RfcsCompilator:
    def __init__(self, extracted_rfcs_dir: str, rfcs_dict: dict, debug_level: int = 0):
        self.config = create_config()
        self.html_path = self.config.get('Web-Section', 'private-directory')
        self.result_html_dir = self.config.get('Web-Section', 'result-html-dir')

        self.extracted_rfcs_dir = extracted_rfcs_dir
        self.rfcs_dict = rfcs_dict
        self.debug_level = debug_level

        self.results_dict = {}
        self.results_no_submodules_dict = {}

    def compile_rfcs(self, all_yang_catalog_metadata: dict, force_compilation: bool):
        fileHasher = FileHasher(force_compilation)
        validators_versions = ValidatorsVersions()
        versions = validators_versions.get_versions()

        updated_modules = []

        try:
            with open(os.path.join(self.html_path, 'IETFYANGRFC.json'), 'r') as f:
                existing_results_dict = json.load(f)
        except Exception:
            existing_results_dict = {}

        for yang_file in self.rfcs_dict:
            yang_file_path = os.path.join(self.extracted_rfcs_dir, yang_file)
            should_parse, file_hash = fileHasher.should_parse(yang_file_path)
            rfc_url_anchor = existing_results_dict.get(yang_file, '')

            if should_parse or rfc_url_anchor == '':
                document_name = self.rfcs_dict[yang_file]
                rfc_name = document_name.split('.')[0]
                mailto = None
                datatracker_url = 'https://datatracker.ietf.org/doc/html/{}'.format((rfc_name))
                rfc_url_anchor = '<a href="{}">{}</a>'.format(datatracker_url, rfc_name)
                compilation_status = None
                updated_modules.extend(
                    check_yangcatalog_data(self.config, yang_file_path, datatracker_url, document_name, mailto,
                                           compilation_status, {}, all_yang_catalog_metadata, True, versions, 'ietf-rfc'))
                if len(updated_modules) > 100:
                    updated_modules = push_to_confd(updated_modules, self.config)
                fileHasher.updated_hashes[yang_file_path] = file_hash

            self.results_dict[yang_file] = rfc_url_anchor
            if module_or_submodule(yang_file_path) == 'module':
                self.results_no_submodules_dict[yang_file] = rfc_url_anchor

        updated_modules = push_to_confd(updated_modules, self.config)
        # Update files content hashes and dump into .json file
        if len(fileHasher.updated_hashes) > 0:
            fileHasher.dump_hashed_files_list(fileHasher.updated_hashes)
