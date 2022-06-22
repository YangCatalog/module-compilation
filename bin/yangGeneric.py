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

from create_config import create_config
from fileHasher import FileHasher
from filesGenerator import FilesGenerator
from parsers.confdcParser import ConfdcParser
from parsers.pyangParser import PyangParser
from parsers.yangdumpProParser import YangdumpProParser
from parsers.yanglintParser import YanglintParser
from utility.utility import (check_yangcatalog_data, dict_to_list,
                             list_br_html_addition, module_or_submodule,
                             number_that_passed_compilation, push_to_confd)
from versions import ValidatorsVersions

__author__ = 'Benoit Claise'
__copyright__ = 'Copyright(c) 2015-2018, Cisco Systems, Inc.,  Copyright The IETF Trust 2019, All Rights Reserved'
__license__ = 'Apache License, Version 2.0'
__email__ = 'bclaise@cisco.com'

# ----------------------------------------------------------------------
# Validators versions
# ----------------------------------------------------------------------
validators_versions = ValidatorsVersions()
versions = validators_versions.get_versions()

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


def combined_compilation(yang_file_name: str, result: dict):
    """
    Determine the combined compilation result based on individual compilation results from parsers.

    Arguments:
        :param yang_file_name   (str) Name of the yang file
        :param result           (dict) Dictionary of compilation results with following keys:
                                        pyang_lint, confdrc, yumadump, yanglint
    :return: the combined compilation result
    """
    if 'error:' in result['pyang_lint']:
        compilation_pyang = 'FAILED'
    elif 'warning:' in result['pyang_lint']:
        compilation_pyang = 'PASSED WITH WARNINGS'
    elif result['pyang_lint'] == '':
        compilation_pyang = 'PASSED'
    else:
        compilation_pyang = 'UNKNOWN'

    # logic for confdc compilation result:
    if 'error:' in result['confdrc']:
        compilation_confd = 'FAILED'
    #   The following doesn't work. For example, ietf-diffserv@2016-06-15.yang, now PASSED (TBC):
    #     Error: 'ietf-diffserv@2016-06-15.yang' import of module 'ietf-qos-policy' failed
    #     ietf-diffserv@2016-06-15.yang:11.3: error(250): definition not found
    #   This issue is that an import module that fails => report the main module as FAILED
    #   Another issue with ietf-bgp-common-structure.yang
    elif 'warning:' in result['confdrc']:
        compilation_confd = 'PASSED WITH WARNINGS'
    elif result['confdrc'] == '':
        compilation_confd = 'PASSED'
    else:
        compilation_confd = 'UNKNOWN'
    # 'cannot compile submodules; compile the module instead' error message
    # => still print the message, but doesn't report it as FAILED
    if 'error: cannot compile submodules; compile the module instead' in result['confdrc']:
        compilation_confd = 'PASSED'

    # logic for yumadump-pro compilation result:
    if result['yumadump'] == '':
        compilation_yuma = 'PASSED'
    elif '0 Errors, 0 Warnings' in result['yumadump']:
        compilation_yuma = 'PASSED'
    elif 'Error' in result['yumadump'] and yang_file_name in result['yumadump'] and '0 Errors' not in result['yumadump']:
        # This is an approximation: if Error in an imported module, and warning on this current module
        # then it will report the module as FAILED
        # Solution: look at line by line comparision of Error and yang_file_name
        compilation_yuma = 'FAILED'
    elif 'Warning:' in result['yumadump'] and yang_file_name in result['yumadump']:
        compilation_yuma = 'PASSED WITH WARNINGS'
    elif 'Warning:' in result['yumadump'] and yang_file_name not in result['yumadump']:
        compilation_yuma = 'PASSED'
    else:
        compilation_yuma = 'UNKNOWN'

    # logic for yanglint compilation result:
    if 'err :' in result['yanglint']:
        compilation_yanglint = 'FAILED'
    elif 'warn:' in result['yanglint']:
        compilation_yanglint = 'PASSED WITH WARNINGS'
    elif result['yanglint'] == '':
        compilation_yanglint = 'PASSED'
    else:
        compilation_yanglint = 'UNKNOWN'
    # 'err : Input data contains submodule which cannot be parsed directly without its main module.' error message
    # => still print the message, but doesn't report it as FAILED
    if 'err : Input data contains submodule which cannot be parsed directly without its main module.' in result['yanglint']:
        compilation_yanglint = 'PASSED'

    # determine the combined compilation status, based on the different compilers
    compilation_list = [compilation_pyang, compilation_confd, compilation_yuma, compilation_yanglint]
    if 'FAILED' in compilation_list:
        compilation = 'FAILED'
    elif 'PASSED WITH WARNINGS' in compilation_list:
        compilation = 'PASSED WITH WARNINGS'
    elif compilation_list == ['PASSED', 'PASSED', 'PASSED', 'PASSED']:
        compilation = 'PASSED'
    else:
        compilation = 'UNKNOWN'

    return compilation


