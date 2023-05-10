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
import subprocess
from configparser import ConfigParser

from create_config import create_config


def _remove_duplicate_messages(result: str) -> str:
    """Same result messages are often found in the compilation result multiple times.
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
            path_command = f'-p {workdir}'
        else:
            path_command = f'-p {self._modules_directory}/'

        bash_command = f'{self._yanglint_exec} -i {path_command} {yang_file_path} 2>&1'

        if self._debug_level > 0:
            print(f'DEBUG: running command {bash_command}')

        try:
            result_yanglint = subprocess.run(
                bash_command,
                capture_output=True,
                text=True,
                shell=True,
                check=True,
                timeout=60,
            )
            final_result = self._clean_yanglint_result(result_yanglint.stdout, yang_file_path)
        except subprocess.TimeoutExpired:
            if self._debug_level > 0:
                print(f'yanglint timed out for: {yang_file_path}')
            final_result = f'Timeout exception occurred while running command: {bash_command}'
        except subprocess.CalledProcessError as e:
            # This error is raised if the bash command's return code isn't equal to 0 and a non-zero status can be
            # returned by yangdump-pro itself if there are any Errors in the file, so we should still check the output
            final_result = self._clean_yanglint_result(e.stdout, yang_file_path)
            final_result = f'libyang err : Problem occurred while running command "{bash_command}":\n{final_result}'

        return final_result

    def _clean_yanglint_result(self, result: str, yang_file_path: str) -> str:
        result = result.strip().replace('\n\n', '\n').replace('\n', '\n\n')
        result = result.replace(yang_file_path, os.path.basename(yang_file_path))
        return _remove_duplicate_messages(result)
