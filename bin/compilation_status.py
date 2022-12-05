# Copyright The IETF Trust 2022, All Rights Reserved
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

__author__ = 'Richard Zilincik'
__copyright__ = 'Copyright(c) 2015-2018, Cisco Systems, Inc.,  Copyright The IETF Trust 2022, All Rights Reserved'
__license__ = 'Apache License, Version 2.0'
__email__ = 'richard.zilincik@pantheon.tech'

import re
import typing as t


def pyang_compilation_status(compilation_result: str) -> str:
    if 'error:' in compilation_result:
        ret = 'FAILED'
    elif 'warning:' in compilation_result:
        ret = 'PASSED WITH WARNINGS'
    elif compilation_result == '':
        ret = 'PASSED'
    else:
        ret = 'UNKNOWN'
    return ret


def confd_compilation_status(compilation_result: str) -> str:
    if 'error:' in compilation_result:
        ret = 'FAILED'
    #   The following doesn't work. For example, ietf-diffserv@2016-06-15.yang, now PASSED (TBC):
    #     Error: 'ietf-diffserv@2016-06-15.yang' import of module 'ietf-qos-policy' failed
    #     ietf-diffserv@2016-06-15.yang:11.3: error(250): definition not found
    #   This issue is that an import module that fails => report the main module as FAILED
    #   Another issue with ietf-bgp-common-structure.yang
    elif 'warning:' in compilation_result:
        ret = 'PASSED WITH WARNINGS'
    elif compilation_result == '':
        ret = 'PASSED'
    else:
        ret = 'UNKNOWN'
    # 'cannot compile submodules; compile the module instead' error message
    # => still print the message, but doesn't report it as FAILED
    if 'error: cannot compile submodules; compile the module instead' in compilation_result:
        ret = 'PASSED'
    return ret


def yuma_compilation_status(compilation_result: str, yang_file_name: str) -> str:
    imports_with_errors = 0
    lines = compilation_result.splitlines()
    for line in lines:
        if 'Error:' in line:
            if 'error(332)' not in line:
                return 'FAILED'
            else:
                imports_with_errors += 1

    for line in lines:
        if re.search(r'{}:\d+\.\d+: warning\(\d+\):'.format(yang_file_name), line):
            return 'PASSED WITH WARNINGS'
    if '*** {} Errors, 0 Warnings'.format(imports_with_errors) in compilation_result or compilation_result == '':
        ret = 'PASSED'
    else:
        ret = 'UNKNOWN'
    return ret


def yanglint_compilation_status(compilation_result: str) -> str:
    # logic for yanglint compilation result:
    if 'err :' in compilation_result:
        ret = 'FAILED'
    elif 'warn:' in compilation_result:
        ret = 'PASSED WITH WARNINGS'
    elif compilation_result == '':
        ret = 'PASSED'
    else:
        ret = 'UNKNOWN'
    # 'err : Input data contains submodule which cannot be parsed directly without its main module.' error message
    # => still print the message, but doesn't report it as FAILED
    if (
        'err : Input data contains submodule which cannot be parsed directly without its main module.'
        in compilation_result
    ):
        ret = 'PASSED'
    return ret


def combined_compilation_status(compilation_list: t.List[str]) -> str:
    if 'FAILED' in compilation_list:
        ret = 'FAILED'
    elif 'PASSED WITH WARNINGS' in compilation_list:
        ret = 'PASSED WITH WARNINGS'
    elif compilation_list == ['PASSED', 'PASSED', 'PASSED', 'PASSED']:
        ret = 'PASSED'
    else:
        ret = 'UNKNOWN'
    return ret


def combined_compilation(yang_file_name: str, result: t.Dict[str, str]) -> str:
    """
    Determine the combined compilation result based on individual compilation results from parsers.

    Arguments:
        :param yang_file_name   (str) Name of the yang file
        :param result           (dict) Dictionary of compilation results with following keys:
                                        pyang_lint, confdrc, yumadump, yanglint
    :return: the combined compilation result
    """
    compilation_pyang = pyang_compilation_status(result['pyang_lint'])
    compilation_confd = confd_compilation_status(result['confdrc'])
    compilation_yuma = yuma_compilation_status(result['yumadump'], yang_file_name)
    compilation_yanglint = yanglint_compilation_status(result['yanglint'])

    return combined_compilation_status([compilation_pyang, compilation_confd, compilation_yuma, compilation_yanglint])
