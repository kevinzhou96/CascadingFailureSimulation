import pypower.api as pp
import networkx as nx
import numpy as np
import copy

import pypower.idx_brch as idx_brch
import pypower.idx_bus as idx_bus
import pypower.idx_gen as idx_gen

"""
components.py - Helper functions for dealing with the connected components of a
disconnected power system
"""

## HELPER FUNCTIONS FOR get_components 

def ppc_to_nx(ppc, includeInactive=False, includeReactance=False):
    """Converts a PYPOWER case file to a NetworkX graph, with nodes labeled with
    bus ID's and edges including reactance values as edge attributes. If
    includeInactive lines is set to True, the graph will include failed lines
    (useful for graph drawing purposes). 

    ARGUMENTS: ppc: dict (representing a PYPOWER case file)
               includeInactive: bool
               includeReactance: bool
    RETURNS:   NetworkX Graph
    """
    G = nx.Graph()
    G.add_nodes_from(ppc['bus'][:, idx_bus.BUS_I].astype(int))
    if includeInactive:
        G.add_edges_from(ppc['branch'][:,0:2].astype(int))
    else:
        # filter out failed lines
        isActive = lambda branch : branch[idx_brch.BR_X] != np.inf
        active_lines = np.array(list(filter(isActive, ppc['branch'])))
        if len(active_lines) > 0:
            # ignore edges for grids with no active lines
            G.add_edges_from(active_lines[:, 0:2].astype(int))

    # add in reactance values (for drawing purposes)
    if includeReactance:
        for edge in ppc['branch']:
            G[int(edge[idx_brch.F_BUS])][int(edge[idx_brch.T_BUS])]['x'] = edge[idx_brch.BR_X]

    return G

def buses_to_ppc_subgrid(buses, ppc):
    """Given a set of buses, reduces a PYPOWER case file to the grid only
    consisting of the buses in the bus set.

    ARGUMENTS: buses: iterable (of bus ID's),
               ppc: dict (representing a PYPOWER case file)
    RETURNS:   dict (representing a PYPOWER case file)
    """
    new_ppc = copy.deepcopy(ppc)

    # remove buses not in bus set
    busInSet = lambda bus : bus[idx_bus.BUS_I] in buses
    new_ppc['bus'] = np.array(list(filter(busInSet, ppc['bus'])))
    if idx_bus.REF not in new_ppc['bus'][:,idx_bus.BUS_TYPE]:
        # set new slack bus if needed
        new_ppc['bus'][0, idx_bus.BUS_TYPE] = idx_bus.REF

    # remove generators not in bus set
    genInSet = lambda gen : gen[idx_gen.GEN_BUS] in buses
    new_ppc['gen'] = np.array(list(filter(genInSet, ppc['gen'])))
    if len(new_ppc['gen']) == 0:
        # create a dummy generator if there are no generators
        new_ppc['gen'] = np.zeros((1,21))
        newGenMask = [idx_gen.GEN_BUS, idx_gen.VG, idx_gen.MBASE, idx_gen.GEN_STATUS]
        newGenVals = np.array([new_ppc['bus'][0, idx_bus.BUS_I], 1, 100, 1])
        new_ppc['gen'][0, newGenMask] = newGenVals
        
    # remove lines not in bus set
    lineInSet = lambda line: line[idx_brch.F_BUS] in buses and line[idx_brch.T_BUS] in buses
    new_ppc['branch'] = np.array(list(filter(lineInSet, ppc['branch'])))

    return new_ppc

def nx_to_ppc_components(graph, ppc):
    """Helper function for get_components. Uses the NetworkX Graph representation
    of a PYPOWER case file to split it into its connected components.

    ARGUMENTS: graph: networkx.Graph,
               ppc: dict (representing a PYPOWER case file)
    RETURNS:   list of dicts (representing PYPOWER case files)
    """
    output = []
    for component in nx.connected_components(graph):
        sub_ppc = buses_to_ppc_subgrid(component, ppc) 
        output.append(sub_ppc)
    return output

## END HELPER FUNCTIONS

def get_components(ppc):
    """Splits a PYPOWER case file into case files for each of its connected 
    components. A nice wrapper function for nx_to_ppc_components().

    ARGUMENTS: ppc: dict (representing a PYPOWER case file)
    RETURNS:   list of dicts (representing PYPOWER case files)
    """
    return nx_to_ppc_components(ppc_to_nx(ppc), ppc)


def combine_components(components, original):
    """Recombines the connected components of a power grid back into a single 
    PYPOWER case file

    ARGUMENTS: components: list of dicts (representing PYPOWER case files)
               original: dict (representing a PYPOWER case file)
    RETURNS:   dict (representing a PYPOWER case file)
    """
    output = copy.deepcopy(original)
    for component in components:
        # update bus data
        buses = set(component['bus'][:,0])
        busInComp = lambda bus : bus[idx_bus.BUS_I] in buses
        bus_mask = np.apply_along_axis(busInComp, 1, original['bus'])
        output['bus'][bus_mask] = component['bus']

        # update generator data
        genInComp = lambda gen : gen[idx_gen.GEN_BUS] in buses
        gen_mask = np.apply_along_axis(genInComp, 1, original['gen'])
        output['gen'][gen_mask] = component['gen']

        # update line data
        lineInComp = lambda line : ((line[idx_brch.F_BUS] in buses)
                                     and (line[idx_brch.T_BUS] in buses))
        line_mask = np.apply_along_axis(lineInComp, 1, original['branch'])

        if len(component['branch']) > 0:
            # only save if there's something to save
            output['branch'][line_mask] = component['branch']

    # ensure no power flowing through failed lines
    isFailed = lambda branch : branch[idx_brch.BR_X] == np.inf
    failed_line_mask = np.apply_along_axis(isFailed, 1, output['branch'])
    output['branch'][failed_line_mask, idx_brch.PF] = 0
    output['branch'][failed_line_mask, idx_brch.PT] = 0    

    return output
