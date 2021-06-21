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


class YangdumpProParser:
    def __init__(self, debug_level: int = 0):
        self.__debug_level = debug_level
        self.__yangdump_exec = 'yangdump-pro'

    def run_yumadumppro(self, yang_file_path: str, workdir: str, allinclusive: bool = False):
        """
        Run yumadump-pro on the YANG model.

        Arguments:
            :param yang_file_path   (str) Full path to the yang model to parse
            :param workdir          (str) Root directory where to find the source YANG models
            :param allinclusive     (bool) Whether the 'yangpath' directory contains all imported YANG modules or not
        :return: the outcome of the yangdump-pro compilation.
        """
        workdir = os.path.dirname(yang_file_path)
        os.chdir(workdir)

        if allinclusive:
            config_command = '--config=/etc/yumapro/yangdump-pro-allinclusive.conf'
        else:
            config_command = '--config=/etc/yumapro/yangdump-pro.conf'

        bash_command = [self.__yangdump_exec, '--quiet-mode', config_command, yang_file_path, '2>&1']
        if self.__debug_level > 0:
            print('DEBUG: running command {}'.format(' '.join(bash_command)))

        # Modify command output
        try:
            result_yumadump = os.popen(' '.join(bash_command)).read()
            final_result = result_yumadump.strip()
            final_result = final_result.replace('\n*** {}'.format(yang_file_path), '')

            if '*** 0 Errors, 0 Warnings' in final_result:
                final_result = ''
        except:
            final_result = 'Problem occured while running command: {}'.format(' '.join(bash_command))

        return final_result
