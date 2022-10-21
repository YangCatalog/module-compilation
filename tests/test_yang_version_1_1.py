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

import os
import shutil
import subprocess
import unittest

import yang_version_1_1 as yv11


class TestYangVersion11(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.resource_path = os.path.join(os.environ['VIRTUAL_ENV'], 'tests/resources/yang_version_1_1')
        self.script_path = os.path.join(os.environ['VIRTUAL_ENV'], 'bin/yang_version_1_1.py')
        self.src = os.path.join(self.resource_path, 'YANG')
        self.dst = os.path.join(self.resource_path, 'YANG-v11')

    def setUp(self) -> None:
        shutil.rmtree(self.dst, ignore_errors=True)

    def test_yang_version_1_1(self):
        """Find and copy the yang files that contain 'yang-version 1.1' string."""
        result = yv11.find_v11_models(self.src, self.dst, 1)
        self.assertNotEqual(result, [])
        self.assertIn('test.yang', result)
        self.assertNotIn('test2.yang', result)

        v1_files = os.listdir(self.dst)
        self.assertNotEqual(v1_files, [])
        self.assertIn('test.yang', v1_files)

    def test_yang_version_1_1_src_not_exists(self):
        """Test the case when the src directory does not exist."""
        result = yv11.find_v11_models('', self.dst)
        self.assertEqual(result, [])

    def test_yang_version_1_1_from_console(self):
        """Run the script from the console by passing the arguments."""
        bash_command = 'python {} --srcpath {} --dstpath {} --debug 1'.format(self.script_path, self.src, self.dst)
        subprocess.run(bash_command, shell=True, capture_output=True, check=False).stdout.decode()

        v1_files = os.listdir(self.dst)
        self.assertNotEqual(v1_files, [])
        self.assertIn('test.yang', v1_files)


if __name__ == '__main__':
    unittest.main()
