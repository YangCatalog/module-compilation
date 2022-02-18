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
import time
from operator import itemgetter

import jinja2
import requests

from compilators.draftsCompilator import DraftsCompilator
from compilators.examplesCompilator import ExamplesCompilator
from compilators.rfcsCompilator import RfcsCompilator
from create_config import create_config
from extract_emails import extract_email_string
from extractors.dratfExtractor import DraftExtractor
from extractors.rfcExtractor import RFCExtractor
from fileHasher import FileHasher
from filesGenerator import FilesGenerator
from parsers.confdcParser import ConfdcParser
from parsers.pyangParser import PyangParser
from parsers.yangdumpProParser import YangdumpProParser
from parsers.yanglintParser import YanglintParser
from remove_directory_content import remove_directory_content
from utility.utility import dict_to_list, list_br_html_addition
from versions import ValidatorsVersions

# ----------------------------------------------------------------------
# Validators versions
# ----------------------------------------------------------------------
validators_versions = ValidatorsVersions()
versions = validators_versions.get_versions()


# ----------------------------------------------------------------------
# Functions
# ----------------------------------------------------------------------


def number_of_yang_modules_that_passed_compilation(in_dict: dict, compilation_condition: str):
    """
    Return the number of the modules that have compilation status equal to the 'compilation_condition'.

    Arguments:
        :param in_dict                  (dict) Dictionary of key:yang-model, value:list of compilation results
        :param compilation_condition    (str) Compilation result we are looking for - PASSED, PASSED WITH WARNINGS, FAILED
    :return: the number of YANG models which meet the 'compilation_condition'
    """
    t = 0
    for k, v in in_dict.items():
        if in_dict[k][3] == compilation_condition:
            t += 1
    return t


