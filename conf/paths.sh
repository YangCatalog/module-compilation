# Copyright The IETF Trust 2019, All Rights Reserved
# Copyright (c) 2018 Cisco and/or its affiliates.
# This software is licensed to you under the terms of the Apache License, Version 2.0 (the "License").
# You may obtain a copy of the License at http:/www.apache.org/licenses/LICENSE-2.0
# The code, technical concepts, and all information contained herein, are the property of Cisco Technology, Inc.
# and/or its affiliated entities, under various laws including copyright, international treaties, patent,
# and/or contract. Any use of the material herein must be in accordance with the terms of the License.
# All rights not expressly granted by the License are reserved.
# Unless required by applicable law or agreed to separately in writing, software distributed under the
# License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied.
PATH="$VIRTUAL_ENV":/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH
python_exec=$(readlink -f "$(command -v python)")
python_version="${python_exec##*/}"
PYTHONPATH=/usr/lib/$python_version/site-packages:"$VIRTUAL_ENV"
export PYTHONPATH
export PYTHONIOENCODING=utf-8
export LC_ALL=C.UTF-8

export YANG=/.
YANGVAR=$(python "$VIRTUAL_ENV"/get_config.py --section Directory-Section --key var)
export YANGVAR
BACKUPDIR=$(python "$VIRTUAL_ENV"/get_config.py --section Directory-Section --key backup)
export BACKUPDIR
CONFD_DIR=$(python "$VIRTUAL_ENV"/get_config.py --section Tool-Section --key confd-dir)
export CONFD_DIR
PYANG=$(python "$VIRTUAL_ENV"/get_config.py --section Tool-Section --key pyang-exec)
export PYANG
CREDENTIALS=$(python "$VIRTUAL_ENV"/get_config.py --section Secrets-Section --key confd-credentials)
export CREDENTIALS
IS_PROD=$(python "$VIRTUAL_ENV"/get_config.py --section General-Section --key is-prod)
export IS_PROD
GIT_TOKEN=$(python "$VIRTUAL_ENV"/get_config.py --section Secrets-Section --key yang-catalog-token)
export GIT_TOKEN

#
# Repositories
#
NONIETFDIR=$(python "$VIRTUAL_ENV"/get_config.py --section Directory-Section --key non-ietf-directory)
export NONIETFDIR
IETFDIR=$(python "$VIRTUAL_ENV"/get_config.py --section Directory-Section --key ietf-directory)
export IETFDIR
MODULES=$(python "$VIRTUAL_ENV"/get_config.py --section Directory-Section --key modules-directory)
export MODULES

#
# Working directories
LOGS=$(python "$VIRTUAL_ENV"/get_config.py --section Directory-Section --key logs)
export LOGS
TMP=$(python "$VIRTUAL_ENV"/get_config.py --section Directory-Section --key temp)
export TMP

#
# Where the HTML pages lie
#
WEB_PRIVATE=$(python "$VIRTUAL_ENV"/get_config.py --section Web-Section --key private-directory)
export WEB_PRIVATE
WEB_DOWNLOADABLES=$(python "$VIRTUAL_ENV"/get_config.py --section Web-Section --key downloadables-directory)
export WEB_DOWNLOADABLES
WEB=$(python "$VIRTUAL_ENV"/get_config.py --section Web-Section --key public-directory)
export WEB
MY_URI=$(python "$VIRTUAL_ENV"/get_config.py --section Web-Section --key my-uri)
export MY_URI
