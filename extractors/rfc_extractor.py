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
import shutil
from dataclasses import dataclass

from xym import xym

from extractors.extract_elem import extract_elem
from extractors.helper import check_after_xym_extraction, invert_yang_modules_dict, remove_invalid_files


@dataclass
class RFCExtractorPaths:
    rfc_path: str
    rfc_yang_path: str
    rfc_extraction_yang_path: str
    code_snippets_directory: str


class RFCExtractor:
    def __init__(self, rfc_extractor_paths: RFCExtractorPaths, debug_level: int):
        self.rfc_extractor_paths = rfc_extractor_paths
        self.debug_level = debug_level
        self.code_snippets_directory = rfc_extractor_paths.code_snippets_directory
        self.ietf_rfcs = []
        self.rfc_yang_dict = {}
        self.inverted_rfc_yang_dict = {}
        self.__create_ietf_rfcs_list()

    def __create_ietf_rfcs_list(self):
        self.ietf_rfcs = [
            f
            for f in os.listdir(self.rfc_extractor_paths.rfc_path)
            if os.path.isfile(os.path.join(self.rfc_extractor_paths.rfc_path, f))
        ]
        self.ietf_rfcs.sort()
        print('IETF RFCs list created')

    def extract(self):
        self.extract_rfcs()
        self.invert_dict()
        self.remove_invalid_files()

    def extract_rfcs(self):
        for rfc_file in self.ietf_rfcs:
            extracted_yang_models = self.extract_from_rfc_file(rfc_file)

            if extracted_yang_models:
                correct = check_after_xym_extraction(rfc_file, extracted_yang_models)
                if not correct:
                    self.ietf_rfcs.remove(rfc_file)
                    continue

                if self.debug_level > 0:
                    print(f'DEBUG: Extracted YANG models from RFC\n {extracted_yang_models}')

                # typedef, grouping and identity extraction from RFCs
                for extracted_model in extracted_yang_models:
                    if not extracted_model.startswith('example-'):
                        print(f'Identifier definition extraction for {extracted_model}')
                        module_fname = os.path.join(self.rfc_extractor_paths.rfc_yang_path, extracted_model)
                        extract_elem(module_fname, self.rfc_extractor_paths.rfc_extraction_yang_path, 'typedef')
                        extract_elem(module_fname, self.rfc_extractor_paths.rfc_extraction_yang_path, 'grouping')
                        extract_elem(module_fname, self.rfc_extractor_paths.rfc_extraction_yang_path, 'identity')
                self.rfc_yang_dict[rfc_file] = extracted_yang_models

    def extract_from_rfc_file(self, rfc_file: str) -> list[str]:
        return xym.xym(
            rfc_file,
            self.rfc_extractor_paths.rfc_path,
            self.rfc_extractor_paths.rfc_yang_path,
            strict=True,
            strict_examples=False,
            debug_level=self.debug_level,
            add_line_refs=False,
            force_revision_pyang=False,
            force_revision_regexp=True,
            extract_code_snippets=True,
            code_snippets_dir=os.path.join(self.code_snippets_directory, os.path.splitext(rfc_file)[0]),
        )

    def invert_dict(self):
        self.inverted_rfc_yang_dict = invert_yang_modules_dict(self.rfc_yang_dict, self.debug_level)

    def remove_invalid_files(self):
        remove_invalid_files(self.rfc_extractor_paths.rfc_yang_path, self.inverted_rfc_yang_dict)

    def clean_old_rfc_yang_modules(self, srcdir: str, dstdir: str):
        """
        Move some YANG modules, which are documented at
        http://www.claise.be/IETFYANGOutOfRFCNonStrictToBeCorrected.html:
        ietf-foo@2010-01-18.yang, hw.yang, hardware-entities.yang, udmcore.yang, and ct-ipfix-psamp-example.yang
        Those YANG modules, from old RFCs, don't follow the example- conventions

        Arguments:
            :param srcdir       (str) Source dir path from where we move the YANG modules
            :param dstdir       (str) Destinationd dir path to where we move the YANG modules
        """
        with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../resources/old-rfcs.json'), 'r') as f:
            old_modules = json.load(f)

        for old_module in old_modules:
            src_path = os.path.join(srcdir, old_module)
            dst_path = os.path.join(dstdir, old_module)
            if not os.path.isfile(src_path):
                continue
            try:
                shutil.move(src_path, dst_path)
            except IOError as e:
                print('Unable to copy file. %s' % e)

        self.inverted_rfc_yang_dict = {k: v for k, v in self.inverted_rfc_yang_dict.items() if k not in old_modules}
