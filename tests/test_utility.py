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

import os
import unittest

import utility.utility as u
from create_config import create_config


class TestUtility(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.resource_path = os.path.join(os.environ['VIRTUAL_ENV'], 'tests/resources/utility')
        self.config = create_config(os.path.join(os.path.dirname(self.resource_path), 'test.conf'))

    def test_module_or_submodule(self):
        result = u.module_or_submodule(os.path.join(self.resource_path, 'module_or_submodule/module.yang'))
        self.assertEqual(result, 'module')

        result = u.module_or_submodule(os.path.join(self.resource_path, 'module_or_submodule/submodule.yang'))
        self.assertEqual(result, 'submodule')

        result = u.module_or_submodule(os.path.join(self.resource_path, 'module_or_submodule/neither.yang'))
        self.assertEqual(result, 'wrong file')

    def test_dict_to_list(self):
        result = u.dict_to_list({'foo': ['bar', 'foobar'], 'boo': ['far', 'boofar']}, is_rfc=False)
        self.assertEqual(result, [['foo', 'bar', 'foobar'], ['boo', 'far', 'boofar']])

        result = u.dict_to_list({'foo': ['bar', 'foobar'], 'boo': ['far', 'boofar']}, is_rfc=True)
        self.assertEqual(result, [['foo', ['bar', 'foobar']], ['boo', ['far', 'boofar']]])

    def test_list_br_html_addition(self):
        result = u.list_br_html_addition([['foo\n', 'bar\n'], [42, 'foo\nbar\n'], []])
        self.assertEqual(result, [['foo<br>', 'bar<br>'], ['foo<br>bar<br>'], []])

    def test_resolve_maturity_level(self):
        result = u._resolve_maturity_level(None, 'fake-ietf-document')
        self.assertEqual(result, 'not-applicable')

        result = u._resolve_maturity_level(u.IETF.RFC, 'foo-document-name')
        self.assertEqual(result, 'ratified')

        result = u._resolve_maturity_level(u.IETF.DRAFT, 'draft-ietf-new-thing')
        self.assertEqual(result, 'adopted')

        result = u._resolve_maturity_level(u.IETF.DRAFT, 'draft-new-thing')
        self.assertEqual(result, 'initial')

    def test_resolve_working_group(self):
        result = u._resolve_working_group('iana-crypt-hash@2014-08-06', u.IETF.RFC, 'iana-crypt-hash')
        self.assertEqual(result, 'NETMOD')

        result = u._resolve_working_group('ietf-restconf@2017-01-26', u.IETF.RFC, 'ietf-restconf')
        self.assertEqual(result, 'NETCONF')

        result = u._resolve_working_group('draft-foo-groupname-bar@2017-01-26', u.IETF.DRAFT, 'draft-foo-groupname-bar')
        self.assertEqual(result, 'groupname')

    def test_path_in_dir(self):
        result = u._path_in_dir(os.path.join(self.resource_path, 'path_in_dir/foo.yang'))
        self.assertEqual(result, os.path.join(self.resource_path, 'path_in_dir/foo.yang'))

        result = u._path_in_dir(os.path.join(self.resource_path, 'path_in_dir/bar.yang'))
        self.assertEqual(result, os.path.join(self.resource_path, 'path_in_dir/subdir/bar.yang'))

        result = u._path_in_dir(os.path.join(self.resource_path, 'path_in_dir/foobar.yang'))
        self.assertEqual(result, os.path.join(self.resource_path, 'path_in_dir/subdir/subsubdir/foobar.yang'))

        result = u._path_in_dir(os.path.join(self.resource_path, 'path_in_dir/boofar.yang'))
        self.assertEqual(result, os.path.join(self.resource_path, 'path_in_dir/boofar.yang'))

    def test_number_that_passed_compilation(self):
        result = u.number_that_passed_compilation(
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
