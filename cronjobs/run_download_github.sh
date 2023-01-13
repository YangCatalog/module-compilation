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

declare -A REPOSITORIES
REPOSITORIES=([yangmodels/yang]=https://github.com/YangModels/yang.git \
              [openconfig/public]=https://github.com/openconfig/public.git \
              [sysrepo/yang]=https://github.com/sysrepo/yang.git \
              [onf/Snowmass-ONFOpenTransport]=https://github.com/OpenNetworkingFoundation/Snowmass-ONFOpenTransport.git \
              [openroadm/OpenROADM_MSA_Public]=https://github.com/OpenROADM/OpenROADM_MSA_Public.git \
              [mef/YANG-public]=https://github.com/MEF-GIT/YANG-public.git)

declare -A modified

refresh_repo () {
    local repo=$1
    local owner=${1%%/*}
    local directory=${1##*/}
    if [ ! -d "$NONIETFDIR"/"$repo" ]
    then
        mkdir -p "$NONIETFDIR"/"$owner"
        cd "$NONIETFDIR"/"$owner"
        git clone --recurse-submodules "${REPOSITORIES[$repo]}" "$directory" >> "$LOG" 2>&1
    else
        cd "$NONIETFDIR"/"$repo"
        if [ "$(git pull origin HEAD 2>&1 | tee -a "$LOG" | tail -n 1)" != "Already up to date." ]
        then
            modified+=([$repo]=true)
        fi
        git submodule update --init --recursive >> "$LOG" 2>&1
    fi
}

if [ "$1" != "--test" ]
then
    # Get the local configuration
    source "$CONF"/configure.sh
    LOG=$LOGS/downloadGitHub.log
    date +"%c: Starting" >"$LOG"

    for repo in "${!REPOSITORIES[@]}"
    do
        refresh_repo "$repo"
    done

    # "Flatten" all .yang files from subdirectories into one directory to avoid confd path issues.
    if [ "${modified[openconfig/public]}" ]
    then
        cd "$NONIETFDIR"/openconfig
        rm -rf public-flat
        cp -r public public-flat
        cd public-flat
        mkdir -p release/models-flat
        cd release
        find ./models -name "*.yang" -exec mv -t "$NONIETFDIR"/openconfig/public-flat/release/models-flat/ {} + >>"$LOG" 2>&1
        rm -rf models
        mv models-flat models
    fi

    date +"%c: End of the script!" >>"$LOG"
fi
echo "$(date +%c): GitHub downloading is successful"