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

# TODO use a function rather repeating code
# TODO avoid git init / pull when not needed
# TODO fix the flattening

# Get the local configuration
source configure.sh
LOG=$LOGS/downloadGitHub.log
date +"%c: Starting" >$LOG

#
# Get the entire content of github.com/YangModels (including submodules == symbolic links)
# BEWARE was nadeau/yang before
#
mkdir -p $NONIETFDIR/yangmodels
if [ ! -d $NONIETFDIR/yangmodels/yang ]; then
	cd $NONIETFDIR/yangmodels
	git clone --recurse-submodules https://github.com/YangModels/yang.git >>$LOG 2>&1
fi
cd $NONIETFDIR/yangmodels/yang
# Be sure that remote is also set to yang-catalog/yang fork
git config remote.fork.url >&- || git remote add fork https://$GIT_TOKEN@github.com/yang-catalog/yang.git >>$LOG 2>&1
git remote update >>$LOG 2>&1
git pull origin main >>$LOG 2>&1
git submodule update --init --recursive >>$LOG 2>&1

# get the entire content of github (openconfig)
mkdir -p $NONIETFDIR/openconfig
cd $NONIETFDIR/openconfig
if [ ! -d $NONIETFDIR/openconfig/public ]; then
	git clone --recurse-submodules https://github.com/openconfig/public.git >>$LOG 2>&1
fi
cd $NONIETFDIR/openconfig/public
git pull --recurse-submodules https://github.com/openconfig/public.git >>$LOG 2>&1

# Trick below is "flatten" all .yang files from subdirectories into one directory, to avoid the ConfD path issues
cd $NONIETFDIR/openconfig/public/release/models
if [ -d $NONIETFDIR/openconfig-flat/public/release/models ]; then
	rm -rf $NONIETFDIR/openconfig-flat/public/release/models
fi
mkdir -p $NONIETFDIR/openconfig-flat/public/release/models
find . -name "*.yang" -exec cp -t $NONIETFDIR/openconfig-flat/public/release/models/ {} + >>$LOG 2>&1

# get the entire content of github (sysrepo)
mkdir -p $NONIETFDIR/sysrepo
if [ ! -d $NONIETFDIR/sysrepo/yang ]; then
	cd $NONIETFDIR/sysrepo
	git clone --recurse-submodules https://github.com/sysrepo/yang.git >>$LOG 2>&1
fi
cd $NONIETFDIR/sysrepo/yang
git init >>$LOG 2>&1
git pull --recurse-submodules https://github.com/sysrepo/yang.git >>$LOG 2>&1

# get the entire content of github (ONF)
mkdir -p $NONIETFDIR/onf
if [ ! -d $NONIETFDIR/onf/Snowmass-ONFOpenTransport ]; then
	cd $NONIETFDIR/onf
	git clone --recurse-submodules https://github.com/OpenNetworkingFoundation/Snowmass-ONFOpenTransport.git >>$LOG 2>&1
fi
cd $NONIETFDIR/onf/Snowmass-ONFOpenTransport
git init >>$LOG 2>&1
git pull --recurse-submodules https://github.com/OpenNetworkingFoundation/Snowmass-ONFOpenTransport.git >>$LOG 2>&1

# get the entire content of OpenROADM (ONF)
mkdir -p $NONIETFDIR/openroadm
if [ ! -d $NONIETFDIR/openroadm/OpenROADM_MSA_Public ]; then
	cd $NONIETFDIR/openroadm
	git clone --recurse-submodules https://github.com/OpenROADM/OpenROADM_MSA_Public.git >>$LOG 2>&1
fi
cd $NONIETFDIR/openroadm/OpenROADM_MSA_Public
git init >>$LOG 2>&1
git pull --recurse-submodules https://github.com/OpenROADM/OpenROADM_MSA_Public.git >>$LOG 2>&1

#
# This private repository is private and requires specific credentials
#
#mkdir -p $NONIETFDIR/openroadm
#if [ ! -d $NONIETFDIR/openroadm/OpenROADM_MSA_Private ]
#then
#	cd $NONIETFDIR/openroadm
#	git clone --recurse-submodules https://git@github.com/OpenROADM/OpenROADM_MSA_Private.git
#fi
#cd $NONIETFDIR/openroadm/OpenROADM_MSA_Private
#git init
#git pull --recurse-submodules https://git@github.com/OpenROADM/OpenROADM_MSA_Private.git

# MEF
mkdir -p $NONIETFDIR/mef
if [ ! -d $NONIETFDIR/mef/YANG-public ]; then
	cd $NONIETFDIR/mef
	git clone --recurse-submodules https://github.com/MEF-GIT/YANG-public.git >>$LOG 2>&1
fi
cd $NONIETFDIR/mef/YANG-public
git init >>$LOG 2>&1
git pull --recurse-submodules https://github.com/MEF-GIT/YANG-public.git >>$LOG 2>&1

date +"%c: End of the script!" >>$LOG
