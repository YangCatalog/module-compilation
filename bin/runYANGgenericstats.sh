#!/bin/bash

# Copyright The IETF Trust 2021, All Rights Reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

wait_for_processes() {
   PIDS=("$@")
   max_processes=4

   if [ $running -eq $max_processes ]; then
      for PID in ${PIDS[@]}; do
         wait $PID || exit 1
      done
      running=0
   fi
}

source configure.sh
export LOG=$LOGS/YANGgenericstats.log
date +"%c: Starting" >$LOG

# Need to set some ENV variables for subsequent calls in .PY to confd...
source $CONFD_DIR/confdrc >>$LOG 2>&1

# BBF, we need to flatten the directory structure
mkdir -p $TMP/bbf >>$LOG 2>&1
rm -f $TMP/bbf/* >>$LOG 2>&1
find $NONIETFDIR/yangmodels/yang/standard/bbf -name "*.yang" -exec cp {} $TMP/bbf/ \; >>$LOG 2>&1

mkdir -p $MODULES >>$LOG 2>&1

curl -s -H "Accept: application/json" $MY_URI/api/search/modules -o "$TMP/all_modules_data.json" >>$LOG 2>&1

date +"%c: forking all sub-processes" >>$LOG

declare -a PIDS
# ETSI v2.6.1
(python $BIN/yangGeneric.py --metadata "ETSI Complete Report: YANG Data Models compilation from https://github.com/etsi-forge/nfv-sol006/tree/v2.6.1" --lint True --prefix ETSI261 --rootdir "$NONIETFDIR/yangmodels/yang/standard/etsi/NFV-SOL006-v2.6.1/" >>$LOG 2>&1) &
PIDS+=("$!")

# ETSI v2.7.1
(python $BIN/yangGeneric.py --metadata "ETSI Complete Report: YANG Data Models compilation from https://github.com/etsi-forge/nfv-sol006/tree/v2.7.1" --lint True --prefix ETSI271 --rootdir "$NONIETFDIR/yangmodels/yang/standard/etsi/NFV-SOL006-v2.7.1/" >>$LOG 2>&1) &
PIDS+=("$!")

# BBF
(python $BIN/yangGeneric.py --metadata "BBF Complete Report: YANG Data Models compilation from https://github.com/BroadbandForum/yang/tree/master" --lint True --prefix BBF --rootdir "$TMP/bbf/" >>$LOG 2>&1) &
PIDS+=("$!")

# Standard MEF
(python $BIN/yangGeneric.py --metadata "MEF: Standard YANG Data Models compilation from https://github.com/MEF-GIT/YANG-public/tree/master/src/model/standard/" --lint True --prefix MEFStandard --rootdir "$NONIETFDIR/mef/YANG-public/src/model/standard/" >>$LOG 2>&1) &
PIDS+=("$!")

# Experimental MEF
(python $BIN/yangGeneric.py --metadata "MEF: Draft YANG Data Models compilation from https://github.com/MEF-GIT/YANG-public/tree/master/src/model/draft/" --lint True --prefix MEFExperimental --rootdir "$NONIETFDIR/mef/YANG-public/src/model/draft/" >>$LOG 2>&1) &
PIDS+=("$!")

# Standard IEEE published
(python $BIN/yangGeneric.py --metadata "IEEE: YANG Data Models compilation from https://github.com/YangModels/yang/tree/master/standard/ieee/published: The 'standard/ieee/published' branch is intended for published standards modules (with approved PARs)." --lint True --prefix IEEEStandard --rootdir "$NONIETFDIR/yangmodels/yang/standard/ieee/published/" >>$LOG 2>&1) &
PIDS+=("$!")

# Standard IEEE drafts
(python $BIN/yangGeneric.py --metadata "IEEE: YANG Data Models compilation from https://github.com/YangModels/yang/tree/master/standard/ieee/draft: The 'standard/ieee/draft' branch is intended for draft modules with an approved Project Authorization Request (PAR)." --lint True --prefix IEEEStandardDraft --rootdir "$NONIETFDIR/yangmodels/yang/standard/ieee/draft/" >>$LOG 2>&1) &
PIDS+=("$!")

# Experimental IEEE
(python $BIN/yangGeneric.py --metadata "IEEE: Draft YANG Data Models compilation from https://github.com/YangModels/yang/tree/master/experimental/ieee: The 'experimental/ieee' branch is intended for IEEE work that does not yet have a Project Authorization Request (PAR)." --lint True --prefix IEEEExperimental --rootdir "$NONIETFDIR/yangmodels/yang/experimental/ieee/" --forcecompilation True >>$LOG 2>&1) &
PIDS+=("$!")

# Standard IANA
(python $BIN/yangGeneric.py --metadata "IANA: Standard YANG Data Models compilation from https://github.com/YangModels/yang/tree/master/standard/iana: The 'standard/iana' branch is intended for IANA-maintained YANG models." --lint True --prefix IANAStandard --rootdir "$NONIETFDIR/yangmodels/yang/standard/iana/" >>$LOG 2>&1) &
PIDS+=("$!")

# Openconfig
(python $BIN/yangGeneric.py --metadata "Openconfig: YANG Data Models compilation from https://github.com/openconfig/public" --lint True --prefix Openconfig --rootdir "$NONIETFDIR/openconfig/public/release/models/" >>$LOG 2>&1) &
PIDS+=("$!")

# ONF Open Transport
(python $BIN/yangGeneric.py --metadata "ONF Open Transport: YANG Data Models compilation from https://github.com/OpenNetworkingFoundation/Snowmass-ONFOpenTransport" --lint True --prefix ONFOpenTransport --rootdir "$NONIETFDIR/onf/Snowmass-ONFOpenTransport" >>$LOG 2>&1) &
PIDS+=("$!")

# sysrepo internal
(python $BIN/yangGeneric.py --metadata "Sysrepo: internal YANG Data Models compilation from https://github.com/sysrepo/yang/tree/master/internal" --lint True --prefix SysrepoInternal --rootdir "$NONIETFDIR/sysrepo/yang/internal/" >>$LOG 2>&1) &
PIDS+=("$!")

# sysrepo applications
(python $BIN/yangGeneric.py --metadata "Sysrepo: applications YANG Data Models compilation from https://github.com/sysrepo/yang/tree/master/applications" --lint True --prefix SysrepoApplication --rootdir "$NONIETFDIR/sysrepo/yang/applications/" >>$LOG 2>&1) &
PIDS+=("$!")

# Wait for all child-processes
for PID in ${PIDS[@]}; do
   wait $PID || exit 1
done

# OpenROADM public
#
# OpenROADM directory structure need to be flatten
# Each branch representing the version is copied to a separate folder
# This allows to run the yangGeneric.py script on multiple folders in parallel
cur_dir=$(pwd)
cd $NONIETFDIR/openroadm/OpenROADM_MSA_Public
branches=$(git branch -a | grep remotes)
for b in $branches; do
   version=${b##*/}
   first_char=${version:0:1}
   if [[ $first_char =~ ^[[:digit:]] ]]; then
      git checkout $version >>$LOG 2>&1
      mkdir -p $TMP/openroadm-public/$version >>$LOG 2>&1
      rm -f $TMP/openroadm-public/$version/* >>$LOG 2>&1
      find $NONIETFDIR/openroadm/OpenROADM_MSA_Public -name "*.yang" -exec cp {} $TMP/openroadm-public/$version/ \; >>$LOG 2>&1
   fi
done

date +"%c: forking all sub-processes for OpenROADM versions" >>$LOG
declare -a PIDS2
running=0
for path in $(ls -d $TMP/openroadm-public/*/); do
   ((running = running + 1))
   version=$(basename $path)
   (python $BIN/yangGeneric.py --metadata "OpenRoadm $version: YANG Data Models compilation from https://github.com/OpenROADM/OpenROADM_MSA_Public/tree/master/model" --lint True --prefix OpenROADM$version --rootdir "$TMP/openroadm-public/$version/" >>$LOG 2>&1) &
   PIDS2+=("$!")
   wait_for_processes "${PIDS2[@]}"
