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

import json
import os
import shutil
import unittest
from unittest import mock
from unittest.mock import MagicMock

import check_archived_drafts
from create_config import create_config


class MessageFactoryMock(MagicMock):
    pass


class TestCheckArchivedDrafts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        resources_path = os.path.join(os.environ['TESTS_RESOURCES_DIR'], 'check_archived_drafts')
        cls.config = create_config()
        cls.cronjob_result_path = os.path.join(cls.config.get('Directory-Section', 'temp'), 'cronjob.json')
        cls.config.set('Directory-Section', 'var', os.path.join(resources_path, 'var'))
        cls.ietf_directory = os.path.join(resources_path, 'ietf')
        cls.config.set('Directory-Section', 'ietf-directory', cls.ietf_directory)

    def setUp(self):
        self.check_archived_drafts_instance = check_archived_drafts.CheckArchivedDrafts(
            config=self.config,
            message_factory=MessageFactoryMock(),
        )

    def tearDown(self):
        if os.path.exists(self.cronjob_result_path):
            os.remove(self.cronjob_result_path)
        shutil.rmtree(self.check_archived_drafts_instance.extracted_missing_modules_directory, ignore_errors=True)
        shutil.rmtree(self.check_archived_drafts_instance.yang_path, ignore_errors=True)

    @mock.patch('requests.get')
    def test_check_archived_drafts_script_successful(self, requests_get_mock):
        requests_get_mock.return_value = mock.MagicMock()
        requests_get_mock.return_value.json = lambda: {}
        os.makedirs(self.check_archived_drafts_instance.yang_path, exist_ok=True)
        os.makedirs(self.check_archived_drafts_instance.all_yang_drafts_strict, exist_ok=True)
        self.check_archived_drafts_instance.start_process()
        self.assertNotEqual(self.check_archived_drafts_instance.missing_modules, [])
        self.assertListEqual(
            sorted(self.check_archived_drafts_instance.missing_modules),
            sorted(os.listdir(self.check_archived_drafts_instance.extracted_missing_modules_directory)),
        )
        self.check_archived_drafts_instance.message_factory.send_missing_modules.assert_called_with(
            self.check_archived_drafts_instance.missing_modules,
            [],
        )
        self.assertTrue(os.path.exists(self.cronjob_result_path))
        with open(self.cronjob_result_path, 'r') as f:
            cronjob_result = json.load(f)
        self.assertNotEqual(cronjob_result, {})
        self.assertTrue(
            (script_result := cronjob_result.get(check_archived_drafts.file_basename.split('.py')[0])) is not None
            and script_result['status'] == 'Success',
        )

    def test_check_archived_drafts_script_failure(self):
        self.check_archived_drafts_instance._extract_drafts = mock.MagicMock()
        self.check_archived_drafts_instance._extract_drafts.side_effect = Exception()
        try:
            self.check_archived_drafts_instance.start_process()
        except Exception:
            pass
        self.assertTrue(os.path.exists(self.cronjob_result_path))
        with open(self.cronjob_result_path, 'r') as f:
            cronjob_result = json.load(f)
        self.assertNotEqual(cronjob_result, {})
        self.assertTrue(
            (script_result := cronjob_result.get(check_archived_drafts.file_basename.split('.py')[0])) is not None
            and script_result['status'] == 'Fail',
        )

    def test_extract_drafts(self):
        os.makedirs(self.check_archived_drafts_instance.yang_path, exist_ok=True)
        self.check_archived_drafts_instance._extract_drafts()
        self.assertNotEqual(os.listdir(self.check_archived_drafts_instance.yang_path), [])

    @mock.patch('requests.get')
    def test_get_all_modules(self, requests_get_mock):
        requests_get_mock.return_value = mock.MagicMock()
        requests_get_mock.return_value.json = lambda: {'module': [{'name': 'test', 'revision': '2020-02-02'}]}
        self.check_archived_drafts_instance._get_all_modules()
        self.assertEqual(self.check_archived_drafts_instance.all_modules_keys, ['test@2020-02-02'])
        with open(os.path.join(os.path.dirname(check_archived_drafts.__file__), 'resources/old-rfcs.json'), 'r') as f:
            old_modules = json.load(f)
        with open(os.path.join(self.check_archived_drafts_instance.var_path, 'unparsable-modules.json'), 'r') as f:
            unparsable_modules = json.load(f)
        self.assertTupleEqual(
            self.check_archived_drafts_instance.modules_to_skip,
            (*old_modules, *unparsable_modules),
        )

    def test_get_incorrect_and_missing_modules(self):
        os.makedirs(self.check_archived_drafts_instance.yang_path, exist_ok=True)
        without_revision_module_path = os.path.join(
            self.check_archived_drafts_instance.yang_path,
            'without_revision.yang',
        )
        missing_module_path = os.path.join(
            self.check_archived_drafts_instance.yang_path,
            'missing_module@2020-20-20.yang',
        )
        absent_module_path = os.path.join(
            self.check_archived_drafts_instance.yang_path,
            'absent_module@2020-20-20.yang',
        )
        with (
            open(without_revision_module_path, 'w') as without_revision_module,
            open(missing_module_path, 'w') as missing_module,
            open(absent_module_path, 'w') as absent_module,
        ):
            without_revision_module.write('')
            missing_module.write('')
            absent_module.write('')
        self.check_archived_drafts_instance.all_modules_keys = ['present_module@2020-20-20']
        self.check_archived_drafts_instance.modules_to_skip = ['unparsable_module@2020-20-20.yang']
        self.check_archived_drafts_instance.draft_extractor.inverted_draft_yang_dict = {
            'example@2020-20-20.yang': '',
            '@2020-20-20.yang': '',
            'unparsable_module@2020-20-20.yang': '',
            'incorrect_revision@2020-2-20.yang': '',
            'without_revision.yang': '',
            'present_module@2020-20-20.yang': '',
            'missing_module@2020-20-20.yang': '',
            'absent_module@2020-20-20.yang': '',
        }
        self.check_archived_drafts_instance._get_incorrect_and_missing_modules()
        self.assertListEqual(
            self.check_archived_drafts_instance.incorrect_revision_modules,
            ['incorrect_revision@2020-2-20.yang'],
        )
        self.assertListEqual(
            self.check_archived_drafts_instance.missing_modules,
            ['without_revision.yang', 'missing_module@2020-20-20.yang', 'absent_module@2020-20-20.yang'],
        )
        self.assertTrue(
            os.path.exists(
                os.path.join(
                    self.check_archived_drafts_instance.extracted_missing_modules_directory,
                    'without_revision.yang',
                ),
            ),
        )
        self.assertTrue(
            os.path.exists(
                os.path.join(
                    self.check_archived_drafts_instance.extracted_missing_modules_directory,
                    'missing_module@2020-20-20.yang',
                ),
            ),
        )
        self.assertTrue(
            os.path.exists(
                os.path.join(
                    self.check_archived_drafts_instance.extracted_missing_modules_directory,
                    'absent_module@2020-20-20.yang',
                ),
            ),
        )


if __name__ == '__main__':
    unittest.main()
