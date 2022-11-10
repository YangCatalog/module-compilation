# SDO ANALYSIS

<img src=".github/images/coverage.svg" alt="">

---

## Overview
This container's main purpose is to collect the outputs of several open source and proprietary validators run on YANG modules: [pyang](https://github.com/mbj4668/pyang), [yanglint](https://github.com/CESNET/libyang), [yumadump-pro](https://www.yumaworks.com/tools/yang-compiler/), and [confdc](https://www.tail-f.com/management-agent/). This data is then displayed on YANG Catalog's [statistics page](https://yangcatalog.org/private-page).

YANG modules are retrieved from several sources:
- [YangModels/yang](https://github.com/YangModels/yang)
- [openconfig/public](https://github.com/openconfig/public)
- [sysrepo/yang](https://github.com/sysrepo/yang)
- [onf/Snowmass-ONFOpenTransport](https://github.com/OpenNetworkingFoundation/Snowmass-ONFOpenTransport)
- [openroadm/OpenROADM_MSA_Public](https://github.com/OpenROADM/OpenROADM_MSA_Public)
- [mef/YANG-public](https://github.com/MEF-GIT/YANG-public)
- automatically extracted from IETF Internet Drafts and RFCs

YANG modules are extracted from RFCs and Internet Drafts by running [xym](https://github.com/xym-tool/xym) on the text or xml versions of the documents.
When extracting data from IETF documents, the document's metadata is added to the extracted module's properties.

---

Most of the code is in the `bin/` directory and uses `bash` and Python3 scripts.

Some configuration files are in the `conf/` directory including `paths.sh` which defines all paths used by the scripts. This script merely reads the global configuration file `/etc/yangcatalog/yangcatalog.conf` and creates the required environement variables required by the shell scripts.

*Some pre-requisistes are defined in the README.md in bin directory*

## Overall data flow

There are daily and weekly cronjob as described in the `crontab` file:
- `cronjob`: Fetch, extract and validate all modules daily. This also includes modules from archived Internet Drafts once a week.
- `cronjob-drafts`: Check if all modules from Internet Drafts (including archived ones) are populated into YANG Catalog. Runs weekly.

After validation by several validators/compilers, the result is presented in several HTML pages (one per set of models: specific vendor OS version, or set of IETF drafts, ...) but also in several JSON files which are then used by another cronjob of the backend part to populate the YangCatalog main database (Redis). 

## Directory structure

After running all those scripts, the following directories are populated:

- Directory-Section:modules_directory ($MODULES in shell):
- Directory-Section:non_ietf_directory ($NONIETFDIR in shell):
- Directory-Section:ietf_directory ($IETFDIR in shell):
  - `YANG/` correctly extracted models from IETF drafts
  - `YANG-all/` all extracted models (including bad ones) from IETF drafts
  - `YANG-example/` all extracted example models (starting with example- and not with CODE BEGINS/END)
  - `YANG-example-old-rfc/` the hardcoded YANG module example models from old RFCs (not starting with example-)
  - `draft-with-YANG-strict/` all IETF drafts containing YANG model(s), with strict xym rule = True
  - `draft-with-YANG-no-strict/` all IETF drafts containing YANG model(s), with strict xym rule = False
  - `draft-with-YANG-example/` all IETF drafts containing YANG model(s) with examples
  - `YANG-rfc/` correctly extracted models from RFCs
  - `YANG-rfc-extraction/` the typedef, grouping, identity from data models extracted from RFCs
  - `YANG-extraction/` the typedef, grouping, identity from data models correctely extracted from drafts
  - `my-id-mirror/` a mirror of all IETF drafts (rsynch from IETF)
  - `rfc/` a mirror of all IETF RFC (rsynch from IETF)
- ($WEB in shell):
  - `YANG-modules/` all YANG modules extracted from IETF documents (a copy of $IETFDIR/YANG)
- Web-Section:private_directory ($WEBPRIVATE in shell):
  - `<SDO>.json` the list of all YANG modules of the SDO including compilation statistics
  - `<SDO>YANGPageCompilation.html` table of all YANG modules of the SDO including compilation statistics
  - `<SDO>YANGPageMain.html` summary of compilation results for all YANG modules of this SDO
  - `figures/*.png` a couple of graphics including dependency graphs for some modules (ietf-interfaces, ..), for all YANG modules known (heavy graph), and history statistics
  - `stats/*.json` statistics about YANG modules extracted from IETF drafts and RFC 
- Directory-Section:backup ($BACKUPDIR in shell): a history directory containing all files from <SDO> with a date suffix (used to generated the history graphcis)

