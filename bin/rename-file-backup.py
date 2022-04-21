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
__copyright__ = "Copyright(c) 2015-2018, Cisco Systems, Inc.,  Copyright The IETF Trust 2019, All Rights Reserved"
__license__ = "Apache V2.0"
__email__ = "bclaise@cisco.com"

import argparse
import os
import shutil
import time
from datetime import datetime

from create_config import create_config

if __name__ == "__main__":
    config = create_config()
    web_private = config.get('Web-Section', 'private-directory')
    backup_directory = config.get('Directory-Section', 'backup')
    parser = argparse.ArgumentParser(description='Move file to the their creation time')
    parser.add_argument("--documentpath", default=web_private + '/',
                        help="The optional directory where to find the file to backup. "
                             "Default is '" + web_private + "'")
    parser.add_argument("--backuppath", default=backup_directory + '/',
                        help="The optional directory where to backup the file. "
                             "Default is '" + backup_directory + "'")
    parser.add_argument("--debug", type=int, default=0, help="Debug level; the default is 0")

    args = parser.parse_args()
    debug_level = args.debug

    name_to_backup = ['IETFYANGPageMain.html', 'HydrogenODLPageCompilation.html', 'HeliumODLPageCompilation.html', 'LithiumODLPageCompilation.html',
                    'IETFCiscoAuthorsYANGPageCompilation.html', 'IETFYANGOutOfRFC.html', 'IETFDraftYANGPageCompilation.html',
                    'IEEEStandardYANGPageCompilation.html', 'IEEEStandardDraftYANGPageCompilation.html', 'IANAStandardYANGPageCompilation.html',
                    'IEEEExperimentalYANGPageCompilation.html', 'YANGPageMain.html', 'IETFYANGRFC.html']
    # name_to_backup = ['temp.html']
    for file in name_to_backup:
        file_no_extension = file.split(".")[0]
        file_extension = file.split(".")[-1]
        full_path_file = args.documentpath + file
        if os.path.isfile(full_path_file):
            modifiedTime = os.path.getmtime(full_path_file)
            timestamp = (datetime.fromtimestamp(modifiedTime).strftime("%Y_%m_%d"))
            if file_no_extension == 'IETFYANGRFC':
                file_no_extension = 'IETFYANGOutOfRFC'
            new_full_path_file = args.backuppath + file_no_extension + "_" + timestamp + "." + file_extension
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
