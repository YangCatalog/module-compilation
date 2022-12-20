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

import glob
import os
from configparser import ConfigParser

from create_config import create_config


class ConfdcParser:
    def __init__(self, debug_level: int = 0, config: ConfigParser = create_config()):
        self._confdc_exec = config.get('Tool-Section', 'confdc-exec')
        self._modules_directory = config.get('Directory-Section', 'modules-directory')

        self._debug_level = debug_level
        self._symlink_paths = self.get_symlink_paths()
        self._tail_warning = (
            '-w TAILF_MUST_NEED_DEPENDENCY'  # Treat ErrorCode as a warning, even if --fail-onwarnings is given
        )

    def run_confdc(self, yang_file_path: str, rootdir: str, allinclusive: bool = False):
        """
        Run Confd compilator on the YANG model.

        Arguments:
            :param yang_file_path   (str) Full path to the yang model to parse
            :param rootdir          (str) Root directory where to find the source YANG models
            :param allinclusive     (bool) Whether the 'rootdir' directory contains all imported YANG modules or not
        :return: the outcome of the confdc compilation

        NOTE:
        confdc doesn't include YANG modules recursively and doesn't follow symbolic links.
        All the paths need to be set as an input parameter of confdc command.
        """
        workdir = os.path.dirname(yang_file_path)
        os.chdir(workdir)

        file_command = '-c {}'.format(yang_file_path)

        if allinclusive:
            path_command = '--yangpath {}'.format(rootdir)
        else:
            subdir_paths = self.list_all_subdirs(rootdir)
            paths_list = self._symlink_paths + subdir_paths

            path_command = '--yangpath {}'.format(':'.join(paths_list))

        bash_command = [self._confdc_exec, path_command, self._tail_warning, file_command, '2>&1']
        if self._debug_level > 0:
            print('DEBUG: running command {}'.format(' '.join(bash_command)))

        try:
            result_confdc = os.popen(' '.join(bash_command)).read()
            result_confdc = result_confdc.strip()
            result_confdc = result_confdc.replace('\n\n', '\n').replace('\n', '\n\n')
            # Remove absolute path from output
            result_confdc = result_confdc.replace(yang_file_path, os.path.basename(yang_file_path))
            for sym_link in self._symlink_paths:
                result_confdc = result_confdc.replace('{}/'.format(sym_link), '')
        except Exception:
            result_confdc = 'Problem occured while running command: {}'.format(' '.join(bash_command))

        return result_confdc

    def get_symlink_paths(self):
        """
        List all the symbolic links which are stored on modules_directory.
        :return: list of symbolic links of the modules_directory
        """
        symlink_paths = []
        for _, dirs, _ in os.walk(self._modules_directory, followlinks=True):
            for direc in dirs:
                path = '{}/{}'.format(self._modules_directory, direc)
                if os.path.islink(path) and path != '{}/YANG'.format(self._modules_directory):
                    symlink_paths.append(path)

        return symlink_paths

    def list_all_subdirs(self, directory: str):
        """
        List all the sub-directories of the given directory.

        Argument:
            :param directory    (str) Path to the directory
        :return: list of subdirectories of the given directory
        """
        subdirs = []
        for direc in glob.glob('{}/*/'.format(directory)):
            subdirs.append(direc)
            subdirs.extend(self.list_all_subdirs(direc))

        return subdirs
