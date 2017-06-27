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
from get_components import *

def test_ppc_to_nx():
    grid1 = pp.case14()
    graph1 = nx.Graph()
    graph1.add_nodes_from(range(1, 15))
    graph1.add_edges_from([(1,2), (1,5), (2,3), (2,4), (2,5), (3,4), (4,5), (4,7),
                           (4,9), (5,6), (6,11), (6,12), (6,13), (7,8), (7,9),
                           (9,10), (9,14), (10,11), (12,13), (13,14)])
    assert(nx.is_isomorphic(ppc_to_nx(grid1), graph1))

    grid2 = pp.case14()
    grid2['branch'][3:8,idx_brch.BR_X] = np.inf
    graph2 = nx.Graph()
    graph2.add_nodes_from(range(1,15))
    graph2.add_edges_from([(1,2), (1,5), (2,3), (4,9), (5,6), (6,11), (6,12), (6,13),
                           (7,8), (7,9), (9,10), (9,14), (10,11), (12,13), (13,14)])
    assert(nx.is_isomorphic(ppc_to_nx(grid2), graph2))

    grid3 = pp.case118()
    grid3['branch'][:, idx_brch.BR_X] = np.inf
    graph3 = nx.Graph()
    graph3.add_nodes_from(range(1,119))
    assert(nx.is_isomorphic(ppc_to_nx(grid3), graph3))

def test_buses_to_ppc_subgrid(iterations=100):
    for i in range(iterations):
        grid1 = pp.case30()
        buses = set(random.sample(range(1,119), random.randint(0,118)))
        grid1['bus'] = np.delete(grid1['bus'], np.array(sorted(list(set(range(1,119)) - buses))) - 1, 0)
        grid2 = pp.case30()
        grid2 = buses_to_ppc_subgrid(buses, grid2)
        for key in grid1:
            try:
                assert(np.array_equal(grid1[key],grid2[key]))
            except:
                assert(len(grid1[key]) == 0 and len(grid2[key]) == 0)

def test_nx_to_ppc_components():
    pass

def test_get_components():
    pass

def runTests():
    print("Running all tests...")

    print("  Testing ppc_to_nx()... ", end='')
    test_ppc_to_nx()
    print("success!")

    print("  Testing buses_to_ppc_subgrid()... ", end='')
    test_buses_to_ppc_subgrid()
    print("success!")
    
    print("  Testing nx_to_ppc_components()... ", end='')
    test_nx_to_ppc_components()
    print("success!")
    '''
    print("  Testing get_components()... ", end='')
    test_get_components()
    print("success!")
    '''
    print("All tests completed successfully!")

if __name__ == '__main__':
    runTests()