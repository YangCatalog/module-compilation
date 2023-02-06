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

__author__ = 'Benoit Claise, Eric Vyncke'
__copyright__ = 'Copyright(c) 2015-2019, Cisco Systems, Inc., Copyright The IETF Trust 2019, All Rights Reserved'
__license__ = 'Apache License, Version 2.0'
__email__ = 'bclaise@cisco.com, evyncke@cisco.com'

import argparse
import datetime
import json
import os

from create_config import create_config
from extractors.draft_extractor import DraftExtractor
from extractors.rfc_extractor import RFCExtractor
from utility.utility import remove_directory_content

file_basename = os.path.basename(__file__)


def custom_print(message: str):
    timestamp = f'{datetime.datetime.now().time()} ({os.getpid()}):'
    print(f'{timestamp} {message}', flush=True)


def main():
    config = create_config()
    ietf_directory = config.get('Directory-Section', 'ietf-directory')
    draft_path = config.get('Directory-Section', 'ietf-drafts')
    rfc_path = config.get('Directory-Section', 'ietf-rfcs')
    cache_directory = config.get('Directory-Section', 'cache')
    public_directory = config.get('Web-Section', 'public-directory')
    downloadables_directory = config.get('Web-Section', 'downloadables-directory')
    code_snippets_directory = config.get(
        'Web-Section',
        'code-snippets-directory',
        fallback=os.path.join(downloadables_directory, 'code-snippets'),
    )
    send_emails_about_problematic_drafts = (
        config.get('General-Section', 'send_emails_about_problematic_drafts', fallback='False') == 'True'
    )

    parser = argparse.ArgumentParser(description='YANG RFC/Draft Processor')
    parser.add_argument('--archived', help='Extract expired drafts as well', action='store_true', default=False)
    parser.add_argument(
        '--yangpath',
        help='Path to the directory where to extract models (only correct). ' f'Default is "{ietf_directory}/YANG/"',
        type=str,
        default=f'{ietf_directory}/YANG/',
    )
    parser.add_argument(
        '--allyangpath',
        help='Path to the directory where to extract models (including bad ones). '
        f'Default is "{ietf_directory}/YANG-all/"',
        type=str,
        default=f'{ietf_directory}/YANG-all/',
    )
    parser.add_argument(
        '--allyangexamplepath',
        help='Path to the directory where to extract example models '
        '(starting with example- and not with CODE BEGINS/END). '
        f'Default is "{ietf_directory}/YANG-example/"',
        type=str,
        default=f'{ietf_directory}/YANG-example/',
    )
    parser.add_argument(
        '--yangexampleoldrfcpath',
        help='Path to the directory where to extract '
        'the hardcoded YANG module example models from old RFCs (not starting with example-). '
        f'Default is "{ietf_directory}/YANG-example-old-rfc/"',
        type=str,
        default=f'{ietf_directory}/YANG-example-old-rfc/',
    )
    parser.add_argument(
        '--draftpathstrict',
        help='Path to the directory where to extract the drafts containing the YANG model(s) - '
        'with xym flag strict=True. '
        f'Default is "{ietf_directory}/draft-with-YANG-strict/"',
        type=str,
        default=f'{ietf_directory}/draft-with-YANG-strict/',
    )
    parser.add_argument(
        '--draftpathnostrict',
        help='Path to the directory where to extract the drafts containing the YANG model(s) - '
        'with xym flag strict=False. '
        f'Default is "{ietf_directory}/draft-with-YANG-no-strict/"',
        type=str,
        default=f'{ietf_directory}/draft-with-YANG-no-strict/',
    )
    parser.add_argument(
        '--draftpathonlyexample',
        help='Path to the directory where to extract the drafts containing examples -'
        'with xym flags strict=False and strict_examples=True. '
        f'Default is "{ietf_directory}/draft-with-YANG-example/"',
        type=str,
        default=f'{ietf_directory}/draft-with-YANG-example/',
    )
    parser.add_argument(
        '--rfcyangpath',
        help='Path to the directory where to extract the data models extracted from RFCs. '
        f'Default is "{ietf_directory}/YANG-rfc/"',
        type=str,
        default=f'{ietf_directory}/YANG-rfc/',
    )
    parser.add_argument(
        '--rfcextractionyangpath',
        help='Path to the directory where to extract '
        'the typedef, grouping, identity from data models extracted from RFCs. '
        f'Default is "{ietf_directory}/YANG-rfc-extraction/"',
        type=str,
        default=f'{ietf_directory}/YANG-rfc-extraction/',
    )
    parser.add_argument(
        '--draftelementspath',
        help='Path to the directory where to extract '
        'the typedef, grouping, identity from data models correctely extracted from drafts. '
        f'Default is "{ietf_directory}/draft-elements/"',
        type=str,
        default=f'{ietf_directory}/draft-elements/',
    )
    parser.add_argument(
        '--code-snippets-directory',
        help='Path to the directory where the extract code snippets from drafts will be stored. '
        f'Default is {code_snippets_directory}',
        type=str,
        default=code_snippets_directory,
    )
    parser.add_argument('--debug', help='Debug level - default is 0', type=int, default=0)

    args = parser.parse_args()
    if args.archived:
        draft_path = os.path.join(ietf_directory, 'my-id-archive-mirror')
    custom_print(f'Start of {os.path.basename(__file__)} job in {draft_path}')
    debug_level = args.debug

    draft_extractor_paths = {
        'draft_path': draft_path,
        'yang_path': args.yangpath,
        'draft_elements_path': args.draftelementspath,
        'draft_path_strict': args.draftpathstrict,
        'all_yang_example_path': args.allyangexamplepath,
        'draft_path_only_example': args.draftpathonlyexample,
        'all_yang_path': args.allyangpath,
        'draft_path_no_strict': args.draftpathnostrict,
        'code_snippets_dir': args.code_snippets_directory,
    }

    # Remove directories content
    for dir in [
        args.yangpath,
        args.allyangpath,
        args.rfcyangpath,
        args.allyangexamplepath,
        args.yangexampleoldrfcpath,
        args.draftpathstrict,
        args.draftpathstrict,
        args.draftpathnostrict,
        args.draftpathonlyexample,
        args.rfcextractionyangpath,
        args.draftelementspath,
    ]:
        remove_directory_content(dir, debug_level)

    # Extract YANG models from IETF RFCs files
    rfc_extractor = RFCExtractor(
        rfc_path,
        args.rfcyangpath,
        args.rfcextractionyangpath,
        args.code_snippets_directory,
        debug_level,
    )
    rfc_extractor.extract()
    rfc_extractor.clean_old_rfc_yang_modules(args.rfcyangpath, args.yangexampleoldrfcpath)
    custom_print('Old examples YANG modules moved')
    custom_print('All IETF RFCs pre-processed')

    # Extract YANG models from IETF draft files
    draft_extractor = DraftExtractor(draft_extractor_paths, debug_level)
    draft_extractor.extract()
    draft_extractor.dump_incorrect_drafts(
        public_directory,
        send_emails_about_problematic_drafts=send_emails_about_problematic_drafts,
    )
    custom_print('All IETF Drafts pre-processed')

    # Dump dicts for later use by compile_modules.py
    with open(os.path.join(cache_directory, 'rfc_dict.json'), 'w') as f:
        json.dump(rfc_extractor.inverted_rfc_yang_dict, f)

    with open(os.path.join(cache_directory, 'draft_dict.json'), 'w') as f:
        json.dump(draft_extractor.inverted_draft_yang_dict, f)

    with open(os.path.join(cache_directory, 'example_dict.json'), 'w') as f:
        json.dump(draft_extractor.inverted_draft_yang_example_dict, f)

    custom_print(f'end of {os.path.basename(__file__)} job')


if __name__ == '__main__':
    main()
