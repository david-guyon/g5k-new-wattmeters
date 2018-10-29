# Retrieving power values from new Grid'5000 wattmeters

Python script to retrieve power values from new wattmeters installed on Lyon site of Grid'5000. These wattmeters deliver 50 values per second with a 0.125W resolution.

You need to execute this script from **within** Grid'5000. It generates a _power.csv_ file that contains powers value of the node given in parameter. The range of data depends on start/end timestamps given in parameters.

### Example:

'''
python wattmeters.py nova-1 1540562403 1540567403 
'''

### Inputs:

- name of node (string)
- timestamp start (int)
- timestamp end (int)

### Output:
- _power.csv_

For more information, documentation is available in header of Python script.
