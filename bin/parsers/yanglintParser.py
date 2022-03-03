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

import os

from create_config import create_config


class YanglintParser:
    def __init__(self, debug_level: int = 0):
        self._config = create_config()
        self._modules_directory = self._config.get('Directory-Section', 'modules-directory')

        self._debug_level = debug_level
        self._yanglint_exec = 'yanglint'

    def run_yanglint(self, yang_file_path: str, workdir: str, allinclusive: bool = False):
        """
        Run yanglint on the YANG model.

        Arguments:
            :param yang_file_path   (str) Full path to the yang model to parse
            :param workdir          (str) Root directory where to find the source YANG models
            :param allinclusive     (bool) Whether the 'workdir' directory contains all imported YANG modules or not
        :return: the outcome of the yanglint compilation.
        """
        os.chdir(workdir)

        if allinclusive:
            path_command = '-p {}'.format(workdir)
        else:
            path_command = '-p {}/'.format(self._modules_directory)

        bash_command = [self._yanglint_exec, '-i', path_command, yang_file_path, '2>&1']

        if self._debug_level > 0:
            print('DEBUG: running command {}'.format(' '.join(bash_command)))

        try:
            result_yanglint = os.popen(' '.join(bash_command)).read()
            result_yanglint = result_yanglint.strip()
            result_yanglint = result_yanglint.replace('\n\n', '\n').replace('\n', '\n\n')
            result_yanglint = result_yanglint.replace(workdir, '')
            # Same result messages are often found in the result_yanglint multiple times
            # splitted_result_yanglint = result_yanglint.split('\n')
            # unique_results_list = sorted(set(splitted_result_yanglint), key=splitted_result_yanglint.index)
            # result_yanglint = '\n'.join(unique_results_list)
        except Exception:
            result_yanglint = 'libyang err : Problem occured while running command: {}'.format(' '.join(bash_command))

        return result_yanglint
