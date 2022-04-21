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

__author__ = 'Eric Vyncke'
__copyright__ = "Copyright(c) 2018, Cisco Systems, Inc.,  Copyright The IETF Trust 2019, All Rights Reserved"
__license__ = "Apache V2.0"
__email__ = "evyncke@cisco.com"

"""
Extract a single value out of the main /etc/yangcatalog/yangcatalog.conf file
"""

import configparser
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract the value for a single key from a configuration file')
    parser.add_argument("--configuration", default= '/etc/yangcatalog/yangcatalog.conf',
        help="The optional file location for the configuration file. Default is /etc/yangcatalog/yangcatalog.conf")
    parser.add_argument("--section", help="The mandatory configuration section.") 
    parser.add_argument("--key", help="The mandatory key to seach.")

    args = parser.parse_args()

    config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
    config.read(args.configuration)
    print(config.get(args.section, args.key))

