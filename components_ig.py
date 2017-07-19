import pypower.api as pp
import igraph as ig
import numpy as np
import copy

import pypower.idx_brch as idx_brch
import pypower.idx_bus as idx_bus
import pypower.idx_gen as idx_gen

def vertex_renumbering(ppc):
    ppc_id_to_ig = dict()
    ig_id_to_ppc = dict()
    for i in range(len(ppc['bus'])):
        bus_id = ppc['bus'][i][idx_bus.BUS_I]
        ppc_id_to_ig[bus_id] = i
        ig_id_to_ppc[i] = bus_id
    return (ppc_id_to_ig, ig_id_to_ppc)

def renumber_branch(branch, refDict):
    branch = copy.deepcopy(branch)
    branch[idx_brch.F_BUS] = refDict[branch[idx_brch.F_BUS]]
    branch[idx_brch.T_BUS] = refDict[branch[idx_brch.T_BUS]]
    return branch

def ppc_to_ig(ppc, includeInactive=False, includeData=False):
    G = ig.Graph()
    n = len(ppc['bus'])
    G.add_vertices(n)
    ppc_id_to_ig = vertex_renumbering(ppc)[0]
    renumber = lambda branch : renumber_branch(branch, ppc_id_to_ig)

    if includeInactive:
        branches = np.apply_along_axis(renumber, 1, ppc['branch'])
    else:
        isActive = lambda branch : branch[idx_brch.BR_X] != np.inf
        active_lines = np.array(list(filter(isActive, ppc['branch'])))
        branches = np.apply_along_axis(renumber, 1, active_lines)
    edges = branches[:, 0:2].astype(int)
    G.add_edges(edges)

    if includeData:
        bus_gen = [0.] * len(ppc['bus'])
        for gen in ppc['gen']:
            bus_gen[ppc_id_to_ig[gen[idx_gen.GEN_BUS]]] = gen[idx_gen.PG]
        bus_loads = ppc['bus'][:, idx_bus.PD]
        loads = branches[:, idx_brch.PF]
        G.vs['gen'] = bus_gen
        G.vs['load'] = bus_loads
        G.es['load'] = loads
        G.es['isFailed'] = np.apply_along_axis(lambda x : x == np.inf, 0, branches[:, idx_brch.BR_X])

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

def ig_to_ppc_components(graph, ppc):
    output = []
    ig_id_to_ppc = vertex_renumbering(ppc)[1]

    output = []
    for component in graph.components():
        buses = [ig_id_to_ppc[vtx] for vtx in component]
        output.append(buses_to_ppc_subgrid(buses, ppc))
    return output

def get_components(ppc):
    return ig_to_ppc_components(ppc_to_ig(ppc), ppc)


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
