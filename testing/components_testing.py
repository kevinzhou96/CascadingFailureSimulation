import pypower.api as pp
import networkx as nx
import numpy as np
import copy
import random

import pypower.idx_brch as idx_brch
import pypower.idx_bus as idx_bus
import pypower.idx_gen as idx_gen

import sys
sys.path.insert(0, '../')
from components import *

def test_ppc_to_nx(iterations=1000):
    for i in range(iterations):
        grid = pp.case118()
        all_branches = grid['branch'][:,0:2]
        branches = sorted(random.sample(range(1,187), random.randint(0,186)))
        del_branches = sorted(list(set(range(1,187)) - set(branches)))
        branches = [1,2,3]
        del_branches = list(range(4,187))
        grid['branch'][np.array(del_branches, dtype=int)-1, idx_brch.BR_X] = np.inf

        graph = nx.Graph()
        graph.add_nodes_from(range(1,119))
        graph.add_edges_from(all_branches[np.array(branches)-1].astype(int))
        assert(nx.could_be_isomorphic(ppc_to_nx(grid), graph))

def test_buses_to_ppc_subgrid(iterations=2000):
    # out of date
    for i in range(iterations):
        grid1 = pp.case118()
        buses = sorted(random.sample(range(1,119), random.randint(0,118)))
        del_buses = sorted(list(set(range(1,119)) - set(buses)))
        grid1['bus'] = np.delete(grid1['bus'], np.array(del_buses, dtype=int)-1, 0)

        grid2 = pp.case118()
        grid2 = buses_to_ppc_subgrid(set(buses), grid2)
        
        for key in grid1:
            try:
                assert(np.array_equal(grid1[key],grid2[key]))
            except:
                assert(len(grid1[key]) == 0 and len(grid2[key]) == 0)

def test_nx_to_ppc_components():
    pass

def test_get_components():
    pass

def test_combine_components():
    pass

def runTests():
    print("Running all tests...")

    print("  Testing ppc_to_nx()... ", end='', flush=True)
    test_ppc_to_nx()
    print("success!")

    print("  Testing buses_to_ppc_subgrid()... ", end='', flush=True)
    test_buses_to_ppc_subgrid()
    print("success!")
    
    print("  Testing nx_to_ppc_components()... ", end='', flush=True)
    test_nx_to_ppc_components()
    print("success!")
    '''
    print("  Testing get_components()... ", end='', flush=True)
    test_get_components()
    print("success!")

    print("  Testing combine_components()... ", end='', flush=True)
    test_combine_components()
    print("success!")
    '''
    print("All tests completed successfully!")

if __name__ == '__main__':
    runTests()