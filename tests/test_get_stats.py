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

__author__ = 'Bohdan Konovalenko'
__copyright__ = 'Copyright The IETF Trust 2022, All Rights Reserved'
__license__ = 'Apache License, Version 2.0'
__email__ = 'bohdan.konovalenko@pantheon.tech'

import argparse
import json
import os
import shutil
import unittest
from configparser import ConfigParser
from datetime import datetime, timedelta
from uuid import uuid4

from create_config import create_config
from figures_and_stats.yang_get_stats import GetStats
from utility.utility import list_files_by_extensions


class TestGetStats(unittest.TestCase):
    config: ConfigParser
    backup_directory: str
    web_private_directory: str
    directory_to_store_backup_files: str

    @classmethod
    def setUpClass(cls):
        cls.resources_path = os.path.join(os.environ['TESTS_RESOURCES_DIR'], 'yang_get_stats')
        cls.config = create_config()
        cls.backup_directory = cls.resource('backup')
        cls.config.set('Directory-Section', 'backup', cls.backup_directory)
        cls.config.set('Directory-Section', 'ietf-directory', cls.resource('ietf'))
        cls.config.set('Web-Section', 'private-directory', cls.resource('private'))
        cls.web_private_directory = cls.config.get('Web-Section', 'private-directory')
        cls.directory_to_store_backup_files = cls.resource(uuid4().hex)
        cls.stats_directory = os.path.join(cls.web_private_directory, 'stats')
        os.makedirs(cls.directory_to_store_backup_files, exist_ok=True)
        for filename in os.listdir(cls.backup_directory):
            if cls._check_filename_contains_prefix(filename):
                shutil.copy2(
                    os.path.join(cls.backup_directory, filename),
                    os.path.join(cls.directory_to_store_backup_files, filename),
                )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.directory_to_store_backup_files, ignore_errors=True)

    def setUp(self):
        args = argparse.Namespace()
        setattr(args, 'days', -1)
        setattr(args, 'debug', 1)
        self.get_stats_instance: GetStats = GetStats(args=args, config=self.config)

    def tearDown(self):
        for filename in os.listdir(self.directory_to_store_backup_files):
            shutil.copy2(
                os.path.join(self.directory_to_store_backup_files, filename),
                os.path.join(self.backup_directory, filename),
            )
        for filename in os.listdir(self.stats_directory):
            if not (self._check_filename_contains_prefix(filename) and 'Stats' in filename):
                continue
            with open(os.path.join(self.stats_directory, filename), 'w') as f:
                json.dump({}, f)

    @classmethod
    def resource(cls, path: str) -> str:
        return os.path.join(cls.resources_path, path)

    @classmethod
    def _check_filename_contains_prefix(cls, filename: str) -> bool:
        return (
            GetStats.IETF_YANG_OUT_OF_RFC_PREFIX in filename
            or GetStats.YANG_PAGE_MAIN_PREFIX in filename
            or GetStats.IETF_YANG_PAGE_MAIN_PREFIX in filename
            or any([prefix in filename for prefix in GetStats.BACKUPS_PREFIXES])
        )

    def test_yang_get_stats_script(self):
        self.get_stats_instance.start_process()
        for path in self.get_stats_instance.remove_old_html_file_paths:
            self.assertTrue(not os.path.exists(path))
        for prefix in (
            GetStats.IETF_YANG_OUT_OF_RFC_PREFIX,
            GetStats.YANG_PAGE_MAIN_PREFIX,
            GetStats.IETF_YANG_PAGE_MAIN_PREFIX,
            'IEEEStandardDraftYANGPageCompilation_',
        ):
            stats_data, history_data = self._get_stats_and_history_files_data(prefix)
            self.assertNotEqual(stats_data, {})
            self.assertNotEqual(history_data, {})

    def _get_stats_and_history_files_data(self, files_prefix: str) -> tuple[dict, dict]:
        stats_filename = f'{files_prefix[:-1]}Stats.json'
        with open(os.path.join(self.stats_directory, stats_filename), 'r') as stats_file:
            stats_data = json.load(stats_file)
        with open(os.path.join(self.backup_directory, f'{files_prefix}history.json'), 'r') as history_file:
            history_data = json.load(history_file)
        return stats_data, history_data

    def test_gather_yang_page_main_compilation_stats(self):
        self.get_stats_instance.files = list_files_by_extensions(
            self.backup_directory,
            ('html',),
            debug_level=self.get_stats_instance.debug_level,
        )
        self.get_stats_instance.gather_yang_page_main_compilation_stats('YANGPageMain_2022_01_01.html')
        page_main_prefix = self.get_stats_instance.YANG_PAGE_MAIN_PREFIX
        self.assertTrue(
            next(iter(self.get_stats_instance.prefixes_info[page_main_prefix]['compilation_stats'].values()))
            == {
                'name': {
                    'generated-at': '2021.01.01',
                    'passed': 15,
                    'warnings': 15,
                    'failed': 15,
                },
            },
        )
        self.assertTrue(
            os.path.join(self.backup_directory, f'{page_main_prefix}2022_01_01.html')
            in self.get_stats_instance.remove_old_html_file_paths,
        )

    def test_gather_ietf_yang_page_main_compilation_stats(self):
        self.get_stats_instance.files = list_files_by_extensions(
            self.backup_directory,
            ('html',),
            debug_level=self.get_stats_instance.debug_level,
        )
        self.get_stats_instance.gather_ietf_yang_page_main_compilation_stats('IETFYANGPageMain_2022_01_01.html')
        ietf_page_main_prefix = self.get_stats_instance.IETF_YANG_PAGE_MAIN_PREFIX
        self.assertTrue(
            next(iter(self.get_stats_instance.prefixes_info[ietf_page_main_prefix]['compilation_stats'].values()))
            == {
                'total': 30,
                'warnings': 15,
                'passed': 15,
                'badly formated': 15,
                'examples': 15,
            },
        )
        self.assertTrue(
            os.path.join(self.backup_directory, f'{ietf_page_main_prefix}2022_01_01.html')
            in self.get_stats_instance.remove_old_html_file_paths,
        )

    def test_gather_ietf_yang_out_of_rfc_compilation_stats(self):
        self.get_stats_instance.files = list_files_by_extensions(
            self.backup_directory,
            ('html',),
            debug_level=self.get_stats_instance.debug_level,
        )
        self.get_stats_instance.gather_ietf_yang_out_of_rfc_compilation_stats('IETFYANGOutOfRFC_2022_01_01.html')
        out_of_rfc_prefix = self.get_stats_instance.IETF_YANG_OUT_OF_RFC_PREFIX
        self.assertTrue(
            next(iter(self.get_stats_instance.prefixes_info[out_of_rfc_prefix]['compilation_stats'].values()))
            == {'total': 3},
        )
        self.assertTrue(
            os.path.join(self.backup_directory, f'{out_of_rfc_prefix}2022_01_01.html')
            in self.get_stats_instance.remove_old_html_file_paths,
        )

    def test_gather_backups_compilation_stats(self):
        self.get_stats_instance.files = list_files_by_extensions(
            self.backup_directory,
            ('html',),
            debug_level=self.get_stats_instance.debug_level,
        )
        self.get_stats_instance.gather_backups_compilation_stats(
            'IEEEStandardDraftYANGPageCompilation_2022_01_01.html',
            'IEEEStandardDraftYANGPageCompilation_',
        )
        backup_prefix = 'IEEEStandardDraftYANGPageCompilation_'
        self.assertTrue(
            next(iter(self.get_stats_instance.prefixes_info[backup_prefix]['compilation_stats'].values()))
            == {
                'total': 9,
                'warning': 3,
                'success': 3,
            },
        )
        self.assertTrue(
            os.path.join(self.backup_directory, f'{backup_prefix}2022_01_01.html')
            in self.get_stats_instance.remove_old_html_file_paths,
        )

    def test_list_of_files_in_dir_created_after_date(self):
        self.get_stats_instance.days = 2
        current_date = datetime.now().date()
        first_file = f'{(current_date - timedelta(days=1)).strftime("%Y-%m-%d")}.txt'
        second_file = f'{(current_date - timedelta(days=2)).strftime("%Y_%m-%d")}.txt'
        third_file = f'{(current_date - timedelta(days=3)).strftime("%Y-%m-%d")}.txt'
        files = [first_file, second_file, third_file]
        matching_files = self.get_stats_instance._list_of_files_in_dir_created_after_date(files)
        self.assertEqual(len(matching_files), 2)
        self.assertIn(first_file, matching_files)
        self.assertIn(second_file, matching_files)
        self.assertNotIn(third_file, matching_files)


if __name__ == '__main__':
    unittest.main()
