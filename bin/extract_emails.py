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


__author__ = 'Benoit Claise'
__copyright__ = 'Copyright(c) 2015-2018, Cisco Systems, Inc.,  Copyright The IETF Trust 2019, All Rights Reserved'
__license__ = 'Apache License, Version 2.0'
__email__ = 'bclaise@cisco.com'

import argparse
import os

from create_config import create_config


# ----------------------------------------------------------------------
# Functions
# ----------------------------------------------------------------------
def list_of_ietf_drafts(directory: str):
    """ Returns a list of all the files in a directory.

    Arguments:
        :param directory        (str) Directory to search for drafts

    :return: list of found drafts
    """
    only_files = [file for file in os.listdir(directory) if os.path.isfile(os.path.join(directory, file))]
    only_drafts = [file for file in only_files if 'draft-' in file]

    return only_drafts


def extract_email_string(draft_path: str, email_domain: str, debug_level: int = 0):
    """ Returns a string, comma separated, of all the email addresses for the company email domain,
    within an IETF draft.

    Arguments:
        :param draft_path       (str) Full path to the draft
        :param email_domain     (str) Domain of search email (e.g. @cisco.com, @tail-f.com)
        :param debug_level      (int) Debug level
    :return: a string, comma separated, of all the unique email addresses for the company email domain,
    """
    list_of_email_address = []

    bash_command = 'grep "{}" {}'.format(email_domain, draft_path)
    if debug_level > 1:
        print('DEBUG: running command {}'.format(bash_command))
    temp_result = os.popen(bash_command).readlines()
    for line in temp_result:
        line = line.strip(' \r\n')
        if debug_level > 1:
            print('DEBUG: proccesing line: {}'.format(line))
        if 'mailto:' in line:
            mailto = line.split('>')[0].split('mailto:')[-1]
            emails = [e for e in mailto.split(' ') if '@' in e]
            list_of_email_address.extend(emails)
        if any(term in line.lower() for term in ['email', 'e-mail']):
            line = line.split(':')[-1]
            line = line.split('mail')[-1]
            emails = [e for e in line.split(' ') if '@' in e]
            list_of_email_address.extend(emails)
            if emails and debug_level > 0:
                print('DEBUG: {}: {}'.format(draft_path, emails))
    unique_list_of_email_address = list(set(list_of_email_address))
    email_string = ','.join(unique_list_of_email_address)

    return email_string


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
if __name__ == '__main__':
    config = create_config()
    ietf_directory = config.get('Directory-Section', 'ietf-directory')

    parser = argparse.ArgumentParser(description='Extract comma-separated list of email addresses')
    parser.add_argument('--draftpath',
                        help='Path to the directory where all the drafts will be stored. '
                             'Default is {}/my-id-mirror/'.format(ietf_directory),
                        type=str,
                        default='{}/my-id-mirror/'.format(ietf_directory))
    parser.add_argument('--debug',
                        help='Debug level - default is 0',
                        type=int,
                        default=0)
    args = parser.parse_args()

    debug_level = args.debug

    os.chdir(args.draftpath)

    ietf_drafts = list_of_ietf_drafts(args.draftpath)
    for draft_file in ietf_drafts:
        output = extract_email_string(draft_file, '@cisco.com', debug_level)
        if output and debug_level > 0:
            print('Main: {}: {}'.format(draft_file, output))
