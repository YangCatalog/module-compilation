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


__author__ = 'Richard Zilincik'
__copyright__ = 'Copyright The IETF Trust 2022, All Rights Reserved'
__license__ = 'Apache License, Version 2.0'
__email__ = 'richard.zilincik@pantheon.tech'

import dataclasses
import filecmp
import json
import os
import shutil
import unittest
import uuid
from unittest import mock

from extractors import draft_extractor, extract_elem, extract_emails, helper, rfc_extractor
from utility.utility import remove_directory_content


class TestExtractElem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.resource_path = os.path.join(os.environ['TESTS_RESOURCES_DIR'], 'extractors/extract_elem')

    def test_extract_elem_grouping(self):
        groupings = [
            'grouping-catalog-module-metadata.txt',
            'grouping-online-source-file.txt',
            'grouping-organization-specific-metadata.txt',
            'grouping-shared-implementation-leafs.txt',
            'grouping-shared-module-leafs.txt',
            'grouping-yang-lib-common-leafs.txt',
            'grouping-yang-lib-implementation-leafs.txt',
            'grouping-yang-lib-schema-leaf.txt',
        ]

        extract_elem.extract_elem(
            os.path.join(self.resource_path, 'yang-catalog@2018-04-03.yang'),
            os.path.join(self.resource_path, 'extracted'),
            'grouping',
        )
        match, mismatch, errors = filecmp.cmpfiles(
            os.path.join(self.resource_path, 'extracted'),
            os.path.join(self.resource_path, 'expected'),
            groupings,
        )
        self.assertFalse(mismatch or errors)

    def test_extract_elem_identity(self):
        identities = ['identity-netconf.txt', 'identity-protocol.txt', 'identity-restconf.txt']

        extract_elem.extract_elem(
            os.path.join(self.resource_path, 'yang-catalog@2018-04-03.yang'),
            os.path.join(self.resource_path, 'extracted'),
            'identity',
        )
        match, mismatch, errors = filecmp.cmpfiles(
            os.path.join(self.resource_path, 'extracted'),
            os.path.join(self.resource_path, 'expected'),
            identities,
        )
        self.assertFalse(mismatch or errors)

    def test_extract_elem_typedef(self):
        typedefs = ['typedef-email-address.txt', 'typedef-path.txt', 'typedef-semver.txt']

        extract_elem.extract_elem(
            os.path.join(self.resource_path, 'yang-catalog@2018-04-03.yang'),
            os.path.join(self.resource_path, 'extracted'),
            'typedef',
        )
        match, mismatch, errors = filecmp.cmpfiles(
            os.path.join(self.resource_path, 'extracted'),
            os.path.join(self.resource_path, 'expected'),
            typedefs,
        )
        self.assertFalse(mismatch or errors)


