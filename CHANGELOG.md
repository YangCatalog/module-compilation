## SDO Analysis Release Notes

* ##### vm.m.p - 2021-MM-DD

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
