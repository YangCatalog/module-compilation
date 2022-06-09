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
__copyright__ = 'Copyright(c) 2015-2018, Cisco Systems, Inc.,  Copyright The IETF Trust 2019, All Rights Reserved'
__license__ = 'Apache V2.0'
__email__ = 'bclaise@cisco.com'

import argparse
import os
import shutil
import time
from datetime import datetime

from create_config import create_config

if __name__ == '__main__':
    config = create_config()
    web_private = config.get('Web-Section', 'private-directory')
    backup_directory = config.get('Directory-Section', 'backup')
    parser = argparse.ArgumentParser(description='Append creation timestamps to filenames')
    parser.add_argument('--documentpath',
                        help='Directory containing the file to backup. '
                             'Default is {}'.format(web_private),
                        type=str,
                        default=web_private)
    parser.add_argument('--backuppath',
                        help='Directory where to backup the file. '
                             'Default is {}'.format(backup_directory),
                        type=str,
                        default=backup_directory)
    parser.add_argument('--debug',
                        help='Debug level - default is 0',
                        type=int,
                        default=0)

    args = parser.parse_args()
    debug_level = args.debug

    name_to_backup = ['IETFYANGPageMain.html', 'HydrogenODLPageCompilation.html', 'HeliumODLPageCompilation.html',
                      'LithiumODLPageCompilation.html', 'IETFCiscoAuthorsYANGPageCompilation.html',
                      'IETFYANGOutOfRFC.html', 'IETFDraftYANGPageCompilation.html',
                      'IEEEStandardYANGPageCompilation.html', 'IEEEStandardDraftYANGPageCompilation.html',
                      'IANAStandardYANGPageCompilation.html', 'IEEEExperimentalYANGPageCompilation.html',
                      'YANGPageMain.html', 'IETFYANGRFC.html']
    # name_to_backup = ['temp.html']
    for file in name_to_backup:
        file_no_extension = file.split('.')[0]
        file_extension = file.split('.')[-1]
        full_path_file = os.path.join(args.documentpath, file)
        if os.path.isfile(full_path_file):
            modifiedTime = os.path.getmtime(full_path_file)
            timestamp = (datetime.fromtimestamp(modifiedTime).strftime("%Y_%m_%d"))
            if file_no_extension == 'IETFYANGRFC':
                file_no_extension = 'IETFYANGOutOfRFC'
            new_filename = '{}_{}.{}'.format(file_no_extension, timestamp, file_extension)
            new_full_path_file = os.path.join(args.backuppath, new_filename)
            if debug_level > 0:
                print("file full path: " + full_path_file)
                print("file without extension: " + file_no_extension)
                print("file extension: " + file_extension)
                print("full path: " + full_path_file)
                print("last modified: %s" % time.ctime(os.path.getmtime(full_path_file)))
                print("timestamp: " + str(timestamp))
                print("new file name: " + new_full_path_file)
            shutil.copy2(full_path_file, new_full_path_file)
        else:
            print('*** file {} not present!'.format(full_path_file))
