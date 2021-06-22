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

__author__ = "Slavomir Mazur"
__copyright__ = "Copyright The IETF Trust 2021, All Rights Reserved"
__license__ = "Apache License, Version 2.0"
__email__ = "slavomir.mazur@pantheon.tech"

import os


class PyangParser:
    def __init__(self, pyang_exec: str, modules_directory: str, debug_level: int = 0):
        self.__pyang_exec = pyang_exec
        self.__modules_directory = modules_directory
        self.__debug_level = debug_level

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

        path_command = '--path="{}"'.format(self.__modules_directory)
        bash_command = [self.__pyang_exec, path_command, filename]
        if ietf:
            bash_command.append('--ietf')
        bash_command.append('2>&1')

        if self.__debug_level > 0:
            print('DEBUG: running command {}'.format(' '.join(bash_command)))

        result_pyang = os.popen(' '.join(bash_command)).read()

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
            path_command = '--path="{}"'.format(self.__modules_directory)

        bash_command = [self.__pyang_exec, path_command, filename]

        if use_pyang_params:
            pyang_param = '--lint' if lint else '--ietf'
            bash_command.append(pyang_param)

        bash_command.append('2>&1')

        if self.__debug_level > 0:
            print('DEBUG: running command {}'.format(' '.join(bash_command)))

        result_pyang = os.popen(' '.join(bash_command)).read()

        return result_pyang
