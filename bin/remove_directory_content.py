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


import argparse
import os
import shutil

__author__ = 'bclaise@cisco.com'

def remove_directory_content(directory: str, debug_level: int = 0):
    """
    Empty content of the directory passed as an argument.

    Arguments:
        :param directory    (str) Path to the directory from which the content should be removed
        :param debug_level  (int) debug level; If > 0 print some debug statements to the console
    """
    if not os.path.isdir(directory):
        return
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
                if debug_level > 0:
                    print('DEBUG: removing the file {}'.format(file_path))
            elif os.path.isdir(file_path) and not os.path.islink(file_path):
                shutil.rmtree(file_path)
                if debug_level > 0:
                    print('DEBUG: removing the subdirectory {}'.format(file_path))
        except Exception as e:
            print('Exception: %s' % e)


if __name__ == "__main__":
    """
    Testing functions
    """
    parser = argparse.ArgumentParser(description='Remove Directory Content')
    parser.add_argument("dir", help="The directory content to remove")
    parser.add_argument("--debug", type=int, default=0, help="Debug level; default is 0")
    args = parser.parse_args()

    if args.debug > 0:
        print('DEBUG: attempting to remove the {} directory content'.format(args.dir))
    remove_directory_content(args.dir, args.debug)
