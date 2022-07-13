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
import datetime
import json
import os
import re

import requests
from filelock import FileLock

from compilation_status import combined_compilation, pyang_compilation_status
from create_config import create_config
from file_hasher import FileHasher
from files_generator import FilesGenerator
from metadata_generators.base_metadata_generator import BaseMetadataGenerator
from metadata_generators.draft_metadata_generator import (
    ArchivedMetadataGenerator, DraftMetadataGenerator)
from metadata_generators.example_metadata_generator import \
    ExampleMetadataGenerator
from metadata_generators.rfc_metadata_generator import RfcMetadataGenerator
from parsers.confdc_parser import ConfdcParser
from parsers.pyang_parser import PyangParser
from parsers.yangdump_pro_parser import YangdumpProParser
from parsers.yanglint_parser import YanglintParser
from utility.utility import (check_yangcatalog_data, module_or_submodule,
                             number_that_passed_compilation, push_to_redis)

__author__ = 'Benoit Claise'
__copyright__ = 'Copyright(c) 2015-2018, Cisco Systems, Inc.,  Copyright The IETF Trust 2022, All Rights Reserved'
__license__ = 'Apache License, Version 2.0'
__email__ = 'bclaise@cisco.com'


# ----------------------------------------------------------------------
# Functions
# ----------------------------------------------------------------------


def list_of_yang_modules_in_subdir(srcdir: str, debug_level: int):
    """
    Returns the list of YANG Modules (.yang) in all sub-directories

    Arguments:
        :param srcdir           (str) root directory to search for yang files
        :param debug_level      (int) If > 0 print some debug statements to the console
        :return: list of YANG files found in all sub-directories of root directory
    """
    ll = []
    for root, _, files in os.walk(srcdir):
        for f in files:
            if f.endswith('.yang'):
                if debug_level > 0:
                    print(os.path.join(root, f))
                ll.append(os.path.join(root, f))
    return ll


def get_mod_rev(yang_file) -> str:
    name = ''
    revision = ''

    with open(yang_file, 'r', encoding='utf-8', errors='ignore') as module:
        for line in module:
            if name != '' and revision != '':
                return name + '@' + revision

            if name == '':
                match = re.search(r'^\s*(sub)?module\s+([\w\-\d]+)', line)
                if match:
                    name = match.group(2).strip()
                    continue

            if revision == '':
                match = re.search(r'^\s*revision\s+"?([\d\-]+)"?', line)
                if match:
                    revision = match.group(1).strip()
                    continue

    if revision == '':
        return name
    else:
        return name + '@' + revision


def custom_print(message: str):
    timestamp = '{} ({}):'.format(datetime.datetime.now().time(), os.getpid())
    print('{} {}'.format(timestamp, message), flush=True)


def get_name_with_revision(yang_file: str) -> str:
    yang_file_base = os.path.basename(yang_file)
    out = get_mod_rev(yang_file)

    if out.rstrip():
        # Add the @revision to the yang_file if not present
        if '@' in yang_file and '.yang' in yang_file:
            new_yang_file_base_with_revision = out.rstrip() + '.yang'
            if new_yang_file_base_with_revision.split('@')[0] != yang_file_base.split('@')[0]:
                print(
                    'Name of the YANG file ' + yang_file_base + ' is wrong changing to correct one into ' + new_yang_file_base_with_revision,
                    flush=True)
                yang_file_base = new_yang_file_base_with_revision
            if new_yang_file_base_with_revision.split('@')[1].split('.')[0] != \
                    yang_file_base.split('@')[1].split('.')[0]:
                print(
                    'Revision of the YANG file ' + yang_file_base + ' is wrong changing to correct as ' + new_yang_file_base_with_revision,
                    flush=True)
                yang_file_base = new_yang_file_base_with_revision

            return yang_file_base
        else:
            new_yang_file_base_with_revision = out.rstrip() + '.yang'
            if debug_level > 0:
                print(
                    "DEBUG: Adding the revision to YANG module because xym can't get revision(missing from the YANG module): " + yang_file)
                print('DEBUG:  out: ' + new_yang_file_base_with_revision)

            return new_yang_file_base_with_revision
    else:
        print('Unable to get name@revision out of ' + yang_file + ' - no output', flush=True)

    return ''


