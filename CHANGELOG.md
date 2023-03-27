## Module Compilation Release Notes

* ##### v5.10.1 - 2023-03-20

  * No changes - released with other [deployment submodules](https://github.com/YangCatalog/deployment)

* ##### v5.10.0 - 2023-03-07

  * Extract and store code snippets from draft documents [#3](https://github.com/YangCatalog/module-compilation/issues/3)
  * Code refactoring changes to compile_modules.py and private_page.py scripts [#262](https://github.com/YangCatalog/module-compilation/issues/262)

* ##### v5.9.0 - 2023-01-26

  * YumaPro validator updated to version 21.10-12 [deployment #178](https://github.com/YangCatalog/deployment/issues/178)
  * job_log transformed into function decorator [#252](https://github.com/YangCatalog/module-compilation/issues/252)
  * 'In Progress' status added to the job_log [#250](https://github.com/YangCatalog/module-compilation/issues/250)
  * All the code in repository reorganized into directories [#247](https://github.com/YangCatalog/module-compilation/issues/247)
  * Modules hashing improved to decrease compilation time [#237](https://github.com/YangCatalog/module-compilation/issues/237)

* ##### v5.8.0 - 2022-12-20

  * GitHub Actions environment updated to use Ubuntu 22.04 [deployment #173](https://github.com/YangCatalog/deployment/issues/173)
  * Python base image bumped to version 3.10 [deployment #172](https://github.com/YangCatalog/deployment/issues/172)
  * Unit tests covering check_archived_drafts.py [#240](https://github.com/YangCatalog/module-compilation/issues/240)

* ##### v5.7.0 - 2022-11-11
 
  * Repository renamed from sdo_analysis to module-compilation [deployment #154](https://github.com/YangCatalog/deployment/issues/154)
  * Coverage badge added to the README.md file
  * Coverage report generation adde to GitHub Actions
  * Bugfix: check_archived_drafts.py attempting to use nonexistent directory [#208](https://github.com/YangCatalog/module-compilation/issues/208)
  * Bugfix: Problem with YANGPageMain_ prefix fixed [#223](https://github.com/YangCatalog/module-compilation/issues/223)
  * setUpClass and tearDownClass methods use for tests [#220](https://github.com/YangCatalog/module-compilation/issues/220)
  * README.md file for tests directory added [#218](https://github.com/YangCatalog/module-compilation/issues/218)
  * matplotlibrc file added [#217](https://github.com/YangCatalog/module-compilation/issues/217)
  * Bugfix: Do not report modules with "broken" name [#210](https://github.com/YangCatalog/module-compilation/issues/210)
  * Code reformatted according to the defined style guide [deployment #163](https://github.com/YangCatalog/deployment/issues/163)
  * parsing of modules with pypy3, replaced parsing by using pyang directly [#209](https://github.com/YangCatalog/module-compilation/issues/209)

* ##### v5.6.1 - 2022-10-10

  * Loading xym tool version from .env file [deployment #161](https://github.com/YangCatalog/deployment/issues/161)
  * yang_get_stats.py script refactored [#204](https://github.com/YangCatalog/sdo_analysis/issues/204)

* ##### v5.6.0 - 2022-09-30

  * Unsubscribe functionality added for emails of problematic drafts [#203](https://github.com/YangCatalog/sdo_analysis/issues/203)
  * Overview section added to README.md file [deployment #156](https://github.com/YangCatalog/deployment/issues/156)
  * Fetching .xml files with draft information using rsync [#195](https://github.com/YangCatalog/sdo_analysis/issues/195)
  * Sending email notification to the authors of problematic drafts [#194](https://github.com/YangCatalog/sdo_analysis/issues/194)
  * Storing compilation result of modules from archived drafts [#193](https://github.com/YangCatalog/sdo_analysis/issues/193)

* ##### v5.5.0 - 2022-08-16

  * yang_exclude_bad_drafts.py script removed [#186](https://github.com/YangCatalog/sdo_analysis/issues/186)
  * Unit tests covering gather_ietf_dependent_modules.py [#140](https://github.com/YangCatalog/sdo_analysis/issues/140)
  * Unit tests covering remove_directory_content.py [#140](https://github.com/YangCatalog/sdo_analysis/issues/140)
  * Unit tests covering rename_file_backup.py [#140](https://github.com/YangCatalog/sdo_analysis/issues/140)
  * Unit tests covering yang_version_1_1.py [#140](https://github.com/YangCatalog/sdo_analysis/issues/140)
  * Always populate data to the Redis [#175](https://github.com/YangCatalog/sdo_analysis/issues/175)
  * Metadata generators moved to separate files 
  * Rename files to snake_case naming convention [#189](https://github.com/YangCatalog/sdo_analysis/issues/189)

* ##### v5.4.0 - 2022-07-08

  * Unit tests covering utility.py [#140](https://github.com/YangCatalog/sdo_analysis/issues/140)
  * Unit tests covering private_page.py [#140](https://github.com/YangCatalog/sdo_analysis/issues/140)
  * Unit tests covering file_hasher.py [#140](https://github.com/YangCatalog/sdo_analysis/issues/140)
  * Unit tests covering extract_emails.py [#140](https://github.com/YangCatalog/sdo_analysis/issues/140)
  * Unit tests covering extract_elem.py [#140](https://github.com/YangCatalog/sdo_analysis/issues/140)
  * Set up for Github Actions tests job [#172](https://github.com/YangCatalog/sdo_analysis/issues/172)
  * runYANGgenericstats.sh script organized into functions [#171](https://github.com/YangCatalog/sdo_analysis/issues/171)
  * rundownloadgithub.sh script organized into functions [#167](https://github.com/YangCatalog/sdo_analysis/issues/167)
  * Repeated cloning and deleting of openconfig repo canceled [#166](https://github.com/YangCatalog/sdo_analysis/issues/166)
  * networkx package version upgraded [#165](https://github.com/YangCatalog/sdo_analysis/issues/165)
  * Workaround: iana-if-type@2021-06-21 warnings removed from compilation results [#164](https://github.com/YangCatalog/sdo_analysis/issues/164)
  * Loading URL prefixes from a config file [deployment #141](https://github.com/YangCatalog/deployment/issues/141)
  * Running pyang with pypy3 [#163](https://github.com/YangCatalog/sdo_analysis/issues/163)
  * Creating list of problematic IETF drafts [deployment #139](https://github.com/YangCatalog/deployment/issues/139)
  * Compilation of multiple ETSI versions [#142](https://github.com/YangCatalog/sdo_analysis/issues/142)
  * Scripts arguments cleaned up and reduced [#147](https://github.com/YangCatalog/sdo_analysis/issues/147)

* ##### v5.3.0 - 2022-06-06

  * Python scripts arguments refactored [#141](https://github.com/YangCatalog/sdo_analysis/issues/141)
  * Duplicate messages removed from validators output [#137](https://github.com/YangCatalog/sdo_analysis/issues/137)
  * Yanglint version passed as argument into Docker image build [deployment #137](https://github.com/YangCatalog/deployment/issues/137)
  * Various code adjustments after config file update [deployment #135](https://github.com/YangCatalog/deployment/issues/135)

* ##### v5.2.0 - 2022-05-03

  * Pyang update to version 2.5.3 [deployment #124](https://github.com/YangCatalog/deployment/issues/124)
  * Type checking fixes with pyright [deployment #126](https://github.com/YangCatalog/deployment/issues/126)

* ##### v5.1.0 - 2022-03-28

  * Various changes after YangModels/yang default branch rename [#129](https://github.com/YangCatalog/sdo_analysis/issues/129)
  * extract_emails.py script refactored [#128](https://github.com/YangCatalog/sdo_analysis/issues/128)
  * Compilation functionality moved into separate classes [#127](https://github.com/YangCatalog/sdo_analysis/issues/127)
  * Shared methods/variables moved to the separate files [#126](https://github.com/YangCatalog/sdo_analysis/issues/126)
  * Run yangIetf.py over all the archived drafts once a week [#125](https://github.com/YangCatalog/sdo_analysis/issues/125)
  * Absolute paths removed from validators output [#124](https://github.com/YangCatalog/sdo_analysis/issues/124)
  * Formatting imporved for compilation results files [#119](https://github.com/YangCatalog/sdo_analysis/issues/119)
  * Various pip packages updated

* ##### v5.0.0 - 2022-02-02

  * Pyang update to version 2.5.2 [deployment #113](https://github.com/YangCatalog/deployment/issues/113)
  * Minor updates to checkArchivedDrafts.py cronjob

* ##### v4.3.0 - 2021-12-03

  * Modify data also in Redis when sending patch request to ConfD [#110](https://github.com/YangCatalog/sdo_analysis/issues/110)
  * New cronjob: script will check whether there are no missing modules from drafts [#106](https://github.com/YangCatalog/sdo_analysis/issues/106)

* ##### v4.2.1 - 2021-10-06

  * Hide compilation-result if compilation-status is unknown [#100](https://github.com/YangCatalog/sdo_analysis/issues/100)
  * ConfD update to version 7.6 [deployment #99](https://github.com/YangCatalog/deployment/issues/99)
  * Title changed for HTML page containing compilation result [#99](https://github.com/YangCatalog/sdo_analysis/issues/99)
  * Date of validation added to module compilation results html [#98](https://github.com/YangCatalog/sdo_analysis/issues/98)
  * Bugfix: IETFYANGRFC.json file generating fixed [#96](https://github.com/YangCatalog/sdo_analysis/issues/96)
  * Pass YANGCATALOG_CONFIG_PATH as Docker image argument to crontab [deployment #96](https://github.com/YangCatalog/deployment/issues/96)

* ##### v4.2.0 - 2021-09-09

  * Config loading simplified [deployment #96](https://github.com/YangCatalog/deployment/issues/96)
  * Huawei modules parsing adjustments
  * IANA modules parsing introduced
  * Dockerfile reorganized - image build speed up [#95](https://github.com/YangCatalog/sdo_analysis/issues/95)
  * OpenROADM versions generating fixed [#94](https://github.com/YangCatalog/sdo_analysis/issues/94)
  * Bugfix: Modules compilation status/result overwriting [#52](https://github.com/YangCatalog/sdo_analysis/issues/52)

* ##### v4.1.0 - 2021-08-10

  * Parsers and extractors moved into separate classes [#86](https://github.com/YangCatalog/sdo_analysis/issues/86)
  * Attributions printing moved into separate method

* ##### v4.0.0 - 2021-07-09

  * Pyang update to version 2.5.0 [deployment #85](https://github.com/YangCatalog/deployment/issues/85)
  * YumaPro validator updated to version 20.10-9 [deployment #84](https://github.com/YangCatalog/deployment/issues/84)
  * Bugfix: Credentials provided correctly for cURL command
  * UnicodeDecodeError fixed for parsing modules using libyang [#82](https://github.com/YangCatalog/sdo_analysis/issues/82)
  * Updated libyang build requirements
  * AllYANGPageMain.json stats file created [#88](https://github.com/YangCatalog/sdo_analysis/issues/88)
  * yangGeneric.py running for vendors only on PROD environment by default [#82](https://github.com/YangCatalog/sdo_analysis/issues/82)
  * cronjob-daily and cronjob-weekly merged into one job [#82](https://github.com/YangCatalog/sdo_analysis/issues/82)
  * Bugfix: Parsing modules which have compilation result None correctly [#80](https://github.com/YangCatalog/sdo_analysis/issues/80)
  * Functionality adjustments to parse Huawei models
  * Functionality adjustments to parse Cisco SVO models [#78](https://github.com/YangCatalog/sdo_analysis/issues/78)
  * yang2.amsl.com mailname replaced by yangcatalog.org [deployment #73](https://github.com/YangCatalog/deployment/issues/73)

* ##### v3.2.1 - 2021-05-04

  * Crontab MAILTO variable set during Docker image build [deployment #72](https://github.com/YangCatalog/deployment/issues/72)
  * JSON files generating for future use in Web UI

* ##### v3.2.0 - 2021-04-15

  * FileLock added for protected access to hashes JSON file [#73](https://github.com/YangCatalog/sdo_analysis/issues/73)
  * Number of spawned processes limited to optimize RAM memory load
  * Fix: JSON dictionaries rewriten each time - unnecessary modules are properly removed from JSON files
  * Old log messages in crons-log.log no longer removed after cronjob start
  * YumaPro validator updated to version 20.10-6 [deployment #53](https://github.com/YangCatalog/deployment/issues/53)
  * jinja2 package version bumped

* ##### v3.1.0 - 2021-03-18

  * Directory structure of cloned OpenROADM repo modified [#63](https://github.com/YangCatalog/sdo_analysis/issues/63)
  * Hashing file content with validators version to track modifications [#55](https://github.com/YangCatalog/sdo_analysis/issues/63)
  * xym tool update to version 0.5 [deployment #50](https://github.com/YangCatalog/deployment/issues/50)
  * Removed unnecessary cURL command message [#58](https://github.com/YangCatalog/sdo_analysis/issues/58)

* ##### v3.0.1 - 2021-02-26

  * rsyslog and systemd added to Docker image build [deployment #48](https://github.com/YangCatalog/deployment/issues/48)

* ##### v3.0.0 - 2021-02-10

  * Update Dockerfile
  * ConfD update [deployment #34](https://github.com/YangCatalog/deployment/issues/34)
  * Pyang update to version 2.4.0 [deployment #36](https://github.com/YangCatalog/deployment/issues/36)
  * YumaPro validator update
  * Run more in parallel [#48](https://github.com/YangCatalog/sdo_analysis/issues/48)
  * List cisco xe files correctly [#49](https://github.com/YangCatalog/sdo_analysis/issues/49)
  * Speed up processing of juniper modules [#50](https://github.com/YangCatalog/sdo_analysis/issues/50)
  * Get modules data faster [#51](https://github.com/YangCatalog/sdo_analysis/issues/51)
  * Add health check endpoint
  * Save result of cronjob for admin ui
  * Various major/minor bug fixes and improvements

* ##### v2.0.0 - 2020-08-14

  * Update graphical representation of ietf modules
  * Update Pyang version
  * Various major/minor bug fixes and improvements

* ##### v1.1.0 - 2020-07-16

  * Update Dockerfile
  * Various major/minor bug fixes and improvements

* ##### v1.0.1 - 2020-07-03

  * Various major/minor bug fixes and improvements

* ##### v1.0.0 - 2020-06-23

  * Initial submitted version
