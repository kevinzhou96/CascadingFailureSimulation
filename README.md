# Cascading Failure Simulation

## Overview

Simulates the propagation of branch failures in power systems under a variety of power redistribution rules.

## Usage information

Our simulation runs on Python 3. It also requires the installation of a few Python packages, listed below:

1. PYPOWER

...PYPOWER is a module for running power flow simulations. PYPOWER installation instructions can be found here: https://github.com/rwl/PYPOWER. It can be installed with pip:
```
$ pip install pypower
```
...Running the simulation requires a small change to the PYPOWER code - in the file loadcase.py (located in the directory that PYPOWER was installed), line 14 (reproduced below)
```python
from numpy import array, zeroes, ones, c_
```
...should be modified to include `inf`, i.e. it should read
```python
from numpy import array, zeores, ones, c_, inf
```
...PYPOWER documentation for command line use can be found here: https://rwl.github.io/PYPOWER/, while documentation for its Python API can be found here: http://rwl.github.io/PYPOWER/api/

2. NetworkX

...NetworkX is a module for modeling graphs. We use it to find connected components in the power system topology after lines have failed. Installation instructions, and a link to documentation, can be found here: https://github.com/networkx/networkx. It can be installed with pip:
```
$ pip install networkx
```
