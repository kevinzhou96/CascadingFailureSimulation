import pypower.api as pp
import networkx as nx
import numpy as np
import copy

import pypower.idx_brch as idx_brch
import pypower.idx_bus as idx_bus
import pypower.idx_gen as idx_gen

def ppc_to_nx(ppc):
    """Converts a PYPOWER case file to a NetworkX graph, with nodes labeled with
    bus ID's.

    ARGUMENTS:  ppc: dict (representing a PYPOWER case file)
    RETURNS:   NetworkX Graph
    """
    G = nx.Graph()
    G.add_nodes_from(ppc['bus'][:, 0].astype(int))
    # filter out failed lines
    isActive = lambda bus : bus[idx_brch.BR_X] != np.inf
    active_lines = np.array(list(filter(isActive, ppc['branch'])))
    if len(active_lines) > 0:
        # ignore edges for grids with no active lines
        G.add_edges_from(active_lines[:, 0:2].astype(int))
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
    inBusSet = lambda bus: bus[idx_bus.BUS_I] in buses
    new_ppc['bus'] = np.array(list(filter(inBusSet, ppc['bus'])))

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

def get_components(ppc):
    """Splits a PYPOWER case file into case files for each of its connected 
    components. A nice wrapper function for nx_to_ppc_components().

    ARGUMENTS: ppc: dict (representing a PYPOWER case file)
    RETURNS:   list of dicts (representing PYPOWER case files)
    """
    return nx_to_ppc_components(ppc_to_nx(ppc), ppc)
