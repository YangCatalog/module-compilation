# Copyright The IETF Trust 2023, All Rights Reserved
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

import json
import os
import shutil
import unittest
from unittest import mock

import modules_compilation.compile_modules as compile_modules
from create_config import create_config
from versions import validator_versions


class TestCompileModules(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.resources_path = os.path.join(os.environ['TESTS_RESOURCES_DIR'], 'compile_modules')
        cls.config = create_config()
        cls.cache_directory = cls.config.get('Directory-Section', 'cache')
        cls.ietf_directory = cls.resource('ietf')
        cls.config.set('Directory-Section', 'ietf-directory', cls.ietf_directory)
        cls.all_modules_dir = cls.resource('all_modules')
        cls.config.set('Directory-Section', 'save-file-dir', cls.all_modules_dir)
        cls.web_private = cls.resource('html/private')
        cls.config.set('Web-Section', 'private-directory', cls.web_private)
        cls.config.set('Directory-Section', 'modules-directory', cls.resource('modules-directory'))
        cls.validator_versions: dict[str, str] = {
            'pyang': validator_versions['pyang_version'],
            'confdc': validator_versions['confd_version'],
            'yangdumppro': validator_versions['yangdump_version'],
            'yanglint': validator_versions['yanglint_version'],
        }

    def setUp(self):
        self.basic_compile_modules_options = compile_modules.CompileModulesABC.Options(
            debug_level=1,
            force_compilation=True,
            lint=False,
            allinclusive=True,
            metadata='',
            config=self.config,
        )

    def tearDown(self):
        for root, _, filenames in os.walk(self.web_private):
            for filename in filenames:
                if filename == '.gitkeep':
                    continue
                os.remove(os.path.join(root, filename))
        for filename in os.listdir(self.all_modules_dir):
            if filename == '.gitkeep':
                continue
            os.remove(os.path.join(self.all_modules_dir, filename))
        hashes_file = os.path.join(self.cache_directory, 'sdo_files_modification_hashes.json')
        if os.path.exists(hashes_file):
            os.remove(hashes_file)

    @classmethod
    def resource(cls, path: str) -> str:
        return os.path.join(cls.resources_path, path)

    @mock.patch('modules_compilation.compile_modules.check_yangcatalog_data')
    def test_rfc_modules_compilation(self, check_yang_catalog_mock: mock.MagicMock):
        modules_count = len(os.listdir(os.path.join(self.ietf_directory, 'YANG-rfc')))
        rfc_modules_compilation_instance = compile_modules.CompileRfcModules(self.basic_compile_modules_options)
        prefix = rfc_modules_compilation_instance.prefix
        json_file = f'{prefix}.json'
        rfc_modules_compilation_instance()
        check_yang_catalog_mock.assert_called()
        private_dir_files = os.listdir(self.web_private)
        self.assertIn('IETFYANGRFC.html', private_dir_files)
        self.assertIn('IETFYANGRFC.json', private_dir_files)
        with open(os.path.join(self.web_private, 'IETFYANGRFC.json')) as f:
            self.assertEqual(len(json.load(f)), modules_count)
        self.assertIn(f'{prefix}YANGPageMain.html', private_dir_files)
        self.assertIn(f'{prefix}YANGPageCompilation.html', private_dir_files)
        with open(os.path.join(self.web_private, json_file)) as f:
            self.assertEqual(len(json.load(f)), modules_count)

    @mock.patch('modules_compilation.compile_modules.check_yangcatalog_data')
    def test_draft_modules_compilation(self, check_yang_catalog_mock: mock.MagicMock):
        modules_count = len(os.listdir(os.path.join(self.ietf_directory, 'YANG')))
        draft_modules_compilation_instance = compile_modules.CompileDraftModules(self.basic_compile_modules_options)
        prefix = draft_modules_compilation_instance.prefix
        json_file = f'{prefix}.json'
        draft_modules_compilation_instance()
        check_yang_catalog_mock.assert_called()
        private_dir_files = os.listdir(self.web_private)
        self.assertIn('IETFYANGPageMain.html', private_dir_files)
        self.assertIn('IETFCiscoAuthorsYANGPageCompilation.html', private_dir_files)
        self.assertIn('IETFDraftArchive.json', private_dir_files)
        with open(os.path.join(self.web_private, 'IETFDraftArchive.json')) as f:
            self.assertEqual(len(json.load(f)), modules_count)
        self.assertIn(f'{prefix}YANGPageCompilation.html', private_dir_files)
        with open(os.path.join(self.web_private, json_file)) as f:
            self.assertEqual(len(json.load(f)), modules_count)

    @mock.patch('modules_compilation.compile_modules.check_yangcatalog_data')
    def test_draft_archive_modules_compilation(self, check_yang_catalog_mock: mock.MagicMock):
        modules_count = len(os.listdir(os.path.join(self.ietf_directory, 'YANG')))
        draft_archive_modules_compilation_instance = compile_modules.CompileDraftArchiveModules(
            self.basic_compile_modules_options,
        )
        prefix = draft_archive_modules_compilation_instance.prefix
        json_file = f'{prefix}.json'
        draft_archive_modules_compilation_instance()
        check_yang_catalog_mock.assert_called()
        private_dir_files = os.listdir(self.web_private)
        self.assertIn('IETFYANGPageMain.html', private_dir_files)
        self.assertIn('IETFDraftArchive.json', private_dir_files)
        with open(os.path.join(self.web_private, 'IETFCiscoAuthors.json')) as f:
            self.assertEqual(len(json.load(f)), modules_count)
        with open(os.path.join(self.web_private, json_file)) as f:
            self.assertEqual(len(json.load(f)), modules_count)

    @mock.patch('modules_compilation.compile_modules.check_yangcatalog_data')
    def test_example_modules_compilation(self, check_yang_catalog_mock: mock.MagicMock):
        modules_count = len(os.listdir(os.path.join(self.ietf_directory, 'YANG')))
        example_modules_compilation_instance = compile_modules.CompileExampleModules(self.basic_compile_modules_options)
        prefix = example_modules_compilation_instance.prefix
        json_file = f'{prefix}.json'
        example_modules_compilation_instance()
        check_yang_catalog_mock.assert_called()
        private_dir_files = os.listdir(self.web_private)
        self.assertIn('IETFYANGPageMain.html', private_dir_files)
        self.assertIn(f'{prefix}YANGPageCompilation.html', private_dir_files)
        with open(os.path.join(self.web_private, json_file)) as f:
            self.assertEqual(len(json.load(f)), modules_count)

    @mock.patch('modules_compilation.compile_modules.check_yangcatalog_data')
    def test_hashed_files_compilation(self, check_yang_catalog_mock: mock.MagicMock):
        prefix = 'TestPrefix'
        json_file = f'{prefix}.json'
        root_dir = os.path.join(self.ietf_directory, 'test_dir')
        self.write_cached_result_to_json_file(json_file, root_dir, root_dir)
        modules_count = len(os.listdir(root_dir))
        self.basic_compile_modules_options.force_compilation = False
        modules_compilation_instance = compile_modules.CompileBaseModules(
            prefix,
            root_dir,
            self.basic_compile_modules_options,
        )
        self.add_modules_to_file_hasher(modules_compilation_instance, root_dir, root_dir)
        modules_compilation_instance()
        check_yang_catalog_mock.assert_not_called()
        self.assertEqual(modules_compilation_instance.file_hasher.updated_hashes, {})
        private_dir_files = os.listdir(self.web_private)
        self.assertIn(f'{prefix}YANGPageCompilation.html', private_dir_files)
        with open(os.path.join(self.web_private, json_file)) as f:
            self.assertEqual(len(json.load(f)), modules_count)

    @mock.patch('modules_compilation.compile_modules.check_yangcatalog_data')
    def test_change_modules_already_available_in_all_modules_dir(self, check_yang_catalog_mock: mock.MagicMock):
        prefix = 'TestPrefix'
        json_file = f'{prefix}.json'
        root_dir = os.path.join(self.ietf_directory, '_test_test_dir')
        os.makedirs(os.path.join(self.ietf_directory, '_test_test_dir'), exist_ok=True)
        for filename in os.listdir((test_dir := os.path.join(self.ietf_directory, 'test_dir'))):
            file_path = os.path.join(test_dir, filename)
            shutil.copy(file_path, os.path.join(self.all_modules_dir, filename))
            shutil.copy(file_path, os.path.join(root_dir, filename))
        modules_count = len(os.listdir(root_dir))
        self.write_cached_result_to_json_file(json_file, root_dir, self.all_modules_dir)
        self.basic_compile_modules_options.force_compilation = False
        modules_compilation_instance = compile_modules.CompileBaseModules(
            prefix,
            root_dir,
            self.basic_compile_modules_options,
        )
        self.add_modules_to_file_hasher(modules_compilation_instance, root_dir, self.all_modules_dir)
        root_dir_files = os.listdir(root_dir)
        for i, filename in enumerate(os.listdir((test_dir := os.path.join(self.ietf_directory, 'YANG')))):
            if i >= modules_count:
                break
            root_dir_file = root_dir_files[i]
            shutil.copy(os.path.join(test_dir, filename), root_dir_file)
        modules_compilation_instance()
        check_yang_catalog_mock.assert_not_called()
        self.assertEqual(modules_compilation_instance.file_hasher.updated_hashes, {})
        private_dir_files = os.listdir(self.web_private)
        self.assertIn(f'{prefix}YANGPageCompilation.html', private_dir_files)
        with open(os.path.join(self.web_private, json_file)) as f:
            self.assertEqual(len(json.load(f)), modules_count)
        shutil.rmtree(root_dir)

    def write_cached_result_to_json_file(self, json_filename: str, modules_dir: str, cached_result_file_directory: str):
        json_file_data = {}
        module_filenames = os.listdir(modules_dir)
        for filename in module_filenames:
            json_file_data[filename] = {
                'yang_file_path': os.path.join(cached_result_file_directory, filename),
                'compilation_metadata': ['FAILED'] * len(module_filenames),
                'compilation_results': {
                    'test_parser': '',
                },
            }
        with open(os.path.join(self.web_private, json_filename), 'w') as f:
            json.dump(json_file_data, f)

    def add_modules_to_file_hasher(
        self,
        modules_compilation_instance: compile_modules.CompileModulesABC,
        modules_directory: str,
        modules_directory_to_use_in_hasher: str,
    ):
        file_hasher = modules_compilation_instance.file_hasher
        for filename in os.listdir(modules_directory):
            file_hasher.files_hashes[os.path.join(modules_directory_to_use_in_hasher, filename)] = {
                'hash': file_hasher.hash_file(os.path.join(modules_directory, filename)),
                'validator_versions': self.validator_versions,
            }


if __name__ == '__main__':
    unittest.main()
