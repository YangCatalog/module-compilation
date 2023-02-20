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
import typing as t

import jinja2

from create_config import create_config


def alnum(s: str):
    return ''.join(c for c in s if c.isalnum())


def get_vendor_context(
    directory: str,
    get_alpha_numeric: t.Callable[[str, str], str],
    get_all_characters: t.Callable[[str, str], str],
    separate: bool = False,
) -> list[dict]:
    operating_systems = [name for name in os.listdir(directory) if os.path.isdir(os.path.join(directory, name))]
    separate_contexts = {}
    vendor_context = []
    for operating_system in operating_systems:
        os_dir = os.path.join(directory, operating_system)
        os_specific_dirs = [name for name in os.listdir(os_dir) if os.path.isdir(os.path.join(os_dir, name))]
        for os_specific_dir in os_specific_dirs:
            vendor_context.append(
                {
                    'alphaNumeric': get_alpha_numeric(operating_system, os_specific_dir),
                    'allCharacters': get_all_characters(operating_system, os_specific_dir),
                },
            )
        if separate:
            separate_contexts[operating_system.upper()] = sorted(vendor_context, key=lambda i: i['alphaNumeric'])
            vendor_context.clear()

    if separate:
        return separate_contexts
    return sorted(vendor_context, key=lambda i: i['alphaNumeric'])


def get_etsi_context(etsi_dir: str) -> list[dict]:
    etsi_all_versions = [name for name in os.listdir(etsi_dir) if os.path.isdir(os.path.join(etsi_dir, name))]
    etsi_context = []
    for etsi_version in etsi_all_versions:
        etsi_context.append(
            {
                'alphaNumeric': alnum(etsi_version.strip('NFV-SOL006-v')),
                'allCharacters': etsi_version.strip('NFV-SOL006-v'),
            },
        )
    return sorted(etsi_context, key=lambda i: i['alphaNumeric'])


def get_openroadm_context(openroadm_files: list[str]) -> list[dict]:
    return [
        {'alphaNumeric': specific_version, 'allCharacters': specific_version} for specific_version in openroadm_files
    ]


def render(tpl_path: str, context: dict) -> str:
    """Render jinja html template

    Arguments:
        :param tpl_path     (str) path to a template file
        :param context      (dict) dictionary containing data to render jinja template file
    :return: string containing rendered html file
    """

    path, filename = os.path.split(tpl_path)
    return jinja2.Environment(loader=jinja2.FileSystemLoader(path or './')).get_template(filename).render(context)


def main():
    parser = argparse.ArgumentParser(description='Generate yangcatalog main private page.')
    parser.add_argument('--openRoadM', help='List of openRoadM files', nargs='*')
    args = parser.parse_args()

    config = create_config()
    private_dir = config.get('Web-Section', 'private-directory')
    yang_repo_dir = config.get('Directory-Section', 'yang-models-dir')

    cisco_dir = os.path.join(yang_repo_dir, 'vendor/cisco')
    juniper_dir = os.path.join(yang_repo_dir, 'vendor/juniper')
    huawei_dir = os.path.join(yang_repo_dir, 'vendor/huawei/network-router')
    fujitsu_dir = os.path.join(yang_repo_dir, 'vendor/fujitsu/FSS2-API-Yang')
    nokia_dir = os.path.join(yang_repo_dir, 'vendor/nokia')
    etsi_dir = os.path.join(yang_repo_dir, 'standard/etsi')

    context = {}

    cisco_contexts = get_vendor_context(
        cisco_dir,
        lambda _, os_specific_dir: alnum(os_specific_dir),
        lambda _, os_specific_dir: os_specific_dir,
        separate=True,
    )
    context.update(cisco_contexts)

    context['juniper'] = get_vendor_context(
        juniper_dir,
        lambda _, os_specific_dir: alnum(os_specific_dir),
        lambda _, os_specific_dir: os_specific_dir,
    )

    context['huawei'] = get_vendor_context(
        huawei_dir,
        lambda os_name, os_specific_dir: alnum(f'{os_name}{os_specific_dir}'),
        lambda os_name, os_specific_dir: f'{os_name} {os_specific_dir}',
    )

    context['fujitsu'] = get_vendor_context(
        fujitsu_dir,
        lambda os_name, os_specific_dir: alnum(f'{os_name}{os_specific_dir}'),
        lambda os_name, os_specific_dir: f'{os_name}{os_specific_dir}',
    )

    context['nokia'] = get_vendor_context(
        nokia_dir,
        lambda _, os_specific_dir: alnum(os_specific_dir.strip('latest_sros_')),
        lambda _, os_specific_dir: os_specific_dir.strip('latest_sros_'),
    )

    context['etsi'] = get_etsi_context(etsi_dir)

    context['openroadm'] = get_openroadm_context(args.openRoadM)

    tpl_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../resources/index.html')
    result = render(tpl_path, context)
    if result:
        with open(os.path.join(private_dir, 'index.html'), 'w') as writer:
            writer.write(result)
    context['graphs-cisco-authors'] = [
        'IETFCiscoAuthorsYANGPageCompilation.json',
        'figures/IETFCiscoAuthorsYANGPageCompilation.png',
        'figures/IETFYANGOutOfRFC.png',
        'figures/IETFYANGPageCompilation.png',
    ]
    context['sdo-stats'] = [
        'IETFDraft.json',
        'IETFDraftExample.json',
        'IETFYANGRFC.json',
        'RFCStandard.json',
        'BBF.json',
        'MEFStandard.json',
        'MEFExperimental.json',
        'IEEEStandard.json',
        'IEEEStandardDraft.json',
        'IANAStandard.json',
        'SysrepoInternal.json',
        'SysrepoApplication.json',
        'ONFOpenTransport.json',
        'Openconfig.json',
    ]
    context['dependency-graph'] = [
        'figures/modules-ietf.png',
        'figures/modules-all.png',
        'figures/ietf-interfaces.png',
        'figures/ietf-interfaces-all.png',
        'figures/ietf-routing.png',
    ]
    with open(os.path.join(private_dir, 'private.json'), 'w') as writer:
        json.dump(context, writer)


if __name__ == '__main__':
    main()