def get_mod_rev(module):
    mname = ''
    mrev = ''

    with open(module, 'r', encoding='utf-8', errors='ignore') as ym:
        for line in ym:
            if mname != '' and mrev != '':
                return mname + '@' + mrev

            if mname == '':
                m = re.search(r'^\s*(sub)?module\s+([\w\-\d]+)', line)
                if m:
                    mname = m.group(2).strip()
                    continue

            if mrev == '':
                m = re.search(r'^\s*revision\s+"?([\d\-]+)"?', line)
                if m:
                    mrev = m.group(1).strip()
                    continue

    if mrev == '':
        return mname
    else:
        return mname + '@' + mrev


def custom_print(message: str):
    timestamp = '{} ({}):'.format(datetime.datetime.now().time(), os.getpid())
    print('{} {}'.format(timestamp, message), flush=True)


def get_name_with_revision(yang_file: str):
    yang_file_without_path = yang_file.split('/')[-1]
    out = get_mod_rev(yang_file)

    if out.rstrip():
        # Add the @revision to the yang_file if not present
        if '@' in yang_file and '.yang' in yang_file:
            new_yang_file_without_path_with_revision = out.rstrip() + '.yang'
            if new_yang_file_without_path_with_revision.split('@')[0] != yang_file_without_path.split('@')[0]:
                print(
                    'Name of the YANG file ' + yang_file_without_path + ' is wrong changing to correct one into ' + new_yang_file_without_path_with_revision,
                    flush=True)
                yang_file_without_path = new_yang_file_without_path_with_revision
            if new_yang_file_without_path_with_revision.split('@')[1].split('.')[0] != \
                    yang_file_without_path.split('@')[1].split('.')[0]:
                print(
                    'Revision of the YANG file ' + yang_file_without_path + ' is wrong changing to correct as ' + new_yang_file_without_path_with_revision,
                    flush=True)
                yang_file_without_path = new_yang_file_without_path_with_revision

            return yang_file_without_path
        else:
            new_yang_file_without_path_with_revision = out.rstrip() + '.yang'
            if args.debug > 0:
                print(
                    "DEBUG: Adding the revision to YANG module because xym can't get revision(missing from the YANG module): " + yang_file)
                print('DEBUG:  out: ' + new_yang_file_without_path_with_revision)

            return new_yang_file_without_path_with_revision
    else:
        print('Unable to get name@revision out of ' + yang_file + ' - no output', flush=True)

    return ''


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
if __name__ == '__main__':
    config = create_config()
    yangcatalog_api_prefix = config.get('Web-Section', 'yangcatalog-api-prefix')
    resutl_html_dir = config.get('Web-Section', 'result-html-dir')
    web_private = config.get('Web-Section', 'private-directory') + '/'
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
                             'If set to "True", pyang --lint is run. '
                             'Otherwise, pyang --ietf is run. '
                             'Default is False',
                        action='store_true',
                        default=False)
    parser.add_argument('--allinclusive',
                        help='Optional flag that determines whether the rootdir directory '
                             'contains all imported YANG modules; '
                             'If set to "True", the YANG validators will only look in the rootdir directory. '
                             'Otherwise, the YANG validators look in {}. '
                             'Default is False'.format(modules_directory),
                        type=bool,
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
                        type=bool,
                        default=False)
    args = parser.parse_args()
    custom_print('Start of job in {}'.format(args.rootdir))

    # Get list of hashed files
    fileHasher = FileHasher(args.forcecompilation)

    all_yang_catalog_metadata = {}
    modules = {}
    try:
        with open(os.path.join(temp_dir, 'all_modules_data.json'), 'r') as f:
            modules = json.load(f)
            custom_print('All the modules data loaded from JSON files')
    except Exception:
        modules = {}
    if modules == {}:
        modules = requests.get('{}/search/modules'.format(yangcatalog_api_prefix)).json()
        custom_print('All the modules data loaded from API')

    for mod in modules['module']:
        key = '{}@{}'.format(mod['name'], mod['revision'])
        all_yang_catalog_metadata[key] = mod
    yang_list = list_of_yang_modules_in_subdir(args.rootdir, args.debug)
    if args.debug > 0:
        print('yang_list content:\n{}'.format(yang_list))
    custom_print('relevant files list built, {} modules found in {}'.format(len(yang_list), args.rootdir))

    # YANG modules from drafts: PYANG validation, dictionary generation, dictionary inversion, and page generation
    dictionary = {}
    dictionary_no_submodules = {}
    updated_modules = []

    # Initialize parsers
    pyangParser = PyangParser(args.debug)
    confdcParser = ConfdcParser(args.debug)
    yumadumpProParser = YangdumpProParser(args.debug)
    yanglintParser = YanglintParser(args.debug)

    # Load compilation results from .json file, if any exists
    try:
        with open('{}/{}.json'.format(web_private, args.prefix), 'r') as f:
            dictionary_existing = json.load(f)
    except Exception:
        dictionary_existing = {}

    updated_hashes = {}
    for yang_file in yang_list:
        yang_file_without_path = yang_file.split('/')[-1]
        yang_file_with_revision = get_name_with_revision(yang_file)
        should_parse, file_hash = fileHasher.should_parse(yang_file)
        yang_file_compilation = dictionary_existing.get(yang_file_with_revision, None)

        if should_parse or yang_file_compilation is None:
            result_pyang = pyangParser.run_pyang_lint(args.rootdir, yang_file, args.lint, args.allinclusive, True)
            result_no_pyang_param = pyangParser.run_pyang_lint(args.rootdir, yang_file, args.lint, args.allinclusive, False)
            result_confd = confdcParser.run_confdc(yang_file, args.rootdir, args.allinclusive)
            result_yuma = yumadumpProParser.run_yumadumppro(yang_file, args.rootdir, args.allinclusive)
            result_yanglint = yanglintParser.run_yanglint(yang_file, args.rootdir, args.allinclusive)
            document_name = None
            mailto = None
            datatracker_url = None
            # If we are parsing RFCStandard
            ietf = 'ietf-rfc' if '/YANG-rfc' in yang_file else None
            is_rfc = os.path.isfile('{}/YANG-rfc/{}'.format(ietf_directory, yang_file_with_revision))
            compilation_results = {
                'pyang_lint': result_pyang,
                'pyang': result_no_pyang_param,
                'confdrc': result_confd,
                'yumadump': result_yuma,
                'yanglint': result_yanglint
            }
            compilation_status = combined_compilation(yang_file_without_path, compilation_results)
            updated_modules.extend(
                check_yangcatalog_data(config, yang_file, datatracker_url, document_name, mailto,
                                       compilation_status, compilation_results, all_yang_catalog_metadata, is_rfc,
                                       versions, ietf))
            yang_file_compilation = [
                compilation_status, result_pyang, result_no_pyang_param, result_confd, result_yuma, result_yanglint]
            if len(updated_modules) > 100:
                updated_modules = push_to_confd(updated_modules, config)

            # Do not store hash if compilation_status is 'UNKNOWN' -> try to parse model again next time
            if compilation_status != 'UNKNOWN':
                fileHasher.updated_hashes[yang_file] = file_hash

        if yang_file_with_revision != '':
            dictionary[yang_file_with_revision] = yang_file_compilation
            if module_or_submodule(yang_file) == 'module':
                dictionary_no_submodules[yang_file_with_revision] = yang_file_compilation

    custom_print('all modules compiled/validated')

    # Make a list out of the no-submodules dictionary
    sorted_modules_list = sorted(dict_to_list(dictionary_no_submodules))
    # Replace CR by the BR HTML tag
    sorted_modules_list_br_tags = list_br_html_addition(sorted_modules_list)

    filesGenerator = FilesGenerator(web_private)
    filesGenerator.write_dictionary(dictionary, args.prefix)
    headers = filesGenerator.getYANGPageCompilationHeaders(args.lint)
    filesGenerator.generateYANGPageCompilationHTML(sorted_modules_list_br_tags, headers, args.prefix, args.metadata)

    # Generate modules compilation results statistics HTML page
    passed = number_that_passed_compilation(dictionary, 0, 'PASSED')
    passed_with_warnings = number_that_passed_compilation(dictionary, 0, 'PASSED WITH WARNINGS')
    total_number = len(yang_list)
    failed = total_number - passed - passed_with_warnings
    compilation_stats = {'passed': passed,
                         'warnings': passed_with_warnings,
                         'total': total_number,
                         'failed': failed
                         }
    filesGenerator.generateYANGPageMainHTML(args.prefix, compilation_stats)

    with FileLock('{}/stats/stats.json.lock'.format(web_private)):
        stats_file_path = os.path.join(web_private, 'stats/AllYANGPageMain.json')
        counter = 5
        while True:
            try:
                if not os.path.exists(stats_file_path):
                    with open(stats_file_path, 'w') as f:
                        f.write('{}')
                with open(stats_file_path, 'r') as f:
                    stats = json.load(f)
                    stats[args.prefix] = compilation_stats
                with open(stats_file_path, 'w') as f:
                    json.dump(stats, f)
                break
            except Exception:
                counter = counter - 1
                if counter == 0:
                    break

    push_to_confd(updated_modules, config)

    # Print the summary of the compilation results
    print('--------------------------')
    print('Number of YANG data models from {}: {}'.format(args.prefix, total_number))
    print('Number of YANG data models from {} that passed compilation: {}/{}'.format(args.prefix, passed, total_number))
    print('Number of YANG data models from {} that passed compilation with warnings: {}/{}'.format(args.prefix, passed_with_warnings, total_number))
    print('Number of YANG data models from {} that failed compilation: {}/{}'.format(args.prefix, failed, total_number))

    custom_print('end of yangGeneric.py job for {}'.format(args.prefix))

    # Update files content hashes and dump into .json file
    if len(fileHasher.updated_hashes) > 0:
        fileHasher.dump_hashed_files_list(fileHasher.updated_hashes)
