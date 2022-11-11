Module Compilation
============

Parameters
----------

All configuration of all the Python and shell scripts are defined into `configure.sh` (which refers to several files in ../conf). The global configuration file `/etc/yangcatalog/yangcatalog.conf`(from doc repo) must also be updated.

Cronjobs
--------

The file `crontab` contains sample entries for a daily/weekly cronjob. Please note that the first run of each of those must be done, errors and warnings can be ignored for this first run. The subsequent runs should be OK.

Pre-requisites
--------------
It is strongly advised to use virtualenv to ensure a clean Python3 environment
```
virtualenv -p /usr/bin/python3  --system-site-packages
```

The `/etc/yangcatalog/yangcatalog.conf` file be installed. Se https://github.com/YangCatalog/doc

History
-------

By default, /var/yang/backup contains all the main pages and is used to build graphics. It is advised to copy the content of this directory from a old server in order to have access to the history.

### Other packages
install libyang (apt-get or from https://github.com/CESNET/libyang)

install confd from https://developer.cisco.com/site/confD/downloads/

install yangdump-pro from https://www.yumaworks.com/support/download-yumapro-client/ (free but registration is required)

	- copy `/etc/yumapro/yangdump-pro-sample.conf` into `/etc/yumapro/yangdump-pro.conf`
	- copy `/etc/yumapro/yangdump-pro-sample.conf`into `/etc/yumapro/yangdump-pro-allinclusive.conf` and modify the `modpath`option to be like `modpath ".:/var/yang/yang/modules:/var/yang/nonietf/yangmodels/yang/standard/ieee/draft:/var/yang/nonietf/yangmodels/yang/standard/ieee/draft/802.1:/var/yang/nonietf/yangmodels/yang/standard/ieee/draft/802.3:/var/yang/ietf/YANG-all"`(of course updated to reflext your YANG subtree)

Python package https://www.decalage.info/files/HTML.py-0.04.zip (needs to be ported to python3 first...)

`pip3 install pyang`

`pip3 install xym` with line 571 (may depend on the xym version) modified as `with open(os.path.join(srcdir, source_id), encoding='latin-1', errors='ignore') as sf:`

`pip3 install matplotlib`
`pip3 install mpl_finance`
`pip3 install networkx`
