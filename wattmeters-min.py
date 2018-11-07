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
Last update: 7/11/2018
"""
import re
import sys
import json
import datetime
from csv import reader
from os import path, remove
from subprocess import Popen, PIPE
from datetime import datetime as dt

def exec_bash(cmd):
    process = Popen(cmd.split(), stdout=PIPE, stderr=PIPE)
    output, error = process.communicate()
    if process.returncode != 0: 
        if "unable to resolve host address" in error.decode('utf-8'):
            print("It seems that the Grid'5000 API is not accessible")
        else:
            print("bash command failed: %s" % error)
        sys.exit(-1)
    return output


# variables used for the graph generation
# optimization to avoid to load the file again
graph = False
saved_timestamps = list()
saved_values = list()

def parse_csv(filename, port, output_file, t_start, t_end):
    with open(output_file, 'a') as output_file:
        with open(filename, 'r') as csv_file: 
            csv_reader = reader(csv_file, delimiter=',')

            def search_timestamp(row):
                index = 0
                for item in row:
                    if re.match(r"^([0-9]{10}).([0-9]{9})$", item):
                        return index
                    index += 1
                print("### DEBUG ###")
                print("Could not find timestamp in row\nIgnoring the following line")
                print(row)
                

            for row in csv_reader:
                index = search_timestamp(row)
                if index is None:
                    continue

                if row[index+1] != "OK":
                    print("### DEBUG ###")
                    print('status of wattmeter for the following line is NOT OK')
                    print(row)
                    sys.exit(-1)
                timestamp = row[index]
                short_timestamp = int(timestamp.split('.')[0])
                if t_start <= short_timestamp <= t_end:
                    value = row[index+2+port]
                    output_file.write(timestamp + ' ' + value + '\n')
                    if graph:
                        saved_timestamps.append(float(timestamp))
                        saved_values.append(float(value))
    

if len(sys.argv) < 4:
    print("Required arguments: <node (e.g. nova-1)> <timestamp-start> <timestamp-end>")
    sys.exit()

###
# Prepare date/time variables
timestamp_start = int(sys.argv[2])
start_date = dt.fromtimestamp(timestamp_start)
start_day = start_date.day
start_month = start_date.month
start_year = start_date.year
start_hour = start_date.hour

timestamp_end = int(sys.argv[3])
end_date = dt.fromtimestamp(timestamp_end)
end_day = end_date.day
end_month = end_date.month
end_year = end_date.year
end_hour = end_date.hour


###
# Get wattmeter/port information
node = sys.argv[1].lower()
cluster = node.split('-')[0]
print("Getting wattmeter information from %s" % node)
curl_cmd = "curl -s -k https://api.grid5000.fr/stable/sites/lyon/clusters/" + cluster + "/nodes/" + node
output = exec_bash(curl_cmd).decode('utf-8')
if "401 Unauthorized" in output:
    print("You need to execute this script from WITHIN Grid'5000")
    sys.exit()
json_data = json.loads(output)
pdu = json_data['sensors']['power']['via']['pdu'][0]
wattmeter = pdu['uid']
port = pdu['port']


###
# Remove "power.csv" if existing from previous executions
power_csv = "power.csv"
if path.exists(power_csv):
    print("Removing %s because file aleady exists" % power_csv)
    remove(power_csv)
    

###
# For each hour between start and end, get power values
print("Getting power values")
for year in range(start_year, end_year+1):
    for month in range(start_month, end_month+1):
        for day in range(start_day, end_day+1):
            for hour in range(start_hour, end_hour+1):
                print(" * current working date: %d/%d/%d at %dh" % (day, month, year, hour))

                now = datetime.datetime.now()
                filename="power.csv.%d-%02d-%02dT%02d" % (year, month, day, hour)
                url = "http://wattmetre.lyon.grid5000.fr/data/%s-log/%s" % (wattmeter, filename)
                if day == now.day and month == now.month and year == now.year and hour == now.hour:
                    wget_cmd = "wget %s" % url
                    exec_bash(wget_cmd)
                else:
                    wget_cmd = "wget %s.gz" % url
                    exec_bash(wget_cmd)
                    gzip_cmd = "gunzip -f %s.gz" % filename
                    exec_bash(gzip_cmd)
                parse_csv(filename, port, power_csv, timestamp_start, timestamp_end)
                remove(filename)
                print("   data retrieved and parsed with success")

print("Power values are available in 'power.csv'")

