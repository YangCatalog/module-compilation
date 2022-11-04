#!/usr/bin/env python

# Copyright The IETF Trust 2019, All Rights Reserved
# Copyright (c) 2018 Cisco and/or its affiliates.
# This software is licensed to you under the terms of the Apache License, Version 2.0 (the "License").
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
# The code, technical concepts, and all information contained herein, are the property of Cisco Technology, Inc.
# and/or its affiliated entities, under various laws including copyright, international treaties, patent,
# and/or contract. Any use of the material herein must be in accordance with the terms of the License.
# All rights not expressly granted by the License are reserved.
# Unless required by applicable law or agreed to separately in writing, software distributed under the
# License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied.

__author__ = 'Benoit Claise'
__copyright__ = 'Copyright(c) 2015-2018, Cisco Systems, Inc.,  Copyright The IETF Trust 2019, All Rights Reserved'
__license__ = 'Apache V2.0'
__email__ = 'bclaise@cisco.com'

import argparse
import datetime
import json
import os
import re
import typing as t
from configparser import ConfigParser

import matplotlib as mpl
from create_config import create_config
from matplotlib.dates import date2num
from utility.utility import list_files_by_extensions

mpl.use('Agg')


class GetStats:
    COMPANIES = (
        ('Yumaworks', 'yumaworks.com'),
        ('Tail-f', 'tail-f.com'),
        ('Cisco', 'cisco.com'),
        ('Huawei', 'huawei.com'),
        ('Juniper', 'juniper.net'),
        ('Ericsson', 'ericsson.com'),
        ('Alcatel-Lucent', 'alcatel-lucent.com'),
        ('Ciena', 'ciena.com'),
        ('Brocade', 'brocade.com'),
        ('ZTE', 'zte.com'),
        ('Fujitsu', 'jp.fujitsu.com'),
        ('Intel', 'intel.com'),
        ('Infinera', 'infinera.com'),
        ('Metaswitch', 'metaswitch.com'),
        ('', ''),
        ('Google', 'google.com'),
        ('Verizon', 'verizon.com'),
        ('AT&T', 'att.com'),
        ('Telefonica', 'telefonica.com'),
        ('Orange', 'orange.com'),
        ('BT', 'bt.com'),
        ('Level 3', 'level3.com'),
        ('Comcast', 'cable.comcast.com'),
        ('China Unicom', 'chinaunicom.cn'),
        ('China Mobile', 'chinamobile.com'),
        ('Microsoft', 'microsoft.com'),
        ('DT', 'telekom.de'),
        ('Softbank', 'softbank.co.jp'),
        ('Packet Design', 'packetdesign.com'),
        ('Qosmos', 'qosmos.com'),
    )
    YANG_PAGE_MAIN_PREFIX = 'YANGPageMain_'
    IETF_YANG_PAGE_MAIN_PREFIX = 'IETFYANGPageMain_'
    IETF_YANG_OUT_OF_RFC_PREFIX = 'IETFYANGOutOfRFC_'
    BACKUPS_PREFIXES = (
        'IETFCiscoAuthorsYANGPageCompilation_',
        'IETFDraftYANGPageCompilation_',
        'IANAStandardYANGPageCompilation_',
        'IEEEStandardYANGPageCompilation_',
        'IEEEStandardDraftYANGPageCompilation_',
        'IEEEExperimentalYANGPageCompilation_',
    )

    def __init__(self, args: argparse.Namespace, config: ConfigParser = create_config()):
        self.debug_level = args.debug
        self.days = int(args.days)
        self.web_private = config.get('Web-Section', 'private-directory')
        self.backup_directory = config.get('Directory-Section', 'backup')
        self.ietf_directory = config.get('Directory-Section', 'ietf-directory')

        self.draft_path_strict = os.path.join(self.ietf_directory, 'draft-with-YANG-strict')
        self.draft_path_nostrict = os.path.join(self.ietf_directory, 'draft-with-YANG-no-strict')
        self.draft_path_diff = os.path.join(self.ietf_directory, 'draft-with-YANG-diff')
        self.stats_path = os.path.join(self.web_private, 'stats')
        self.files: list[str] = []
        self.remove_old_html_file_paths: list[str] = []

        self.ALL_PREFIXES = (
            self.YANG_PAGE_MAIN_PREFIX,
            self.IETF_YANG_PAGE_MAIN_PREFIX,
            self.IETF_YANG_OUT_OF_RFC_PREFIX,
            *self.BACKUPS_PREFIXES,
        )
        self.prefixes_info = {}
        for prefix in self.ALL_PREFIXES:
            json_history_file = os.path.join(self.backup_directory, f'{prefix}history.json')
            self.prefixes_info[prefix] = {
                'json_history_file': json_history_file,
                'compilation_stats': self._load_compilation_stats_from_history_file(json_history_file),
                'stats_filename': (
                    'IETFYANGPageCompilationStats.json'
                    if prefix == 'IETFDraftYANGPageCompilation_'
                    else f'{prefix[:-1]}Stats.json'
                ),
            }

    def _load_compilation_stats_from_history_file(self, json_history_file: str) -> dict:
        compilation_stats = {}
        if os.path.isfile(json_history_file):
            with open(json_history_file, 'r') as f:
                compilation_stats_temp = json.load(f)
            for key, value in compilation_stats_temp.items():
                compilation_stats[float(key)] = value
            del compilation_stats_temp
        return compilation_stats

    def start_process(self):
        all_files = list_files_by_extensions(
            self.backup_directory,
            ('html',),
            debug_level=self.debug_level,
        )
        # only select the files created within the number of days selected
        if self.days > 0:
            self.files = self._list_of_files_in_dir_created_after_date(
                all_files,
                self.backup_directory,
                self.days,
            )
        else:
            self.files = all_files

        self.gather_stats()

        self.print_files_information()

        for path in self.remove_old_html_file_paths:
            if os.path.exists(path):
                os.unlink(path)

    def gather_stats(self):
        for filename in self.files:
            prefix = self._filename_contains_prefix(filename)
            if not prefix:
                print(f'DEBUG: "{filename}" does not contain any prefix')
                continue
            print(f'DEBUG: "{filename}" contains "{prefix}"')
            if prefix == self.YANG_PAGE_MAIN_PREFIX:
                self.gather_yang_page_main_compilation_stats(filename)
            elif prefix == self.IETF_YANG_PAGE_MAIN_PREFIX:
                self.gather_ietf_yang_page_main_compilation_stats(filename)
            elif prefix == self.IETF_YANG_OUT_OF_RFC_PREFIX:
                self.gather_ietf_yang_out_of_rfc_compilation_stats(filename)
            else:
                self.gather_backups_compilation_stats(filename, prefix=prefix)
        if self.days == -1:
            for prefix_info in self.prefixes_info.values():
                with open(prefix_info['json_history_file'], 'w') as filename:
                    json.dump(prefix_info['compilation_stats'], filename)
                self._write_dictionary_file_in_json(
                    prefix_info['compilation_stats'],
                    self.stats_path,
                    prefix_info['stats_filename'],
                )

    def _filename_contains_prefix(self, filename: str) -> t.Optional[str]:
        filename = filename.lower()
        for prefix in self.ALL_PREFIXES:
            if filename.startswith(prefix.lower()):
                return prefix

    def gather_yang_page_main_compilation_stats(self, filename: str):
        prefix_info = self.prefixes_info[self.YANG_PAGE_MAIN_PREFIX]
        path_to_file = os.path.join(self.backup_directory, filename)
        generated_at = 0
        passed = 0
        passed_with_warnings = 0
        failed = 0
        extracted_date = self._extract_date_from_filename(filename)
        if (datetime.date.today() - extracted_date).days > 30:
            self.remove_old_html_file_paths.append(path_to_file)
        i = 0
        with open(path_to_file) as f:
            for line in f:
                i += 1
                if i == 2:
                    generated_at = line.split('on')[-1].split('by')[0].strip()
                elif i == 6:
                    result = line.split(':')[-1].split('/')[0].strip()
                    passed = int(result) if result.isnumeric() else 0
                elif i == 7:
                    result = line.split(':')[-1].split('/')[0].strip()
                    passed_with_warnings = int(result) if result.isnumeric() else 0
                elif i == 8:
                    result = line.split(':')[-1].split('/')[0].strip()
                    failed = int(result) if result.isnumeric() else 0
                elif i == 9:
                    i = 0
                    prefix_info['compilation_stats'][date2num(extracted_date)] = {
                        'name': {
                            'generated-at': generated_at,
                            'passed': passed,
                            'warnings': passed_with_warnings,
                            'failed': failed,
                        },
                    }

    def gather_ietf_yang_page_main_compilation_stats(self, filename: str):
        prefix_info = self.prefixes_info[self.IETF_YANG_PAGE_MAIN_PREFIX]
        path_to_file = os.path.join(self.backup_directory, filename)
        total = 0
        passed_with_warnings = 0
        passed = 0
        badly_formated = 0
        examples = 0
        with open(path_to_file, 'r') as f:
            for line in f:
                if 'correctly extracted YANG models' in line:
                    amount = line.split(':')[-1].strip()
                    total = int(amount) if amount.isnumeric() else total
                elif 'without warnings' in line:
                    amount = line.split(':')[-1].split('/')[0].strip()
                    passed = int(amount) if amount.isnumeric() else passed
                elif 'with warnings' in line:
                    amount = line.split(':')[-1].split('/')[0].strip()
                    passed_with_warnings = int(amount) if amount.isnumeric() else passed_with_warnings
                elif '(example, badly formatted, etc. )' in line:
                    amount = line.split(':')[-1].strip()
                    badly_formated = int(amount) if amount.isnumeric() else badly_formated
                elif 'correctly extracted example YANG' in line:
                    amount = line.split(':')[-1].strip()
                    examples = int(amount) if amount.isnumeric() else examples
        extracted_date = self._extract_date_from_filename(filename)
        if (datetime.date.today() - extracted_date).days > 30:
            self.remove_old_html_file_paths.append(path_to_file)
        prefix_info['compilation_stats'][date2num(extracted_date)] = {
            'total': total,
            'warnings': passed_with_warnings,
            'passed': passed,
            'badly formated': badly_formated,
            'examples': examples,
        }

    def gather_ietf_yang_out_of_rfc_compilation_stats(self, filename: str):
        print(f'\nGathering stats for "{filename}" with "{self.IETF_YANG_OUT_OF_RFC_PREFIX}" prefix')
        prefix_info = self.prefixes_info[self.IETF_YANG_OUT_OF_RFC_PREFIX]
        path_to_file = os.path.join(self.backup_directory, filename)
        rfc_result = 0
        with open(path_to_file, 'r') as f:
            for line in f:
                if '.yang' in line:
                    rfc_result += 1
        extracted_date = self._extract_date_from_filename(filename)
        if (datetime.date.today() - extracted_date).days > 30:
            self.remove_old_html_file_paths.append(path_to_file)
        prefix_info['compilation_stats'][date2num(extracted_date)] = {'total': rfc_result}

    def gather_backups_compilation_stats(self, filename: str, prefix: str):
        print(f'\nGathering stats for "{filename}" with "{prefix}" prefix')
        prefix_info = self.prefixes_info[prefix]
        path_to_file = os.path.join(self.backup_directory, filename)
        failed_result = 0
        passed_result = 0
        passed_with_warning_result = 0
        total_result = 0
        with open(path_to_file, 'r') as f:
            for line in f:
                if 'FAILED' in line:
                    failed_result += 1
                elif 'PASSED WITH WARNINGS' in line:
                    passed_with_warning_result += 1
                elif 'PASSED' in line:
                    passed_result += 1
                elif '.txt' in line:
                    total_result += 1
        extracted_date = self._extract_date_from_filename(filename)
        if (datetime.date.today() - extracted_date).days > 30:
            self.remove_old_html_file_paths.append(path_to_file)
        prefix_info['compilation_stats'][date2num(extracted_date)] = {
            'total': total_result,
            'warning': passed_with_warning_result,
            'success': passed_result,
        }

    def _extract_date_from_filename(self, filename: str) -> datetime.date:
        filename_without_extension = filename.split('.')[0]
        _, year, month, day = filename_without_extension.split('_')
        return datetime.date(int(year), int(month), int(day))

    def print_files_information(self):
        # determine the number of company authored drafts
        files = [
            filename
            for filename in os.listdir(self.draft_path_strict)
            if os.path.isfile(os.path.join(self.draft_path_strict, filename))
        ]
        files_no_strict = [
            filename
            for filename in os.listdir(self.draft_path_nostrict)
            if os.path.isfile(os.path.join(self.draft_path_nostrict, filename))
        ]
        total_number_drafts = len(files)
        total_number_drafts_no_strict = len(files_no_strict)
        print('\nPrint, per company, the number of IETF drafts containing YANG model(s)')
        print(
            f'Total numbers of drafts with YANG Model(s): {total_number_drafts} - '
            f'non strict rules: {total_number_drafts_no_strict}\n',
        )

        def print_attribution(name: str, domain: str):
            if not name and not domain:
                print()
                return
            strict = len(self._list_of_ietf_draft_containing_keyword(files, domain, self.draft_path_strict))
            non_strict = len(
                self._list_of_ietf_draft_containing_keyword(files_no_strict, domain, self.draft_path_nostrict),
            )
            print(f'{name}: {strict} - non strict rules: {non_strict}')

        for company in self.COMPANIES:
            print_attribution(*company)

        # diff between files and files_no_strict lists
        files_diff = []
        for filename in files_no_strict:
            if filename in files:
                continue
            files_diff.append(filename)
            bash_command = f'cp {os.path.join(self.draft_path_nostrict, filename)} {self.draft_path_diff}'
            temp_result = os.popen(bash_command).read()
            if self.debug_level > 0:
                print(
                    f'DEBUG: copy the IETF draft containing a YANG model in {self.draft_path_diff}: '
                    f'error {temp_result}',
                )
        if self.debug_level > 0:
            print(
                'DEBUG: print the diff between files and files_no_strict lists, '
                f'so the files with xym extraction issues: {files_diff}',
            )

    def _list_of_files_in_dir_created_after_date(self, files: list[str], srcdir: str, days: int) -> list[str]:
        """
        Selects the files created wihin the number of days selected

        Arguments:
            :param files:  (list[str]) list of files
            :param srcdir:  (str) directory to search for files
            :param days:  (int) number of days
        :return: list of files
        """
        new_files = []
        dt = datetime.datetime.utcnow()  # datetime now (all in UTC)
        if self.debug_level > 0:
            print(dt)
        delta = datetime.timedelta(days)  # x days interval
        dtdays = dt - delta  # datetime x days earlier than now
        dtdays = dtdays.date()
        if self.debug_level > 0:
            print(dtdays)
        for filename in files:
            if self.debug_level > 0:
                print(f'{srcdir}/{filename}')
            t_date = re.findall(r'\d+[_-]\d+[_-]\d+', filename)[0]
            t_date = re.findall(r'\d+', t_date)
            dt = datetime.date(int(t_date[0]), int(t_date[1]), int(t_date[2]))  # time of last modification in seconds
            if dt >= dtdays:
                if self.debug_level > 0:
                    print(f'Keep {filename}')
                new_files.append(filename)
            else:
                if self.debug_level > 0:
                    print(f'Dont keep {filename}')
        return new_files

    def _list_of_ietf_draft_containing_keyword(self, drafts: list[str], keyword: str, draft_path: str) -> list[str]:
        """
        Returns the IETF drafts that contain a specific keyword

        Arguments:
            :param drafts:  (list[str]) List of ietf drafts to search for the keyword
            :param keyword:  (str) Keyword to search for
            :param draft_path:  (str) Path to drafts folder
        :return: List of ietf drafts containing the keyword
        """
        keyword = keyword.lower()
        list_of_ietf_draft_with_keyword = []
        for draft_filename in drafts:
            with open(os.path.join(draft_path, draft_filename), 'r', encoding='utf-8') as draft_file:
                draft_file_content = draft_file.read().lower()
            if draft_file_content.find(keyword) == -1:
                continue
            list_of_ietf_draft_with_keyword.append(draft_filename)
            if self.debug_level > 0:
                print(f'DEBUG: {draft_filename} in list_of_ietf_draft_containing_keyword: contains {keyword}')
        if self.debug_level > 0:
            print(
                'DEBUG: in list_of_ietf_draft_containing_keyword: '
                f'list_of_ietf_draft_with_keyword contains {list_of_ietf_draft_with_keyword}',
            )
        return list_of_ietf_draft_with_keyword

    def _write_dictionary_file_in_json(self, in_dict: dict, path: str, file_name: str):
        """
        Dumps data from in_dict to the json file.

        Arguments:
            :param in_dict: The dictionary to write
            :param path: The directory where the json file with be created
            :param file_name: The file name to be created
        :return: None
        """
        file_path = os.path.join(path, file_name)
        with open(file_path, 'w', encoding='utf-8') as outfile:
            json.dump(in_dict, outfile, indent=2, sort_keys=True, separators=(',', ': '), ensure_ascii=True)
        os.chmod(file_path, 0o664)


if __name__ == '__main__':
    config = create_config()
    parser = argparse.ArgumentParser(description='YANG Stats Extractor')
    parser.add_argument(
        '--days',
        help='Numbers of days to get back in history. Default is -1 = unlimited',
        type=int,
        default=-1,
    )
    parser.add_argument('--debug', help='Debug level - default is 0', type=int, default=0)
    args = parser.parse_args()
    GetStats(args, config).start_process()
