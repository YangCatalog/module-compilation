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
__license__ = 'Eclipse Public License v1.0'
__email__ = 'miroslav.kovac@pantheon.tech'

import argparse
import json
import os
import re

import jinja2

from create_config import create_config


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


if __name__ == '__main__':
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

    config = create_config(args.config_path)
    private_dir = config.get('Web-Section', 'private-directory')
    yang_repo_dir = config.get('Directory-Section', 'yang-models-dir')

    context = {}
    cisco_dir = '{}/vendor/cisco'.format(yang_repo_dir)
    juniper_dir = '{}/vendor/juniper'.format(yang_repo_dir)
    huawei_dir = '{}/vendor/huawei/network-router'.format(yang_repo_dir)
    fujitsu_dir = '{}/vendor/fujitsu/FSS2-API-Yang'.format(yang_repo_dir)
    nokia_dir = '{}/vendor/nokia'.format(yang_repo_dir)

    cisco_all_os = [name for name in os.listdir(cisco_dir) if os.path.isdir(os.path.join(cisco_dir, name))]
    for directory in cisco_all_os:
        os_dir = '{}/{}'.format(cisco_dir, directory)
        specific_os_dir = [name for name in os.listdir(os_dir) if os.path.isdir(os.path.join(os_dir, name))]
        directory_upper = directory.upper()
        context[directory_upper] = []
        for directory_specific_os in specific_os_dir:
            context[directory_upper].append({'alphaNumeric': re.sub(r'\W+', '', directory_specific_os),
                                             'allCharacters': directory_specific_os})
        context[directory_upper] = sorted(context[directory_upper], key=lambda i: i['alphaNumeric'])

    juniper_all_os = [name for name in os.listdir(juniper_dir) if os.path.isdir(os.path.join(juniper_dir, name))]
    context['juniper'] = []
    for directory in juniper_all_os:
        os_dir = '{}/{}'.format(juniper_dir, directory)
        specific_os_dir = [name for name in os.listdir(os_dir) if os.path.isdir(os.path.join(os_dir, name))]
        directory_upper = directory.upper()
        for directory_specific_os in specific_os_dir:
            context['juniper'].append({'alphaNumeric': re.sub(r'\W+', '', directory_specific_os),
                                       'allCharacters': directory_specific_os})
    context['juniper'] = sorted(context['juniper'], key=lambda i: i['alphaNumeric'])

    huawei_all_os = [name for name in os.listdir(huawei_dir) if os.path.isdir(os.path.join(huawei_dir, name))]
    context['huawei'] = []
    for directory in huawei_all_os:
        os_dir = '{}/{}'.format(huawei_dir, directory)
        specific_os_dir = [name for name in os.listdir(os_dir) if os.path.isdir(os.path.join(os_dir, name))]
        for directory_specific_os in specific_os_dir:
            context['huawei'].append({'alphaNumeric': re.sub(r'\W+', '', '{}{}'.format(directory, directory_specific_os)),
                                      'allCharacters': '{} {}'.format(directory, directory_specific_os)})
    context['huawei'] = sorted(context['huawei'], key=lambda i: i['alphaNumeric'])

    fujitsu_all_os = [name for name in os.listdir(fujitsu_dir) if os.path.isdir(os.path.join(fujitsu_dir, name))]
    context['fujitsu'] = []
    for directory in fujitsu_all_os:
        os_dir = '{}/{}'.format(fujitsu_dir, directory)
        specific_os_dir = [name for name in os.listdir(os_dir) if os.path.isdir(os.path.join(os_dir, name))]
        directory_upper = directory.upper()
        for directory_specific_os in specific_os_dir:
            context['fujitsu'].append(
                {'alphaNumeric': re.sub(r'\W+', '', '{}{}'.format(directory, directory_specific_os)),
                 'allCharacters': '{}{}'.format(directory, directory_specific_os)})
    context['fujitsu'] = sorted(context['fujitsu'], key=lambda i: i['alphaNumeric'])

    nokia_all_os = [name for name in os.listdir(nokia_dir) if os.path.isdir(os.path.join(nokia_dir, name))]
    context['nokia'] = []
    for directory in nokia_all_os:
        os_dir = '{}/{}'.format(nokia_dir, directory)
        specific_os_dir = [name for name in os.listdir(os_dir) if os.path.isdir(os.path.join(os_dir, name))]
        directory_upper = directory.upper()
        for directory_specific_os in specific_os_dir:
            context['nokia'].append(
                {'alphaNumeric': re.sub(r'\W+', '', directory_specific_os.strip('latest_sros_')),
                 'allCharacters': directory_specific_os.strip('latest_sros_')})
    context['nokia'] = sorted(context['nokia'], key=lambda i: i['alphaNumeric'])

    context['openroadm'] = []
    for specific_version in args.openRoadM:
        context['openroadm'].append({'alphaNumeric': specific_version,
                                     'allCharacters': specific_version})
    result = render('./resources/index.html', context)
    with open('{}/index.html'.format(private_dir), 'w') as f:
        f.write(result)
    with open('{}/private.json'.format(private_dir), 'w') as f:
        context['graphs-cisco-authors'] = ['IETFCiscoAuthorsYANGPageCompilation.json',
                                           'figures/IETFCiscoAuthorsYANGPageCompilation.png',
                                           'figures/IETFYANGOutOfRFC.png',
                                           'figures/IETFYANGPageCompilation.png']
        context['sdo-stats'] = ['IETFDraft.json', 'IETFDraftExample.json', 'IETFYANGRFC.json', 'RFCStandard.json',
                                'BBF.json', 'MEFStandard.json', 'MEFExperimental.json', 'IEEEStandard.json',
                                'IEEEStandardDraft.json', 'IANAStandard.json', 'SysrepoInternal.json', 'SysrepoApplication.json',
                                'ONFOpenTransport.json', 'Openconfig.json']
        context['dependency-graph'] = ['figures/modules-ietf.png', 'figures/modules-all.png',
                                       'figures/ietf-interfaces.png', 'figures/ietf-interfaces-all.png',
                                       'figures/ietf-routing.png']
        json.dump(context, f)
