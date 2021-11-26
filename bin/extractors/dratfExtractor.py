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

__author__ = "Slavomir Mazur"
__copyright__ = "Copyright The IETF Trust 2021, All Rights Reserved"
__license__ = "Apache License, Version 2.0"
__email__ = "slavomir.mazur@pantheon.tech"

import os
import shutil

from extract_elem import extract_elem
from xym import xym

from extractors.helper import (check_after_xym_extraction,
                               invert_yang_modules_dict, remove_invalid_files)


class DraftExtractor:
    def __init__(self, draft_extractor_paths: dict, debug_level: int,
                 extract_elements: bool = True, extract_examples: bool = True):
        self.draft_path = draft_extractor_paths.get('draft_path', '')
        self.yang_path = draft_extractor_paths.get('yang_path', '')
        self.draft_elements_path = draft_extractor_paths.get('draft_elements_path', '')
        self.all_yang_draft_path_strict = draft_extractor_paths.get('all_yang_draft_path_strict', '')
        self.all_yang_example_path = draft_extractor_paths.get('all_yang_example_path', '')
        self.all_yang_draft_path_only_example = draft_extractor_paths.get('all_yang_draft_path_only_example', '')
        self.all_yang_path = draft_extractor_paths.get('all_yang_path', '')
        self.all_yang_draft_path_no_strict = draft_extractor_paths.get('all_yang_draft_path_no_strict', '')
        self.debug_level = debug_level
        self.extract_examples = extract_examples
        self.extract_elements = extract_elements
        self.ietf_drafts = []
        self.draft_yang_dict = {}
        self.draft_yang_example_dict = {}
        self.draft_yang_all_dict = {}
        self.inverted_draft_yang_dict = {}
        self.inverted_draft_yang_example_dict = {}
        self.inverted_draft_yang_all_dict = {}
        self.__create_ietf_drafts_list()

    def __create_ietf_drafts_list(self):
        for filename in os.listdir(self.draft_path):
            full_path = os.path.join(self.draft_path, filename)
            if os.path.isfile(full_path):
                try:
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        for line in f:
                            if '<CODE BEGINS>' in line:
                                self.ietf_drafts.append(filename)
                                break
                except:
                    continue
        self.ietf_drafts.sort()
        print('Drafts list created')

    def extract_drafts(self):
        for draft_file in self.ietf_drafts:
            draft_file_path = '{}{}'.format(self.draft_path, draft_file)

            # Extract the correctly formatted YANG Models into yang_path
            extracted_yang_models = self.extract_from_draft_file(draft_file, self.draft_path, self.yang_path, strict=True)

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
                shutil.copy2(draft_file_path, self.all_yang_draft_path_strict)

            # Extract the correctly formatted example YANG Models into all_yang_example_path
            if self.extract_examples:
                extracted_yang_models = self.extract_from_draft_file(draft_file, self.draft_path, self.all_yang_example_path,
                                                                     strict=True, strict_examples=True)
                if extracted_yang_models:
                    correct = check_after_xym_extraction(draft_file, extracted_yang_models)
                    if not correct:
                        self.ietf_drafts.remove(draft_file)
                        continue

                    if self.debug_level > 0:
                        print('DEBUG: Extracted YANG models from Draft\n {}'.format(str(extracted_yang_models)))

                    self.draft_yang_example_dict[draft_file] = extracted_yang_models
                    # copy the draft file in a specific directory for strict = True
                    shutil.copy2(draft_file_path, self.all_yang_draft_path_only_example)

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
                shutil.copy2(draft_file_path, self.all_yang_draft_path_no_strict)

    def extract_from_draft_file(self, draft_file: str, srcdir: str, dstdir: str,
                                strict: bool = False, strict_examples: bool = False):
        return xym.xym(draft_file, srcdir, dstdir, strict=strict, strict_examples=strict_examples,
                       debug_level=self.debug_level, add_line_refs=False, force_revision_pyang=False,
                       force_revision_regexp=True)

    def invert_dict(self):
        self.inverted_draft_yang_dict = invert_yang_modules_dict(self.draft_yang_dict, self.debug_level)
        self.inverted_draft_yang_example_dict = invert_yang_modules_dict(self.draft_yang_example_dict, self.debug_level)
        self.inverted_draft_yang_all_dict = invert_yang_modules_dict(self.draft_yang_all_dict, self.debug_level)

    def remove_invalid_files(self):
        remove_invalid_files(self.yang_path, self.inverted_draft_yang_dict)
        remove_invalid_files(self.all_yang_example_path, self.inverted_draft_yang_example_dict)
        remove_invalid_files(self.all_yang_path, self.inverted_draft_yang_all_dict)

    def extract_all_elements(self, extracted_yang_models: list):
        """ Extract typedefs, groupings and identities from data models into .txt files.
        These elements are not extracted from example models.
        """
        for extracted_model in extracted_yang_models:
            if not extracted_model.startswith('example-'):
                print('Identifier definition extraction for {}'.format(extracted_model))
                module_fname = '{}{}'.format(self.yang_path, extracted_model)
                extract_elem(module_fname, self.draft_elements_path, 'typedef')
                extract_elem(module_fname, self.draft_elements_path, 'grouping')
                extract_elem(module_fname, self.draft_elements_path, 'identity')
