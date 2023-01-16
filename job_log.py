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
import time
import typing as t
from enum import Enum

from create_config import create_config


class JobLogStatuses(str, Enum):
    SUCCESS = 'Success'
    IN_PROGRESS = 'In Progress'
    FAIL = 'Fail'


def job_log(file_basename: str):
    def _job_log_decorator(func):
        config = create_config()
        temp_dir = config.get('Directory-Section', 'temp')

        def _job_log(*args, **kwargs):
            nonlocal temp_dir, file_basename
            start_time = int(time.time())
            write_job_log(start_time, '', temp_dir, file_basename, status=JobLogStatuses.IN_PROGRESS)
            try:
                success_messages: list[dict[str, str], ...] = func(*args, **kwargs)
            except Exception as e:
                write_job_log(
                    start_time,
                    int(time.time()),
                    temp_dir,
                    file_basename,
                    error=str(e),
                    status=JobLogStatuses.FAIL,
                )
                return
            write_job_log(
                start_time,
                int(time.time()),
                temp_dir,
                file_basename,
                messages=success_messages,
                status=JobLogStatuses.SUCCESS,
            )

        return _job_log

    return _job_log_decorator


def write_job_log(
    start_time: int,
    end_time: t.Union[str, int],
    temp_dir: str,
    filename: str,
    messages: t.Optional[list[dict[str, str]]] = None,
    error: str = '',
    status: str = JobLogStatuses,
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
    last_successful = None
    if status == JobLogStatuses.SUCCESS:
        last_successful = end_time
    elif previous_state := file_content.get(filename):
        last_successful = previous_state.get('last_successfull')

    result['last_successfull'] = last_successful
    file_content[filename] = result

    with open(cronjob_results_path, 'w') as f:
        f.write(json.dumps(file_content, indent=4))


if __name__ == '__main__':
    config = create_config()
    temp_dir = config.get('Directory-Section', 'temp')
    parser = argparse.ArgumentParser()
    parser.add_argument('--start', help='Cronjob start time', type=int, default=0, required=True)
    parser.add_argument('--end', help='Cronjob end time', type=str, default='', required=True)
    parser.add_argument('--status', help='Result of cronjob run', type=str, default='Fail', required=True)
    parser.add_argument('--filename', help='Name of job', type=str, default='', required=True)
    parser.add_argument('--error', help='Error message in case of an exception', type=str, default='')
    parser.add_argument('--messages', help='Success messages, could be 0 or more', nargs='*')
    parser.add_argument(
        '--load-messages-json',
        help='True if messages should be json loaded',
        action='store_true',
        default=False,
    )
    parsed_args = parser.parse_args()

    if parsed_args.load_messages_json:
        parsed_args.messages = [json.loads(message) for message in parsed_args.messages]

    write_job_log(
        int(parsed_args.start),
        int(parsed_args.end) if parsed_args.end.isnumeric() else '',
        temp_dir,
        parsed_args.filename,
        status=parsed_args.status,
        error=parsed_args.error,
        messages=parsed_args.messages,
    )
