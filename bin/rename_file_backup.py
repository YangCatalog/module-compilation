#!/usr/bin/env python

# Copyright The IETF Trust 2019, All Rights Reserved
# Copyright (c) 2018 Cisco and/or its affiliates.
# This software is licensed to you under the terms of the Apache License, Version 2.0 (the "License").
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
# The code, technical concepts, and all information contained herein, are the property of Cisco Technology, Inc.
# and/or its affiliated entities, under various laws including copyright, international treaties, patent,
# and/or contract. Any use of the material herein must be in accordance with the terms of the License.
# All rights not expressly granted by the License are reserved.
# Unless required by applicable law or agreed to separately in writing, software distributed under the
# License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied.

__author__ = 'Benoit Claise'
__copyright__ = 'Copyright(c) 2015-2018, Cisco Systems, Inc., Copyright The IETF Trust 2019, All Rights Reserved'
__license__ = 'Apache V2.0'
__email__ = 'bclaise@cisco.com'

import argparse
import os
import shutil
import time
from datetime import datetime

from create_config import create_config


def rename_file_backup(src_dir: str, backup_dir: str, debug_level: int = 0) -> None:
    """Backup each of the files by renaming them with the current timestamp appended to the file name.

    Arguments:
        :param src_dir      (str) Directory where the files to back up are stored
        :param backup_dir   (str) Directory where to save backup files
        :param debug_level  (int) debug level; If > 0 print some debug statements to the console
    """
    if not os.path.exists(src_dir):
        return

    if not os.path.exists(backup_dir):
        try:
            os.makedirs(backup_dir)
        except OSError:
            print(f'Unable to create directory: {backup_dir}')
            return

    files_to_backup = (
        'IETFYANGPageMain.html',
        'IETFCiscoAuthorsYANGPageCompilation.html',
        'IETFYANGOutOfRFC.html',
        'IETFDraftYANGPageCompilation.html',
        'IEEEStandardYANGPageCompilation.html',
        'IEEEStandardDraftYANGPageCompilation.html',
        'IANAStandardYANGPageCompilation.html',
        'IEEEExperimentalYANGPageCompilation.html',
        'YANGPageMain.html',
        'IETFYANGRFC.html',
    )
    for filename in files_to_backup:
        name, extension = filename.split('.')
        full_path_file = os.path.join(src_dir, filename)
        if not os.path.isfile(full_path_file):
            print(f'*** file {full_path_file} not present!')
            continue
        modified_time = os.path.getmtime(full_path_file)
        timestamp = datetime.fromtimestamp(modified_time).strftime('%Y_%m_%d')
        if name == 'IETFYANGRFC':
            name = 'IETFYANGOutOfRFC'
        new_filename = f'{name}_{timestamp}.{extension}'
        new_full_path_file = os.path.join(backup_dir, new_filename)
        if debug_level > 0:
            print(f'DEBUG: file full path: {full_path_file}')
            print('DEBUG: last modified: %s' % time.ctime(os.path.getmtime(full_path_file)))
            print(f'DEBUG: new file name: {new_full_path_file}')
        shutil.copy2(full_path_file, new_full_path_file)


if __name__ == '__main__':
    config = create_config()
    web_private = config.get('Web-Section', 'private-directory')
    backup_directory = config.get('Directory-Section', 'backup')
    parser = argparse.ArgumentParser(description='Append creation timestamps to filenames')
    parser.add_argument('--srcdir', help='Directory the content of which to remove', type=str, default=web_private)
    parser.add_argument(
        '--backupdir',
        help='Directory the content of which to remove',
        type=str,
        default=backup_directory,
    )
    parser.add_argument('--debug', help='Debug level - default is 0', type=int, default=0)
    args = parser.parse_args()

    rename_file_backup(args.srcdir, args.backupdir, args.debug)
