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
LOG=$LOGS/extract_ietf_modules.log
date +"%c: Starting" >"$LOG"

# Need to set some ENV variables for subsequent calls in .PY to confd...
# TODO probably to be moved inside the confd caller
source "$CONFD_DIR"/confdrc

# rsync the IETF drafts and RFCs
mkdir -p "$IETFDIR"/my-id-mirror
mkdir -p "$IETFDIR"/rfc

cd "$IETFDIR"

date +"%c: Retrieving current IETF drafts" >>"$LOG"
rsync -avz --include 'draft-*.txt' --include 'draft-*.xml' --exclude '*' --delete rsync.ietf.org::internet-drafts my-id-mirror >>"$LOG" 2>&1
if [ "$IS_PROD" = "True" ]; then
	date +"%c: Retrieving archived IETF drafts" >>"$LOG"
	rsync -avz --include 'draft-*.txt' --include 'draft-*.xml' --exclude '*' --delete rsync.ietf.org::id-archive my-id-archive-mirror >>"$LOG" 2>&1
fi
date +"%c: Retrieving IETF RFCs" >>"$LOG"
rsync -avlz --delete --include="rfc[0-9]*.txt" --exclude="*" ftp.rfc-editor.org::rfcs rfc >>"$LOG" 2>&1

#copy the current content to the -old files
if [ -f "$WEB_PRIVATE"/IETFDraftYANGPageCompilation.html ]; then
	cp "$WEB_PRIVATE"/IETFDraftYANGPageCompilation.html "$WEB_PRIVATE"/IETFDraftYANGPageCompilation-old.html
fi
if [ -f "$WEB_PRIVATE"/IETFCiscoAuthorsYANGPageCompilation.html ]; then
	cp "$WEB_PRIVATE"/IETFCiscoAuthorsYANGPageCompilation.html "$WEB_PRIVATE"/IETFCiscoAuthorsYANGPageCompilation-old.html
fi

# Some directory and symbolic links may need to be created
# TODO have a script to create those
date +"%c: Creating required directories and symbolic links" >>"$LOG"
mkdir -p "$IETFDIR"/YANG
echo "All YANG modules extracted correctly from IETF drafts" >"$IETFDIR"/YANG/README.md
mkdir -p "$IETFDIR"/YANG-all
echo "All YANG modules extracted (bad or good) from IETF drafts" >"$IETFDIR"/YANG-all/README.md
mkdir -p "$IETFDIR"/YANG-example
mkdir -p "$IETFDIR"/YANG-extraction
mkdir -p "$IETFDIR"/YANG-rfc
echo "All YANG modules extracted correctly from RFCs" >"$IETFDIR"/YANG-rfc/README.md
mkdir -p "$IETFDIR"/YANG-rfc-extraction
mkdir -p "$IETFDIR"/YANG-example-old-rfc
mkdir -p "$IETFDIR"/YANG-v11
mkdir -p "$IETFDIR"/draft-with-YANG-strict
mkdir -p "$IETFDIR"/draft-with-YANG-no-strict
mkdir -p "$IETFDIR"/draft-with-YANG-example
mkdir -p "$IETFDIR"/draft-with-YANG-diff
mkdir -p "$MODULES"
echo "Set of all YANG modules known" >"$MODULES"/README.md
rm -f "$MODULES"/YANG
ln -f -s "$IETFDIR"/YANG "$MODULES"/YANG
rm -f "$MODULES"/YANG-rfc
ln -f -s "$IETFDIR"/YANG-rfc "$MODULES"/YANG-rfc

# Try to flatten a little the IETF structure
rm -f "$MODULES"/ieee.draft
# ln -f -s "$NONIETFDIR"/yangmodels/yang/standard/ieee/draft/ $MODULES/ieee.draft
rm -f "$MODULES"/ieee.published
ln -f -s "$NONIETFDIR"/yangmodels/yang/standard/ieee/published/ "$MODULES"/ieee.published
rm -f "$MODULES"/ieee.1588.draft
# ln -f -s "$NONIETFDIR"/yangmodels/yang/standard/ieee/draft/1588/ $MODULES/ieee.1588.draft
rm -f "$MODULES"/ieee.1588.published
ln -f -s "$NONIETFDIR"/yangmodels/yang/standard/ieee/published/1588/ "$MODULES"/ieee.1588.published
rm -f "$MODULES"/ieee.802.1.draft
# ln -f -s "$NONIETFDIR"/yangmodels/yang/standard/ieee/draft/802.1/ "$MODULES"/ieee.802.1.draft
rm -f "$MODULES"/ieee.802.1.published
ln -f -s "$NONIETFDIR"/yangmodels/yang/standard/ieee/published/802.1/ "$MODULES"/ieee.802.1.published
rm -f "$MODULES"/ieee.802.draft
# ln -f -s "$NONIETFDIR"/yangmodels/yang/standard/ieee/draft/802/ "$MODULES"/ieee.802.draft
rm -f "$MODULES"/ieee.802.published
ln -f -s "$NONIETFDIR"/yangmodels/yang/standard/ieee/published/802/ "$MODULES"/ieee.802.published
rm -f "$MODULES"/ieee.802.3.draft
# ln -f -s "$NONIETFDIR"/yangmodels/yang/standard/ieee/draft/802.3/ "$MODULES"/ieee.802.3.draft
rm -f "$MODULES"/ieee.802.3.published
ln -f -s "$NONIETFDIR"/yangmodels/yang/standard/ieee/published/802.3/ "$MODULES"/ieee.802.3.published
rm -f "$MODULES"/ieee.802.11.draft
# ln -f -s "$NONIETFDIR"/yangmodels/yang/standard/ieee/draft/802.11/ "$MODULES"/ieee.802.11.draft
rm -f "$MODULES"/ieee.802.11.published
ln -f -s "$NONIETFDIR"/yangmodels/yang/standard/ieee/published/802.11/ "$MODULES"/ieee.802.11.published

