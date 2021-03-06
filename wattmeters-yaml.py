#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Script to retrieve value from wattmeters

This Python script downloads and parse power values retrieved
from the new wattmeters installed on the Lyon site of Grid'5000.
It downloads the CVS file/archives of the wattmeter connected to
the node given in parameter for the time interval also given in
parameter. It unzips archives if required and parse the power
data to only retrieve the power value of the given node only.
The output of the script is a file called "power.csv" that
contains a list of keys/values where the key is the timestamp
and the value the power.

Examples:
    $ python wattmeters.py nova-1 1540823060 1540826060
    $ ./wattmeters.py nova-1 1540823060 1540826060

Attributes:
    node (string): name of the node from which to get the power
        values. The given node has to be located in the Lyon site
        of Grid'5000.

    timestamp-start (int): timestamp from when to start getting
        the power values.

    timestamp-stop (int): timestamp from when to stop getting the
        power values.

Script written by David Guyon (david <at> guyon <dot> me).
Creation date: 26/10/2018
Last update:   30/04/2019
"""

import sys
import lib
import json
import pprint
import datetime
from os import path, remove


# Getting configuration from YAML file
start, end, nodes = lib.get_config()

###
# Get wattmeter/port information
analyzed_nodes = dict()
for node in nodes:
    cluster = node.split('-')[0]
    print("Getting wattmeter information from %s" % node)
    curl_cmd = "curl -s -k https://api.grid5000.fr/stable/sites/lyon/clusters/" + cluster + "/nodes/" + node
    output = lib.exec_bash(curl_cmd).decode('utf-8')
    if "401 Unauthorized" in output:
        print("You need to execute this script from WITHIN Grid'5000")
        sys.exit()
    json_data = json.loads(output)

    # skip node if not equiped with wattmeter
    if not json_data['sensors']['power']['per_outlets']:
        print("[w] node %s ignored because it is not equiped with a wattmeter" % node)
        continue

    pdu = json_data['sensors']['power']['via']['pdu'][0]
    wattmeter = pdu['uid']
    port = pdu['port']
    if wattmeter not in analyzed_nodes:
        # create wattmeter entry in dict
        analyzed_nodes[wattmeter] = dict()
    analyzed_nodes[wattmeter][port] = node

#pprint.pprint(analyzed_nodes)

###
# Download raw data and uncompress if needed
print("Getting power values")
analyzed_hour = lib.date_to_hour(start)
end_hour = lib.date_to_hour(end)
current_hour = lib.get_current_hour()
total_size = 0
while analyzed_hour <= end_hour:
    print(" * dowloading raw data for date %s" % analyzed_hour.strftime("%d %b %Y at %HH"))
    filename="power.csv.%s" % analyzed_hour.strftime("%Y-%m-%dT%H")
    for wattmeter in analyzed_nodes.keys():
        url = "http://wattmetre.lyon.grid5000.fr/data/%s-log/%s" % (wattmeter, filename)
        # if analyzed hour is equal to current hour
        if analyzed_hour >= current_hour:
            lib.exec_bash("wget %s" % url)
            lib.exec_bash('mv %s %s-%s' % (filename, filename, wattmeter))
        # if not...
        else:
            lib.exec_bash("wget %s.gz" % url)
            lib.exec_bash('mv %s.gz %s-%s.gz' % (filename, filename, wattmeter))
            lib.exec_bash("gunzip -f %s-%s.gz" % (filename, wattmeter))
        # save total downloaded size of data
        total_size += path.getsize("%s-%s" % (filename, wattmeter))
    analyzed_hour += datetime.timedelta(hours=1)
print(" * total downloaded size: %dMB" % (total_size/1000000))
sys.exit(1)


###
# Remove "power.csv" if existing from previous executions
power_csv = "power.csv"
if path.exists(power_csv):
    print("Removing %s because file aleady exists" % power_csv)
    remove(power_csv)


###
# For each hour between start and end, get power values
print("Getting power values")
# /!\ this loop does not work properly (i.e. 28/08/2019 -> 02/09/2019, day range is wrong)
# TO BE FIXED IN LATER VERSION
for year in range(start.year, end.year+1):
    for month in range(start.month, end.month+1):
        for day in range(start.day, end.day+1):
            for hour in range(start.hour, end.hour+1):
                print(" * current working date: %d/%d/%d at %dh" % (day, month, year, hour))

                now = datetime.datetime.now()
                filename="power.csv.%d-%02d-%02dT%02d" % (year, month, day, hour)
                url = "http://wattmetre.lyon.grid5000.fr/data/%s-log/%s" % (wattmeter, filename)
                if day == now.day and month == now.month and year == now.year and hour == now.hour:
                    wget_cmd = "wget %s" % url
                    lib.exec_bash(wget_cmd)
                else:
                    wget_cmd = "wget %s.gz" % url
                    lib.exec_bash(wget_cmd)
                    gzip_cmd = "gunzip -f %s.gz" % filename
                    lib.exec_bash(gzip_cmd)
                lib.parse_csv(filename, port, power_csv, timestamp_start, timestamp_end)
                remove(filename)
                print("   data retrieved and parsed with success")

print("Power values are available in 'power.csv'")

