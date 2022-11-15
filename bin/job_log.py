#!/usr/bin/env python

# Copyright The IETF Trust 2020, All Rights Reserved
# This software is licensed to you under the terms of the Apache License, Version 2.0 (the 'License").
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
# The code, technical concepts, and all information contained herein, are the property of Cisco Technology, Inc.
# and/or its affiliated entities, under various laws including copyright, international treaties, patent,
# and/or contract. Any use of the material herein must be in accordance with the terms of the License.
# All rights not expressly granted by the License are reserved.
# Unless required by applicable law or agreed to separately in writing, software distributed under the
# License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied.

__author__ = 'Slavomir Mazur'
__copyright__ = 'Copyright The IETF Trust 2020, All Rights Reserved'
__license__ = 'Apache License, Version 2.0'
__email__ = 'slavomir.mazur@pantheon.tech'

import argparse
import json
import os.path
import typing as t

from create_config import create_config


def job_log(
    start_time: int,
    end_time: int,
    temp_dir: str,
    filename: str,
    messages: t.Optional[list] = None,
    error: str = '',
    status: str = '',
):
    cronjob_results_path = os.path.join(temp_dir, 'cronjob.json')
    result = {'start': start_time, 'end': end_time, 'status': status, 'error': error, 'messages': messages or []}

    try:
        with open(cronjob_results_path, 'r') as f:
            file_content = json.load(f)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        file_content = {}

    filename = filename.split('.py')[0]
    # If successful rewrite, otherwise use last_successful value from JSON
    if status == 'Success':
        last_successful = end_time
    else:
        try:
            previous_state = file_content[filename]
            last_successful = previous_state.get('last_successfull')
        except KeyError:
            last_successful = None

    result['last_successfull'] = last_successful
    file_content[filename] = result

    with open(cronjob_results_path, 'w') as f:
        f.write(json.dumps(file_content, indent=4))


if __name__ == '__main__':
    config = create_config()
    temp_dir = config.get('Directory-Section', 'temp')
    parser = argparse.ArgumentParser()
    parser.add_argument('--start', help='Cronjob start time', type=int, default=0, required=True)
    parser.add_argument('--end', help='Cronjob end time', type=int, default=0, required=True)
    parser.add_argument('--status', help='Result of cronjob run', type=str, default='Fail', required=True)
    parser.add_argument('--filename', help='Name of job', type=str, default='', required=True)
    args = parser.parse_args()

    job_log(int(args.start), int(args.end), temp_dir, args.filename, status=args.status)
