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
__copyright__ = 'Copyright(c) 2015-2019, Cisco Systems, Inc.,  Copyright The IETF Trust 2019, All Rights Reserved'
__email__ = 'bclaise@cisco.com, evyncke@cisco.com'

import argparse
import datetime
import json
import os
from operator import itemgetter

import requests

from compilators.draftsCompilator import DraftsCompilator
from compilators.examplesCompilator import ExamplesCompilator
from compilators.rfcsCompilator import RfcsCompilator
from create_config import create_config
from extractors.dratfExtractor import DraftExtractor
from extractors.rfcExtractor import RFCExtractor
from filesGenerator import FilesGenerator
from parsers.confdcParser import ConfdcParser
from parsers.pyangParser import PyangParser
from parsers.yangdumpProParser import YangdumpProParser
from parsers.yanglintParser import YanglintParser
from remove_directory_content import remove_directory_content
from utility.utility import (dict_to_list, list_br_html_addition,
                             number_that_passed_compilation)
from versions import ValidatorsVersions

# ----------------------------------------------------------------------
# Validators versions
# ----------------------------------------------------------------------
validators_versions = ValidatorsVersions()
versions = validators_versions.get_versions()


# ----------------------------------------------------------------------
# Functions
# ----------------------------------------------------------------------

def custom_print(message: str):
    timestamp = '{} ({}):'.format(datetime.datetime.now().time(), os.getpid())
    print('{} {}'.format(timestamp, message), flush=True)


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
if __name__ == '__main__':
    config = create_config()
    web_url = config.get('Web-Section', 'my-uri')
    web_private = config.get('Web-Section', 'private-directory')
    ietf_directory = config.get('Directory-Section', 'ietf-directory')
    temp_dir = config.get('Directory-Section', 'temp')
    modules_directory = config.get('Directory-Section', 'modules-directory')
    pyang_exec = config.get('Tool-Section', 'pyang-exec')
    confdc_exec = config.get('Tool-Section', 'confdc-exec')
    api_ip = config.get('Web-Section', 'ip')
    protocol = config.get('Web-Section', 'protocol-api')
    resutl_html_dir = config.get('Web-Section', 'result-html-dir')
    public_directory = config.get('Web-Section', 'public-directory')

    parser = argparse.ArgumentParser(description='YANG RFC/Draft Processor')
    parser.add_argument('--draftpath',
                        help='Path to the directory where all the drafts will be stored. '
                             'Default is {}/my-id-mirror/ '
                             'To get expired drafts as well, use {}/my-id-archive-mirror/'
                             .format(ietf_directory, ietf_directory),
                        type=str,
                        default='{}/my-id-mirror/'.format(ietf_directory))
    parser.add_argument('--rfcpath',
                        help='Path to the directory where all the RFCs will be stored. '
                             'Default is {}/rfc/'.format(ietf_directory),
                        type=str,
                        default='{}/rfc/'.format(ietf_directory))
    parser.add_argument('--yangpath',
                        help='Path to the directory where extracted models will be stored (only correct). '
                             'Default is "{}/YANG/"'.format(ietf_directory),
                        type=str,
                        default='{}/YANG/'.format(ietf_directory))
    parser.add_argument('--allyangpath',
                        help='Path to the directory where extracted models will be stored (including bad ones). '
                             'Default is "{}/YANG-all/"'.format(ietf_directory),
                        type=str,
                        default='{}/YANG-all/'.format(ietf_directory))
    parser.add_argument('--allyangexamplepath',
                        help='Path to the directory where extracted example models will be stored '
                        '(starting with example- and not with CODE BEGINS/END). '
                        'Default is "{}/YANG-example/"'.format(ietf_directory),
                        type=str,
                        default='{}/YANG-example/'.format(ietf_directory))
    parser.add_argument('--yangexampleoldrfcpath',
                        help='Directory where to store '
                             'the hardcoded YANG module example models from old RFCs (not starting with example-). '
                             'Default is "{}/YANG-example-old-rfc/"'.format(ietf_directory),
                        type=str,
                        default='{}/YANG-example-old-rfc/'.format(ietf_directory))
    parser.add_argument('--draftpathstrict',
                        help='Path to the directory where the drafts containing the YANG model(s) are stored - '
                        'with xym flag strict=True. '
                        'Default is "{}/draft-with-YANG-strict/"'.format(ietf_directory),
                        type=str,
                        default='{}/draft-with-YANG-strict/'.format(ietf_directory))
    parser.add_argument('--draftpathnostrict',
                        help='Path to the directory where the drafts containing the YANG model(s) are stored - '
                        'with xym flag strict=False. '
                        'Default is "{}/draft-with-YANG-no-strict/"'.format(ietf_directory),
                        type=str,
                        default='{}/draft-with-YANG-no-strict/'.format(ietf_directory))
    parser.add_argument('--draftpathonlyexample',
                        help='Path to the directory where the drafts containing examples are stored -'
                        'with xym flags strict=False and strict_examples=True. '
                        'Default is "{}/draft-with-YANG-example/"'.format(ietf_directory),
                        type=str,
                        default='{}/draft-with-YANG-example/'.format(ietf_directory))
    parser.add_argument('--rfcyangpath',
                        help='Directory where to store the data models extracted from RFCs. '
                             'Default is "{}/YANG-rfc/"'.format(ietf_directory),
                        type=str,
                        default='{}/YANG-rfc/'.format(ietf_directory))
    parser.add_argument('--rfcextractionyangpath',
                        help='Directory where to store '
                             'the typedef, grouping, identity from data models extracted from RFCs. '
                             'Default is "{}/YANG-rfc-extraction/"'.format(ietf_directory),
                        type=str,
                        default='{}/YANG-rfc-extraction/'.format(ietf_directory))
    parser.add_argument('--draftelementspath',
                        help='Directory where to store '
                             'the typedef, grouping, identity from data models correctely extracted from drafts. '
                             'Default is "{}/draft-elements/"'.format(ietf_directory),
                        type=str,
                        default='{}/draft-elements/'.format(ietf_directory))
    parser.add_argument('--debug',
                        help='Debug level - default is 0',
                        type=int,
                        default=0)
    parser.add_argument('--forcecompilation',
                        help='Optional flag that determines wheter compilation should be run '
                             'for all files even if they have not been changed '
                             'or even if the validators versions have not been changed.',
                        type=bool,
                        default=False)

    args = parser.parse_args()
    custom_print('Start of yangIetf.py job in {}'.format(args.draftpath))
    debug_level = args.debug

    # Initialize files generator -> used in creating JSON/HTML results files
    filesGenerator = FilesGenerator(web_private)

    all_yang_catalog_metadata = {}
    prefix = '{}://{}'.format(protocol, api_ip)

    modules = {}
    try:
        with open(os.path.join(temp_dir, 'all_modules_data.json'), 'r') as f:
            modules = json.load(f)
            custom_print('All the modules data loaded from JSON files')
    except Exception:
        modules = {}
    if modules == {}:
        modules = requests.get('{}/api/search/modules'.format(prefix)).json()
        custom_print('All the modules data loaded from API')

    for mod in modules['module']:
        key = '{}@{}'.format(mod['name'], mod['revision'])
        all_yang_catalog_metadata[key] = mod

    draft_extractor_paths = {
        'draft_path': args.draftpath,
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
    remove_directory_content(args.yangpath, debug_level)
    remove_directory_content(args.allyangpath, debug_level)
    remove_directory_content(args.rfcyangpath, debug_level)
    remove_directory_content(args.allyangexamplepath, debug_level)
    remove_directory_content(args.yangexampleoldrfcpath, debug_level)
    remove_directory_content(args.draftpathstrict, debug_level)
    remove_directory_content(args.draftpathnostrict, debug_level)
    remove_directory_content(args.draftpathonlyexample, debug_level)
    remove_directory_content(args.rfcextractionyangpath, debug_level)
    remove_directory_content(args.draftelementspath, debug_level)

    # ----------------------------------------------------------------------
    # Extract YANG models from IETF RFCs files
    # ----------------------------------------------------------------------
    rfcExtractor = RFCExtractor(args.rfcpath, args.rfcyangpath, args.rfcextractionyangpath, args.debug)
    rfcExtractor.extract_rfcs()
    rfcExtractor.invert_dict()
    rfcExtractor.remove_invalid_files()
    rfcExtractor.clean_old_RFC_YANG_modules(args.rfcyangpath, args.yangexampleoldrfcpath)
    custom_print('Old examples YANG modules moved')
    custom_print('All IETF RFCs pre-processed')

    # ----------------------------------------------------------------------
    # Extract YANG models from IETF draft files
    # ----------------------------------------------------------------------
    draftExtractor = DraftExtractor(draft_extractor_paths, args.debug)
    draftExtractor.extract_drafts()
    draftExtractor.invert_dict()
    draftExtractor.remove_invalid_files()
    draftExtractor.dump_incorrect_drafts(public_directory)
    custom_print('All IETF Drafts pre-processed')

    # TODO: Remove this - make these variables as input to another classes (compilation/parser)
    yang_rfc_dict = rfcExtractor.inverted_rfc_yang_dict
    yang_draft_dict = draftExtractor.inverted_draft_yang_dict
    yang_example_draft_dict = draftExtractor.inverted_draft_yang_example_dict

    # ----------------------------------------------------------------------
    # Initialize parsers
    # ----------------------------------------------------------------------
    pyangParser = PyangParser(args.debug)
    confdcParser = ConfdcParser(args.debug)
    yumadumpProParser = YangdumpProParser(args.debug)
    yanglintParser = YanglintParser(args.debug)

    # ----------------------------------------------------------------------
    # Compile extracted example- modules
    # ----------------------------------------------------------------------
    custom_print('Starting compilation in {} directory'.format(args.allyangexamplepath))
    examplesCompilator = ExamplesCompilator(args.allyangexamplepath, yang_example_draft_dict, args.debug)
    examplesCompilator.compile_examples(all_yang_catalog_metadata, args.forcecompilation)
    custom_print('example- YANG modules extracted from IETF Drafts validated/compiled')

    # Make a list out of the no-submodules dictionary
    sorted_modules_list = sorted(dict_to_list(examplesCompilator.results_no_submodules_dict))
    # Replace CR by the BR HTML tag
    sorted_modules_list_br_tags = list_br_html_addition(sorted_modules_list)

    # Generate json and html files with compilation results of extracted example- modules
    filesGenerator.write_dictionary(examplesCompilator.results_dict, 'IETFDraftExample')
    headers = filesGenerator.getIETFDraftExampleYANGPageCompilationHeaders()
    filesGenerator.generateYANGPageCompilationHTML(sorted_modules_list_br_tags, headers, 'IETFDraftExample')

    # ----------------------------------------------------------------------
    # Compile extracted RFC modules
    # ----------------------------------------------------------------------
    custom_print('Starting compilation in {} directory'.format(args.rfcyangpath))
    rfcsCompilator = RfcsCompilator(args.rfcyangpath, yang_rfc_dict, args.debug)
    rfcsCompilator.compile_rfcs(all_yang_catalog_metadata, args.forcecompilation)
    custom_print('RFC YANG modules validated/compiled')

    # Uncomment next two lines if you want to remove the submodules from the RFC report in http://www.claise.be/IETFYANGOutOfRFC.png
    sorted_modules_list = sorted(dict_to_list(rfcsCompilator.results_dict, True))
    # sorted_modules_list = sorted(dict_to_list(rfcsCompilator.results_no_submodules_dict, True), key=itemgetter(1))

    # Generate json and html files with compilation results of extracted RFC modules
    filesGenerator.write_dictionary(rfcsCompilator.results_dict, 'IETFYANGRFC')
    headers = ['YANG Model (and submodel)', 'RFC']
    filesGenerator.generateHTMLTable(sorted_modules_list, headers)

    # ----------------------------------------------------------------------
    # Compile modules extracted from drafts
    # ----------------------------------------------------------------------
    paths = {
        'draftpath': args.draftpath,
        'rfcpath': args.rfcyangpath
    }
    custom_print('Starting compilation in {} directory'.format(args.yangpath))
    draftsCompilator = DraftsCompilator(args.yangpath, yang_draft_dict, args.debug)
    draftsCompilator.compile_drafts(all_yang_catalog_metadata, args.forcecompilation, paths)
    custom_print('Modules extracted from IETF Drafts validated/compiled')

    # Make a list out of the no-submodules dictionary
    sorted_modules_list = sorted(dict_to_list(draftsCompilator.results_dict))
    # Replace CR by the BR HTML tag
    sorted_modules_list_br_tags = list_br_html_addition(sorted_modules_list)

    # Generate json and html files with compilation results of modules extracted from IETF Drafts
    filesGenerator.write_dictionary(draftsCompilator.results_dict, 'IETFDraft')
    headers = filesGenerator.getIETFDraftYANGPageCompilationHeaders()
    filesGenerator.generateYANGPageCompilationHTML(sorted_modules_list_br_tags, headers, 'IETFDraft')

    # Make a list out of the no-submodules dictionary
    sorted_modules_list = sorted(dict_to_list(draftsCompilator.results_dict_authors))
    # Replace CR by the BR HTML tag
    sorted_modules_list_br_tags = list_br_html_addition(sorted_modules_list)

    # Generate json and html files with compilation results of modules extracted from IETF Drafts with cisco authors
    filesGenerator.write_dictionary(draftsCompilator.results_dict_authors, 'IETFCiscoAuthors')
    headers = filesGenerator.getIETFCiscoAuthorsYANGPageCompilationHeaders()
    filesGenerator.generateYANGPageCompilationHTML(sorted_modules_list_br_tags, headers, 'IETFCiscoAuthors')

    output_email_list_unique = list(set(draftsCompilator.output_cisco_emails))
    output_email_string_unique = ', '.join(output_email_list_unique)
    custom_print('List of emails of Cisco authors:\n{}'.format(output_email_string_unique))

    # Create IETF drafts extraction and compilation statistics
    drafts_stats = {
        'total-drafts': len(yang_draft_dict.keys()),
        'draft-passed': number_that_passed_compilation(draftsCompilator.results_dict, 3, 'PASSED'),
        'draft-warnings': number_that_passed_compilation(draftsCompilator.results_dict, 3, 'PASSED WITH WARNINGS'),
        'all-ietf-drafts': len([f for f in os.listdir(args.allyangpath) if os.path.isfile(os.path.join(args.allyangpath, f))]),
        'example-drafts': len(yang_example_draft_dict.keys())
    }
    filesGenerator.generateIETFYANGPageMainHTML(drafts_stats)

    # ----------------------------------------------------------------------
    # Store IETF drafts statistics into AllYANGPageMain.json files
    # ----------------------------------------------------------------------
    stats_file_path = os.path.join(web_private, 'stats/AllYANGPageMain.json')
    counter = 5
    while True:
        try:
            if not os.path.exists(stats_file_path):
                with open(stats_file_path, 'w') as f:
                    f.write('{}')
            with open(stats_file_path, 'r') as f:
                stats = json.load(f)
                stats['ietf-yang'] = drafts_stats
            with open(stats_file_path, 'w') as f:
                json.dump(stats, f)
            break
        except Exception:
            counter = counter - 1
            if counter == 0:
                break

    # ----------------------------------------------------------------------
    # Print the summary of the IETF Drafts extraction and compilation results
    # ----------------------------------------------------------------------
    print('--------------------------')
    print('Number of correctly extracted YANG models from IETF drafts: {}'
          .format(drafts_stats.get('total-drafts')))
    print('Number of YANG models in IETF drafts that passed compilation: {}/{}'
          .format(drafts_stats.get('draft-passed'), drafts_stats.get('total-drafts')))
    print('Number of YANG models in IETF drafts that passed compilation with warnings: {}/{}'
          .format(drafts_stats.get('draft-warnings'), drafts_stats.get('total-drafts'))),
    print('Number of all YANG models in IETF drafts (examples, badly formatted, etc. ): {}'
          .format(drafts_stats.get('all-ietf-drafts')))
    print('Number of correctly extracted example YANG models from IETF drafts: {}'
          .format(drafts_stats.get('example-drafts')), flush=True)

    custom_print('end of yangIetf.py job')
