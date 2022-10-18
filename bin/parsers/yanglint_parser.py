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
from configparser import ConfigParser

from create_config import create_config


def _remove_duplicate_messages(result: str) -> str:
    """ Same result messages are often found in the compilation result multiple times.
    This method filter out duplicate messages.
    """
    splitted_result = result.split('\n\n')
    unique_results_list = sorted(set(splitted_result), key=splitted_result.index)
    final_result = '\n\n'.join(unique_results_list)

    return final_result


class YanglintParser:
    def __init__(self, debug_level: int = 0, config: ConfigParser = create_config()):
        self._modules_directory = config.get('Directory-Section', 'modules-directory')

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
            result_yanglint = result_yanglint.replace(yang_file_path, os.path.basename(yang_file_path))

            final_result = _remove_duplicate_messages(result_yanglint)
        except Exception:
            final_result = 'libyang err : Problem occured while running command: {}'.format(' '.join(bash_command))

        return final_result
