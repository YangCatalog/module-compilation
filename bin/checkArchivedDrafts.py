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
from extractors.dratfExtractor import DraftExtractor
from job_log import job_log
from messageFactory.messageFactory import MessageFactory
from remove_directory_content import remove_directory_content


def custom_print(message: str):
    timestamp = '{} ({}):'.format(datetime.datetime.now().time(), os.getpid())
    print('{} {}'.format(timestamp, message), flush=True)


def main():
    start = int(time.time())
    config = create_config()
    ietf_directory = config.get('Directory-Section', 'ietf-directory')
    temp_dir = config.get('Directory-Section', 'temp')
    api_ip = config.get('Web-Section', 'ip')
    protocol = config.get('General-Section', 'protocol-api')
    var_path = config.get('Directory-Section', 'var')

    parser = argparse.ArgumentParser(description='Check if modules from all the Drafts are populated in YANG Catalog')
    parser.add_argument('--draftpath', default='{}/my-id-archive-mirror/'.format(ietf_directory),
                        help='Path to the directory where all the drafts will be stored.'
                             'Default is {}/my-id-archive-mirror/'.format(ietf_directory))
    parser.add_argument('--yangpath', default='{}/archived-drafts-modules/'.format(temp_dir),
                        help='Path to the directory where all the modules should be extracted.'
                        'Default is {}/archived-drafts-modules'.format(temp_dir))
    parser.add_argument('--debug', type=int, default=0, help='Debug level; the default is 0')
    args = parser.parse_args()

    custom_print('Starting checkArchivedDrafts.py script')

    all_yang_drafts_strict = os.path.join(temp_dir, 'draft-with-YANG-strict')
    missing_modules_directory = os.path.join(temp_dir, 'drafts-missing-modules')
    draft_extractor_paths = {
        'draft_path': args.draftpath,
        'yang_path': args.yangpath,
        'all_yang_draft_path_strict': all_yang_drafts_strict,
        'all_yang_path': '{}/YANG-ALL'.format(temp_dir)
    }

    try:
        remove_directory_content(args.yangpath, args.debug)
        remove_directory_content(missing_modules_directory, args.debug)
        remove_directory_content(all_yang_drafts_strict, args.debug)

        custom_print('Extracting modules from drafts stored in {}'.format(args.draftpath))
        draftExtractor = DraftExtractor(draft_extractor_paths, args.debug, extract_elements=False, extract_examples=False)
        draftExtractor.extract_drafts()
        draftExtractor.invert_dict()
        draftExtractor.remove_invalid_files()
    except Exception:
        custom_print('Error occured while extracting modules')
        end = int(time.time())
        job_log(start, end, temp_dir, 'checkArchivedDrafts', status='Fail')
        return

    custom_print('Loading all modules data from API')
    prefix = '{}://{}'.format(protocol, api_ip)
    all_modules = requests.get('{}/api/search/modules'.format(prefix)).json()
    all_modules_keys = []
    if all_modules:
        all_modules = all_modules.get('module', [])
        all_modules_keys = ['{}@{}'.format(m.get('name'), m.get('revision')) for m in all_modules]

    try:
        with open('{}/resources/old-rfcs.json'.format(os.path.dirname(os.path.realpath(__file__))), 'r') as f:
            old_modules = json.load(f)
    except Exception:
        old_modules = []
    try:
        with open('{}/unparsable-modules.json'.format(var_path), 'r') as f:
            unparsable_modules = json.load(f)
    except Exception:
        unparsable_modules = []

    # Prepare a directory where the missing modules will be copied
    dst_path = '{}/yangmodels/yang/experimental/ietf-extracted-YANG-modules'.format(missing_modules_directory)
    if not os.path.isdir(dst_path):
        os.makedirs(dst_path)

    missing_modules = []
    incorrect_revision_modules = []
    for yang_file in draftExtractor.inverted_draft_yang_dict:
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
        if name_revision not in all_modules_keys:
            missing_modules.append(yang_file)
            src = os.path.join(args.yangpath, yang_file)
            dst = os.path.join(dst_path, yang_file)
            shutil.copy2(src, dst)

    custom_print('Following modules from Drafts are missing in YANG Catalog')
    for module in missing_modules:
        print(module)

    shutil.rmtree(args.yangpath)
    shutil.rmtree(all_yang_drafts_strict)

    if missing_modules:
        mf = MessageFactory()
        mf.send_missing_modules(missing_modules, incorrect_revision_modules)

    message = {'label': 'Number of missing modules', 'message': len(missing_modules)}
    end = int(time.time())
    job_log(start, end, temp_dir, 'checkArchivedDrafts', messages=[message], status='Success')


if __name__ == '__main__':
    main()
