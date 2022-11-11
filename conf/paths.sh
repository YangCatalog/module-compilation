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
PATH=/module-compilation/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH
export PATH
python_exec=$(readlink -f $(command -v python))
python_version="${python_exec##*/}"
PYTHONPATH=/usr/lib/$python_version/site-packages
export PYTHONPATH
export PYTHONIOENCODING=utf-8
export LC_ALL=C.UTF-8

export YANG=/.
export YANGVAR=$(python get_config.py --section Directory-Section --key var)
export BIN=$YANG/module-compilation/bin
export CONF=$YANG/module-compilation/conf
export BACKUPDIR=$(python get_config.py --section Directory-Section --key backup)
export CONFD_DIR=$(python get_config.py --section Tool-Section --key confd-dir)
export PYANG=$(python get_config.py --section Tool-Section --key pyang-exec)
export CREDENTIALS=$(python get_config.py --section Secrets-Section --key confd-credentials)
export IS_PROD=$(python get_config.py --section General-Section --key is-prod)
export GIT_TOKEN=$(python get_config.py --section Secrets-Section --key yang-catalog-token)

#
# Repositories
#
export NONIETFDIR=$(python get_config.py --section Directory-Section --key non-ietf-directory)
export IETFDIR=$(python get_config.py --section Directory-Section --key ietf-directory)
export MODULES=$(python get_config.py --section Directory-Section --key modules-directory)

#
# Working directories
export LOGS=$(python get_config.py --section Directory-Section --key logs)
export TMP=$(python get_config.py --section Directory-Section --key temp)

#
# Where the HTML pages lie
#
export WEB_PRIVATE=$(python get_config.py --section Web-Section --key private-directory)
export WEB_DOWNLOADABLES=$(python get_config.py --section Web-Section --key downloadables-directory)
export WEB=$(python get_config.py --section Web-Section --key public-directory)
export MY_URI=$(python get_config.py --section Web-Section --key my-uri)
