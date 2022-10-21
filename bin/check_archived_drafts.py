# Copyright The IETF Trust 2021, All Rights Reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

__author__ = 'Slavomir Mazur'
__copyright__ = 'Copyright The IETF Trust 2021, All Rights Reserved'
__license__ = 'Apache License, Version 2.0'
__email__ = 'slavomir.mazur@pantheon.tech'


import argparse
import datetime
import json
import os
import shutil
import time

import requests
from create_config import create_config
from extractors.draft_extractor import DraftExtractor
from job_log import job_log
from message_factory.message_factory import MessageFactory
from remove_directory_content import remove_directory_content


def custom_print(message: str):
    timestamp = '{} ({}):'.format(datetime.datetime.now().time(), os.getpid())
    print('{} {}'.format(timestamp, message), flush=True)


def main():
    start = int(time.time())
    config = create_config()
    ietf_directory = config.get('Directory-Section', 'ietf-directory')
    temp_dir = config.get('Directory-Section', 'temp')
    yangcatalog_api_prefix = config.get('Web-Section', 'yangcatalog-api-prefix')
    var_path = config.get('Directory-Section', 'var')

    archived_draft_path = os.path.join(ietf_directory, 'my-id-archive-mirror')
    yang_path = os.path.join(ietf_directory, 'archived-drafts-modules')

    parser = argparse.ArgumentParser(description='Check if modules from all the Drafts are populated in YANG Catalog')
    parser.add_argument('--debug', help='Debug level - default is 0', type=int, default=0)
    args = parser.parse_args()

    custom_print('Starting {} script'.format(os.path.basename(__file__)))

    all_yang_drafts_strict = os.path.join(temp_dir, 'draft-with-YANG-strict')
    missing_modules_directory = os.path.join(temp_dir, 'drafts-missing-modules')
    all_yang_path = os.path.join(temp_dir, 'YANG-ALL')
    draft_extractor_paths = {
        'draft_path': archived_draft_path,
        'yang_path': yang_path,
        'all_yang_draft_path_strict': all_yang_drafts_strict,
        'all_yang_path': all_yang_path,
    }

    try:
        remove_directory_content(yang_path, args.debug)
        remove_directory_content(missing_modules_directory, args.debug)
        remove_directory_content(all_yang_drafts_strict, args.debug)

        custom_print('Extracting modules from drafts stored in {}'.format(archived_draft_path))
        draft_extractor = DraftExtractor(
            draft_extractor_paths,
            args.debug,
            extract_elements=False,
            extract_examples=False,
            copy_drafts=False,
        )
        draft_extractor.extract()
    except Exception as err:
        custom_print('Error occured while extracting modules')
        end = int(time.time())
        job_log(start, end, temp_dir, os.path.basename(__file__), error=repr(err), status='Fail')
        return

    custom_print('Loading all modules data from API')
    all_modules = requests.get('{}/search/modules'.format(yangcatalog_api_prefix)).json()
    all_modules_keys = []
    if all_modules:
        all_modules = all_modules.get('module', [])
        all_modules_keys = ['{}@{}'.format(m.get('name'), m.get('revision')) for m in all_modules]

    try:
        resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')
        with open(os.path.join(resources_dir, 'old-rfcs.json'), 'r') as f:
            old_modules = json.load(f)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        old_modules = []
    try:
        with open(os.path.join(var_path, 'unparsable-modules.json'), 'r') as f:
            unparsable_modules = json.load(f)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        unparsable_modules = []

    # Prepare a directory where the missing modules will be copied
    dst_path = '{}/yangmodels/yang/experimental/ietf-extracted-YANG-modules'.format(missing_modules_directory)
    if not os.path.isdir(dst_path):
        os.makedirs(dst_path)

    missing_modules = []
    incorrect_revision_modules = []
    for yang_file in draft_extractor.inverted_draft_yang_dict:
        name_revision = yang_file.split('.yang')[0]
        if any(yang_file in module for module in (old_modules, unparsable_modules)) or yang_file.startswith('example'):
            continue
        if '@' in yang_file:
            revision = yang_file.split('@')[-1].split('.yang')[0]
            _, month, day = revision.split('-')
            if len(month) != 2 or len(day) != 2:
                incorrect_revision_modules.append(yang_file)
                continue
        else:
            name_revision += '@1970-01-01'
        if name_revision in all_modules_keys:
            continue
        missing_modules.append(yang_file)
        src = os.path.join(yang_path, yang_file)
        dst = os.path.join(dst_path, yang_file)
        shutil.copy2(src, dst)

    custom_print('Following modules from Drafts are missing in YANG Catalog')
    for module in missing_modules:
        print(module)

    shutil.rmtree(yang_path)
    shutil.rmtree(all_yang_drafts_strict)

    if missing_modules:
        mf = MessageFactory()
        mf.send_missing_modules(missing_modules, incorrect_revision_modules)

    message = {'label': 'Number of missing modules', 'message': len(missing_modules)}
    end = int(time.time())
    job_log(start, end, temp_dir, os.path.basename(__file__), messages=[message], status='Success')
    custom_print('end of {} job'.format(os.path.basename(__file__)))


if __name__ == '__main__':
    main()
