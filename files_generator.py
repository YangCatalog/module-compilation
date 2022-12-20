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

import datetime
import json
import os
import time

import HTML

from utility.utility import dict_to_list, list_br_html_addition
from versions import validator_versions


class FilesGenerator:
    def __init__(self, htmlpath: str):
        self._htmlpath = htmlpath
        self.__imported_note = 'Note: also generates errors for imported files.'
        self._versions = validator_versions

    def write_dictionary(self, dictionary_data: dict, file_name: str):
        """
        Create a JSON file by dumping compilation result messages from 'dictionary_data' dictionary.

        Arguments:
            :param dictionary_data  (dict) Dictionary of modules with compilation results
            :param file_name        (str) The json file name to be created
        """
        file_name += '.json'
        full_path = os.path.join(self._htmlpath, file_name)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(dictionary_data, indent=2, sort_keys=True))
        os.chmod(full_path, 0o664)

        self._custom_print(f'{file_name} file generated')

    def generate_yang_page_compilation_html(
        self,
        dictionary_data: dict,
        headers: list,
        file_name: str,
        metadata: str = '',
    ):
        """
        Create YANGPageCompilation HTML table out of the modules compilation messages and generate an HTML file.

        Arguments:
            :param modules_results  (list) List of the values to generate the HTML table
            :param headers          (list) Headers list to generate the HTML table
            :param metadata         (str) Extra metadata text to be inserted in the generated message
        :return: None
        """
        modules_results = list_br_html_addition(sorted(dict_to_list(dictionary_data)))
        generated_message = f'Generated on {time.strftime("%d/%m/%Y")} by the YANG Catalog. {metadata}'
        message_html = HTML.list([generated_message])
        table_html = HTML.table(modules_results, header_row=headers)
        file_name += 'YANGPageCompilation.html'
        html_filename = os.path.join(self._htmlpath, file_name)

        with open(html_filename, 'w', encoding='utf-8') as f:
            f.write(message_html)
            f.write(table_html)

        os.chmod(html_filename, 0o664)
        self._custom_print(f'{file_name} HTML page generated in directory {self._htmlpath}')

    def generate_yang_page_main_html(self, file_name: str, stats: dict):
        """
        Create YANGPageMain HTML with compilation results statistics and generate a HTML file.

        Arguments:
            :param file_name    (str) Prefix of the YANGPageMain html file name to be created
            :param stats        (dict) Dictionary containing number of passed, failed and total number of modules
        """
        generated_message = f'Generated on {time.strftime("%d/%m/%Y")} by the YANG Catalog.'
        content = [
            f'{file_name} YANG MODELS',
            f'Number of YANG data models from {file_name} that passed compilation: {stats["passed"]}/{stats["total"]}',
            (
                f'Number of YANG data models from {file_name} that passed compilation with warnings: '
                f'{stats["warnings"]}/{stats["total"]}'
            ),
            f'Number of YANG data models from {file_name} that failed compilation: {stats["failed"]}/{stats["total"]}',
        ]
        message_html = HTML.list([generated_message])
        content_html = HTML.list(content)
        file_name += 'YANGPageMain.html'
        html_filename = os.path.join(self._htmlpath, file_name)

        with open(html_filename, 'w', encoding='utf-8') as f:
            f.write(message_html)
            f.write(content_html)

        os.chmod(html_filename, 0o664)
        self._custom_print(f'{file_name} HTML page generated in directory {self._htmlpath}')

    def generate_ietfyang_page_main_html(self, drafts_stats: dict):
        """
        Create IETFYANGPageMain HTML with compilation results statistics of IETF YANG draft modules
        and generate a HTML file.

        Argument:
            :param drafts_stats  (dict) Dictionary containing number of passed, failed and total number of draft modules
        """
        generated_message = f'Generated on {time.strftime("%d/%m/%Y")} by the YANG Catalog.'
        content = [
            '<h3>IETF YANG MODELS</h3>',
            f'Number of correctly extracted YANG models from IETF drafts: {drafts_stats.get("total-drafts")}',
            (
                f'Number of YANG models in IETF drafts that passed compilation: '
                f'{drafts_stats.get("draft-passed")}/{drafts_stats.get("total-drafts")}'
            ),
            (
                f'Number of YANG models in IETF drafts that passed compilation with warnings: '
                f'{drafts_stats.get("draft-warnings")}/{drafts_stats.get("total-drafts")}'
            ),
            (
                f'Number of all YANG models in IETF drafts (examples, badly formatted, etc. ): '
                f'{drafts_stats.get("all-ietf-drafts")}'
            ),
            f'Number of correctly extracted example YANG models from IETF drafts: {drafts_stats.get("example-drafts")}',
        ]
        message_html = HTML.list([generated_message])
        content_html = HTML.list(content)
        html_filename = os.path.join(self._htmlpath, 'IETFYANGPageMain.html')

        with open(html_filename, 'w', encoding='utf-8') as f:
            f.write(message_html)
            f.write(content_html)

        os.chmod(html_filename, 0o664)
        self._custom_print(f'IETFYANGPageMain.html HTML page generated in directory {self._htmlpath}')

    def generate_html_table(self, dictionary_data: dict, headers: list):
        """
        Create IETFYANGRFC HTML with links to RFC documents.

        Argument:
            :param rfcs_list        (list) List of modules with links to the RFC documents
            :param headers          (list) Headers list to generate the HTML table
        """
        rfcs_list = sorted(dict_to_list(dictionary_data, True))
        generated_message = f'Generated on {time.strftime("%d/%m/%Y")} by the YANG Catalog.'
        htmlcode = HTML.list([generated_message])
        htmlcode1 = HTML.table(rfcs_list, header_row=headers)

        html_filename = os.path.join(self._htmlpath, 'IETFYANGRFC.html')
        with open(html_filename, 'w', encoding='utf-8') as f:
            f.write(htmlcode)
            f.write(htmlcode1)

        os.chmod(html_filename, 0o664)
        self._custom_print(f'{html_filename} HTML page generated in directory {self._htmlpath}')

    def get_yang_page_compilation_headers(self, lint: bool):
        """
        Create headers for YANGPageCompilation HTML table.
        """
        if lint:
            pyang_flag = '--lint'
        else:
            pyang_flag = '--ietf'

        return [
            'YANG Model',
            'Compilation',
            f'Compilation Results (pyang {pyang_flag}). {self._versions.get("pyang_version")}',
            f'Compilation Results (pyang). {self.__imported_note} {self._versions.get("pyang_version")}',
            f'Compilation Results (confdc). {self.__imported_note} {self._versions.get("confd_version")}',
            f'Compilation Results (yangdump-pro). {self.__imported_note} {self._versions.get("yangdump_version")}',
            f'Compilation Results (yanglint -i). {self.__imported_note} {self._versions.get("yanglint_version")}',
        ]

    def get_ietf_draft_yang_page_compilation_headers(self):
        """
        Create headers for IETFDraftYANGPageCompilation HTML table.
        """
        return [
            'YANG Model',
            'Draft Name',
            'Email',
            'Download the YANG model',
            'Compilation',
            f'Compilation Results (pyang --ietf). {self._versions.get("pyang_version")}',
            f'Compilation Results (pyang). {self.__imported_note} {self._versions.get("pyang_version")}',
            f'Compilation Results (confdc). {self.__imported_note} {self._versions.get("confd_version")}',
            f'Compilation Results (yangdump-pro). {self.__imported_note} {self._versions.get("yangdump_version")}',
            f'Compilation Results (yanglint -i). {self.__imported_note} {self._versions.get("yanglint_version")}',
        ]

    def get_ietf_draft_example_yang_page_compilation_headers(self):
        """
        Create headers for IETFDraftExampleYANGPageCompilation HTML table.
        """
        return [
            'YANG Model',
            'Draft Name',
            'Email',
            'Compilation',
            f'Compilation Results (pyang --ietf). {self._versions.get("pyang_version")}',
            f'Compilation Results (pyang). {self.__imported_note} {self._versions.get("pyang_version")}',
        ]

    def get_ietf_cisco_authors_yang_page_compilation_headers(self):
        """
        Create headers for IETFCiscoAuthorsYANGPageCompilation HTML table.
        """
        return [
            'YANG Model',
            'Draft Name',
            'All Authors Email',
            'Only Cisco Email',
            'Download the YANG model',
            'Compilation',
            f'Compilation Results (pyang --ietf). {self._versions.get("pyang_version")}',
            f'Compilation Results (pyang). {self.__imported_note} {self._versions.get("pyang_version")}',
            f'Compilation Results (confdc). {self.__imported_note} {self._versions.get("confd_version")}',
            f'Compilation Results (yangdump-pro). {self.__imported_note} {self._versions.get("yangdump_version")}',
            f'Compilation Results (yanglint -i). {self.__imported_note} {self._versions.get("yanglint_version")}',
        ]

    def _custom_print(self, message: str):
        timestamp = f'{datetime.datetime.now().time()} ({os.getpid()}):'
        print(f'{timestamp} {message}', flush=True)
