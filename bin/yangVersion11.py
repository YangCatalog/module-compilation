#!/usr/bin/env python

# Copyright The IETF Trust 2019, All Rights Reserved
# Copyright 2015-2018, Cisco Systems
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from remove_directory_content import remove_directory_content
import argparse
import os

from create_config import create_config

__author__ = 'Benoit Claise'
__copyright__ = "Copyright(c) 2015, Cisco Systems, Inc.,  Copyright The IETF Trust 2019, All Rights Reserved"
__license__ = "Apache v2.0"
__email__ = "bclaise@cisco.com"


def YANGversion11(srcpath, rfcpath, YANGmodel, yangpath, test, debug):
    """
    YANG 1.1 Processing Tool.
    This is the main (external) API entry for the module.
    if the test argument is True, the function tests whether a module is YANG 1.1\
    if the test arugment is False, the functions copies all YANG 1.1 modules to a yangpath
    :param srcpath: The optional directory where to find the source YANG data models
    :param rfcpath: The optional directory where to find the source RFC-produced YANG data models
    :param YANGmodel: A specific YANG model, to be tested for YANG version 1.1 compliance, with the --test option
    :param yangpath: The path to store the version 1.1 YANG data models
    :param debug: Determines how much debug output is printed to the console
    :return: True/False with the --test. Return None otherwise
    """ 
    # test action
    if debug > 0:
        print("Should I do the test?: " + str(test))
    # bug: whatever I enter in 'script --test' results in True
    if test is True:
        if YANGmodel == "":
            print("   --test MUST be used with the -- YANGmodel filename option.")
            return False
        else:
            print("we're good")
            bash_command = "grep yang-version " + srcpath  + YANGmodel + " | grep 1.1"
            temp_result = os.popen(bash_command).read()
            if debug > 0:
                print("bash command: " + bash_command)
            if "1.1" in temp_result :
                if debug > 0:
                    print("DEBUG: " + YANGmodel + " is version 1.1 ")
                return True
            else:
                if debug > 0:
                    print("DEBUG: " + YANGmodel + " is NOT version 1.1 ")
                return False

    if debug > 0:
        print("No test condition")
    
    remove_directory_content(yangpath, debug)
    yang_model_list = [f for f in os.listdir(srcpath) if os.path.isfile(os.path.join(srcpath, f))]
    yang_model_list_v11 = []
    
    for yang_model in yang_model_list:      
        bash_command = "grep yang-version " + srcpath  + yang_model + " | grep 1.1"
        if debug > 0:
            print("bash command: " + bash_command)
        temp_result = os.popen(bash_command).read()
        if "1.1" in temp_result:
            if debug > 0:
                print("DEBUG: " + yang_model + " is version 1.1 ")
            yang_model_list_v11.append(yang_model)
            # copy function below could be improved with python command, as opposed to a bash
            bash_command = "cp  " + srcpath + "/" + yang_model + " " + yangpath + "/" + yang_model
            temp_result = os.popen(bash_command).read()
    if debug > 0:
        print("DEBUG: YANG Model list with YANG version 1.1: " )
        if yang_model_list_v11:
            print(yang_model_list_v11)
        else:
            print("  No YANG modules version 1.1")

 
# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------


if __name__ == "__main__":
    config = create_config()
    ietf_directory = config.get('Directory-Section', 'ietf-directory')

    parser = argparse.ArgumentParser(description='YANG 1.1 Processing Tool. Either test if a YANG module is YANG 1.1 (test option), or copy all YANG 1.1 modules to yangpath')
    parser.add_argument("--srcpath", default= ietf_directory + "/YANG/",
                        help="The optional directory where to find the source YANG data models. "
                             "Default is '" + ietf_directory + "/YANG/'")
    parser.add_argument("--rfcpath", default= ietf_directory + "/YANG-rfc/",
                        help="The optional directory where to find the source RFC-produced YANG data models. Default is '" + ietf_directory + "/YANG-rfc/'")
    parser.add_argument("--YANGmodule", default="",
                        help="A specific YANG module, to be tested for YANG version 1.1 compliance, with the --test option")
    parser.add_argument("--yangpath", default= ietf_directory + "/YANG-v11/",
                        help="The path to store the version 1.1 YANG data models. Default is '" + ietf_directory + "/YANG-v11/'") 
    # Following should be improve so that we don't need to enter a boolean
    # bug: whatever I enter in 'script --test' results in True
    parser.add_argument("--test", type=bool, default=False,
                        help="--test tests whether a YANG data model is based on version 1.1. In which case, it returns 'true'")
    parser.add_argument("--debug", type=int, default=0, help="Debug level; the default is 0")

    args = parser.parse_args()
        
    YANGversion11(args.srcpath, args.rfcpath, args.YANGmodule, args.yangpath, args.test, args.debug)
