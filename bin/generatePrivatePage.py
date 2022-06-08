#!/usr/bin/env python

# Copyright The IETF Trust 2020, All Rights Reserved
# This software is licensed to you under the terms of the Apache License, Version 2.0 (the "License").
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
# The code, technical concepts, and all information contained herein, are the property of Cisco Technology, Inc.
# and/or its affiliated entities, under various laws including copyright, international treaties, patent,
# and/or contract. Any use of the material herein must be in accordance with the terms of the License.
# All rights not expressly granted by the License are reserved.
# Unless required by applicable law or agreed to separately in writing, software distributed under the
# License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied.

__author__ = 'Miroslav Kovac'
__copyright__ = 'Copyright The IETF Trust 2020, All Rights Reserved'
__license__ = 'Apache License, Version 2.0'
__email__ = 'miroslav.kovac@pantheon.tech'

import argparse
import json
import os
import re

import jinja2

from create_config import create_config


def render(tpl_path: str, context: dict):
    """Render jinja html template

    Arguments:
        :param tpl_path     (str) path to a template file
        :param context      (dict) dictionary containing data to render jinja template file
    :return: string containing rendered html file
    """

    path, filename = os.path.split(tpl_path)
    return jinja2.Environment(
        loader=jinja2.FileSystemLoader(path or './')
    ).get_template(filename).render(context)


