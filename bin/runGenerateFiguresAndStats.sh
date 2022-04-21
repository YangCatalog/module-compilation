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

function on_exit {
	local reason=$?
	# Matplot seems to create temporary directories
	rm -rf $TMP/matplot*
	date +"%c: Abort of the script" >> $LOG
	date +"%c: Abort of $0"
	exit $reason
}

trap on_exit EXIT ERR
	
date +"%c: Start of $0"
export LOG=$LOGS/GenerateFiguresAndStats.log
date +"%c: Starting" > $LOG

source configure.sh >> $LOG 2>&1
# Generate the statistics since the beginning and ftp the files
# the yangGetStats.py (without arguements) generates the full stats in json in $WEB_PRIVATE/stats/ :
# this is necessary so that the figures are up to date with today stats, and yang-figures can pick those latest stats up
# the yangGetStats.py --days 5 doesn't generate the json file.
mkdir -p $WEB_PRIVATE/stats >> $LOG 2>&1

date +"%c: Generating the JSON files in $WEB_PRIVATE/stats" >> $LOG
python $BIN/yangGetStats.py >> $LOG  2>&1

date +"%c: Generating the JSON files with --days 5" >> $LOG
python $BIN/yangGetStats.py --days 5 >> $LOG 2>&1

date +"%c: Generating the pictures" >> $LOG
mkdir -p $WEB_PRIVATE/figures >> $LOG 2>&1
python $BIN/yangFigures.py >> $LOG 2>&1

date +"%c: Generating the dependency pictures" >> $LOG
cd $WEB_PRIVATE/figures >> $LOG
python $BIN/symd.py --draft-repos $IETFDIR/YANG/ --rfc-repos $IETFDIR/YANG-rfc/ --graph >>$LOG 2>&1
mv modules.png modules-ietf.png
python $BIN/symd.py --recurse --draft-repos $MODULES --rfc-repos $IETFDIR/YANG-rfc/ --graph >>$LOG 2>&1
mv modules.png modules-all.png
python $BIN/symd.py --recurse --draft-repos $MODULES --rfc-repos $IETFDIR/YANG-rfc/ --sub-graph ietf-interfaces >>$LOG 2>&1
mv ietf-interfaces.png ietf-interfaces-all.png
python $BIN/symd.py --recurse --draft-repos $IETFDIR/YANG/ --rfc-repos $IETFDIR/YANG-rfc/ --sub-graph ietf-interfaces >>$LOG 2>&1
python $BIN/symd.py --recurse --draft-repos $IETFDIR/YANG/ --rfc-repos $IETFDIR/YANG-rfc/ --sub-graph ietf-routing >>$LOG 2>&1


trap - EXIT ERR
date +"%c: End of the script" >> $LOG
date +"%c: End of $0"
