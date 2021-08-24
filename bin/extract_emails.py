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


__author__ = 'bclaise'

import argparse
import os

from create_config import create_config

# ----------------------------------------------------------------------
# Functions
# ----------------------------------------------------------------------
def list_of_ietf_drafts(directory, debug_level):
    """
    Returns the list of files in a directory
    # status: troubleshooting done
    
    :param directory: directory to search for drafts
    :return: list of found drafts
    """
    only_files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    # Remove the non-drafts from the list of files
    only_drafts = []
    for f in only_files:
        if debug_level > 1:
            print("DEBUG: " + f + " in list_of_ietf_drafts: is a IETF Drafts")
        if "draft-" in f:
            only_drafts.append(f)
    return only_drafts


def extract_email_string(d, email_domain, debug_level):
    """
    Returns a string, comma separated, of all the email addresses for the company email domain,  
    within an IETF draft
    :param d: an IETF draft, including the path
    :param email_domain: example "@cisco.com"
    :param debug
    :return: a string, comma separated, of all the email addresses for the company email domain,  
    """
    email_string = ""
    list_of_email_address = []

    bash_command = "grep \"" + email_domain + "\" " + d
    if debug_level > 1:
        print("bash_command: " + bash_command)
    temp_result = os.popen(bash_command).readlines()
    for line in temp_result:
        line = line.strip(' \r\n')
        if debug_level > 1:
            print("  line: " + line)
        if "email" in line.lower() or "e-mail" in line.lower():
            try: 
                email = line.split(":")[1]
            except: 
                email = line.split("mail")[1]              
            email = email.rstrip(" ")
            email = email.lstrip(" ")
            if debug_level > 0:
                print("  draft name: " + d + " email: " + email)
            list_of_email_address.append(email)
    if list_of_email_address:
        for i in list_of_email_address:
            email_string = email_string + i + ", "
    email_string = email_string.rstrip(", ")
    return email_string


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
if __name__ == "__main__":
    config = create_config()
    ietf_directory = config.get('Directory-Section', 'ietf-directory')

    parser = argparse.ArgumentParser(description='Yang RFC/Draft Processor')

    # Host Config
    parser.add_argument("--draftpath", default= ietf_directory + "/my-id-mirror/", help="The path to the draft directory).")
    parser.add_argument("--yangpath", default= ietf_directory + "/YANG/", help="The path where to store extracted models")
    parser.add_argument("--debug", type=int, default=0, help="Debug level")
    args = parser.parse_args()

    debug_level = args.debug

    os.chdir(args.draftpath)

    ietf_drafts = list_of_ietf_drafts(args.draftpath, args.debug)
    for draft_file in ietf_drafts:
        if debug_level > 1:
            print("Main: " + draft_file)
        output = extract_email_string(draft_file, "@cisco.com")
        if output: 
            print("Main: " + draft_file + ": " + output)
