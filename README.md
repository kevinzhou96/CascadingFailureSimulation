# Cascading Failure Simulation

## Overview

Simulates the propagation of branch failures in power systems under a variety of power redistribution rules.

## Usage information

Our simulation runs on Python 3 and requires installation of the PYPOWER package. Installation instructions can be found here: https://github.com/rwl/PYPOWER. Running the simulation requires a small change to the PYPOWER code - in the file loadcase.py (located in the directory that PYPOWER was installed), line 14 (reproduced below)
```python
from numpy import array, zeroes, ones, c_
```
should be modified to include `inf`, i.e. it should read
```python
from numpy import array, zeores, ones, c_, inf
```

PYPOWER documentation for command line use can be found here: https://rwl.github.io/PYPOWER/, while documentation for its Python API can be found here: http://rwl.github.io/PYPOWER/api/