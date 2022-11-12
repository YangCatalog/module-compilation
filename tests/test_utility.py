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

import json
import os
import unittest
from configparser import ConfigParser
from unittest import mock

import utility.utility as utility
from create_config import create_config
from redis_connections.constants import RedisDatabasesEnum
from redis_connections.redis_connection import RedisConnection
from versions import ValidatorsVersions


class TestUtilityBase(unittest.TestCase):
    resource_path: str
    config: ConfigParser

    @classmethod
    def setUpClass(cls):
        cls.resource_path = os.path.join(os.environ['VIRTUAL_ENV'], 'tests/resources/utility')
        cls.config = create_config(os.path.join(os.path.dirname(cls.resource_path), 'test.conf'))


class TestUtility(TestUtilityBase):
    def test_module_or_submodule(self):
        result = utility.module_or_submodule(os.path.join(self.resource_path, 'module_or_submodule/module.yang'))
        self.assertEqual(result, 'module')

        result = utility.module_or_submodule(os.path.join(self.resource_path, 'module_or_submodule/submodule.yang'))
        self.assertEqual(result, 'submodule')

        result = utility.module_or_submodule(os.path.join(self.resource_path, 'module_or_submodule/neither.yang'))
        self.assertEqual(result, 'wrong file')

    def test_dict_to_list(self):
        result = utility.dict_to_list({'foo': ['bar', 'foobar'], 'boo': ['far', 'boofar']}, is_rfc=False)
        self.assertEqual(result, [['foo', 'bar', 'foobar'], ['boo', 'far', 'boofar']])

        result = utility.dict_to_list({'foo': ['bar', 'foobar'], 'boo': ['far', 'boofar']}, is_rfc=True)
        self.assertEqual(result, [['foo', ['bar', 'foobar']], ['boo', ['far', 'boofar']]])

    def test_list_br_html_addition(self):
        result = utility.list_br_html_addition([['foo\n', 'bar\n'], [42, 'foo\nbar\n'], []])
        self.assertEqual(result, [['foo<br>', 'bar<br>'], ['foo<br>bar<br>'], []])

    def test_resolve_maturity_level(self):
        result = utility._resolve_maturity_level(None, 'fake-ietf-document')
        self.assertEqual(result, 'not-applicable')

        result = utility._resolve_maturity_level(utility.IETF.RFC, 'foo-document-name')
        self.assertEqual(result, 'ratified')

        result = utility._resolve_maturity_level(utility.IETF.DRAFT, 'draft-ietf-new-thing')
        self.assertEqual(result, 'adopted')

        result = utility._resolve_maturity_level(utility.IETF.DRAFT, 'draft-new-thing')
        self.assertEqual(result, 'initial')

    def test_resolve_working_group(self):
        result = utility._resolve_working_group('iana-crypt-hash@2014-08-06', utility.IETF.RFC, 'iana-crypt-hash')
        self.assertEqual(result, 'NETMOD')

        result = utility._resolve_working_group('ietf-restconf@2017-01-26', utility.IETF.RFC, 'ietf-restconf')
        self.assertEqual(result, 'NETCONF')

        result = utility._resolve_working_group(
            'draft-foo-groupname-bar@2017-01-26',
            utility.IETF.DRAFT,
            'draft-foo-groupname-bar',
        )
        self.assertEqual(result, 'groupname')

    def test_path_in_dir(self):
        result = utility._path_in_dir(os.path.join(self.resource_path, 'path_in_dir/foo.yang'))
        self.assertEqual(result, os.path.join(self.resource_path, 'path_in_dir/foo.yang'))

        result = utility._path_in_dir(os.path.join(self.resource_path, 'path_in_dir/bar.yang'))
        self.assertEqual(result, os.path.join(self.resource_path, 'path_in_dir/subdir/bar.yang'))

        result = utility._path_in_dir(os.path.join(self.resource_path, 'path_in_dir/foobar.yang'))
        self.assertEqual(result, os.path.join(self.resource_path, 'path_in_dir/subdir/subsubdir/foobar.yang'))

        result = utility._path_in_dir(os.path.join(self.resource_path, 'path_in_dir/boofar.yang'))
        self.assertEqual(result, os.path.join(self.resource_path, 'path_in_dir/boofar.yang'))

    def test_number_that_passed_compilation(self):
        result = utility.number_that_passed_compilation(
            {
                'foo': ['test', 'stuff', 'PASSED', 'more stuff'],
                'bar': ['test', 'stuff', 'FAILED', 'more stuff'],
                'foobar': ['test', 'stuff', 'PASSED WITH WARNINGS', 'more stuff'],
                'boofar': ['test', 'stuff', 'PASSED', 'more stuff'],
            },
            2,
            'PASSED',
        )
        self.assertEqual(result, 2)

    def test_list_files_by_extension_not_recursive(self):
        srcdir = os.path.join(self.resource_path, 'files_by_extension')
        txt_files_not_recursive = utility.list_files_by_extensions(
            srcdir=srcdir,
            extensions=('txt',),
            recursive=False,
            return_full_paths=False,
        )
        self.assertEqual(len(txt_files_not_recursive), 2)
        self.assertListEqual(sorted(txt_files_not_recursive), ['f1.txt', 'f2.txt'])
        html_and_txt_files_not_recursive = utility.list_files_by_extensions(
            srcdir=srcdir,
            extensions=('html', 'txt'),
            recursive=False,
        )
        self.assertEqual(len(html_and_txt_files_not_recursive), 4)
        self.assertListEqual(sorted(html_and_txt_files_not_recursive), ['f1.html', 'f1.txt', 'f2.html', 'f2.txt'])

    def test_list_files_by_extension_recursive(self):
        srcdir = os.path.join(self.resource_path, 'files_by_extension')
        recursive_dir1 = os.path.join(srcdir, 'recursive_dir1')
        recursive_dir2 = os.path.join(recursive_dir1, 'recursive_dir2')
        txt_files_recursive = utility.list_files_by_extensions(
            srcdir=srcdir,
            extensions=('txt',),
            recursive=True,
            return_full_paths=True,
        )
        self.assertEqual(len(txt_files_recursive), 4)
        self.assertListEqual(
            sorted(txt_files_recursive),
            sorted(
                [
                    os.path.join(srcdir, 'f1.txt'),
                    os.path.join(srcdir, 'f2.txt'),
                    os.path.join(recursive_dir1, 'f1.txt'),
                    os.path.join(recursive_dir2, 'f1.txt'),
                ],
            ),
        )
        html_and_txt_files_recursive = utility.list_files_by_extensions(
            srcdir=srcdir,
            extensions=('html', 'txt'),
            recursive=True,
            return_full_paths=False,
        )
        self.assertEqual(len(html_and_txt_files_recursive), 8)
        self.assertEqual(html_and_txt_files_recursive.count('f1.txt'), 3)
        self.assertEqual(html_and_txt_files_recursive.count('f2.txt'), 1)
        self.assertEqual(html_and_txt_files_recursive.count('f1.html'), 3)
        self.assertEqual(html_and_txt_files_recursive.count('f2.html'), 1)

    def test_generate_compilation_result_file(self):
        result_dir = os.path.join(self.resource_path, 'generation_of_compilation_result_file')
        module_data = {
            'name': 'test',
            'revision': '2020-02-02',
            'organization': 'cisco',
        }
        filename = f'{module_data["name"]}@{module_data["revision"]}_{module_data["organization"]}.html'
        result_file_path = os.path.join(result_dir, filename)
        with open(result_file_path, 'rb') as f:
            file_data = f.read()
        file_last_modification_time = os.path.getmtime(result_file_path)
        versions = ValidatorsVersions().get_versions()
        compilation_results = {
            'pyang_lint': 'lint',
            'pyang': versions.get('pyang_version', 'test'),
            'confdrc': versions.get('confd_version', 'test'),
            'yumadump': versions.get('yangdump_version', 'test'),
            'yanglint': versions.get('yanglin4t_version', 'test'),
        }
        file_url = utility._generate_compilation_result_file(
            module_data=module_data,
            compilation_results=compilation_results,
            result_html_dir=result_dir,
            is_rfc=False,
            versions=versions,
        )
        self.assertEqual(file_url, filename)
        self.assertGreater(os.path.getmtime(result_file_path), file_last_modification_time)
        with open(result_file_path, 'wb') as f:
            f.write(file_data)


