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
import subprocess
from typing import List

from create_config import create_config

__author__ = 'Benoit Claise'
__copyright__ = 'Copyright(c) 2015-2018, Cisco Systems, Inc., Copyright The IETF Trust 2019, All Rights Reserved'
__license__ = 'Apache V2.0'
__email__ = 'bclaise@cisco.com'


SOURCE = '/etc/yangcatalog/IETF-drafts-list-with-no-YANG-models.txt'
REMOVE_SEQUENCE = '-0123456789'


def list_lines_from_file(path: str, debug_level: int = 0) -> List[str]:
    """ Return individual lines of a file as a list.

    Arguments:
        :param path         (str) full path to the file to read
        :param debug_level  (int) debug level; If > 0 print some debug statements to the console
    """
    list_of_lines = []
    try:
        with open(path, 'r', encoding='utf-8') as reader:
            list_of_lines = reader.read().splitlines()
    except FileNotFoundError:
        print('{} file not exists.'.format(path))
    if debug_level > 0:
        print('DEBUG: List of lines from file {}:\n{}'.format(path, list_of_lines))
    return list_of_lines


def remove_drafts(list_of_lines: List[str], directory: str, debug_level: int = 0) -> None:
    """ Execute the 'rm -f <directory> <line>' command within the directory.

    Arguments:
        :param list_of_lines    (List[str]) list of draft names with asterisk
        :param directory        (str) Path to the directory where the drafts need to be removed
        :param debug_level      (int) debug level; If > 0 print some debug statements to the console
    """
    for line in list_of_lines:
        bash_command = 'rm -f {} {}'.format(directory, line)
        if debug_level > 0:
            print('DEBUG: bash_command {}'.format(bash_command))
        remove_result = subprocess.run(bash_command, shell=True, capture_output=True, check=False).stdout.decode()
        if debug_level > 0:
            print(remove_result)


def replace_draft_versions_by_asterisk(list_of_lines: List[str], debug_level: int = 0) -> List[str]:
    """ Replace the draft versions by an asterisk (*).

    Arguments:
        :param list_of_lines    (List[str]) list of draft names
        :param debug_level      (int) debug level; If > 0 print some debug statements to the console
    """
    new_list_of_lines = []
    for line in list_of_lines:
        head = line.split('.txt')[0]
        new_line = head.rstrip(REMOVE_SEQUENCE) + '*'
        if debug_level > 0:
            print('DEBUG: replaced_draft_version by_asterisk\nold file:{}\nnew file {}'.format(line, new_line))
        new_list_of_lines.append(new_line)
    return new_list_of_lines


if __name__ == '__main__':
    config = create_config()
    ietf_directory = config.get('Directory-Section', 'ietf-directory')
    dst_dir = os.path.join(ietf_directory, 'my-id-mirror')

    parser = argparse.ArgumentParser(description='Remove drafts well-known as having xym errors, '
                                                 'but that do not contain YANG models')
    parser.add_argument('--dstdir',
                        help='Directory from which to remove the drafts. '
                             'Default is "{}"'.format(dst_dir),
                        type=str,
                        default=dst_dir)
    parser.add_argument('--debug',
                        help='Debug level - default is 0',
                        type=int,
                        default=0)
    args = parser.parse_args()

    lines = list_lines_from_file(SOURCE, args.debug)
    list_of_lines_asterisk = replace_draft_versions_by_asterisk(lines, args.debug)
    remove_drafts(list_of_lines_asterisk, args.dstdir, args.debug)
