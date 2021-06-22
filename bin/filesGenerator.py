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

import datetime
import json
import os
import time

import HTML

from versions import ValidatorsVersions


class FilesGenerator:
    def __init__(self, htmlpath: str):
        self.__htmlpath = htmlpath
        self.__imported_note = 'Note: also generates errors for imported files.'
        validators_versions = ValidatorsVersions()
        self.__versions = validators_versions.get_versions()

    def write_dictionary(self, dictionary_data: dict, file_name: str):
        """
        Create a JSON file by dumping compilation result messages from 'dictionary_data' dictionary.

        Arguments:
            :param dictionary_data  (dict) Dictionary of modules with compilation results
            :param file_name        (str) The json file name to be created
        """
        full_path = '{}{}.json'.format(self.__htmlpath, file_name)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(dictionary_data, indent=2, sort_keys=True))
        os.chmod(full_path, 0o664)

        print('{}{}.json file generated'.format(self.__get_timestamp_with_pid(), file_name), flush=True)

    def generateYANGPageCompilationHTML(self, modules_results: list, headers: list, file_name: str, metadata: str = ''):
        """
        Create YANGPageCompilation HTML table out of the modules compilation messages and generate a HTML file.

        Arguments:
            :param modules_results  (list) List of the values to generate the HTML table
            :param headers          (list) Headers list to generate the HTML table
            :param HTML_filename    (str) Full path to the HTML file which will be created
            :param metadata         (str) Extra metadata text to be inserted in the generated message
        :return: None
        """
        generated_message = 'Generated on {} by the YANG Catalog. {}'.format(time.strftime('%d/%m/%Y'), metadata)
        message_html = HTML.list([generated_message])
        table_html = HTML.table(modules_results, header_row=headers)
        HTML_filename = '{}{}YANGPageCompilation.html'.format(self.__htmlpath, file_name)

        with open(HTML_filename, 'w', encoding='utf-8') as f:
            f.write(message_html)
            f.write(table_html)

        os.chmod(HTML_filename, 0o664)
        print('{}{}YANGPageCompilation.html HTML page generated in directory {}'
              .format(self.__get_timestamp_with_pid(), file_name, self.__htmlpath), flush=True)

    def generateYANGPageMainHTML(self, file_name: str, stats: dict):
        """
        Create YANGPageMain HTML with compilation results statistics and generate a HTML file.

        Arguments:
            :param file_name    (str) Prefix of the YANGPageMain html file name to be created
            :param stats        (dict) Dictionary containing number of passed, failed and total number of modules
        """
        generated_message = 'Generated on {} by the YANG Catalog.'.format(time.strftime('%d/%m/%Y'))
        content = [
            '{} YANG MODELS'.format(file_name),
            'Number of YANG data models from {} that passed compilation: {}/{}'.format(file_name, stats['passed'], stats['total']),
            'Number of YANG data models from {} that passed compilation with warnings: {}/{}'.format(file_name, stats['warnings'], stats['total']),
            'Number of YANG data models from {} that failed compilation: {}/{}'.format(file_name, stats['failed'], stats['total'])
        ]
        message_html = HTML.list([generated_message])
        content_html = HTML.list(content)
        HTML_filename = '{}{}YANGPageMain.html'.format(self.__htmlpath, file_name)

        with open(HTML_filename, 'w', encoding='utf-8') as f:
            f.write(message_html)
            f.write(content_html)

        os.chmod(HTML_filename, 0o664)
        print('{}{}YANGPageMain.html HTML page generated in directory {}'
              .format(self.__get_timestamp_with_pid(), file_name, self.__htmlpath), flush=True)

    def generateIETFYANGPageMainHTML(self, drafts_stats: dict):
        """
        Create IETFYANGPageMain HTML with compilation results statistics of IETF YANG draft modules
        and generate a HTML file.

        Argument:
            :param drafts_stats     (dict) Dictionary containing number of passed, failed and total number of draft modules
        """
        generated_message = 'Generated on {} by the YANG Catalog.'.format(time.strftime('%d/%m/%Y'))
        content = ['<h3>IETF YANG MODELS</h3>',
                   'Number of correctly extracted YANG models from IETF drafts: {}'.format(drafts_stats.get('total-drafts')),
                   'Number of YANG models in IETF drafts that passed compilation: {}/{}'.format(
                       drafts_stats.get('draft-passed'),
                       drafts_stats.get('total-drafts')),
                   'Number of YANG models in IETF drafts that passed compilation with warnings: {}/{}'.format(
                       drafts_stats.get('draft-warnings'),
                       drafts_stats.get('total-drafts')),
                   'Number of all YANG models in IETF drafts (examples, badly formatted, etc. ): {}'.format(
                       drafts_stats.get('all-ietf-drafts')),
                   'Number of correctly extracted example YANG models from IETF drafts: {}'.format(
                       drafts_stats.get('example-drafts'))
                   ]
        message_html = HTML.list([generated_message])
        content_html = HTML.list(content)
        HTML_filename = '{}IETFYANGPageMain.html'.format(self.__htmlpath)

        with open(HTML_filename, 'w', encoding='utf-8') as f:
            f.write(message_html)
            f.write(content_html)

        os.chmod(HTML_filename, 0o664)
        print('{}IETFYANGPageMain.html HTML page generated in directory {}'
              .format(self.__get_timestamp_with_pid(), self.__htmlpath), flush=True)

    def generateHTMLTable(self, rfcs_list: list, headers: list, HTML_filename: str):
        """
        Create IETFYANGRFC HTML with links to RFC documents.

        Argument:
            :param rfcs_list        (list) List of modules with links to the RFC documents
            :param headers          (list) Headers list to generate the HTML table
            :param HTML_filename    (str) Full path to the HTML file which will be created
        """
        generated_message = 'Generated on {} by the YANG Catalog.'.format(time.strftime('%d/%m/%Y'))
        htmlcode = HTML.list(generated_message)
        htmlcode1 = HTML.table(rfcs_list, header_row=headers)
        with open(HTML_filename, 'w', encoding='utf-8') as f:
            f.write(htmlcode)
            f.write(htmlcode1)

        os.chmod(HTML_filename, 0o664)
        print('{}{} HTML page generated in directory {}'
              .format(self.__get_timestamp_with_pid(), HTML_filename, self.__htmlpath), flush=True)

    #
    # HEADERS
    #
    def getYANGPageCompilationHeaders(self, lint: bool):
        """
        Create headers for YANGPageCompilation HTML table.
        """
        if lint:
            pyang_flag = '--lint'
        else:
            pyang_flag = '--ietf'

        return ['YANG Model',
                'Compilation',
                'Compilation Results (pyang {}). {}'.format(pyang_flag, self.__versions.get('pyang_version')),
                'Compilation Results (pyang). {} {}'.format(self.__imported_note, self.__versions.get('pyang_version')),
                'Compilation Results (confdc). {} {}'.format(self.__imported_note, self.__versions.get('confd_version')),
                'Compilation Results (yangdump-pro). {} {}'.format(self.__imported_note, self.__versions.get('yangdump_version')),
                'Compilation Results (yanglint -i). {} {}'.format(self.__imported_note, self.__versions.get('yanglint_version'))]

    def getIETFDraftYANGPageCompilationHeaders(self):
        """
        Create headers for IETFDraftYANGPageCompilation HTML table.
        """
        return ['YANG Model',
                'Draft Name',
                'Email',
                'Download the YANG model',
                'Compilation',
                'Compilation Results (pyang --ietf). {}'.format(self.__versions.get('pyang_version')),
                'Compilation Results (pyang). {} {}'.format(self.__imported_note, self.__versions.get('pyang_version')),
                'Compilation Results (confdc). {} {}'.format(self.__imported_note, self.__versions.get('confd_version')),
                'Compilation Results (yangdump-pro). {} {}'.format(self.__imported_note, self.__versions.get('yangdump_version')),
                'Compilation Results (yanglint -i). {} {}'.format(self.__imported_note, self.__versions.get('yanglint_version'))]

    def getIETFDraftExampleYANGPageCompilationHeaders(self):
        """
        Create headers for IETFDraftExampleYANGPageCompilation HTML table.
        """
        return ['YANG Model',
                'Draft Name',
                'Email',
                'Compilation',
                'Compilation Results (pyang --ietf). {}'.format(self.__versions.get('pyang_version')),
                'Compilation Results (pyang). {} {}'.format(self.__imported_note, self.__versions.get('pyang_version'))]

    def getIETFCiscoAuthorsYANGPageCompilationHeaders(self):
        """
        Create headers for IETFCiscoAuthorsYANGPageCompilation HTML table.
        """
        return ['YANG Model',
                'Draft Name',
                'All Authors Email',
                'Only Cisco Email',
                'Download the YANG model',
                'Compilation',
                'Compilation Results (pyang --ietf). {}'.format(self.__versions.get('pyang_version')),
                'Compilation Results (pyang). {} {}'.format(self.__imported_note, self.__versions.get('pyang_version')),
                'Compilation Results (confdc). {} {}'.format(self.__imported_note, self.__versions.get('confd_version')),
                'Compilation Results (yangdump-pro). {} {}'.format(self.__imported_note, self.__versions.get('yangdump_version')),
                'Compilation Results (yanglint -i). {} {}'.format(self.__imported_note, self.__versions.get('yanglint_version'))]

    #
    # HELPERS
    #
    def __get_timestamp_with_pid(self):
        timestamp = datetime.datetime.now().time()
        pid = str(os.getpid())
        return '{} ({}): '.format(timestamp, pid)
