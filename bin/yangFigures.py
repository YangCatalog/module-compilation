#!/usr/bin/env python

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

import matplotlib as mpl
mpl.use('Agg') # To prevent using a X-Windows server
from pylab import *
from matplotlib.dates import MonthLocator, DateFormatter
import json

from create_config import create_config


def historical_yangmodule_compiled_readJSON(jsonfile):
    yangmodule_history_json_file = jsonfile
    with open(yangmodule_history_json_file, 'r') as f:
        yangmodule_history = json.load(f)
    print(" Found " + str(len(yangmodule_history)) + " entrie(s) from " + jsonfile) 

    return yangmodule_history


# fonts
fontr = {'family' : 'serif',
        'color'  : 'red',
        'weight' : 'normal',
        'size'   : 16,
        }

fontb = {'family' : 'serif',
        'color'  : 'blue',
        'weight' : 'normal',
        'size'   : 16,
        }
        
fontg = {'family' : 'serif',
        'color'  : 'green',
        'weight' : 'normal',
        'size'   : 16,
        }
               
# every monday
daysFmt = DateFormatter("%d %b '%y")

# every month
months = MonthLocator(range(1, 13), bymonthday=1, interval=1)
monthsFmt = DateFormatter("%b '%y")

# Get some directory values where to store files
config = create_config()
web_directory = config.get('Web-Section', 'private-directory')


# generate stats for Cisco
yangmoduleCisco_history = historical_yangmodule_compiled_readJSON(web_directory + "/stats/IETFCiscoAuthorsYANGPageCompilationStats.json")
if len(yangmoduleCisco_history) == 0:
    print ('Found no data in IETFCiscoAuthorsYANGPageCompilation.json')
    raise SystemExit
yangmoduledates = []
yangmodulesuccess = []
yangmodulewarning = []
yangmoduletotal = []
for key in sorted(yangmoduleCisco_history):
    # the next line: doesn't take an entry with (0,0,0) for (success,failed,warning)
    if yangmoduleCisco_history[key]['success'] != 0 and yangmoduleCisco_history[key]['warning'] != 0 and yangmoduleCisco_history[key]['total'] != 0:
        yangmoduledates.append(float(key))      # Matplot requires a float for dates
        yangmodulesuccess.append(int(yangmoduleCisco_history[key]['success']))
        yangmodulewarning.append(int(yangmoduleCisco_history[key]['warning']))
        yangmoduletotal.append(int(yangmoduleCisco_history[key]['total']))
fig, ax = plt.subplots()
ax.plot(yangmoduledates, yangmodulesuccess, 'g-', yangmoduledates, yangmoduletotal, 'b-', yangmoduledates, yangmodulewarning, 'r-')
ax.set_ylim(bottom=0, auto=False)  # Leave top unset to be dynamic for this one
plt.text(735727, 80, 'TOTAL', fontdict=fontb)
plt.text(735727, 25, 'PASSED', fontdict=fontg)
plt.text(735732,  5, 'WARNING', fontdict=fontr)
ax.xaxis.set_major_formatter(daysFmt)
ax.xaxis.set_minor_locator(months)
plt.ylabel('# YANG Modules')
ax.set_title('Cisco Authored YANG Modules and Submodules: Compilation Results')
ax.autoscale_view()
ax.grid(True)
fig.autofmt_xdate()
ax.xaxis_date()
savefig(web_directory + '/figures/IETFCiscoAuthorsYANGPageCompilation.png', bbox_inches='tight')

# generate stats for the IETF
yangmodule_history = historical_yangmodule_compiled_readJSON(web_directory + "/stats/IETFYANGPageCompilationStats.json")
if len(yangmodule_history) == 0:
    print ('Found no data in IETFYANGPageCompilationStats.json')
    raise SystemExit
yangmoduledates = []
yangmodulesuccess = []
yangmodulewarning = []
yangmoduletotal = []
for key in sorted(yangmodule_history):
    yangmoduledates.append(float(key))
    yangmodulesuccess.append(int(yangmodule_history[key]['success']))
    yangmodulewarning.append(int(yangmodule_history[key]['warning']))
    yangmoduletotal.append(int(yangmodule_history[key]['total']))
fig, ax = plt.subplots()
ax.plot(yangmoduledates, yangmodulesuccess, 'g-', yangmoduledates, yangmoduletotal, 'b-', yangmoduledates, yangmodulewarning, 'r-')
ax.set_ylim(bottom=0, auto=False)  # Leave top unset to be dynamic for this one
plt.text(735697, 95, 'TOTAL', fontdict=fontb)
plt.text(735697, 40, 'PASSED', fontdict=fontg)
plt.text(735712,  5, 'WARNING', fontdict=fontr)
ax.xaxis.set_major_formatter(daysFmt)
ax.xaxis.set_minor_locator(months)
ax.set_ylabel('# YANG Modules')
ax.set_title('IETF YANG Modules and Submodules: Compilation Results')
ax.autoscale_view()
ax.grid(True)
fig.autofmt_xdate()
ax.xaxis_date()
fig.savefig(web_directory + '/figures/IETFYANGPageCompilation.png', bbox_inches='tight')

# generate stats for the IETF RFCs
yangRFC_history = historical_yangmodule_compiled_readJSON(web_directory + "/stats/IETFYANGOutOfRFCStats.json")
if len(yangRFC_history) == 0:
    print ('Found no data in "IETFYANGOutOfRFC.json')
    raise SystemExit
yangmoduledates = []
yangmoduletotal = []
for key in sorted(yangRFC_history):
    yangmoduledates.append(float(key))
    yangmoduletotal.append(int(yangRFC_history[key]['total']))
figure, axes = plt.subplots()
axes.plot(yangmoduledates, yangmoduletotal)
top_max = yangRFC_history[sorted(list(yangRFC_history.keys()))[-1]]
top_max = int(top_max['total']) + 10
axes.set_ylim(bottom=0, top=top_max, auto=False)
axes.xaxis.set_major_formatter(daysFmt)
axes.xaxis.set_minor_locator(months)
axes.set_ylabel('# RFC YANG Modules')
axes.set_title('IETF YANG Modules and Submodules from RFCs')
axes.autoscale_view()
axes.grid(True)
figure.autofmt_xdate()
axes.xaxis_date()
figure.savefig(web_directory + '/figures/IETFYANGOutOfRFC.png', bbox_inches='tight')
