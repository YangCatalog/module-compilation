#!/usr/bin/env python

# Copyright The IETF Trust 2020, All Rights Reserved
# This software is licensed to you under the terms of the Apache License, Version 2.0 (the "License").
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
# The code, technical concepts, and all information contained herein, are the property of Cisco Technology, Inc.
# and/or its affiliated entities, under various laws including copyright, international treaties, patent,
# and/or contract. Any use of the material herein must be in accordance with the terms of the License.
# All rights not expressly granted by the License are reserved.
# Unless required by applicable law or agreed to separately in writing, software distributed under the
# License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied.

__author__ = 'Miroslav Kovac'
__copyright__ = 'Copyright The IETF Trust 2020, All Rights Reserved'
__license__ = 'Apache License, Version 2.0'
__email__ = 'miroslav.kovac@pantheon.tech'


import os
import shutil
from typing import Set

import requests
from create_config import create_config

ORGANIZATIONS = ['ieee', 'ietf']


def copy_modules(api_prefix: str, src_dir: str, dst_dir: str) -> Set[str]:
    """Get the list of ietf modules from API
    and copy them from 'src_dir' to 'dst_dir' directory.

    Arguments:
        :param api_prefix   (str) YANG Catalog API prefix
        :param src_dir      (str) Source path from where we move the YANG modules
        :param dst_dir      (str) Destination path to where we move the YANG modules
    """
    os.makedirs(dst_dir, exist_ok=True)
    copied_files = set()
    for organization in ORGANIZATIONS:
        url = '{}/search-filter'.format(api_prefix)
        body = {'input': {'organization': organization}}

        response = requests.post(url, json=body)
        resp_body = response.json()
        modules = resp_body.get('yang-catalog:modules', {}).get('module', [])

        for module in modules:
            name = module['name']
            revision = module['revision']
            yang_file = '{}@{}.yang'.format(name, revision)
            yang_file_path = os.path.join(src_dir, yang_file)
            if not os.path.exists(yang_file_path):
                continue
            dst = os.path.join(dst_dir, yang_file)
            shutil.copy2(yang_file_path, dst)
            copied_files.add(yang_file)
    return copied_files


if __name__ == '__main__':
    config = create_config()
    yangcatalog_api_prefix = config.get('Web-Section', 'yangcatalog-api-prefix')
    all_modules_dir = config.get('Directory-Section', 'save-file-dir')
    ietf_dir = config.get('Directory-Section', 'ietf-directory')
    ietf_dependencies_dir = os.path.join(ietf_dir, 'dependencies')

    copy_modules(yangcatalog_api_prefix, all_modules_dir, ietf_dependencies_dir)