def get_modules(temp_dir: str, prefix: str) -> dict:
    try:
        with open(os.path.join(temp_dir, 'all_modules_data.json'), 'r') as f:
            modules = json.load(f)
            custom_print('All the modules data loaded from JSON files')
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        modules = {}
    if modules == {}:
        modules = requests.get('{}/api/search/modules'.format(prefix)).json()
        custom_print('All the modules data loaded from API')
    return modules


def parse_module(parsers: dict, yang_file: str, root_directory: str, lint: bool, allinclusive: bool):
    result_pyang = parsers['pyang'].run_pyang(root_directory, yang_file, lint, allinclusive, True)
    result_no_pyang_param = parsers['pyang'].run_pyang(root_directory, yang_file, lint, allinclusive, False)
    result_confd = parsers['confdc'].run_confdc(yang_file, root_directory, allinclusive)
    result_yuma = parsers['yangdumppro'].run_yumadumppro(yang_file, root_directory, allinclusive)
    result_yanglint = parsers['yanglint'].run_yanglint(yang_file, root_directory, allinclusive)
    module_compilation_results = {
        'pyang_lint': result_pyang,
        'pyang': result_no_pyang_param,
        'confdrc': result_confd,
        'yumadump': result_yuma,
        'yanglint': result_yanglint
    }
    compilation_status = combined_compilation(os.path.basename(yang_file), module_compilation_results)
    return compilation_status, module_compilation_results


def parse_example_module(parsers: dict, yang_file: str, root_directory: str, lint: bool, allinclusive: bool):
    result_pyang = parsers['pyang'].run_pyang(root_directory, yang_file, lint, allinclusive, True)
    result_no_pyang_param = parsers['pyang'].run_pyang(root_directory, yang_file, lint, allinclusive, False)
    module_compilation_results = {
        'pyang_lint': result_pyang,
        'pyang': result_no_pyang_param
    }
    compilation_status = pyang_compilation_status(result_pyang)
    return compilation_status, module_compilation_results


def validate(prefix: str, modules: dict, yang_list: list, parser_args: dict, document_dict: dict) -> dict:
    updated_modules = []
    agregate_results = {'all': {}, 'no_submodules': {}}
    parsers = {
        'pyang': PyangParser(debug_level),
        'confdc': ConfdcParser(debug_level),
        'yangdumppro': YangdumpProParser(debug_level),
        'yanglint': YanglintParser(debug_level)
    }
    all_yang_catalog_metadata = {}
    for module in modules['module']:
        key = '{}@{}'.format(module['name'], module['revision'])
        all_yang_catalog_metadata[key] = module

    # Load compilation results from .json file, if any exists
    try:
        with open('{}/{}.json'.format(web_private, prefix), 'r') as f:
            cached_compilation_results = json.load(f)
    except Exception:
        cached_compilation_results = {}

    for yang_file in yang_list:
        yang_file_with_revision = get_name_with_revision(yang_file)
        should_parse, file_hash = fileHasher.should_parse(yang_file)
        yang_file_compilation = cached_compilation_results.get(yang_file_with_revision)

        if should_parse or yang_file_compilation is None:
            if ietf == 'ietf-example':
                compilation_status, module_compilation_results = parse_example_module(parsers, yang_file, **parser_args)
            else:
                compilation_status, module_compilation_results = parse_module(parsers, yang_file, **parser_args)

            metadata_generator = metadata_generator_cls(module_compilation_results, compilation_status,
                                                        yang_file, document_dict)
            confd_metadata = metadata_generator.get_confd_metadata()
            yang_file_compilation = metadata_generator.get_file_compilation()
            updated_modules.extend(
                check_yangcatalog_data(
                    config, yang_file, confd_metadata, module_compilation_results,
                    all_yang_catalog_metadata, ietf))
            if len(updated_modules) > 100:
                push_to_redis(updated_modules, config)
                updated_modules.clear()

            # Revert to previous hash if compilation status is 'UNKNOWN' -> try to parse model again next time
            if compilation_status != 'UNKNOWN':
                fileHasher.updated_hashes[yang_file] = file_hash

        if yang_file_with_revision != '' or ietf == 'ietf-example':
            agregate_results['all'][yang_file_with_revision] = yang_file_compilation
            if module_or_submodule(yang_file) == 'module':
                agregate_results['no_submodules'][yang_file_with_revision] = yang_file_compilation
    push_to_redis(updated_modules, config)
    return agregate_results


