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
from extract_emails import extract_email_string
from fileHasher import FileHasher
from parsers.confdcParser import ConfdcParser
from parsers.pyangParser import PyangParser
from parsers.yangdumpProParser import YangdumpProParser
from parsers.yanglintParser import YanglintParser
from utility.utility import (check_yangcatalog_data, module_or_submodule,
                             push_to_confd)
from versions import ValidatorsVersions


class DraftsCompilator:
    def __init__(self, extracted_drafts_dir: str, drafts_dict: dict, debug_level: int = 0):
        self.config = create_config()
        self.pyang_exec = self.config.get('Tool-Section', 'pyang-exec')
        self.html_path = self.config.get('Web-Section', 'private-directory')
        self.result_html_dir = self.config.get('Web-Section', 'result-html-dir')
        self.protocol = self.config.get('General-Section', 'protocol-api')
        self.api_ip = self.config.get('Web-Section', 'ip')
        self.web_url = self.config.get('Web-Section', 'my-uri')

        self.extracted_drafts_dir = extracted_drafts_dir
        self.drafts_dict = drafts_dict
        self.debug_level = debug_level

        self.results_dict = {}
        self.results_no_submodules_dict = {}
        self.results_dict_authors = {}
        self.results_no_submodules_dict_authors = {}
        self.output_cisco_emails = []

    def compile_drafts(self, all_yang_catalog_metadata: dict, force_compilation: bool, paths: dict):
        fileHasher = FileHasher(force_compilation)
        pyangParser = PyangParser(self.debug_level)
        confdcParser = ConfdcParser(self.debug_level)
        yumadumpProParser = YangdumpProParser(self.debug_level)
        yanglintParser = YanglintParser(self.debug_level)

        validators_versions = ValidatorsVersions()
        versions = validators_versions.get_versions()

        updated_modules = []

        try:
            with open(os.path.join(self.html_path, 'IETFDraft.json'), 'r') as f:
                existing_results_dict = json.load(f)
        except Exception:
            existing_results_dict = {}
        try:
            with open(os.path.join(self.html_path, 'IETFCiscoAuthors.json'), 'r') as f:
                existing_results_dict_authors = json.load(f)
        except Exception:
            existing_results_dict_authors = {}

        for yang_file in self.drafts_dict:
            yang_file_path = os.path.join(self.extracted_drafts_dir, yang_file)
            yang_file_compilation = existing_results_dict.get(yang_file, None)
            yang_file_compilation_authors = existing_results_dict_authors.get(yang_file, None)

            draft_path = os.path.join(paths['draftpath'], self.drafts_dict[yang_file])
            cisco_email = extract_email_string(draft_path, '@cisco.com', self.debug_level)
            tailf_email = extract_email_string(draft_path, '@tail-f.com', self.debug_level)

            draft_emails = ','.join(filter(None, [cisco_email, tailf_email]))
            if draft_emails:
                self.output_cisco_emails.extend(draft_emails.split(','))

            should_parse, file_hash = fileHasher.should_parse(yang_file_path)

            if should_parse or yang_file_compilation is None or yang_file_compilation_authors is None:
                result_pyang = pyangParser.run_pyang_ietf(yang_file_path, ietf=True)
                result_no_ietf_flag = pyangParser.run_pyang_ietf(yang_file_path, ietf=False)
                result_confd = confdcParser.run_confdc(yang_file_path, self.extracted_drafts_dir)
                result_yuma = yumadumpProParser.run_yumadumppro(yang_file_path, self.extracted_drafts_dir)
                result_yanglint = yanglintParser.run_yanglint(yang_file_path, self.extracted_drafts_dir)
                compilation_results = {
                    'pyang_lint': result_pyang,
                    'pyang': result_no_ietf_flag,
                    'confdrc': result_confd,
                    'yumadump': result_yuma,
                    'yanglint': result_yanglint
                }

                document_name = self.drafts_dict.get(yang_file, '')
                draft_name = document_name.split('.')[0]
                version_number = draft_name.split('-')[-1]
                draft_name = draft_name.rstrip('-0123456789')
                mailto = '{}@ietf.org'.format(draft_name)
                datatracker_url = 'https://datatracker.ietf.org/doc/{}/{}'.format(draft_name, version_number)
                draft_url_anchor = '<a href="{}">{}</a>'.format(datatracker_url, document_name)
                email_anchor = '<a href="mailto:{}">Email Authors</a>'.format(mailto)
                cisco_email_anchor = '<a href="mailto:{}">Email Cisco Authors Only</a>'.format(draft_emails)
                yang_model_url = '{}/YANG-modules/{}'.format(self.web_url, yang_file)
                yang_model_anchor = '<a href="{}">Download the YANG model</a>'.format(yang_model_url)

                is_rfc = os.path.isfile(os.path.join(paths['rfcpath'], yang_file))

                compilation_status = self._combined_compilation(yang_file, compilation_results)
                updated_modules.extend(
                    check_yangcatalog_data(self.config, yang_file_path, datatracker_url, document_name, mailto,
                                           compilation_status, compilation_results, all_yang_catalog_metadata, is_rfc,
                                           versions, 'ietf-draft'))
                if len(updated_modules) > 100:
                    updated_modules = push_to_confd(updated_modules, self.config)
                yang_file_compilation = [draft_url_anchor, email_anchor, yang_model_anchor, compilation_status,
                                         result_pyang, result_no_ietf_flag, result_confd, result_yuma, result_yanglint]
                yang_file_compilation_authors = [draft_url_anchor, email_anchor, cisco_email_anchor, yang_model_anchor,
                                                 compilation_status, result_pyang, result_no_ietf_flag, result_confd,
                                                 result_yuma, result_yanglint]

                # Do not store hash if compilation result is 'UNKNOWN' -> try to parse model again next time
                if compilation_status != 'UNKNOWN':
                    fileHasher.updated_hashes[yang_file_path] = file_hash

            self.results_dict[yang_file] = yang_file_compilation
            self.results_dict_authors[yang_file] = yang_file_compilation_authors
            if module_or_submodule(yang_file_path) == 'module':
                self.results_no_submodules_dict[yang_file] = yang_file_compilation
                self.results_no_submodules_dict_authors[yang_file] = yang_file_compilation

        updated_modules = push_to_confd(updated_modules, self.config)
        # Update files content hashes and dump into .json file
        if len(fileHasher.updated_hashes) > 0:
            fileHasher.dump_hashed_files_list(fileHasher.updated_hashes)

    def _combined_compilation(self, yang_file: str, result: dict):
        """
        Determine the combined compilation result based on individual compilation results from parsers.

        Arguments:
            :param yang_file    (str) Name of the yang files
            :param result       (dict) Dictionary of compilation results with following keys:
                                        pyang_lint, pyang, confdrc, yumadump, yanglint
        :return: the combined compilation result
        """
        if 'error:' in result['pyang_lint']:
            compilation_pyang = 'FAILED'
        elif 'warning:' in result['pyang_lint']:
            compilation_pyang = 'PASSED WITH WARNINGS'
        elif result['pyang_lint'] == '':
            compilation_pyang = 'PASSED'
        else:
            compilation_pyang = 'UNKNOWN'

        # logic for pyang compilation result:
        if 'error:' in result['pyang']:
            compilation_pyang_no_ietf = 'FAILED'
        elif 'warning:' in result['pyang']:
            compilation_pyang_no_ietf = 'PASSED WITH WARNINGS'
        elif result['pyang'] == '':
            compilation_pyang_no_ietf = 'PASSED'
        else:
            compilation_pyang_no_ietf = 'UNKNOWN'

        # logic for confdc compilation result:
        # if 'error' in result['confdrc'] and yang_file in result['confdrc']:
        if 'error:' in result['confdrc']:
            compilation_confd = 'FAILED'
        #   The following doesn't work. For example, ietf-diffserv@2016-06-15.yang, now PASSED (TBC):
        #     Error: 'ietf-diffserv@2016-06-15.yang' import of module 'ietf-qos-policy' failed
        #     ietf-diffserv@2016-06-15.yang:11.3: error(250): definition not found
        #   This issue is that an import module that fails => report the main module as FAILED
        #   Another issue with ietf-bgp-common-structure.yang
        # If the error is on the module itself, then, that's an error
        elif 'warning:' in result['confdrc']:
            compilation_confd = 'PASSED WITH WARNINGS'
        elif result['confdrc'] == '':
            compilation_confd = 'PASSED'
        else:
            compilation_confd = 'UNKNOWN'
        # 'cannot compile submodules; compile the module instead' error  message
        # => still print the message, but doesn't report it as FAILED
        if 'error: cannot compile submodules; compile the module instead' in result['confdrc']:
            compilation_confd = 'PASSED'

        # logic for yumadump-pro compilation result:
        if result['yumadump'] == '':
            compilation_yuma = 'PASSED'
        elif '0 Errors, 0 Warnings' in result['yumadump']:
            compilation_yuma = 'PASSED'
        elif 'Error' in result['yumadump'] and yang_file in result['yumadump'] and '0 Errors' not in result['yumadump']:
            # This is an approximation: if Error in an imported module, and warning on this current module
            # then it will report the module as FAILED
            # Solution: look at line by line comparision of Error and yang_file
            compilation_yuma = 'FAILED'
        elif 'Warning:' in result['yumadump'] and yang_file in result['yumadump']:
            compilation_yuma = 'PASSED WITH WARNINGS'
        elif 'Warning:' in result['yumadump'] and yang_file not in result['yumadump']:
            compilation_yuma = 'PASSED'
        else:
            compilation_yuma = 'UNKNOWN'

        # logic for yanglint compilation result:
        if 'err :' in result['yanglint']:
            compilation_yanglint = 'FAILED'
        elif 'warn:' in result['yanglint']:
            compilation_yanglint = 'PASSED WITH WARNINGS'
        elif result['yanglint'] == '':
            compilation_yanglint = 'PASSED'
        else:
            compilation_yanglint = 'UNKNOWN'
        # 'err : Input data contains submodule which cannot be parsed directly without its main module.' error  message
        # => still print the message, but doesn't report it as FAILED
        if 'err : Input data contains submodule which cannot be parsed directly without its main module.' in result['yanglint']:
            compilation_yanglint = 'PASSED'

        # determine the combined compilation status, based on the different compilers
        compilation_list = [compilation_pyang, compilation_pyang_no_ietf, compilation_confd, compilation_yuma,
                            compilation_yanglint]
        if 'FAILED' in compilation_list:
            compilation = 'FAILED'
        elif 'PASSED WITH WARNINGS' in compilation_list:
            compilation = 'PASSED WITH WARNINGS'
        elif compilation_list == ['PASSED', 'PASSED', 'PASSED', 'PASSED', 'PASSED']:
            compilation = 'PASSED'
        else:
            compilation = 'UNKNOWN'

        return compilation
