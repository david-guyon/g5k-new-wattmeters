# Retrieving power values from new Grid'5000 wattmeters

Python script to retrieve power values from new wattmeters installed on Lyon site of Grid'5000. These wattmeters deliver 50 values per second with a 0.125W resolution.

You need to execute this script from **within** Grid'5000. It generates a _power.csv_ file that contains powers value of the node given in parameter. The range of data depends on start/end timestamps given in parameters. An optional parameter ("graph") enables the generation of a graph based on Matplotlib. However, this feature is very simplistic.

A minimal version of the script exists (wattmeters-min.py). This version does not include the graph generation feature and thus, does not need the Matplotlib tool suite. I would recommand using this version if you don't want to install several python/system packages.

### Example:

```
python wattmeters.py nova-1 1540562403 1540567403 
python wattmeters.py nova-1 1540562403 1540567403 graph 
python wattmeters-min.py nova-1 1540562403 1540567403
```

### Inputs:

- name of node (string)
- timestamp start (int)
- timestamp end (int)
- "graph" (string) -- optional and only compatible with the non-minimal version

### Output:
- _power.csv_

For more information, documentation is available in header of Python script.