def combined_compilation(yang_file: str, result: dict):
    """
    Determine the combined compilation result based on individual compilation results from parsers.

    Arguments:
        :param yang_file    (str) Name of the yang files
        :param result       (dict) Dictionary of compilation results with following keys:
                                    pyang_lint, pyang, confdrc, yumadump, yanglint
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

    # logic for pyang compilation result:
    if 'error:' in result['pyang']:
        compilation_pyang_no_ietf = 'FAILED'
    elif 'warning:' in result['pyang']:
        compilation_pyang_no_ietf = 'PASSED WITH WARNINGS'
    elif result['pyang'] == '':
        compilation_pyang_no_ietf = 'PASSED'
    else:
        compilation_pyang_no_ietf = 'UNKNOWN'

    # logic for confdc compilation result:
    # if 'error' in result['confdrc'] and yang_file in result['confdrc']:
    if 'error:' in result['confdrc']:
        compilation_confd = 'FAILED'
    #   The following doesn't work. For example, ietf-diffserv@2016-06-15.yang, now PASSED (TBC):
    #     Error: 'ietf-diffserv@2016-06-15.yang' import of module 'ietf-qos-policy' failed
    #     ietf-diffserv@2016-06-15.yang:11.3: error(250): definition not found
    #   This issue is that an import module that fails => report the main module as FAILED
    #   Another issue with ietf-bgp-common-structure.yang
    # If the error is on the module itself, then, that's an error
    elif 'warning:' in result['confdrc']:
        compilation_confd = 'PASSED WITH WARNINGS'
    elif result['confdrc'] == '':
        compilation_confd = 'PASSED'
    else:
        compilation_confd = 'UNKNOWN'
    # 'cannot compile submodules; compile the module instead' error  message
    # => still print the message, but doesn't report it as FAILED
    if 'error: cannot compile submodules; compile the module instead' in result['confdrc']:
        compilation_confd = 'PASSED'

    # logic for yumadump-pro compilation result:
    if result['yumadump'] == '':
        compilation_yuma = 'PASSED'
    elif '0 Errors, 0 Warnings' in result['yumadump']:
        compilation_yuma = 'PASSED'
    elif 'Error' in result['yumadump'] and yang_file in result['yumadump'] and '0 Errors' not in result['yumadump']:
        # This is an approximation: if Error in an imported module, and warning on this current module
        # then it will report the module as FAILED
        # Solution: look at line by line comparision of Error and yang_file
        compilation_yuma = 'FAILED'
    elif 'Warning:' in result['yumadump'] and yang_file in result['yumadump']:
        compilation_yuma = 'PASSED WITH WARNINGS'
    elif 'Warning:' in result['yumadump'] and yang_file not in result['yumadump']:
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
    # 'err : Input data contains submodule which cannot be parsed directly without its main module.' error  message
    # => still print the message, but doesn't report it as FAILED
    if 'err : Input data contains submodule which cannot be parsed directly without its main module.' in result['yanglint']:
        compilation_yanglint = 'PASSED'

    # determine the combined compilation status, based on the different compilers
    compilation_list = [compilation_pyang, compilation_pyang_no_ietf, compilation_confd, compilation_yuma,
                        compilation_yanglint]
    if 'FAILED' in compilation_list:
        compilation = 'FAILED'
    elif 'PASSED WITH WARNINGS' in compilation_list:
        compilation = 'PASSED WITH WARNINGS'
    elif compilation_list == ['PASSED', 'PASSED', 'PASSED', 'PASSED', 'PASSED']:
        compilation = 'PASSED'
    else:
        compilation = 'UNKNOWN'

    return compilation


def check_yangcatalog_data(pyang_exec, yang_path, resutl_html_dir, yang_file, datatracker_url, document_name, email, compilation,
                           result, all_modules, prefix, is_rfc, ietf=None):
    def __resolve_maturity_level():
        if ietf == 'ietf-rfc':
            return 'ratified'
        elif ietf in ['ietf-draft', 'ietf-example']:
            maturity_level = document_name.split('-')[1]
            if 'ietf' in maturity_level:
                return 'adopted'
            else:
                return 'initial'
        else:
            return 'not-applicable'

    def __resolve_working_group():
        IETF_RFC_MAP = {
            "iana-crypt-hash@2014-08-06.yang": "NETMOD",
            "iana-if-type@2014-05-08.yang": "NETMOD",
            "ietf-complex-types@2011-03-15.yang": "N/A",
            "ietf-inet-types@2010-09-24.yang": "NETMOD",
            "ietf-inet-types@2013-07-15.yang": "NETMOD",
            "ietf-interfaces@2014-05-08.yang": "NETMOD",
            "ietf-ip@2014-06-16.yang": "NETMOD",
            "ietf-ipfix-psamp@2012-09-05.yang": "IPFIX",
            "ietf-ipv4-unicast-routing@2016-11-04.yang": "NETMOD",
            "ietf-ipv6-router-advertisements@2016-11-04.yang": "NETMOD",
            "ietf-ipv6-unicast-routing@2016-11-04.yang": "NETMOD",
            "ietf-key-chain@2017-06-15.yang": "RTGWG",
            "ietf-l3vpn-svc@2017-01-27.yang": "L3SM",
            "ietf-lmap-common@2017-08-08.yang": "LMAP",
            "ietf-lmap-control@2017-08-08.yang": "LMAP",
            "ietf-lmap-report@2017-08-08.yang": "LMAP",
            "ietf-netconf-acm@2012-02-22.yang": "NETCONF",
            "ietf-netconf-monitoring@2010-10-04.yang": "NETCONF",
            "ietf-netconf-notifications@2012-02-06.yang": "NETCONF",
            "ietf-netconf-partial-lock@2009-10-19.yang": "NETCONF",
            "ietf-netconf-time@2016-01-26.yang": "N/A",
            "ietf-netconf-with-defaults@2011-06-01.yang": "NETCONF",
            "ietf-netconf@2011-06-01.yang": "NETCONF",
            "ietf-restconf-monitoring@2017-01-26.yang": "NETCONF",
            "ietf-restconf@2017-01-26.yang": "NETCONF",
            "ietf-routing@2016-11-04.yang": "NETMOD",
            "ietf-snmp-common@2014-12-10.yang": "NETMOD",
            "ietf-snmp-community@2014-12-10.yang": "NETMOD",
            "ietf-snmp-engine@2014-12-10.yang": "NETMOD",
            "ietf-snmp-notification@2014-12-10.yang": "NETMOD",
            "ietf-snmp-proxy@2014-12-10.yang": "NETMOD",
            "ietf-snmp-ssh@2014-12-10.yang": "NETMOD",
            "ietf-snmp-target@2014-12-10.yang": "NETMOD",
            "ietf-snmp-tls@2014-12-10.yang": "NETMOD",
            "ietf-snmp-tsm@2014-12-10.yang": "NETMOD",
            "ietf-snmp-usm@2014-12-10.yang": "NETMOD",
            "ietf-snmp-vacm@2014-12-10.yang": "NETMOD",
            "ietf-snmp@2014-12-10.yang": "NETMOD",
            "ietf-system@2014-08-06.yang": "NETMOD",
            "ietf-template@2010-05-18.yang": "NETMOD",
            "ietf-x509-cert-to-name@2014-12-10.yang": "NETMOD",
            "ietf-yang-library@2016-06-21.yang": "NETCONF",
            "ietf-yang-metadata@2016-08-05.yang": "NETMOD",
            "ietf-yang-patch@2017-02-22.yang": "NETCONF",
            "ietf-yang-smiv2@2012-06-22.yang": "NETMOD",
            "ietf-yang-types@2010-09-24.yang": "NETMOD",
            "ietf-yang-types@2013-07-15.yang": "NETMOD"
        }
        if ietf == 'ietf-rfc':
            return IETF_RFC_MAP.get('{}.yang'.format(name_revision))
        else:
            return document_name.split('-')[2]

    updated_modules = []
    pyang_module = os.path.join(yang_path, yang_file)
    found = False
    for root, _, files in os.walk(yang_path):
        if found:
            break
        for ff in files:
            if ff == yang_file:
                pyang_module = os.path.join(root, ff)
                found = True
            if found:
                break
    if not found:
        print('Error: file {} not found in dir or subdir of {}'.format(yang_file, yang_path))
    name_revision_command = '{} -fname --name-print-revision --path="$MODULES" {} 2> /dev/null'.format(pyang_exec, pyang_module)
    name_revision = os.popen(name_revision_command).read().rstrip().split(' ')[0]
    if '@' not in name_revision:
        name_revision += '@1970-01-01'
    if name_revision in all_modules:
        module_data = all_modules[name_revision].copy()
        update = False
        if module_data.get('document-name') != document_name and document_name is not None and document_name != '':
            update = True
            module_data['document-name'] = document_name

        if module_data.get('reference') != datatracker_url and datatracker_url is not None and datatracker_url != '':
            update = True
            module_data['reference'] = datatracker_url

        if module_data.get('author-email') != email and email is not None and email != '':
            update = True
            module_data['author-email'] = email

        if compilation is not None and compilation != '' and module_data.get(
                'compilation-status') != compilation.lower().replace(' ', '-'):
            # Module parsed with --ietf flag (= RFC) has higher priority
            if is_rfc:
                if ietf is not None:
                    update = True
                    module_data['compilation-status'] = compilation.lower().replace(' ', '-')
            else:
                update = True
                module_data['compilation-status'] = compilation.lower().replace(' ', '-')

        if compilation is not None:

            def render(tpl_path, context):
                """Render jinja html template
                    Arguments:
                        :param tpl_path: (str) path to a file
                        :param context: (dict) dictionary containing data to render jinja
                            template file
                        :return: string containing rendered html file
                """

                path, filename = os.path.split(tpl_path)
                return jinja2.Environment(
                    loader=jinja2.FileSystemLoader(path or './')
                ).get_template(filename).render(context)

            name = module_data['name']
            rev = module_data['revision']
            org = module_data['organization']
            file_url = '{}@{}_{}.html'.format(name, rev, org)
            result['name'] = name
            result['revision'] = rev
            result['generated'] = time.strftime('%d/%m/%Y')

            ths = list()
            option = '--lint'
            if ietf is not None:
                option = '--ietf'
            ths.append('Compilation Results (pyang {}). {}'.format(option, versions.get('pyang_version')))
            ths.append('Compilation Results (pyang). Note: also generates errors for imported files. {}'.format(
                versions.get('pyang_version')))
            ths.append('Compilation Results (confdc). Note: also generates errors for imported files. {}'.format(
                versions.get('confd_version')))
            ths.append('Compilation Results (yangdump-pro). Note: also generates errors for imported files. {}'.format(
                versions.get('yangdump_version')))
            ths.append(
                'Compilation Results (yanglint -i). Note: also generates errors for imported files. {}'.format(
                    versions.get('yanglint_version')))

            context = {'result': result,
                       'ths': ths}
            template = os.path.dirname(os.path.realpath(__file__)) + '/resources/compilationStatusTemplate.html'
            rendered_html = render(template, context)
            result_html_file = os.path.join(resutl_html_dir, file_url)
            if os.path.isfile(result_html_file):
                with open(result_html_file, 'r', encoding='utf-8') as f:
                    existing_output = f.read()
                if existing_output != rendered_html:
                    if is_rfc:
                        if ietf is not None:
                            with open(result_html_file, 'w', encoding='utf-8') as f:
                                f.write(rendered_html)
                            os.chmod(result_html_file, 0o664)
                    else:
                        with open(result_html_file, 'w', encoding='utf-8') as f:
                            f.write(rendered_html)
                        os.chmod(result_html_file, 0o664)
            else:
                with open(result_html_file, 'w', encoding='utf-8') as f:
                    f.write(rendered_html)
                os.chmod(result_html_file, 0o664)
            if module_data.get('compilation-status') == 'unknown':
                comp_result = ''
            else:
                comp_result = '{}/results/{}'.format(prefix, file_url)
            if module_data.get('compilation-result') != comp_result:
                update = True
                module_data['compilation-result'] = comp_result

        if ietf is not None and module_data.get('organization') == 'ietf':
            wg = __resolve_working_group()
            if (module_data.get('ietf') is None or module_data['ietf']['ietf-wg'] != wg) and wg is not None:
                update = True
                module_data['ietf'] = {}
                module_data['ietf']['ietf-wg'] = wg

        mat_level = __resolve_maturity_level()
        if module_data.get('maturity-level') != mat_level:
            if mat_level == 'not-applicable':
                if module_data.get('maturity-level') is None or module_data.get('maturity-level') == '':
                    update = True
                    module_data['maturity-level'] = mat_level
            else:
                update = True
                module_data['maturity-level'] = mat_level

        if update:
            updated_modules.append(module_data)
            print('DEBUG: updated_modules: {}'.format(name_revision))
    else:
        print('WARN: {} not in confd yet'.format(name_revision))
    return updated_modules


def custom_print(message: str):
    timestamp = '{} ({}):'.format(datetime.datetime.now().time(), os.getpid())
    print('{} {}'.format(timestamp, message), flush=True)


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
if __name__ == '__main__':
    home = os.path.expanduser('~')
    config = create_config()
    web_url = config.get('Web-Section', 'my-uri')
    web_private = config.get('Web-Section', 'private-directory')

    ietf_directory = config.get('Directory-Section', 'ietf-directory')
    temp_dir = config.get('Directory-Section', 'temp')
    modules_directory = config.get('Directory-Section', 'modules-directory')
    pyang_exec = config.get('Tool-Section', 'pyang-exec')
    confdc_exec = config.get('Tool-Section', 'confdc-exec')

    api_ip = config.get('Web-Section', 'ip')
    protocol = config.get('General-Section', 'protocol-api')
    resutl_html_dir = config.get('Web-Section', 'result-html-dir')

    parser = argparse.ArgumentParser(description='YANG RFC/Draft Processor')
    parser.add_argument("--draftpath", default=ietf_directory + "/my-id-mirror/",
                        help="The optional directory where to find the source drafts. "
                             "Default is '" + ietf_directory + "/my-id-mirror/' but could also be '" + ietf_directory + "/my-id-archive-mirror/' to get expired drafts as well")
    parser.add_argument("--rfcpath", default=ietf_directory + "/rfc/",
                        help="The optional directory where to find the source RFCs. Default is '" + ietf_directory + "/rfc/'")
    parser.add_argument("--binpath", default=home + "/bin/", help="Optional directory where to find the "
                                                                  "script executables. Default is '" + home + "/bin/'")
    parser.add_argument("--htmlpath", default=web_private + '/',
                        help="The path to create the HTML file (optional). Default is '" + web_private + "/'")
    parser.add_argument("--yangpath", default=ietf_directory + "/YANG/", help="The optional directory where to put the "
                                                                              "correctly extracted models. "
                                                                              "Default is " + ietf_directory + "'/YANG/'")
    parser.add_argument("--allyangpath", default=ietf_directory + "/YANG-all/",
                        help="The optional directory where to store "
                             "all extracted models (including bad ones). "
                             " Default is '" + ietf_directory + "/YANG-all/'")
    parser.add_argument("--allyangexamplepath", default=ietf_directory + "/YANG-example/",
                        help="The optional directory where to store "
                             "all extracted example models (starting with example- and not with CODE BEGINS/END). "
                             " Default is '" + ietf_directory + "/YANG-example/'")
    parser.add_argument("--yangexampleoldrfcpath", default=ietf_directory + "/YANG-example-old-rfc/",
                        help="The optional directory where to store "
                             "the hardcoded YANG module example models from old RFCs (not starting with example-). "
                             " Default is '" + ietf_directory + "/YANG-example-old-rfc/'")
    parser.add_argument("--allyangdraftpathstrict", default=ietf_directory + "/draft-with-YANG-strict/",
                        help="The optional directory where to store "
                             "all drafts containing YANG model(s), with strict xym rule = True. "
                             " Default is '" + ietf_directory + "/draft-with-YANG-strict/'")
    parser.add_argument("--allyangdraftpathnostrict", default=ietf_directory + "/draft-with-YANG-no-strict/",
                        help="The optional directory where to store "
                             "all drafts containing YANG model(s), with strict xym rule = False. "
                             " Default is '" + ietf_directory + "/draft-with-YANG-no-strict/'")
    parser.add_argument("--allyangdraftpathonlyexample", default=ietf_directory + "/draft-with-YANG-example/",
                        help="The optional directory where to store "
                             "all drafts containing YANG model(s) with examples,"
                             "with strict xym rule = True, and strictexample True. "
                             " Default is '" + ietf_directory + "/draft-with-YANG-example/'")
    parser.add_argument("--rfcyangpath", default=ietf_directory + "/YANG-rfc/",
                        help="The optional directory where to store "
                             "the data models extracted from RFCs"
                             "Default is '" + ietf_directory + "/YANG-rfc/'")
    parser.add_argument("--rfcextractionyangpath", default=ietf_directory + "/YANG-rfc-extraction/",
                        help="The optional directory where to store "
                             "the typedef, grouping, identity from data models extracted from RFCs"
                             "Default is '" + ietf_directory + "/YANG-rfc-extraction/'")
    parser.add_argument("--draftelementspath", default=ietf_directory + "/draft-elements/",
                        help="The optional directory where to store "
                             "the typedef, grouping, identity from data models correctely extracted from drafts"
                             "Default is '" + ietf_directory + "/draft-elements/'")
    parser.add_argument("--strict", type=bool, default=False, help='Optional flag that determines syntax enforcement; '
                                                                   "'If set to 'True' <CODE BEGINS> / <CODE ENDS> are "
                                                                   "required; default is 'False'")
    parser.add_argument("--debug", type=int, default=0, help="Debug level; the default is 0")
    parser.add_argument("--forcecompilation", type=bool, default=False,
                        help="Optional flag that determines wheter compilation should be run "
                        "for all files even if they have not been changed "
                        "or even if the validators versions have not been changed.")

    args = parser.parse_args()
    custom_print('Start of yangIetf.py job in {}'.format(args.draftpath))
    debug_level = args.debug

    # Get list of hashed files
    fileHasher = FileHasher()
    files_hashes = fileHasher.load_hashed_files_list()

    # Initialize files generator -> used in creating JSON/HTML results files
    filesGenerator = FilesGenerator(args.htmlpath)

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
        'all_yang_draft_path_strict': args.allyangdraftpathstrict,
        'all_yang_example_path': args.allyangexamplepath,
        'all_yang_draft_path_only_example': args.allyangdraftpathonlyexample,
        'all_yang_path': args.allyangpath,
        'all_yang_draft_path_no_strict': args.allyangdraftpathnostrict
    }

    # ----------------------------------------------------------------------
    # Empty the yangpath, allyangpath, and rfcyangpath directories content
    # ----------------------------------------------------------------------
    remove_directory_content(args.yangpath, debug_level)
    remove_directory_content(args.allyangpath, debug_level)
    remove_directory_content(args.rfcyangpath, debug_level)
    remove_directory_content(args.allyangexamplepath, debug_level)
    remove_directory_content(args.yangexampleoldrfcpath, debug_level)
    remove_directory_content(args.allyangdraftpathstrict, debug_level)
    remove_directory_content(args.allyangdraftpathnostrict, debug_level)
    remove_directory_content(args.allyangdraftpathonlyexample, debug_level)
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
    custom_print('List of emails of Cisco autthors:\n{}'.format(output_email_string_unique))

    # Create IETF drafts extraction and compilation statistics
    drafts_stats = {
        'total-drafts': len(yang_draft_dict.keys()),
        'draft-passed': number_of_yang_modules_that_passed_compilation(draftsCompilator.results_dict, 'PASSED'),
        'draft-warnings': number_of_yang_modules_that_passed_compilation(draftsCompilator.results_dict, 'PASSED WITH WARNINGS'),
        'all-ietf-drafts': len([f for f in os.listdir(args.allyangpath) if os.path.isfile(os.path.join(args.allyangpath, f))]),
        'example-drafts': len(yang_example_draft_dict.keys())
    }
    filesGenerator.generateIETFYANGPageMainHTML(drafts_stats)

    # Store IETF drafts statistics into AllYANGPageMain.json files
    counter = 5
    while True:
        try:
            if not os.path.exists('{}/stats/AllYANGPageMain.json'.format(args.htmlpath)):
                with open('{}/stats/AllYANGPageMain.json'.format(args.htmlpath), 'w') as f:
                    f.write('{}')
            with open('{}/stats/AllYANGPageMain.json'.format(args.htmlpath), 'r') as f:
                stats = json.load(f)
                stats['ietf-yang'] = drafts_stats
            with open('{}/stats/AllYANGPageMain.json'.format(args.htmlpath), 'w') as f:
                json.dump(stats, f)
            break
        except Exception:
            counter = counter - 1
            if counter == 0:
                break

    # Print the summary of the IETF Drafts extraction and compilation results
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
