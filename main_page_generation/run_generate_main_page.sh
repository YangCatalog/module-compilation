#!/bin/bash -e

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

source "$CONF"/configure.sh

# Main page compilation out of existing created page for the different SDOs/Vendors
cur_dir=$(pwd)
cd "$NONIETFDIR"/openroadm/OpenROADM_MSA_Public
branches=$(git branch -a | grep remotes)
for b in $branches; do
  last_word=${b##*/}
  first_char=${last_word:0:1}
  if [[ $first_char =~ ^[[:digit:]] ]]; then
    openroadm+=" $last_word"
  fi
done

cd "$cur_dir"
python "$VIRTUAL_ENV"/main_page_generation/private_page.py --openRoadM "${openroadm}"
cd "$WEB_PRIVATE"
rm -f YANGPageMain.html
cat *PageMain.html >YANGPageMain.html
echo "$(date +%c): Main page generation is successful" >>"$SUCCESSFUL_MESSAGES_LOG"