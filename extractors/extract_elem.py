#!/usr/bin/env python

# Copyright The IETF Trust 2019, All Rights Reserved
# Copyright (c) 2015-2018 Cisco and/or its affiliates.

# This software is licensed to you under the terms of the Apache License, Version 2.0 (the "License").
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
# The code, technical concepts, and all information contained herein, are the property of Cisco Technology, Inc.
# and/or its affiliated entities, under various laws including copyright, international treaties, patent,
# and/or contract. Any use of the material herein must be in accordance with the terms of the License.
# All rights not expressly granted by the License are reserved.
# Unless required by applicable law or agreed to separately in writing, software distributed under the
# License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied.

__author__ = 'Eric Vyncke'
__copyright__ = 'Copyright(c) 2019, Cisco Systems, Inc.,  Copyright The IETF Trust 2019, All Rights Reserved'
__email__ = 'evyncke@cisco.com'

import re


def extract_elem(module_fname: str, extract_dir: str, elem_type: str):
    # Let's parse the module, we will create files when seeing the keywords such as
    # 'identity-networking-instance-type.txt'
    open_bracket_count = 0
    in_comment = False
    found_keyword = False
    file_out = None
    with open(module_fname, 'r', encoding='utf-8', errors='ignore') as ym:
        for line in ym:
            if not found_keyword:  # Still looking for keyword
                comment_start = line.find('//')
                if comment_start >= 0:
                    line = line[:comment_start]  # Get rid of the one-line comment
                comment_start = line.find('/*')
                comment_end = line.find('*/')
                if comment_start >= 0 and comment_start < comment_end:  # Another one-line comment
                    #                    print("Before cut off line:", comment_start, comment_end, line)
                    line = line[:comment_start] + line[comment_end + 2 :]
                #                    print("After cut off line:", comment_start, comment_end, line)
                else:
                    if comment_start >= 0:
                        in_comment = True
                        #                        print("Before cut off line:", comment_start, comment_end, line)
                        line = line[:comment_start]
                    #                        print("After cut off line:", comment_start, comment_end, line)
                    else:
                        if comment_end >= 0:
                            in_comment = False
                            #                            print("Before cut off line:", comment_start, comment_end, line)
                            line = line[comment_end + 2 :]
                #                            print("After cut off line:", comment_start, comment_end, line)
                # If we are in a multiple-line comment, let's skip this line
                if in_comment:
                    continue
                # Search after the keyword which MUST be the first word in the line (no " for example before)
                # keyword_start = line.lstrip().find(elem_type)
                match = re.match(r'^\s*' + elem_type + r'\s+([-_\.\w]+)' + r'\s*{', line)
                if match:
                    found_keyword = True
                    identifier = match.group(1)
                    # Let's open the output file if not yet done
                    if file_out is None:
                        file_out = open(
                            extract_dir + '/' + elem_type + '-' + identifier + '.txt',
                            'w',
                            encoding='utf-8',
                        )
            # print("Creating file: " + extract_dir + '/' + elem_type + '-' + identifier + '.txt')
            if found_keyword and file_out:  # Processing the keyword
                file_out.write(line)
                if line.find('{') >= 0:
                    open_bracket_count = open_bracket_count + 1
                if line.find('}') >= 0:
                    open_bracket_count = open_bracket_count - 1
                # Are we out of the outermost brackets?
                if open_bracket_count == 0:
                    file_out.close()
                    in_comment = False
                    found_keyword = False
                    file_out = None


if __name__ == '__main__':
    file = '/var/www/html/YANG-modules/ietf-gen-rpc.yang'
    extract_elem(file, '/tmp/extract', 'grouping')
    extract_elem(file, '/tmp/extract', 'typedef')
    extract_elem(file, '/tmp/extract', 'identity')
    file = '/var/yang/all_modules/ietf-yang-types@2010-09-24.yang'
    extract_elem(file, '/tmp/extract', 'grouping')
    extract_elem(file, '/tmp/extract', 'typedef')
    extract_elem(file, '/tmp/extract', 'identity')
    file = '/var/yang/all_modules/ietf-netconf-notifications@2012-02-06.yang'
    extract_elem(file, '/tmp/extract', 'grouping')
    extract_elem(file, '/tmp/extract', 'typedef')
    extract_elem(file, '/tmp/extract', 'identity')
