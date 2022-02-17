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
from parsers.pyangParser import PyangParser
from utility.utility import (check_yangcatalog_data, module_or_submodule,
                             push_to_confd)
from versions import ValidatorsVersions


class ExamplesCompilator:
    def __init__(self, extracted_examples_dir: str, examples_draft_dict: dict, debug_level: int = 0):
        self.config = create_config()
        self.pyang_exec = self.config.get('Tool-Section', 'pyang-exec')
        self.html_path = self.config.get('Web-Section', 'private-directory')
        self.result_html_dir = self.config.get('Web-Section', 'result-html-dir')

        self.extracted_examples_dir = extracted_examples_dir
        self.examples_draft_dict = examples_draft_dict
        self.debug_level = debug_level

        self.results_dict = {}
        self.results_no_submodules_dict = {}

    def _resolve_compilation_status(self, pyang_result: str):
        if 'error:' in pyang_result:
            return 'FAILED'
        elif 'warning:' in pyang_result:
            return 'PASSED WITH WARNINGS'
        elif pyang_result == '':
            return 'PASSED'
        else:
            return 'UNKNOWN'

    def compile_examples(self, all_yang_catalog_metadata: dict, force_compilation: bool):
        fileHasher = FileHasher(force_compilation)
        pyangParser = PyangParser(self.debug_level)
        validators_versions = ValidatorsVersions()
        versions = validators_versions.get_versions()

        updated_modules = []

        try:
            with open(os.path.join(self.html_path, 'IETFDraftExample.json'), 'r') as f:
                existing_results_dict = json.load(f)
        except Exception:
            existing_results_dict = {}

        for yang_file in self.examples_draft_dict:
            yang_file_path = os.path.join(self.extracted_examples_dir, yang_file)
            should_parse, file_hash = fileHasher.should_parse(yang_file_path)
            yang_file_compilation = existing_results_dict.get(yang_file, None)

            if should_parse or yang_file_compilation is None:
                pyang_result = pyangParser.run_pyang_ietf(yang_file_path, ietf=True)
                pyang_result_no_ietf_flag = pyangParser.run_pyang_ietf(yang_file_path, ietf=False)

                document_name = self.examples_draft_dict.get(yang_file, '')
                draft_name = document_name.split('.')[0]
                version_number = draft_name.split('-')[-1]
                draft_name = draft_name.rstrip('-0123456789')
                mailto = '{}@ietf.org'.format(draft_name)
                datatracker_url = 'https://datatracker.ietf.org/doc/{}/{}'.format(draft_name, version_number)
                draft_url_anchor = '<a href="{}">{}</a>'.format(datatracker_url, document_name)
                email_anchor = '<a href="mailto:{}">Email Authors</a>'.format(mailto)
                compilation_status = self._resolve_compilation_status(pyang_result)
                compilation_results = {
                    'pyang_lint': pyang_result,
                    'pyang': pyang_result_no_ietf_flag
                }
                updated_modules.extend(
                    check_yangcatalog_data(self.config, yang_file_path, datatracker_url, document_name, mailto,
                                           compilation_status, compilation_results, all_yang_catalog_metadata, False,
                                           versions, 'ietf-example'))
                if len(updated_modules) > 100:
                    updated_modules = push_to_confd(updated_modules, self.config)
                yang_file_compilation = [draft_url_anchor, email_anchor, compilation_status, pyang_result, pyang_result_no_ietf_flag]

                # Do not store hash if compilation result is 'UNKNOWN' -> try to parse model again next time
                if compilation_status != 'UNKNOWN':
                    fileHasher.updated_hashes[yang_file_path] = file_hash

            self.results_dict[yang_file] = yang_file_compilation
            if module_or_submodule(yang_file_path) == 'module':
                self.results_no_submodules_dict[yang_file] = yang_file_compilation

        updated_modules = push_to_confd(updated_modules, self.config)
        # Update files content hashes and dump into .json file
        if len(fileHasher.updated_hashes) > 0:
            fileHasher.dump_hashed_files_list(fileHasher.updated_hashes)
