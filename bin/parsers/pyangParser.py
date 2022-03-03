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


class PyangParser:
    def __init__(self, debug_level: int = 0):
        self._config = create_config()
        self._pyang_exec = self._config.get('Tool-Section', 'pyang-exec')
        self._modules_directory = self._config.get('Directory-Section', 'modules-directory')

        self._debug_level = debug_level
        self._modules_directories = [os.path.join(self._modules_directory, sym) for sym in os.listdir(self._modules_directory)]

    def run_pyang_ietf(self, yang_file_path: str, ietf: bool):
        """
        Run PYANG parser on the YANG model, with or without the --ietf flag.

        Arguments:
            :param yang_file_path   (str) Full path to the yang model to parse
            :param ietf             (bool) Whether to use --ietf PYANG flag or not
        :return: the outcome of the PYANG compilation
        """
        directory, filename = os.path.split(yang_file_path)
        os.chdir(directory)

        path_command = '--path="{}"'.format(self._modules_directory)
        bash_command = [self._pyang_exec, path_command, filename]
        if ietf:
            bash_command.append('--ietf')
        bash_command.append('2>&1')

        if self._debug_level > 0:
            print('DEBUG: running command {}'.format(' '.join(bash_command)))

        result_pyang = os.popen(' '.join(bash_command)).read()
        result_pyang = result_pyang.strip()
        result_pyang = result_pyang.replace('\n\n', '\n').replace('\n', '\n\n')

        return result_pyang

    def run_pyang_lint(self, rootdir: str, yang_file_path: str, lint: bool, allinclusive: bool, use_pyang_params: bool = True):
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
        if filename.startswith('example'):
            use_pyang_params = False

        if allinclusive:
            path_command = '--path="{}"'.format(rootdir)
        else:
            path_command = '--path="{}"'.format(self._modules_directory)

        bash_command = [self._pyang_exec, path_command, filename]

        if use_pyang_params:
            pyang_param = '--lint' if lint else '--ietf'
            bash_command.append(pyang_param)

        bash_command.append('2>&1')

        if self._debug_level > 0:
            print('DEBUG: running command {}'.format(' '.join(bash_command)))

        result_pyang = os.popen(' '.join(bash_command)).read()
        result_pyang = result_pyang.strip()
        result_pyang = result_pyang.replace('\n\n', '\n').replace('\n', '\n\n')
        # Remove absolute path from output
        result_pyang = result_pyang.replace('{}/'.format(directory), '')
        for mod_dir in self._modules_directories:
            result_pyang = result_pyang.replace('{}/'.format(mod_dir), '')

        return result_pyang
