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
from yangIetf import check_yangcatalog_data, push_to_confd

__author__ = 'Benoit Claise'
__copyright__ = "Copyright(c) 2015-2018, Cisco Systems, Inc.,  Copyright The IETF Trust 2019, All Rights Reserved"
__license__ = "Apache 2.0"
__email__ = "bclaise@cisco.com"


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


def dict_to_list(in_dict: dict):
    """
    Create a list out of compilation results from 'in_dict' dictionary variable.

    Argument:
        :param in_dict      (dict) Dictionary of modules with compilation results
        :return: List of compilation results
    """
    dictlist = []
    for key, value in in_dict.items():
        if value is not None:
            temp_list = [key]
            temp_list.extend(value)
            dictlist.append(temp_list)
    return dictlist


def list_br_html_addition(l: list):
    """
    Replace the /n by the <br> HTML tag throughout the list.

    Argument:
        :param l    (list) List of compilation results
    :return: updated list - <br> HTML tags added
    """
    for sublist in l:
        for i in range(len(sublist)):
            if isinstance(sublist[i], str):
                sublist[i] = sublist[i].replace('\n', '<br>')
    return l


def number_of_yang_modules_that_passed_compilation(in_dict: dict, position: int, compilation_condition: str):
    """
    Return the number of the modules that have compilation status equal to the 'compilation_condition'.

    Arguments:
        :param in_dict                  (dict) Dictionary of key:yang-model, value:list of compilation results
        :param position                 (int) Position in the list where the 'compilation_condidtion' is
        :param compilation_condition    (str) Compilation result we are looking for - PASSED, PASSED WITH WARNINGS, FAILED
    :return: the number of YANG models which meet the 'compilation_condition'
    """
    t = 0
    for k, v in in_dict.items():
        if in_dict[k][position - 1] == compilation_condition:
            t += 1
    return t


def combined_compilation(yang_file: str, result: dict):
    """
    Determine the combined compilation result based on individual compilation results from parsers.

    Arguments:
        :param yang_file        (str) Name of the yang files
        :param result           (dict) Dictionary of compilation results with following keys:
                                        pyang_lint, confdrc, yumadump, yanglint
    :return: the combined compilation result
    """
    if 'error' in result['pyang_lint']:
        compilation_pyang = 'FAILED'
    elif 'warning' in result['pyang_lint']:
        compilation_pyang = 'PASSED WITH WARNINGS'
    elif result['pyang_lint'] == '':
        compilation_pyang = 'PASSED'
    else:
        compilation_pyang = 'UNKNOWN'

    # logic for confdc compilation result:
    if 'error' in result['confdrc']:
        compilation_confd = 'FAILED'
    #   The following doesn't work. For example, ietf-diffserv@2016-06-15.yang, now PASSED (TBC):
    #     Error: 'ietf-diffserv@2016-06-15.yang' import of module 'ietf-qos-policy' failed
    #     ietf-diffserv@2016-06-15.yang:11.3: error(250): definition not found
    #   This issue is that an import module that fails => report the main module as FAILED
    #   Another issue with ietf-bgp-common-structure.yang
    elif 'warning' in result['confdrc']:
        compilation_confd = 'PASSED WITH WARNINGS'
    elif result['confdrc'] == '':
        compilation_confd = 'PASSED'
    else:
        compilation_confd = 'UNKNOWN'
    # 'cannot compile submodules; compile the module instead' error message
    # => still print the message, but doesn't report it as FAILED
    if 'error: cannot compile submodules; compile the module instead' in result['confdrc']:
        compilation_confd = 'PASSED'

    # logic for yumaworks compilation result:
    # remove the draft name from result_yuma
    if result['yumadump'] == '':
        compilation_yuma = 'PASSED'
    elif '0 Errors, 0 Warnings' in result['yumadump']:
        compilation_yuma = 'PASSED'
    elif 'Error' in result['yumadump'] and yang_file in result['yumadump'] and '0 Errors' not in result['yumadump']:
        # This is an approximation: if Error in an imported module, and warning on this current module
        # then it will report the module as FAILED
        # Solution: look at line by line comparision of Error and yang_file
        compilation_yuma = 'FAILED'
    elif 'Warning' in result['yumadump'] and yang_file in result['yumadump']:
        compilation_yuma = 'PASSED WITH WARNINGS'
    elif 'Warning' in result['yumadump'] and yang_file not in result['yumadump']:
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


def module_or_submodule(yang_file_path: str):
    """
    Try to find out if the given model is a submodule or a module.

    Argument:
        :param yang_file_path   (str) Full path to the yang model to check
    """
    if yang_file_path:
        file_input = open(yang_file_path, 'r', encoding='utf-8', errors='ignore')
        all_lines = file_input.readlines()
        file_input.close()
        commented_out = False
        for each_line in all_lines:
            module_position = each_line.find('module')
            submodule_position = each_line.find('submodule')
            cpos = each_line.find('//')
            if commented_out:
                mcpos = each_line.find('*/')
            else:
                mcpos = each_line.find('/*')
            if mcpos != -1 and cpos > mcpos:
                if commented_out:
                    commented_out = False
                else:
                    commented_out = True
            if submodule_position >= 0 and (submodule_position < cpos or cpos == -1) and not commented_out:
                return 'submodule'
            if module_position >= 0 and (module_position < cpos or cpos == -1) and not commented_out:
                return 'module'
        print('File {} not yang file or not well formated'.format(yang_file_path))
        return 'wrong file'
    else:
        return None