class TestCheckCatalogData(TestUtilityBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.modules_redis_connection = RedisConnection(config=cls.config)
        cls.incomplete_modules_redis_connection = RedisConnection(
            modules_db=RedisDatabasesEnum.INCOMPLETE_MODULES_DB.value,
            config=cls.config,
        )
        utility.module_db = cls.modules_redis_connection
        utility.incomplete_db = cls.incomplete_modules_redis_connection

    def tearDown(self):
        super().tearDown()
        self.modules_redis_connection.modules_db.flushdb()
        self.incomplete_modules_redis_connection.modules_db.flushdb()

    @mock.patch('utility.utility._generate_compilation_result_file', mock.MagicMock(return_value=['test.txt']))
    def test_check_yangcatalog_data_complete(self):
        all_modules_data = {
            'yang-catalog@2018-04-03': {'name': 'yang-catalog', 'revision': '2018-04-03', 'organization': 'ietf'},
        }
        new_module_data = {
            'document-name': 'test document name',
            'reference': 'test reference',
            'author-email': 'test_email@example.com',
            'compilation-status': 'test compilation status',
        }
        utility.check_yangcatalog_data(
            config=self.config,
            yang_file_pseudo_path=os.path.join(
                self.resource_path,
                'check_yangcatalog_data',
                'yang-catalog@2018-04-03.yang',
            ),
            new_module_data=new_module_data,
            compilation_results={},
            all_modules_data=all_modules_data,
        )
        redis_key = self.modules_redis_connection._create_module_key(all_modules_data['yang-catalog@2018-04-03'])
        module_data = json.loads(self.modules_redis_connection.get_module(redis_key))
        self.assertEqual(module_data.get('document-name'), new_module_data.get('document-name'))
        self.assertEqual(module_data.get('reference'), new_module_data.get('reference'))
        self.assertEqual(module_data.get('author-email'), new_module_data.get('author-email'))
        self.assertIn('compilation-result', module_data)
        self.assertEqual(self.incomplete_modules_redis_connection.get_module(redis_key), '{}')

    @mock.patch('utility.utility._generate_compilation_result_file', mock.MagicMock(return_value=['test.txt']))
    def test_check_yangcatalog_data_incomplete(self):
        new_module_data = {
            'document-name': 'test document name',
            'reference': 'test reference',
            'author-email': 'test_email@example.com',
        }
        utility.check_yangcatalog_data(
            config=self.config,
            yang_file_pseudo_path=os.path.join(
                self.resource_path,
                'check_yangcatalog_data',
                'yang-catalog@2018-04-03.yang',
            ),
            new_module_data=new_module_data,
            compilation_results={},
            all_modules_data={},
        )
        redis_key = 'yang-catalog@2018-04-03/ietf'
        module_data = json.loads(self.incomplete_modules_redis_connection.get_module(redis_key))
        self.assertEqual(module_data.get('document-name'), new_module_data.get('document-name'))
        self.assertEqual(module_data.get('reference'), new_module_data.get('reference'))
        self.assertEqual(module_data.get('author-email'), new_module_data.get('author-email'))
        self.assertNotIn('compilation-result', module_data)
        self.assertEqual(self.modules_redis_connection.get_module(redis_key), '{}')