def main():
    parser = argparse.ArgumentParser(description='Generate yangcatalog main private page.')
    parser.add_argument('--config',
                        help='Path to the config file '
                             'Default is {}'.format(os.environ['YANGCATALOG_CONFIG_PATH']),
                        type=str,
                        default=os.environ['YANGCATALOG_CONFIG_PATH'])
    parser.add_argument('--openRoadM',
                        help='List of openRoadM files',
                        type=str,
                        nargs='*',
                        default=[])
    args = parser.parse_args()

    config = create_config(args.config)
    private_dir = config.get('Web-Section', 'private-directory')
    yang_repo_dir = config.get('Directory-Section', 'yang-models-dir')

    cisco_dir = os.path.join(yang_repo_dir, 'vendor/cisco')
    juniper_dir = os.path.join(yang_repo_dir, 'vendor/juniper')
    huawei_dir = os.path.join(yang_repo_dir, 'vendor/huawei/network-router')
    fujitsu_dir = os.path.join(yang_repo_dir, 'vendor/fujitsu/FSS2-API-Yang')
    nokia_dir = os.path.join(yang_repo_dir, 'vendor/nokia')
    etsi_dir = os.path.join(yang_repo_dir, 'standard/etsi')

    context = {}
    cisco_all_os = [name for name in os.listdir(cisco_dir) if os.path.isdir(os.path.join(cisco_dir, name))]
    for cisco_os in cisco_all_os:
        os_dir = os.path.join(cisco_dir, cisco_os)
        specific_os_dir = [name for name in os.listdir(os_dir) if os.path.isdir(os.path.join(os_dir, name))]
        directory_upper = cisco_os.upper()
        context[directory_upper] = []
        for directory_specific_os in specific_os_dir:
            context[directory_upper].append({'alphaNumeric': re.sub(r'\W+', '', directory_specific_os),
                                             'allCharacters': directory_specific_os})
        context[directory_upper] = sorted(context[directory_upper], key=lambda i: i['alphaNumeric'])

    juniper_all_os = [name for name in os.listdir(juniper_dir) if os.path.isdir(os.path.join(juniper_dir, name))]
    context['juniper'] = []
    for juniper_os in juniper_all_os:
        os_dir = os.path.join(juniper_dir, juniper_os)
        specific_os_dir = [name for name in os.listdir(os_dir) if os.path.isdir(os.path.join(os_dir, name))]
        for directory_specific_os in specific_os_dir:
            context['juniper'].append({'alphaNumeric': re.sub(r'\W+', '', directory_specific_os),
                                       'allCharacters': directory_specific_os})
    context['juniper'] = sorted(context['juniper'], key=lambda i: i['alphaNumeric'])

    huawei_all_os = [name for name in os.listdir(huawei_dir) if os.path.isdir(os.path.join(huawei_dir, name))]
    context['huawei'] = []
    for huawei_os in huawei_all_os:
        os_dir = os.path.join(huawei_dir, huawei_os)
        specific_os_dir = [name for name in os.listdir(os_dir) if os.path.isdir(os.path.join(os_dir, name))]
        for directory_specific_os in specific_os_dir:
            context['huawei'].append({'alphaNumeric': re.sub(r'\W+', '', '{}{}'.format(huawei_os, directory_specific_os)),
                                      'allCharacters': '{} {}'.format(huawei_os, directory_specific_os)})
    context['huawei'] = sorted(context['huawei'], key=lambda i: i['alphaNumeric'])

    fujitsu_all_os = [name for name in os.listdir(fujitsu_dir) if os.path.isdir(os.path.join(fujitsu_dir, name))]
    context['fujitsu'] = []
    for fujitsu_os in fujitsu_all_os:
        os_dir = os.path.join(fujitsu_dir, fujitsu_os)
        specific_os_dir = [name for name in os.listdir(os_dir) if os.path.isdir(os.path.join(os_dir, name))]
        for directory_specific_os in specific_os_dir:
            context['fujitsu'].append(
                {'alphaNumeric': re.sub(r'\W+', '', '{}{}'.format(fujitsu_os, directory_specific_os)),
                 'allCharacters': '{}{}'.format(fujitsu_os, directory_specific_os)})
    context['fujitsu'] = sorted(context['fujitsu'], key=lambda i: i['alphaNumeric'])

    nokia_all_os = [name for name in os.listdir(nokia_dir) if os.path.isdir(os.path.join(nokia_dir, name))]
    context['nokia'] = []
    for cisco_os in nokia_all_os:
        os_dir = os.path.join(nokia_dir, cisco_os)
        specific_os_dir = [name for name in os.listdir(os_dir) if os.path.isdir(os.path.join(os_dir, name))]
        for directory_specific_os in specific_os_dir:
            context['nokia'].append(
                {'alphaNumeric': re.sub(r'\W+', '', directory_specific_os.strip('latest_sros_')),
                 'allCharacters': directory_specific_os.strip('latest_sros_')})
    context['nokia'] = sorted(context['nokia'], key=lambda i: i['alphaNumeric'])

    etsi_all_versions = [name for name in os.listdir(etsi_dir) if os.path.isdir(os.path.join(etsi_dir, name))]
    context['etsi'] = []
    for etsi_version in etsi_all_versions:
        context['etsi'].append(
            {'alphaNumeric': re.sub(r'\W+', '', etsi_version.strip('NFV-SOL006-v')),
             'allCharacters': etsi_version.strip('NFV-SOL006-v')})
    context['etsi'] = sorted(context['etsi'], key=lambda i: i['alphaNumeric'])

    context['openroadm'] = []
    for specific_version in args.openRoadM:
        context['openroadm'].append({'alphaNumeric': specific_version,
                                     'allCharacters': specific_version})
    tpl_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources/index.html')
    result = render(tpl_path, context)
    if result:
        with open(os.path.join(private_dir, 'index.html'), 'w') as writer:
            writer.write(result)
    with open(os.path.join(private_dir, 'private.json'), 'w') as writer:
        context['graphs-cisco-authors'] = ['IETFCiscoAuthorsYANGPageCompilation.json',
                                           'figures/IETFCiscoAuthorsYANGPageCompilation.png',
                                           'figures/IETFYANGOutOfRFC.png',
                                           'figures/IETFYANGPageCompilation.png']
        context['sdo-stats'] = ['IETFDraft.json', 'IETFDraftExample.json', 'IETFYANGRFC.json', 'RFCStandard.json',
                                'BBF.json', 'MEFStandard.json', 'MEFExperimental.json', 'IEEEStandard.json',
                                'IEEEStandardDraft.json', 'IANAStandard.json', 'SysrepoInternal.json',
                                'SysrepoApplication.json', 'ONFOpenTransport.json', 'Openconfig.json']
        context['dependency-graph'] = ['figures/modules-ietf.png', 'figures/modules-all.png',
                                       'figures/ietf-interfaces.png', 'figures/ietf-interfaces-all.png',
                                       'figures/ietf-routing.png']
        json.dump(context, writer)


if __name__ == '__main__':
    main()
