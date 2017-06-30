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

def test_ppc_to_nx(iterations=2000):
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
        buses_array_idx = sorted(random.sample(range(118), random.randint(1,118)))
        buses = grid1['bus'][buses_array_idx]
        bus_ids = buses[:, idx_bus.BUS_I].astype(int)
        grid1['bus'] = buses


        del_gens = []
        for i, gen in enumerate(grid1['gen']):
            if int(gen[idx_gen.GEN_BUS]) not in bus_ids:
                del_gens.append(i)
        grid1['gen'] = np.delete(grid1['gen'], del_gens, 0)

        del_branches = []
        for i, branch in enumerate(grid1['branch']):
            if int(branch[idx_brch.F_BUS]) not in bus_ids or int(branch[idx_brch.T_BUS]) not in bus_ids:
                del_branches.append(i)
        grid1['branch'] = np.delete(grid1['branch'], del_branches, 0)

        grid2 = pp.case118()
        grid2 = buses_to_ppc_subgrid(set(bus_ids), grid2)
        
        assert(np.array_equal(grid1['bus'][:, idx_bus.BUS_I], grid2['bus'][:, idx_bus.BUS_I]))
        try:
            assert(np.array_equal(grid1['gen'][:, idx_gen.GEN_BUS], grid2['gen'][:, idx_gen.GEN_BUS]))
        except:
            # no generators in the component
            assert(len(grid1['gen']) == 0)
            assert(grid2['gen'][0, idx_gen.GEN_BUS] not in pp.case118()['gen'][:, idx_gen.GEN_BUS])
        try:
            assert(np.array_equal(grid1['branch'][:, idx_brch.F_BUS], grid2['branch'][:, idx_brch.F_BUS]))
            assert(np.array_equal(grid1['branch'][:, idx_brch.T_BUS], grid2['branch'][:, idx_brch.T_BUS]))
        except:
            assert(len(grid1['branch']) == 0 and len(grid2['branch']) == 0)

def test_nx_to_ppc_components():
    pass

def test_get_components():
    pass

def test_combine_components(iterations=100):
    pass




def runTests():
    print("Running all tests...")

    print("  Testing ppc_to_nx()... ", end='', flush=True)
    test_ppc_to_nx()
    print("success!")
    
    print("  Testing buses_to_ppc_subgrid()... ", end='', flush=True)
    test_buses_to_ppc_subgrid()
    print("success!")
    '''
    print("  Testing nx_to_ppc_components()... ", end='', flush=True)
    test_nx_to_ppc_components()
    print("success!")
    
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