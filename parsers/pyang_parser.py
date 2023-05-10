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


class PyangParser:
    def __init__(self, debug_level: int = 0, config: ConfigParser = create_config()):
        self._pyang_exec = config.get('Tool-Section', 'pyang-exec')
        self._modules_directory = config.get('Directory-Section', 'modules-directory')

        self._debug_level = debug_level
        self._modules_directories = [
            os.path.join(self._modules_directory, sym) for sym in os.listdir(self._modules_directory)
        ]

    def run_pyang(
        self,
        rootdir: str,
        yang_file_path: str,
        lint: bool,
        allinclusive: bool,
        use_pyang_params: bool = True,
    ) -> str:
        """
        Run PYANG parser on the YANG model, with or without the --lint flag.

        Arguments:
            :param yang_file_path   (str) Full path to the yang model to parse
            :param lint             (bool) Whether to use --lint PYANG flag or not
            :param allinclusive     (bool) Whether the 'yangpath' directory contains all imported YANG modules or not
            :param use_pyang_params (bool) Whether to take pyang params (--lint or --ietf) into account or not
        :return: the outcome of the PYANG compilation

        NOTE:
        PYANG search path is indicated by the --path parameter which can occur multiple times.
        The following directories are always added to the search path:
            1. current directory
            2. $YANG_MODPATH
            3. $HOME/yang/modules
            4. $YANG_INSTALL/yang/modules OR if $YANG_INSTALL is unset
                <the default installation directory>/yang/modules (on Unix systems: /usr/share/yang/modules)
        """
        directory, filename = os.path.split(yang_file_path)
        os.chdir(directory)

        path = rootdir if allinclusive else self._modules_directory
        path_command = f'--path="{path}"'

        bash_command = ['python3', self._pyang_exec, path_command, filename]
        if use_pyang_params:
            pyang_param = '--lint' if lint else '--ietf'
            bash_command.append(pyang_param)
        bash_command.append('2>&1')
        bash_command = ' '.join(bash_command)

        if self._debug_level > 0:
            print(f'DEBUG: running command {bash_command}')

        try:
            result_pyang = subprocess.run(
                bash_command,
                capture_output=True,
                text=True,
                shell=True,
                check=True,
                timeout=60,
            )
            result_pyang = self._clean_pyang_result(result_pyang.stdout, directory)
        except subprocess.TimeoutExpired:
            if self._debug_level > 0:
                print(f'pyang timed out for: {yang_file_path}')
            result_pyang = f'Timeout exception occurred while running command: {bash_command}'
        except subprocess.CalledProcessError as e:
            # This error is raised if the bash command's return code isn't equal to 0 and a non-zero status can be
            # returned by pyang itself if there are any Errors in the file, so we should still check the output
            result_pyang = self._clean_pyang_result(e.stdout, directory)
            result_pyang = f'Problem occurred while running command "{bash_command}":\n{result_pyang}'

        return result_pyang

    def _clean_pyang_result(self, result: str, directory: str) -> str:
        result = result.strip().replace('\n\n', '\n').replace('\n', '\n\n')
        # Remove absolute path from output
        result = result.replace(f'{directory}/', '')
        for mod_dir in self._modules_directories:
            result = result.replace(f'{mod_dir}/', '')
        return result
