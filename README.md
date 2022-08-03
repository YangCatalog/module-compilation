SDO ANALYSIS
============

This part of YangCatalog.org server fetches all YANG modules from different repositories and also scans all IETF RFCs and drafts for YANG modules.

Once all those modules are retrieved they are validated by several tools.

Most of the code is in the `bin/` directory and uses `bash` and Python3 scripts.

Some configuration files are in the `conf/` directory including `paths.sh` which defines all paths used by the scripts. This script merely reads the global configuration file `/etc/yangcatalog/yangcatalog.conf` and creates the required environement variables required by the shell scripts.

*Some pre-requisistes are defined int he README.md in bin directory*

Overall data flow
-----------------

There are daily and weekly cronjob as described in the `crontab` file:
- `cronjob-daily`: fetch all files (IETF and YangModels repo), but, validates only IETF drafts/RFC and SDO (IEEE, BBF, OpenConfig, ...) YANG models;
- `cronjob-weekly`: fetch all files (IETF and YangModels repo), but, validates only network vendors (Cisco, Juniper, Huawei, ...) YANG models.

After validation by several validators/compilers, the result is presented in several HTML pages (one per set of models: specific vendor OS version, or set of IETF drafts, ...) but also in several .JSON files which are then used by another cronjob of the backend part to populate the YangCatalog main database (that is ConfD database). 

Data source
-----------

The YANG models are either from `https://github.com/YangModels/yang` repository or from the IETF RFC, current IETF drafts and expired IETF drafts (the package `xym` is then used to extract YANG models from the text of RFC & drafts). In the case of IETF, the extracted YANG models are stored in different places (see below) based on their source (RFC vs. draft), ...


Directory structure
-------------------

After running all those scripts, the following directories are populated:

- Directory-Section:modules_directory ($MODULES in shell):
- Directory-Section:non_ietf_directory ($NONIETFDIR in shell):
- Directory-Section:ietf_directory ($IETFDIR in shell):
  - YANG/ correctly extracted models from IETF drafts
  - YANG-all/ all extracted models (including bad ones) from IETF drafts
  - YANG-example/ all extracted example models (starting with example- and not with CODE BEGINS/END)
  - YANG-example-old-rfc/ the hardcoded YANG module example models from old RFCs (not starting with example-)
  - draft-with-YANG-strict/ all IETF drafts containing YANG model(s), with strict xym rule = True
  - draft-with-YANG-no-strict/ all IETF drafts containing YANG model(s), with strict xym rule = False
  - draft-with-YANG-example/ all IETF drafts containing YANG model(s) with examples
  - YANG-rfc/ correctly extracted models from RFCs
  - YANG-rfc-extraction/ the typedef, grouping, identity from data models extracted from RFCs
  - YANG-extraction/ the typedef, grouping, identity from data models correctely extracted from drafts
  - my-id-mirror/ a mirror of all IETF drafts (rsynch from IETF)
  - rfc/ a mirror of all IETF RFC (rsynch from IETF)
- ($WEB in shell):
  - YANG-modules/ all YANG modules extracted from IETF documents (a copy of $IETFDIR/YANG)
- Web-Section:private_directory ($WEBPRIVATE in shell):
  - <SDO>.json the list of all YANG modules of the SDO including compilation statistics
  - <SDO>YANGPageCompilation.html table of all YANG modules of the SDO including compilation statistics
  - <SDO>YANGPageMain.html summary of compilation results for all YANG modules of this SDO
  - figures/*.png a couple of graphics including dependency graphs for some modules (ietf-interfaces, ..), for all YANG modules known (heavy graph), and history statistics
  - stats/*.json statistics about YANG modules extracted from IETF drafts and RFC 
- Directory-Section:backup ($BACKUPDIR in shell): an history directory containing all files from <SDO> with a date suffix (used to generated the history graphcis)