rm -f "$MODULES"/mef
ln -f -s "$NONIETFDIR"/mef/YANG-public/src/model/standard/ "$MODULES"/mef
rm -f "$MODULES"/openconfig-main
ln -f -s "$NONIETFDIR"/openconfig/public-flat/release/models/ "$MODULES"/openconfig-main
rm -f "$MODULES"/iana
ln -f -s "$NONIETFDIR"/yangmodels/yang/standard/iana/ "$MODULES"/iana

# Extract all YANG models from RFC and I-D
date +"%c: Starting to extract all YANG modules from IETF documents" >>"$LOG"
# Using --draftpath "$IETFDIR"/my-id-archive-mirror/ means much longer process as all expired drafts will also be analyzed...
if [ "$(date +%u)" -eq 6 ]; then
	python "$VIRTUAL_ENV"/ietf_modules_extraction/extract_ietf_modules.py --archived >>"$LOG" 2>&1
fi
python "$VIRTUAL_ENV"/ietf_modules_extraction/extract_ietf_modules.py >>"$LOG" 2>&1
date +"%c: Finished extracting all YANG modules from IETF documents" >>"$LOG"

# Clean up of the .fxs files created by confdc
date +"%c: cleaning up the now useless .fxs files" >>"$LOG"
find "$IETFDIR"/ -name *.fxs ! -name fujitsu-optical-channel-interfaces.fxs -print | xargs -r rm >>"$LOG" 2>&1
find "$NONIETFDIR"/ -name *.fxs ! -name fujitsu-optical-channel-interfaces.fxs -print | xargs -r rm >>"$LOG" 2>&1

# move all IETF YANG modules to the web part
# TODO better using a symbolic link ?
mkdir -p "$WEB"/YANG-modules >>"$LOG" 2>&1
rm -f "$WEB"/YANG-modules/* >>"$LOG" 2>&1
cp --preserve "$IETFDIR"/YANG/*.yang "$WEB"/YANG-modules >>"$LOG" 2>&1
date +"%c: IETF YANG modules copied to $WEB/YANG-modules" >>"$LOG"

#Generate the diff files
# Need to add || true as diff returns 1 in case of different files...
diff "$WEB_PRIVATE"/IETFDraftYANGPageCompilation.html "$WEB_PRIVATE"/IETFDraftYANGPageCompilation-old.html >"$WEB_PRIVATE"/IETFDraftYANGPageCompilation-diff.txt || true
diff "$WEB_PRIVATE"/IETFCiscoAuthorsYANGPageCompilation.html "$WEB_PRIVATE"/IETFCiscoAuthorsYANGPageCompilation-old.html >"$WEB_PRIVATE"/IETFCiscoAuthorsYANGPageCompilation-diff.txt || true
date +"%c: Diff files generated" >>"$LOG"

# create the tar files
cd "$IETFDIR"/YANG-rfc
tar cfz "$WEB_DOWNLOADABLES"/YANG-RFC.tgz *yang >>"$LOG" 2>&1
cd "$IETFDIR"/YANG
tar cfz "$WEB_DOWNLOADABLES"/YANG.tgz *yang >>"$LOG" 2>&1
cd "$IETFDIR"/YANG-all
tar cfz "$WEB_DOWNLOADABLES"/All-YANG-drafts.tgz *yang >>"$LOG" 2>&1
date +"%c: YANG v1.0 tarball files generated" >>"$LOG"

# copy the YANG 1.1 data models in $IETF_DIR/YANG-v11
python "$VIRTUAL_ENV"/ietf_modules_extraction/yang_version_1_1.py >>"$LOG" 2>&1

cd "$IETFDIR"/YANG-v11
tar cvfz "$WEB_DOWNLOADABLES"/YANG-v11.tgz *yang >>"$LOG" 2>&1
date +"%c: YANG v1.1 tarball files generated" >>"$LOG"

python "$VIRTUAL_ENV"/ietf_modules_extraction/gather_ietf_dependent_modules.py >>"$LOG" 2>&1
date +"%c: dependencies copied" >>"$LOG"

date +"%c: reloading cache" >>"$LOG"
read -ra CRED <<<"$(sed 's/\"//g' <<<"$CREDENTIALS")"
curl -s -X POST -u "${CRED[0]}":"${CRED[1]}" "$MY_URI"/api/load-cache >>"$LOG" 2>&1

date +"%c: End of the script!" >>"$LOG"
cd "$VIRTUAL_ENV"
echo "$(date +%c): Modules extraction is successful" >>"$SUCCESSFUL_MESSAGES_LOG"