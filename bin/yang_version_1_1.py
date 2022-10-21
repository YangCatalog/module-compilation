#!/usr/bin/env python

# Copyright The IETF Trust 2019, All Rights Reserved
# Copyright 2015-2018, Cisco Systems
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


__author__ = 'Benoit Claise'
__copyright__ = 'Copyright(c) 2015-2018, Cisco Systems, Inc., Copyright The IETF Trust 2019, All Rights Reserved'
__license__ = 'Apache License, Version 2.0'
__email__ = 'bclaise@cisco.com'

import argparse
import os
import shutil
import subprocess

from create_config import create_config
from remove_directory_content import remove_directory_content


def find_v11_models(src_dir: str, dst_dir: str, debug: int = 0) -> list:
    """
    This method will copy all yang models of version 1.1
    from directory 'src_dir' to directory 'dst_dir'.

    Arguments:
        :param src_dir      (str) directory where to find the source YANG models files
        :param dst_dir      (str) directory where to store version 1.1 YANG models
        :param debug_level  (int) debug level; If > 0 print some debug statements to the console
    """
    if not os.path.isdir(src_dir):
        return []
    remove_directory_content(dst_dir, debug)
    yang_model_list = [f for f in os.listdir(src_dir) if os.path.isfile(os.path.join(src_dir, f))]
    yang_model_list_v11 = []

    for yang_model in yang_model_list:
        src_file_path = os.path.join(src_dir, yang_model)
        bash_command = 'grep yang-version {} | grep 1.1'.format(src_file_path)
        if debug > 0:
            print('DEBUG: grep command: {}'.format(bash_command))
        grep_result = subprocess.run(bash_command, shell=True, capture_output=True, check=False).stdout.decode()
        if '1.1' not in grep_result:
            continue
        if debug > 0:
            print('DEBUG: {} is version 1.1 '.format(yang_model))
        yang_model_list_v11.append(yang_model)
        dst_file_path = os.path.join(dst_dir, yang_model)
        shutil.copy2(src_file_path, dst_file_path)
    if debug > 0:
        print('DEBUG: list of YANG models with version 1.1:\n{}'.format(yang_model_list_v11))
    return yang_model_list_v11


if __name__ == '__main__':
    config = create_config()
    ietf_directory = config.get('Directory-Section', 'ietf-directory')

    src = os.path.join(ietf_directory, 'YANG')
    dst = os.path.join(ietf_directory, 'YANG-v11')

    parser = argparse.ArgumentParser(description='YANG 1.1 Processing Tool. Copy all YANG 1.1 modules to destpath')
    parser.add_argument(
        '--srcpath',
        help='Directory where find YANG models. ' 'Default is "{}"'.format(src),
        type=str,
        default=src,
    )
    parser.add_argument(
        '--dstpath',
        help='Directory where to store version 1.1 YANG models. ' 'Default is "{}"'.format(dst),
        type=str,
        default=dst,
    )
    parser.add_argument('--debug', help='Debug level - default is 0', type=int, default=0)

    args = parser.parse_args()

    find_v11_models(args.srcpath, args.dstpath, args.debug)