def get_timestamp_with_pid():
    return str(datetime.datetime.now().time()) + ' (' + str(os.getpid()) + '): '


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
if __name__ == "__main__":
    home = os.path.expanduser('~')
    config = create_config()
    api_ip = config.get('Web-Section', 'ip')
    protocol = config.get('General-Section', 'protocol-api')
    resutl_html_dir = config.get('Web-Section', 'result-html-dir')
    web_private = config.get('Web-Section', 'private-directory') + '/'
    modules_directory = config.get('Directory-Section', 'modules-directory')
    temp_dir = config.get('Directory-Section', 'temp')
    pyang_exec = config.get('Tool-Section', 'pyang-exec')
    confdc_exec = config.get('Tool-Section', 'confdc-exec')
    parser = argparse.ArgumentParser(
        description='YANG Document Processor: generate tables with compilation errors/warnings')
    parser.add_argument("--rootdir", default=".",
                        help="The root directory where to find the source YANG models. "
                             "Default is '.'")
    parser.add_argument("--binpath", default=home + "/bin/",
                        help="Optional directory where to find the "
                             "script executables. Default is '" + home + "/bin/'")
    parser.add_argument("--htmlpath", default=web_private,
                        help="The path to create the HTML file (optional). Default is '" + web_private + "'")
    parser.add_argument("--metadata", default="",
                        help="Metadata text (such as SDOs, github location, etc.) "
                             "to be displayed on the generated HTML page"
                             "Default is NULL")
    parser.add_argument("--lint", type=bool, default=False,
                        help="Optional flag that determines pyang syntax enforcement; "
                             "If set to 'True', pyang --lint is run"
                             "Otherwise, pyang --ietf is run"
                             "Default is False")
    parser.add_argument("--allinclusive", type=bool, default=False,
                        help="Optional flag that determines whether the rootdir directory contains all imported YANG modules; "
                             "If set to 'True', the YANG validators only look in the rootdir directory. "
                             "Otherwise, the YANG validators look in " + modules_directory + ". "
                                                                                             "Default is False")
    parser.add_argument("--prefix", default="", help="Prefix for generating HTML file name"
                                                     "Example: MEF, IEEEStandard, IEEEExperimental"
                                                     "Default is ''")
    parser.add_argument("--debug", type=int, default=0, help="Debug level; the default is 0")
    parser.add_argument("--forcecompilation", type=bool, default=False,
                        help="Optional flag that determines wheter compilation should be run "
                             "for all files even if they have not been changed "
                             "or even if the validators versions have not been changed.")
    args = parser.parse_args()
    print('{}Start of job in {}'.format(get_timestamp_with_pid(), args.rootdir), flush=True)

    # Get list of hashed files
    fileHasher = FileHasher()
    files_hashes = fileHasher.load_hashed_files_list()

    all_yang_catalog_metadata = {}
    prefix = '{}://{}'.format(protocol, api_ip)

    modules = {}
    try:
        with open('{}/all_modules_data.json'.format(temp_dir), 'r') as f:
            modules = json.load(f)
            print(get_timestamp_with_pid() + 'All the modules data loaded from JSON files', flush=True)
    except:
        modules = {}
    if modules == {}:
        modules = requests.get('{}/api/search/modules'.format(prefix)).json()
        print(get_timestamp_with_pid() + 'All the modules data loaded from API', flush=True)

    for mod in modules['module']:
        key = '{}@{}'.format(mod['name'], mod['revision'])
        all_yang_catalog_metadata[key] = mod
    yang_list = list_of_yang_modules_in_subdir(args.rootdir, args.debug)
    if args.debug > 0:
        print('yang_list content:\n{}'.format(yang_list))
    print(get_timestamp_with_pid() +
          'relevant files list built, {} modules found in {}'.format(len(yang_list), args.rootdir), flush=True)

    # YANG modules from drafts: PYANG validation, dictionary generation, dictionary inversion, and page generation
    dictionary = {}
    dictionary_no_submodules = {}
    updated_modules = []

    # Initialize parsers
    pyangParser = PyangParser(pyang_exec, modules_directory, args.debug)
    confdcParser = ConfdcParser(confdc_exec, modules_directory, args.debug)
    yumadumpProParser = YangdumpProParser(args.debug)
    yanglintParser = YanglintParser(modules_directory, args.debug)

    # Load compilation results from .json file, if any exists
    try:
        with open('{}/{}.json'.format(args.htmlpath, args.prefix), 'r') as f:
            dictionary_existing = json.load(f)
    except:
        dictionary_existing = {}

    updated_hashes = {}
    for yang_file in yang_list:
        yang_file_without_path = yang_file.split('/')[-1]
        yang_file_with_revision = get_name_with_revision(yang_file)
        file_hash = fileHasher.hash_file(yang_file)
        old_file_hash = files_hashes.get(yang_file, None)
        yang_file_compilation = dictionary_existing.get(yang_file_with_revision, None)

        if old_file_hash is None or old_file_hash != file_hash or args.forcecompilation or yang_file_compilation is None:
            compilation = ''
            result_pyang = pyangParser.run_pyang_lint(args.rootdir, yang_file, args.lint, args.allinclusive, True)
            result_no_pyang_param = pyangParser.run_pyang_lint(args.rootdir, yang_file, args.lint, args.allinclusive, False)
            result_confd = confdcParser.run_confdc(yang_file, args.rootdir, args.allinclusive)
            result_yuma = yumadumpProParser.run_yumadumppro(yang_file, args.rootdir, args.allinclusive)
            # if want to populate the document location from Github, must uncomment the following 3 lines
            # the difficulty: find back the exact Github location, while everything is already copied in my local
            # directories: maybe Carl's catalog service will help
            # draft_name = yang_file
            # draft_name = "https://github.com/MEF-GIT/YANG-public/tree/master/src/model/draft" + yang_file
            # draft_name_url = '<a href="' + draft_name + '">' + yang_file + '</a>'
            result_yanglint = yanglintParser.run_yanglint(yang_file, args.rootdir, args.allinclusive)

            # if want to populate the document location from github, must uncomment the following line
            # dictionary[yang_file] = (draft_name_url, compilation, result, result_no_pyang_param)

            # If we are parsing RFCStandard
            ietf = 'ietf-rfc' if '/YANG-rfc' in yang_file else None

            result = {
                'pyang_lint': result_pyang,
                'pyang': result_no_pyang_param,
                'confdrc': result_confd,
                'yumadump': result_yuma,
                'yanglint': result_yanglint
            }
            compilation = combined_compilation(yang_file, result)
            updated_modules.extend(
                check_yangcatalog_data(pyang_exec, args.rootdir, resutl_html_dir, yang_file_without_path, None, None, None, compilation,
                                       result, all_yang_catalog_metadata, prefix, ietf))

            yang_file_compilation = [
                compilation, result_pyang, result_no_pyang_param, result_confd, result_yuma, result_yanglint]
            # Do not store hash if compilation result is 'UNKNOWN' -> try to parse model again next time
            if compilation != 'UNKNOWN':
                updated_hashes[yang_file] = file_hash

        if yang_file_with_revision != '':
            dictionary[yang_file_with_revision] = yang_file_compilation
            if module_or_submodule(yang_file) == 'module':
                dictionary_no_submodules[yang_file_with_revision] = yang_file_compilation

    print(get_timestamp_with_pid() + 'all modules compiled/validated', flush=True)

    # Make a list out of the no-submodules dictionary
    sorted_modules_list = sorted(dict_to_list(dictionary_no_submodules))
    # Replace CR by the BR HTML tag
    sorted_modules_list_br_tags = list_br_html_addition(sorted_modules_list)

    filesGenerator = FilesGenerator(args.htmlpath)
    filesGenerator.write_dictionary(dictionary, args.prefix)
    headers = filesGenerator.getYANGPageCompilationHeaders(args.lint)
    filesGenerator.generateYANGPageCompilationHTML(sorted_modules_list_br_tags, headers, args.prefix, args.metadata)

    # Generate modules compilation results statistics HTML page
    passed = number_of_yang_modules_that_passed_compilation(dictionary, 1, 'PASSED')
    passed_with_warnings = number_of_yang_modules_that_passed_compilation(dictionary, 1, 'PASSED WITH WARNINGS')
    total_number = len(yang_list)
    failed = total_number - passed - passed_with_warnings
    compilation_stats = {'passed': passed,
                         'warnings': passed_with_warnings,
                         'total': total_number,
                         'failed': failed
                         }
    filesGenerator.generateYANGPageMainHTML(args.prefix, compilation_stats)

    with FileLock('{}/stats/stats.json.lock'.format(args.htmlpath)):
        counter = 5
        while True:
            try:
                if not os.path.exists('{}/stats/AllYANGPageMain.json'.format(args.htmlpath)):
                    with open('{}/stats/AllYANGPageMain.json'.format(args.htmlpath), 'w') as f:
                        f.write('{}')
                with open('{}/stats/AllYANGPageMain.json'.format(args.htmlpath), 'r') as f:
                    stats = json.load(f)
                    stats[args.prefix] = compilation_stats
                with open('{}/stats/AllYANGPageMain.json'.format(args.htmlpath), 'w') as f:
                    json.dump(stats, f)
                break
            except:
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

    print('{}end of yangGeneric.py job for {}'.format(get_timestamp_with_pid(), args.prefix), flush=True)

    # Update files content hashes and dump into .json file
    if len(updated_hashes) > 0:
        fileHasher.dump_hashed_files_list(updated_hashes)
