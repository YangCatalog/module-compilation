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

import json
import os
import re
import shutil
import sys
import typing as t
from io import StringIO

from extract_elem import extract_elem
from extractors.helper import check_after_xym_extraction, invert_yang_modules_dict, remove_invalid_files
from message_factory.message_factory import MessageFactory
from xym import xym


class DraftExtractor:
    def __init__(
        self,
        draft_extractor_paths: dict,
        debug_level: int,
        extract_elements: bool = True,
        extract_examples: bool = True,
        copy_drafts: bool = True,
        message_factory: t.Optional[MessageFactory] = None,
    ):
        self.draft_path = draft_extractor_paths.get('draft_path', '')
        self.yang_path = draft_extractor_paths.get('yang_path', '')
        self.draft_elements_path = draft_extractor_paths.get('draft_elements_path', '')
        self.draft_path_strict = draft_extractor_paths.get('draft_path_strict', '')
        self.all_yang_example_path = draft_extractor_paths.get('all_yang_example_path', '')
        self.draft_path_only_example = draft_extractor_paths.get('draft_path_only_example', '')
        self.all_yang_path = draft_extractor_paths.get('all_yang_path', '')
        self.draft_path_no_strict = draft_extractor_paths.get('draft_path_no_strict', '')
        self.debug_level = debug_level
        self.extract_examples = extract_examples
        self.extract_elements = extract_elements
        self.copy_drafts = copy_drafts
        self.ietf_drafts = []
        self.draft_yang_dict = {}
        self.draft_yang_example_dict = {}
        self.draft_yang_all_dict = {}
        self.inverted_draft_yang_dict = {}
        self.inverted_draft_yang_example_dict = {}
        self.inverted_draft_yang_all_dict = {}
        self.drafts_missing_code_section = {}
        self._create_ietf_drafts_list()
        self.message_factory = message_factory

    @property
    def message_factory(self):
        if not self._message_factory:
            self.message_factory = MessageFactory(close_connection_after_message_sending=False)
        return self._message_factory

    @message_factory.setter
    def message_factory(self, value: t.Optional[MessageFactory]):
        self._message_factory = value

    def _create_ietf_drafts_list(self):
        for filename in os.listdir(self.draft_path):
            if not filename.endswith('.txt'):
                continue
            full_path = os.path.join(self.draft_path, filename)
            if os.path.isfile(full_path):
                try:
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        for line in f:
                            if '<CODE BEGINS>' in line:
                                self.ietf_drafts.append(filename)
                                break
                except Exception:
                    continue
        self.ietf_drafts.sort()
        print('Drafts list created')

    def extract(self):
        self.extract_drafts()
        self.invert_dict()
        self.remove_invalid_files()

    def extract_drafts(self):
        for draft_file in self.ietf_drafts:
            draft_file_path = os.path.join(self.draft_path, draft_file)

            # Extract the correctly formatted YANG Models into yang_path
            extracted_yang_models = self.extract_from_draft_file(
                draft_file,
                self.draft_path,
                self.yang_path,
                strict=True,
            )

            if extracted_yang_models:
                correct = check_after_xym_extraction(draft_file, extracted_yang_models)
                if not correct:
                    self.ietf_drafts.remove(draft_file)
                    continue

                if self.debug_level > 0:
                    print('DEBUG: Extracted YANG models from Draft\n {}'.format(str(extracted_yang_models)))

                # typedef, grouping and identity extraction from Drafts
                if self.extract_elements:
                    self.extract_all_elements(extracted_yang_models)

                self.draft_yang_dict[draft_file] = extracted_yang_models
                # copy the draft file in a specific directory for strict = True
                if self.copy_drafts:
                    shutil.copy2(draft_file_path, self.draft_path_strict)

            # Extract the correctly formatted example YANG Models into all_yang_example_path
            if self.extract_examples:
                extracted_yang_models = self.extract_from_draft_file(
                    draft_file,
                    self.draft_path,
                    self.all_yang_example_path,
                    strict=True,
                    strict_examples=True,
                )
                if extracted_yang_models:
                    correct = check_after_xym_extraction(draft_file, extracted_yang_models)
                    if not correct:
                        self.ietf_drafts.remove(draft_file)
                        continue

                    if self.debug_level > 0:
                        print('DEBUG: Extracted YANG models from Draft\n {}'.format(str(extracted_yang_models)))

                    self.draft_yang_example_dict[draft_file] = extracted_yang_models
                    # copy the draft file in a specific directory for strict = True
                    if self.copy_drafts:
                        shutil.copy2(draft_file_path, self.draft_path_only_example)

            # Extract all YANG Models, including the wrongly formatted ones, in all_yang_path
            extracted_yang_models = self.extract_from_draft_file(draft_file, self.draft_path, self.all_yang_path)

            if extracted_yang_models:
                correct = check_after_xym_extraction(draft_file, extracted_yang_models)
                if not correct:
                    self.ietf_drafts.remove(draft_file)
                    continue

                if self.debug_level > 0:
                    print('DEBUG: Extracted YANG models from Draft\n {}'.format(str(extracted_yang_models)))

                self.draft_yang_all_dict[draft_file] = extracted_yang_models
                # copy the draft file in a specific directory for strict = False
                if self.copy_drafts:
                    shutil.copy2(draft_file_path, self.draft_path_no_strict)

    def extract_from_draft_file(
        self,
        draft_file: str,
        srcdir: str,
        dstdir: str,
        strict: bool = False,
        strict_examples: bool = False,
    ):

        extracted = []
        old_stderr = None
        try:
            old_stderr = sys.stderr
            result = StringIO()
            sys.stderr = result
            extracted = xym.xym(
                draft_file,
                srcdir,
                dstdir,
                strict=strict,
                strict_examples=strict_examples,
                debug_level=self.debug_level,
                add_line_refs=False,
                force_revision_pyang=False,
                force_revision_regexp=True,
            )
            result_string = result.getvalue()
        finally:
            sys.stderr = old_stderr
        print(result_string, file=sys.stderr)
        if 'WARNING' in result_string or 'ERROR' in result_string:
            # remove "File <file name> exists" error messages
            clean = ''.join(line for line in result_string.splitlines(True) if 'exists' not in line)
            self.drafts_missing_code_section[draft_file] = clean
        return extracted

    def invert_dict(self):
        self.inverted_draft_yang_dict = invert_yang_modules_dict(self.draft_yang_dict, self.debug_level)
        self.inverted_draft_yang_example_dict = invert_yang_modules_dict(self.draft_yang_example_dict, self.debug_level)
        self.inverted_draft_yang_all_dict = invert_yang_modules_dict(self.draft_yang_all_dict, self.debug_level)

    def remove_invalid_files(self):
        remove_invalid_files(self.yang_path, self.inverted_draft_yang_dict)
        remove_invalid_files(self.all_yang_example_path, self.inverted_draft_yang_example_dict)
        remove_invalid_files(self.all_yang_path, self.inverted_draft_yang_all_dict)

    def extract_all_elements(self, extracted_yang_models: list):
        """Extract typedefs, groupings and identities from data models into .txt files.
        These elements are not extracted from example models.
        """
        for extracted_model in extracted_yang_models:
            if not extracted_model.startswith('example-'):
                print('Identifier definition extraction for {}'.format(extracted_model))
                module_fname = os.path.join(self.yang_path, extracted_model)
                extract_elem(module_fname, self.draft_elements_path, 'typedef')
                extract_elem(module_fname, self.draft_elements_path, 'grouping')
                extract_elem(module_fname, self.draft_elements_path, 'identity')

    def dump_incorrect_drafts(self, public_directory: str, send_emails_about_problematic_drafts: bool = True):
        """Dump names of the IETF drafts with xym extraction error to problematic_drafts.json file."""
        drafts_directory = os.path.join(public_directory, 'drafts')
        os.makedirs(drafts_directory, exist_ok=True)
        file_path = os.path.join(drafts_directory, 'problematic_drafts.json')
        if send_emails_about_problematic_drafts:
            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    f.write('{}')
                old_incorrect_drafts_keys = []
            else:
                with open(file_path, 'r') as f:
                    old_incorrect_drafts_keys = json.load(f).keys()
            self._send_email_about_new_problematic_drafts(old_incorrect_drafts_keys)
        with open(file_path, 'w') as writer:
            json.dump(self.drafts_missing_code_section, writer)

    def _send_email_about_new_problematic_drafts(self, old_incorrect_drafts: t.Iterable[str]):
        for draft_filename, errors_string in self.drafts_missing_code_section.items():
            if draft_filename in old_incorrect_drafts:
                continue
            draft_name_without_revision = re.sub(r'-\d+', '', draft_filename.split('.')[0])
            author_email = f'{draft_name_without_revision}@ietf.org'
            self.message_factory.send_problematic_draft(
                [author_email],
                draft_filename,
                errors_string,
                draft_name_without_revision=draft_name_without_revision,
            )
