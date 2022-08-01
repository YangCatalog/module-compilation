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
from extractors.dratf_extractor import DraftExtractor
from extractors.rfc_extractor import RFCExtractor
from remove_directory_content import remove_directory_content

# ----------------------------------------------------------------------
# Functions
# ----------------------------------------------------------------------


def custom_print(message: str):
    timestamp = '{} ({}):'.format(datetime.datetime.now().time(), os.getpid())
    print('{} {}'.format(timestamp, message), flush=True)


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main():
    config = create_config()
    ietf_directory = config.get('Directory-Section', 'ietf-directory')
    draft_path = config.get('Directory-Section', 'ietf-drafts')
    rfc_path = config.get('Directory-Section', 'ietf-rfcs')
    cache_directory = config.get('Directory-Section', 'cache')
    public_directory = config.get('Web-Section', 'public-directory')

    parser = argparse.ArgumentParser(description='YANG RFC/Draft Processor')
    parser.add_argument('--archived',
                        help='Extract expired drafts as well',
                        action='store_true',
                        default=False)
    parser.add_argument('--yangpath',
                        help='Path to the directory where to extract models (only correct). '
                             'Default is "{}/YANG/"'.format(ietf_directory),
                        type=str,
                        default='{}/YANG/'.format(ietf_directory))
    parser.add_argument('--allyangpath',
                        help='Path to the directory where to extract models (including bad ones). '
                             'Default is "{}/YANG-all/"'.format(ietf_directory),
                        type=str,
                        default='{}/YANG-all/'.format(ietf_directory))
    parser.add_argument('--allyangexamplepath',
                        help='Path to the directory where to extract example models '
                        '(starting with example- and not with CODE BEGINS/END). '
                        'Default is "{}/YANG-example/"'.format(ietf_directory),
                        type=str,
                        default='{}/YANG-example/'.format(ietf_directory))
    parser.add_argument('--yangexampleoldrfcpath',
                        help='Path to the directory where to extract '
                             'the hardcoded YANG module example models from old RFCs (not starting with example-). '
                             'Default is "{}/YANG-example-old-rfc/"'.format(ietf_directory),
                        type=str,
                        default='{}/YANG-example-old-rfc/'.format(ietf_directory))
    parser.add_argument('--draftpathstrict',
                        help='Path to the directory where to extract the drafts containing the YANG model(s) - '
                        'with xym flag strict=True. '
                        'Default is "{}/draft-with-YANG-strict/"'.format(ietf_directory),
                        type=str,
                        default='{}/draft-with-YANG-strict/'.format(ietf_directory))
    parser.add_argument('--draftpathnostrict',
                        help='Path to the directory where to extract the drafts containing the YANG model(s) - '
                        'with xym flag strict=False. '
                        'Default is "{}/draft-with-YANG-no-strict/"'.format(ietf_directory),
                        type=str,
                        default='{}/draft-with-YANG-no-strict/'.format(ietf_directory))
    parser.add_argument('--draftpathonlyexample',
                        help='Path to the directory where to extract the drafts containing examples -'
                        'with xym flags strict=False and strict_examples=True. '
                        'Default is "{}/draft-with-YANG-example/"'.format(ietf_directory),
                        type=str,
                        default='{}/draft-with-YANG-example/'.format(ietf_directory))
    parser.add_argument('--rfcyangpath',
                        help='Path to the directory where to extract the data models extracted from RFCs. '
                             'Default is "{}/YANG-rfc/"'.format(ietf_directory),
                        type=str,
                        default='{}/YANG-rfc/'.format(ietf_directory))
    parser.add_argument('--rfcextractionyangpath',
                        help='Path to the directory where to extract '
                             'the typedef, grouping, identity from data models extracted from RFCs. '
                             'Default is "{}/YANG-rfc-extraction/"'.format(ietf_directory),
                        type=str,
                        default='{}/YANG-rfc-extraction/'.format(ietf_directory))
    parser.add_argument('--draftelementspath',
                        help='Path to the directory where to extract '
                             'the typedef, grouping, identity from data models correctely extracted from drafts. '
                             'Default is "{}/draft-elements/"'.format(ietf_directory),
                        type=str,
                        default='{}/draft-elements/'.format(ietf_directory))
    parser.add_argument('--debug',
                        help='Debug level - default is 0',
                        type=int,
                        default=0)

    args = parser.parse_args()
    if args.archived:
        draft_path = os.path.join(ietf_directory, 'my-id-archive-mirror')
    custom_print('Start of {} job in {}'.format(os.path.basename(__file__), draft_path))
    debug_level = args.debug

    draft_extractor_paths = {
        'draft_path': draft_path,
        'yang_path': args.yangpath,
        'draft_elements_path': args.draftelementspath,
        'draft_path_strict': args.draftpathstrict,
        'all_yang_example_path': args.allyangexamplepath,
        'draft_path_only_example': args.draftpathonlyexample,
        'all_yang_path': args.allyangpath,
        'draft_path_no_strict': args.draftpathnostrict
    }

    # ----------------------------------------------------------------------
    # Empty the yangpath, allyangpath, and rfcyangpath directories content
    # ----------------------------------------------------------------------
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
        args.draftelementspath
    ]:
        remove_directory_content(dir, debug_level)

    # Extract YANG models from IETF RFCs files
    rfcExtractor = RFCExtractor(rfc_path, args.rfcyangpath, args.rfcextractionyangpath, debug_level)
    rfcExtractor.extract()
    rfcExtractor.clean_old_RFC_YANG_modules(args.rfcyangpath, args.yangexampleoldrfcpath)
    custom_print('Old examples YANG modules moved')
    custom_print('All IETF RFCs pre-processed')

    # Extract YANG models from IETF draft files
    draftExtractor = DraftExtractor(draft_extractor_paths, debug_level)
    draftExtractor.extract()
    draftExtractor.dump_incorrect_drafts(public_directory)
    custom_print('All IETF Drafts pre-processed')

    # Dump dicts for later use by compile_modules.py
    with open(os.path.join(cache_directory, 'rfc_dict.json'), 'w') as f:
        json.dump(rfcExtractor.inverted_rfc_yang_dict, f)

    with open(os.path.join(cache_directory, 'draft_dict.json'), 'w') as f:
        json.dump(draftExtractor.inverted_draft_yang_dict, f)

    with open(os.path.join(cache_directory, 'example_dict.json'), 'w') as f:
        json.dump(draftExtractor.inverted_draft_yang_example_dict, f)

    custom_print('end of {} job'.format(os.path.basename(__file__)))


if __name__ == '__main__':
    main()
