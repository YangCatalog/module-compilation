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
__license__ = 'Apache License, Version 2.0'
__email__ = 'bclaise@cisco.com'


import argparse
import os
import shutil


def remove_directory_content(directory: str, debug_level: int = 0) -> None:
    """
    Empty the content of the directory passed as an argument.

    Arguments:
        :param directory    (str) Path to the directory from which the content should be removed
        :param debug_level  (int) debug level; If > 0 print some debug statements to the console
    """
    if not directory:
        return
    if not os.path.isdir(directory):
        os.makedirs(directory)
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            os.unlink(file_path)
            if debug_level > 0:
                print('DEBUG: removing the file {}'.format(file_path))
        except IsADirectoryError:
            shutil.rmtree(file_path)
            if debug_level > 0:
                print('DEBUG: removing the subdirectory {}'.format(file_path))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Remove directory content')
    parser.add_argument('--dir',
                        help='Directory the content of which to remove',
                        type=str,
                        default='')
    parser.add_argument('--debug',
                        help='Debug level - default is 0',
                        type=int,
                        default=0)
    args = parser.parse_args()

    if args.debug > 0:
        print('DEBUG: attempting to remove the {} directory content'.format(args.dir))
    remove_directory_content(args.dir, args.debug)