class TestExtractEmails(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.resource_path = os.path.join(os.environ['TESTS_RESOURCES_DIR'], 'extractors/extract_emails')

    def test_extract_emails(self):
        result = extract_emails.extract_email_string(
            os.path.join(self.resource_path, 'emails.txt'),
            'foo.com',
            debug_level=1,
        )
        self.assertSetEqual(set(result.split(',')), {'foo@foo.com', 'bar@foo.com', 'foobar@foo.com'})

    def test_list_of_ietf_drafts(self):
        result = extract_emails.list_of_ietf_drafts(os.path.join(self.resource_path, 'drafts'))
        self.assertSetEqual(set(result), {'draft-foo.txt', 'draft-bar.txt'})


class TestExtractorHelper(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.resource_path = os.path.join(os.environ['TESTS_RESOURCES_DIR'], 'extractors/helper')

    def test_invert_yang_modules_dict(self):
        test_dict = {'test_key': ['test_yang_model_file1', 'test_yang_model_file2', 'test_yang_model_file3']}
        yang_models = test_dict['test_key']
        result = helper.invert_yang_modules_dict(test_dict, debug_level=1)
        self.assertEqual(len(result), len(yang_models))
        for yang_model in yang_models:
            self.assertEqual(result[yang_model], 'test_key')

    def test_remove_invalid_files(self):
        directory = os.path.join(self.resource_path, 'remove_invalid_files')
        yang_dict = {}
        backup_dir = os.path.join(self.resource_path, 'backup_dir')
        os.makedirs(backup_dir, exist_ok=True)
        for filename in os.listdir(directory):
            if os.path.isfile(filepath := os.path.join(directory, filename)):
                yang_dict[filename] = 'test value'
                shutil.copy2(filepath, backup_dir)
        try:
            helper.remove_invalid_files(directory, yang_dict)
            self.assertEqual(len(os.listdir(directory)), 1)
            self.assertEqual(len(yang_dict), 1)
            self.assertIn('valid_filename@1999-12-12.yang', yang_dict)
        finally:
            for filename in os.listdir(backup_dir):
                if os.path.isfile(filepath := os.path.join(backup_dir, filename)):
                    shutil.copy2(filepath, directory)
            shutil.rmtree(backup_dir)


class TestDraftExtractor(unittest.TestCase):
    resource_path: str
    drafts_path: str
    draft_extraction_paths: str
    draft_extractor_paths: draft_extractor.DraftExtractorPaths
    problematic_drafts_dir: str

    @classmethod
    def setUpClass(cls):
        cls.resource_path = os.path.join(os.environ['TESTS_RESOURCES_DIR'], 'extractors/draft_extractor')
        cls.drafts_path = os.path.join(cls.resource_path, 'drafts')
        cls.draft_extraction_paths = os.path.join(cls.resource_path, 'draft_extraction_paths')
        cls.draft_extractor_paths = draft_extractor.DraftExtractorPaths(
            draft_path=cls.drafts_path,
            yang_path=os.path.join(cls.draft_extraction_paths, 'yang'),
            draft_elements_path=os.path.join(cls.draft_extraction_paths, 'draft_elements'),
            draft_path_strict=os.path.join(cls.draft_extraction_paths, 'draft_strict'),
            all_yang_example_path=os.path.join(cls.draft_extraction_paths, 'all_yang_example'),
            draft_path_only_example=os.path.join(cls.draft_extraction_paths, 'only_examples_drafts'),
            all_yang_path=os.path.join(cls.draft_extraction_paths, 'all_yang'),
            draft_path_no_strict=os.path.join(cls.draft_extraction_paths, 'draft_no_strict'),
            code_snippets_dir=os.path.join(cls.draft_extraction_paths, 'code_snippets'),
        )
        for path in dataclasses.asdict(cls.draft_extractor_paths).values():
            os.makedirs(path, exist_ok=True)
        cls.problematic_drafts_dir = os.path.join(cls.resource_path, 'incorrect_drafts/drafts')
        os.makedirs(cls.problematic_drafts_dir, exist_ok=True)
        cls.problematic_drafts_path = os.path.join(cls.problematic_drafts_dir, 'problematic_drafts.json')

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.draft_extraction_paths)
        shutil.rmtree(cls.problematic_drafts_dir)

    def setUp(self):
        with open(self.problematic_drafts_path, 'w') as f:
            json.dump({'draft_name.txt': 'errors'}, f)

    def tearDown(self):
        for directory in os.listdir(self.draft_extraction_paths):
            remove_directory_content(os.path.join(self.draft_extraction_paths, directory))

    def test_extraction(self):
        extractor = draft_extractor.DraftExtractor(
            draft_extractor_paths=self.draft_extractor_paths,
            debug_level=1,
            extract_elements=True,
            extract_examples=True,
            copy_drafts=True,
        )
        extractor.extract()
        self.assertEqual(
            sorted(os.listdir(self.draft_extractor_paths.yang_path)),
            sorted(
                [
                    'ietf-vrrp@2023-03-08.yang',
                    'example@2022-06-01.yang',
                    'example@2022-09-01.yang',
                    'example@2022-07-01.yang',
                ],
            ),
        )
        self.assertTrue(len(os.listdir(self.draft_extractor_paths.draft_elements_path)) > 0)
        self.assertListEqual(
            sorted(os.listdir(self.draft_extractor_paths.draft_path_strict)),
            sorted(['draft-acee-rtgwg-vrrp-rfc8347bis-01.txt', 'draft-eastlake-fnv-19.txt']),
        )
        self.assertListEqual(
            sorted(os.listdir(self.draft_extractor_paths.draft_path_no_strict)),
            sorted(['draft-acee-rtgwg-vrrp-rfc8347bis-01.txt', 'draft-eastlake-fnv-19.txt']),
        )
        self.assertListEqual(
            os.listdir(self.draft_extractor_paths.all_yang_example_path),
            ['example-module@2022-08-01.yang'],
        )
        self.assertListEqual(
            os.listdir(self.draft_extractor_paths.draft_path_only_example),
            ['draft-eastlake-fnv-19.txt'],
        )
        self.assertListEqual(
            sorted(os.listdir(self.draft_extractor_paths.all_yang_path)),
            sorted(
                [
                    'ietf-vrrp@2023-03-08.yang',
                    'example@2022-06-01.yang',
                    'example-module@2022-08-01.yang',
                    'example@2022-09-01.yang',
                    'example@2022-07-01.yang',
                ],
            ),
        )
        code_snippets_dir = self.draft_extractor_paths.code_snippets_dir
        self.assertTrue(len(os.listdir(os.path.join(code_snippets_dir, 'draft-eastlake-fnv-19'))) > 0)
        draft_without_code_snippets = os.path.join(code_snippets_dir, 'draft-acee-rtgwg-vrrp-rfc8347bis-01')
        # After the next update of xym, dirs for drafts without code snippets won't be created anymore
        if os.path.exists(draft_without_code_snippets):
            self.assertTrue(len(os.listdir(draft_without_code_snippets)) == 0)
        self.assertDictEqual(extractor.drafts_missing_code_section, {})
        self.assertDictEqual(
            extractor.draft_yang_example_dict,
            {'draft-eastlake-fnv-19.txt': ['example-module@2022-08-01.yang']},
        )

    @mock.patch('message_factory.MessageFactory')
    def test_dump_incorrect_drafts(self, message_factory_mock: mock.MagicMock):
        incorrect_drafts_dir = os.path.dirname(self.problematic_drafts_dir)
        extractor = draft_extractor.DraftExtractor(
            draft_extractor_paths=self.draft_extractor_paths,
            debug_level=1,
            message_factory=message_factory_mock,
        )
        extractor.drafts_missing_code_section = {'test_draft_name.txt': 'test error string'}
        extractor.dump_incorrect_drafts(incorrect_drafts_dir, send_emails_about_problematic_drafts=True)
        message_factory_mock.send_problematic_draft.assert_called_with(
            ['test_draft_name@ietf.org'],
            'test_draft_name.txt',
            'test error string',
            draft_name_without_revision='test_draft_name',
        )
        with open(self.problematic_drafts_path, 'r') as f:
            problematic_drafts = json.load(f)
        self.assertDictEqual(problematic_drafts, extractor.drafts_missing_code_section)


class TestRFCExtractor(unittest.TestCase):
    resource_path: str
    rfcs_path: str
    rfc_extraction_paths: str
    rfc_extractor_paths: rfc_extractor.RFCExtractorPaths
    old_rfc_modules_move_to_dir: str

    @classmethod
    def setUpClass(cls):
        cls.resource_path = os.path.join(os.environ['TESTS_RESOURCES_DIR'], 'extractors/rfc_extractor')
        cls.rfcs_path = os.path.join(cls.resource_path, 'rfcs')
        cls.rfc_extraction_paths = os.path.join(cls.resource_path, 'rfc_extraction_paths')
        cls.rfc_extractor_paths = rfc_extractor.RFCExtractorPaths(
            rfc_path=cls.rfcs_path,
            rfc_yang_path=os.path.join(cls.rfc_extraction_paths, 'rfc_yang'),
            rfc_extraction_yang_path=os.path.join(cls.rfc_extraction_paths, 'rfc_extraction'),
            code_snippets_directory=os.path.join(cls.rfc_extraction_paths, 'code_snippets'),
        )
        for path in dataclasses.asdict(cls.rfc_extractor_paths).values():
            os.makedirs(path, exist_ok=True)
        cls.old_rfc_modules_dir = os.path.join(cls.resource_path, 'old_rfcs_modules')
        cls.old_rfc_modules_move_to_dir = os.path.join(cls.resource_path, 'old_rfcs_modules_move_to')
        os.makedirs(cls.old_rfc_modules_move_to_dir, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.rfc_extraction_paths)
        shutil.rmtree(cls.old_rfc_modules_move_to_dir)

    def tearDown(self):
        for directory in os.listdir(self.rfc_extraction_paths):
            remove_directory_content(os.path.join(self.rfc_extraction_paths, directory))
        remove_directory_content(self.old_rfc_modules_move_to_dir)

    def test_extraction(self):
        extractor = rfc_extractor.RFCExtractor(rfc_extractor_paths=self.rfc_extractor_paths, debug_level=1)
        extractor.extract()
        self.assertDictEqual(
            extractor.rfc_yang_dict,
            {'rfc8639.txt': ['ietf-subscribed-notifications@2019-09-09.yang']},
        )
        self.assertTrue(len(os.listdir(self.rfc_extractor_paths.rfc_extraction_yang_path)) > 0)
        self.assertListEqual(
            os.listdir(self.rfc_extractor_paths.rfc_yang_path),
            ['ietf-subscribed-notifications@2019-09-09.yang'],
        )
        self.assertEqual(len(os.listdir(os.path.join(self.rfc_extractor_paths.code_snippets_directory, 'rfc8639'))), 1)

    def test_clean_old_rfc_yang_modules(self):
        backup_dir = os.path.join(self.resource_path, uuid.uuid4().hex)
        os.makedirs(backup_dir, exist_ok=True)
        for filename in os.listdir(self.old_rfc_modules_dir):
            filepath = os.path.join(self.old_rfc_modules_dir, filename)
            if os.path.isfile(filepath):
                shutil.copy2(filepath, backup_dir)
        extractor = rfc_extractor.RFCExtractor(rfc_extractor_paths=self.rfc_extractor_paths, debug_level=1)
        extractor.inverted_rfc_yang_dict['ietf-foo@2010-01-18.yang'] = 'test_draft.txt'
        try:
            extractor.clean_old_rfc_yang_modules(self.old_rfc_modules_dir, self.old_rfc_modules_move_to_dir)
            self.assertListEqual(os.listdir(self.old_rfc_modules_dir), ['hw.yang'])
            self.assertListEqual(os.listdir(self.old_rfc_modules_move_to_dir), ['hardware-entities.yang'])
            self.assertDictEqual(extractor.inverted_rfc_yang_dict, {})
        finally:
            for filename in os.listdir(backup_dir):
                shutil.copy2(os.path.join(backup_dir, filename), self.old_rfc_modules_dir)
            shutil.rmtree(backup_dir)


if __name__ == '__main__':
    unittest.main()