def write_page_main(prefix: str, compilation_stats: dict) -> dict:  # pyright: ignore
    stats_directory = os.path.join(web_private, 'stats')
    os.makedirs(stats_directory, exist_ok=True)
    with FileLock(os.path.join(stats_directory, 'stats.json.lock')):
        stats_file_path = os.path.join(stats_directory, 'AllYANGPageMain.json')
        counter = 5
        while True:
            try:
                if not os.path.exists(stats_file_path):
                    with open(stats_file_path, 'w') as f:
                        f.write('{}')
                with open(stats_file_path, 'r') as f:
                    stats = json.load(f)
                    stats[prefix].update(compilation_stats)
                with open(stats_file_path, 'w') as f:
                    json.dump(stats, f)
                return stats[prefix]
            # NOTE: what kind of exception is expected here?
            except Exception:
                counter = counter - 1
                if counter == 0:
                    break


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main():
    global config, debug_level, fileHasher, ietf, metadata_generator_cls, web_private
    config = create_config()
    yangcatalog_api_prefix = config.get('Web-Section', 'yangcatalog-api-prefix')
    web_private = config.get('Web-Section', 'private-directory') + '/'
    cache_directory = config.get('Directory-Section', 'cache')
    modules_directory = config.get('Directory-Section', 'modules-directory')
    temp_dir = config.get('Directory-Section', 'temp')
    ietf_directory = config.get('Directory-Section', 'ietf-directory')

    parser = argparse.ArgumentParser(
        description='YANG Document Processor: generate tables with compilation errors/warnings')
    parser.add_argument('--rootdir',
                        help='Root directory where to find the source YANG models. '
                             'Default is "."',
                        type=str,
                        default='.',)
    parser.add_argument('--metadata',
                        help='Metadata text (such as SDOs, Github location, etc.) '
                             'to be displayed on the generated HTML page. '
                             'Default is ""',
                        type=str,
                        default='')
    parser.add_argument('--lint',
                        help='Optional flag that determines pyang syntax enforcement; '
                             'If set, pyang --lint is run. '
                             'Otherwise, pyang --ietf is run. '
                             'Default is False',
                        action='store_true',
                        default=False)
    parser.add_argument('--allinclusive',
                        help='Optional flag that determines whether the rootdir directory '
                             'contains all imported YANG modules; '
                             'If set, the YANG validators will only look in the rootdir directory. '
                             'Otherwise, the YANG validators look in {}. '
                             'Default is False'.format(modules_directory),
                        action='store_true',
                        default=False)
    parser.add_argument('--prefix',
                        help='Prefix for generating HTML file names. Example: MEF, IEEEStandard, IEEEExperimental. '
                             'Default is ""',
                        default='')
    parser.add_argument('--debug',
                        help='Debug level - default is 0',
                        type=int,
                        default=0)
    parser.add_argument('--forcecompilation',
                        help='Optional flag that determines wheter compilation should be run '
                             'for all files even if they have not been changed '
                             'or even if the validators versions have not been changed.',
                        action='store_true',
                        default=False)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--rfc',
                       help='Set specific options for compiling RFCs.',
                       action='store_true')
    group.add_argument('--draft',
                       help='Include extra metadata in the compilation results when compiling drafts.'
                            ' Does not include archived drafts.',
                       action='store_true')
    group.add_argument('--draft-archive',
                       help='Include extra metadata in the compilation results when compiling drafts.'
                            ' Includes archived drafts.',
                       action='store_true')
    group.add_argument('--example',
                       help='Include extra metadata in the compilation results when compiling examples,'
                            ' only compile examples with pyang.',
                       action='store_true')
    args = parser.parse_args()

    # Set options depending on the type of documents we're compiling
    if not any([args.draft, args.draft_archive, args.example, args.rfc]):
        ietf = None
        metadata_generator_cls = BaseMetadataGenerator
        document_dict = {}
    elif args.rfc:
        ietf = 'ietf-rfc'
        metadata_generator_cls = RfcMetadataGenerator
        with open(os.path.join(cache_directory, 'rfc_dict.json')) as f:
            document_dict = json.load(f)
        args.prefix = 'RFCStandard'
        args.rootdir = os.path.join(ietf_directory, 'YANG-rfc')
    elif args.draft or args.draft_archive:
        ietf = 'ietf-draft'
        if args.draft_archive:
            metadata_generator_cls = ArchivedMetadataGenerator
        else:
            metadata_generator_cls = DraftMetadataGenerator
        with open(os.path.join(cache_directory, 'draft_dict.json')) as f:
            document_dict = json.load(f)
        args.prefix = 'IETFDraft'
        args.rootdir = os.path.join(ietf_directory, 'YANG')
    elif args.example:
        ietf = 'ietf-example'
        metadata_generator_cls = ExampleMetadataGenerator
        with open(os.path.join(cache_directory, 'example_dict.json')) as f:
            document_dict = json.load(f)
        args.prefix = 'IETFDraftExample'
        args.rootdir = os.path.join(ietf_directory, 'YANG-example')
    else:
        assert False, 'This is unreachable'

    custom_print('Start of job in {}'.format(args.rootdir))

    debug_level = args.debug

    # Get list of hashed files
    fileHasher = FileHasher(force_compilation=args.forcecompilation)

    modules = get_modules(temp_dir, yangcatalog_api_prefix)

    yang_list = list_of_yang_modules_in_subdir(args.rootdir, args.debug)

    parser_args = {
        'root_directory': args.rootdir,
        'lint': args.lint,
        'allinclusive': args.allinclusive
    }

    if debug_level > 0:
        print('yang_list content:\n{}'.format(yang_list))
    custom_print('relevant files list built, {} modules found in {}'.format(len(yang_list), args.rootdir))
    agregate_results = validate(args.prefix, modules, yang_list, parser_args, document_dict)
    custom_print('all modules compiled/validated')

    # Generate HTML and JSON files
    filesGenerator = FilesGenerator(web_private)
    if ietf == 'ietf-draft':
        # Generate json and html files with compilation results of modules extracted from IETF Drafts with Cisco authors
        filesGenerator.write_dictionary(agregate_results['all'], 'IETFCiscoAuthors')
        headers = filesGenerator.getIETFCiscoAuthorsYANGPageCompilationHeaders()
        filesGenerator.generateYANGPageCompilationHTML(agregate_results['all'], headers, 'IETFCiscoAuthors')

        # Strip cisco authors out
        agregate_results['all'] = {k: v[:2] + v[3:] for k, v in agregate_results['all'].items()}

        # Generate json and html files with compilation results of modules extracted from IETF Drafts
        filesGenerator.write_dictionary(agregate_results['all'], args.prefix)
        headers = filesGenerator.getIETFDraftYANGPageCompilationHeaders()
        filesGenerator.generateYANGPageCompilationHTML(agregate_results['all'], headers, args.prefix)
    elif ietf == 'ietf-example':
        filesGenerator.write_dictionary(agregate_results['all'], args.prefix)
        headers = filesGenerator.getIETFDraftExampleYANGPageCompilationHeaders()
        filesGenerator.generateYANGPageCompilationHTML(agregate_results['no_submodules'], headers, args.prefix)
    else:
        if ietf == 'ietf-rfc':
            # Create yang module reference table
            module_to_rfc_anchor = {}
            for yang_module, document_name in document_dict.items():
                rfc_name = document_name.split('.')[0]
                datatracker_url = 'https://datatracker.ietf.org/doc/html/{}'.format((rfc_name))
                rfc_url_anchor = '<a href="{}">{}</a>'.format(datatracker_url, rfc_name)
                module_to_rfc_anchor[yang_module] = rfc_url_anchor

            filesGenerator.write_dictionary(module_to_rfc_anchor, 'IETFYANGRFC')
            headers = ['YANG Model (and submodel)', 'RFC']
            filesGenerator.generateHTMLTable(module_to_rfc_anchor, headers)

        filesGenerator.write_dictionary(agregate_results['all'], args.prefix)
        headers = filesGenerator.getYANGPageCompilationHeaders(args.lint)
        filesGenerator.generateYANGPageCompilationHTML(agregate_results['no_submodules'], headers, args.prefix, args.metadata)

    # Generate modules compilation results statistics HTML page
    passed = number_that_passed_compilation(agregate_results['all'], 0, 'PASSED')
    passed_with_warnings = number_that_passed_compilation(agregate_results['all'], 0, 'PASSED WITH WARNINGS')
    total_number = len(yang_list)
    failed = total_number - passed - passed_with_warnings

    if ietf == 'ietf-draft':
        all_yang_path = os.path.join(ietf_directory, 'YANG-all')
        compilation_stats = {
            'total-drafts': len(document_dict.keys()),
            'draft-passed': number_that_passed_compilation(agregate_results['all'], 3, 'PASSED'),
            'draft-warnings': number_that_passed_compilation(agregate_results['all'], 3, 'PASSED WITH WARNINGS'),
            'all-ietf-drafts': len([f for f in os.listdir(all_yang_path) if os.path.isfile(os.path.join(all_yang_path, f))])
        }
        merged_stats = write_page_main('ietf-yang', compilation_stats)
        filesGenerator.generateIETFYANGPageMainHTML(merged_stats)
    elif ietf == 'ietf-example':
        compilation_stats = {
            'example-drafts': len(document_dict.keys())
        }
        merged_stats = write_page_main('ietf-yang', compilation_stats)
        filesGenerator.generateIETFYANGPageMainHTML(merged_stats)
    else:
        compilation_stats = {
            'passed': passed,
            'warnings': passed_with_warnings,
            'total': total_number,
            'failed': failed
        }
        write_page_main(args.prefix, compilation_stats)
        filesGenerator.generateYANGPageMainHTML(args.prefix, compilation_stats)

    # Print the summary of the compilation results
    print('--------------------------')
    if ietf == 'ietf-draft':
        print('Number of correctly extracted YANG models from IETF drafts: {}'
              .format(compilation_stats['total-drafts']))
        print('Number of YANG models in IETF drafts that passed compilation: {}/{}'
              .format(compilation_stats['draft-passed'], compilation_stats.get('total-drafts')))
        print('Number of YANG models in IETF drafts that passed compilation with warnings: {}/{}'
              .format(compilation_stats['draft-warnings'], compilation_stats.get('total-drafts'))),
        print('Number of all YANG models in IETF drafts (examples, badly formatted, etc. ): {}'
              .format(compilation_stats['all-ietf-drafts']))
    elif ietf == 'ietf-example':
        print('Number of correctly extracted example YANG models from IETF drafts: {}'
              .format(compilation_stats['example-drafts']), flush=True)
    else:
        print('Number of YANG data models from {}: {}'.format(args.prefix, compilation_stats['total']))
        print('Number of YANG data models from {} that passed compilation: {}/{}'
              .format(args.prefix, compilation_stats['passed'], compilation_stats['total']))
        print('Number of YANG data models from {} that passed compilation with warnings: {}/{}'
              .format(args.prefix, compilation_stats['warnings'], compilation_stats['total']))
        print('Number of YANG data models from {} that failed compilation: {}/{}'
              .format(args.prefix, compilation_stats['failed'], compilation_stats['total']))

    custom_print('end of {} job for {}'.format(os.path.basename(__file__), args.prefix))

    # Update files content hashes and dump into .json file
    fileHasher.dump_hashed_files_list()


if __name__ == '__main__':
    main()
