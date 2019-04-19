import sys
import yaml
from csv import reader
from subprocess import Popen, PIPE
from datetime import datetime as dt


def get_config():
    yaml_file = "config.yaml"
    try:
        stream = open(yaml_file, 'r')
    except IOError:
        print("[e] cannot read %s ; check if this file exists" % yaml_file)
        sys.exit(-1)
    with stream:
        config = yaml.load(stream)

        # create date object from string
        start = dt.strptime(config['start'], '%d/%m/%Y %H:%M:%S')
        end = dt.strptime(config['end'], '%d/%m/%Y %H:%M:%S')

        return start, end, config['nodes']


def exec_bash(cmd):
    process = Popen(cmd.split(), stdout=PIPE, stderr=PIPE)
    output, error = process.communicate()
    if process.returncode != 0: 
        if "unable to resolve host address" in error.decode('utf-8'):
            print("[e] Grid'5000 API not accessible")
        else:
            print("[e] bash command failed: %s" % error)
        sys.exit(-1)
    return output


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