done
# Wait for all child-processes
for PID in ${PIDS2[@]}; do
   wait $PID || exit 1
done
cd $cur_dir

if [ "$IS_PROD" = "True" ]; then
   # Cisco NX
   date +"%c: processing all Cisco NX modules " >>$LOG
   declare -a PIDSNX
   running=0
   for path in $(ls -d $NONIETFDIR/yangmodels/yang/vendor/cisco/nx/*/); do
      meta="NX OS"
      os="NX"
      for path2 in $(ls -d $path); do
         ((running = running + 1))
         git=${path2##*/cisco/nx/}
         yang_removed=${git%/*}
         prefix=${yang_removed#*/}
         prefix2=$(echo $prefix | tr -cd '[:alnum:]')
         (python yangGeneric.py --allinclusive True --metadata "Cisco $meta $prefix from https://github.com/YangModels/yang/tree/main/vendor/cisco/nx/$git" --lint True --prefix Cisco$os$prefix2 --rootdir "$path2" >>$LOG 2>&1) &
         PIDSNX+=("$!")
         wait_for_processes "${PIDSNX[@]}"
      done
   done
   # Wait for all child-processes until move to next OS
   for PID in ${PIDSNX[@]}; do
      wait $PID || exit 1
   done

   # Cisco XE
   date +"%c: processing all Cisco XE modules " >>$LOG
   declare -a PIDSXE
   running=0
   for path in $(ls -d $NONIETFDIR/yangmodels/yang/vendor/cisco/xe/*/); do
      meta="IOS XE"
      os="XE"
      for path2 in $(ls -d $path); do
         ((running = running + 1))
         git=${path2##*/cisco/xe/}
         yang_removed=${git%/*}
         prefix=${yang_removed#*/}
         prefix2=$(echo $prefix | tr -cd '[:alnum:]')
         (python yangGeneric.py --allinclusive True --metadata "Cisco $meta $prefix from https://github.com/YangModels/yang/tree/main/vendor/cisco/xe/$git" --lint True --prefix Cisco$os$prefix2 --rootdir "$path2" >>$LOG 2>&1) &
         PIDSXE+=("$!")
         wait_for_processes "${PIDSXE[@]}"
      done
   done
   # Wait for all child-processes until move to next OS
   for PID in ${PIDSXE[@]}; do
      wait $PID || exit 1
   done

   # Cisco XR
   date +"%c: processing all Cisco XR modules " >>$LOG
   declare -a PIDSXR
   running=0
   for path in $(ls -d $NONIETFDIR/yangmodels/yang/vendor/cisco/xr/*/); do
      meta="IOS XR"
      os="XR"
      for path2 in $(ls -d $path); do
         ((running = running + 1))
         git=${path2##*/cisco/xr/}
         yang_removed=${git%/*}
         prefix=${yang_removed#*/}
         prefix2=$(echo $prefix | tr -cd '[:alnum:]')
         (python yangGeneric.py --allinclusive True --metadata "Cisco $meta $prefix from https://github.com/YangModels/yang/tree/main/vendor/cisco/xr/$git" --lint True --prefix Cisco$os$prefix2 --rootdir "$path2" >>$LOG 2>&1) &
         PIDSXR+=("$!")
         wait_for_processes "${PIDSXR[@]}"
      done
   done
   # Wait for all child-processes until move to next OS
   for PID in ${PIDSXR[@]}; do
      wait $PID || exit 1
   done

   # Cisco SVO
   date +"%c: processing all Cisco SVO modules " >>$LOG
   declare -a PIDSSVO
   running=0
   for path in $(ls -d $NONIETFDIR/yangmodels/yang/vendor/cisco/svo/*/); do
      meta="NCS"
      os="SVO"
      for path2 in $(ls -d $path); do
         ((running = running + 1))
         git=${path2##*/cisco/svo/}
         yang_removed=${git%/*}
         prefix=${yang_removed#*/}
         prefix2=$(echo $prefix | tr -cd '[:alnum:]')
         (python yangGeneric.py --allinclusive True --metadata "Cisco $meta $prefix from https://github.com/YangModels/yang/tree/main/vendor/cisco/svo/$git" --lint True --prefix Cisco$os$prefix2 --rootdir "$path2" >>$LOG 2>&1) &
         PIDSSVO+=("$!")
         wait_for_processes "${PIDSSVO[@]}"
      done
   done
   # Wait for all child-processes until move to next vendor
   for PID in ${PIDSSVO[@]}; do
      wait $PID || exit 1
   done

   date +"%c: processing non Cisco modules " >>$LOG

   # Juniper
   date +"%c: processing Juniper modules " >>$LOG
   declare -a PIDJUNIPER
   running=0
   for i in {14..21}; do
      # Juniper/14.2 does not contain subdirectories
      if [ $i -eq 14 ]; then
         path=$(ls -d $NONIETFDIR/yangmodels/yang/vendor/juniper/$i*/)
         git=${path##*/juniper/}
         yang_removed=${git%/*}
         prefix=${yang_removed#*/}
         prefix2=$(echo $prefix | tr -cd '[:alnum:]')
         python yangGeneric.py --allinclusive True --metadata "JUNIPER $prefix from https://github.com/Juniper/yang/tree/master/$git" --lint True --prefix Juniper$prefix2 --rootdir "$path" >>$LOG 2>&1
      # Juniper/15* does not exist
      elif [ $i -eq 15 ]; then
         continue
      else
         for path in $(ls -d $NONIETFDIR/yangmodels/yang/vendor/juniper/$i*/); do
            for path2 in $(ls -d $path*/); do
               ((running = running + 1))
               git=${path2##*/juniper/}
               yang_removed=${git%/*}
               prefix=${yang_removed#*/}
               prefix2=$(echo $prefix | tr -cd '[:alnum:]')
               (python yangGeneric.py --allinclusive True --metadata "JUNIPER $prefix from https://github.com/Juniper/yang/tree/master/$git" --lint True --prefix Juniper$prefix2 --rootdir "$path2" >>$LOG 2>&1) &
               PIDJUNIPER+=("$!")
               wait_for_processes "${PIDJUNIPER[@]}"
            done
         done
         for PID in ${PIDJUNIPER[@]}; do
            wait $PID || exit 1
         done
         unset PIDJUNIPER
      fi
   done

   # Huawei
   date +"%c: processing Huawei modules " >>$LOG
   declare -a PIDSHUAWEI
   running=0
   for path in $(ls -d $NONIETFDIR/yangmodels/yang/vendor/huawei/network-router/*/); do
      for path2 in $(ls -d $path*/); do
         ((running = running + 1))
         git=${path2##*/network-router/}
         yang_removed=${git%/*}
         version=${yang_removed%/*}
         platform=${yang_removed#*/}
         prefix=$(echo $yang_removed | tr -cd '[:alnum:]')
         (python yangGeneric.py --allinclusive True --metadata "HUAWEI ROUTER $version $platform https://github.com/Huawei/yang/tree/master/network-router/$git" --lint True --prefix NETWORKROUTER$prefix --rootdir "$path2" >>$LOG 2>&1) &
         PIDSHUAWEI+=("$!")
         wait_for_processes "${PIDSHUAWEI[@]}"
      done
   done
   # Wait for all child-processes
   for PID in ${PIDSHUAWEI[@]}; do
      wait $PID || exit 1
   done

   # Ciena
   date +"%c: processing Ciena modules " >>$LOG
   python yangGeneric.py --allinclusive True --metadata "Ciena https://github.com/YangModels/yang/tree/master/vendor/ciena" --lint True --prefix CIENA --rootdir "$NONIETFDIR/yangmodels/yang/vendor/ciena" >>$LOG 2>&1

   # Fujitsu
   date +"%c: processing Fujitsu modules " >>$LOG
   declare -a PIDSFUJITSU
   running=0
   for path in $(find $NONIETFDIR/yangmodels/yang/vendor/fujitsu/FSS2-API-Yang -name "yang"); do
      ((running = running + 1))
      git=${path##*/fujitsu/}
      yang_removed=${git%/*}
      prefix=${yang_removed#*/}
      prefix=$(echo $prefix | tr -cd '[:alnum:]')
      (python yangGeneric.py --allinclusive True --metadata "Fujitsu https://github.com/FujitsuNetworkCommunications/FSS2-Yang/tree/master/$git" --lint True --prefix Fujitsu$prefix --rootdir "$path" >>$LOG 2>&1) &
      PIDSFUJITSU+=("$!")
      wait_for_processes "${PIDSFUJITSU[@]}"
   done
   # Wait for all child-processes
   for PID in ${PIDSFUJITSU[@]}; do
      wait $PID || exit 1
   done

   # Nokia
   date +"%c: processing Nokia modules " >>$LOG
   declare -a PIDSNOKIA
   running=0
   for path in $(ls -d $NONIETFDIR/yangmodels/yang/vendor/nokia/*/); do
      for path2 in $(ls -d $path*/); do
         ((running = running + 1))
         git=${path2##*/7x50_YangModels/}
         yang_removed=${git%/*}
         prefix=${yang_removed#*/}
         prefix=$(echo $prefix | tr -cd '[:alnum:]' | sed 's/latestsros//g')
         (python yangGeneric.py --allinclusive True --metadata "Nokia $git https://github.com/nokia/7x50_YangModels/tree/master/$git" --lint True --prefix Nokia$prefix --rootdir "$path2" >>$LOG 2>&1) &
         PIDSNOKIA+=("$!")
         wait_for_processes "${PIDSNOKIA[@]}"
      done
   done
   # Wait for all child-processes
   for PID in ${PIDSNOKIA[@]}; do
      wait $PID || exit 1
   done
else
   date +"%c: This is not PROD environment - skipping vendor modules parsing" >>$LOG
fi

date +"%c: all sub-process have ended" >>$LOG

# Clean up of the .fxs files created by confdc
date +"%c: cleaning up the now useless .fxs files" >>$LOG
find $NONIETFDIR/ -name *.fxs ! -name fujitsu-optical-channel-interfaces.fxs -print | xargs -r rm >>$LOG 2>&1

# Remove temp directory structure created for parsing OpenROADM and BBF yang modules
rm -rf $TMP/bbf/ >>$LOG 2>&1
rm -rf $TMP/openroadm-public/ >>$LOG 2>&1

date +"%c: reloading cache" >>$LOG
read -ra CRED <<<$(sed 's/\"//g' <<<"$CREDENTIALS")
curl -s -X POST -u "${CRED[0]}":"${CRED[1]}" $MY_URI/api/load-cache >>$LOG 2>&1

date +"%c: End of the script!" >>$LOG
