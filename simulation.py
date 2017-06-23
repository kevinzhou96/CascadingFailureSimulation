import pypower.api as pp
import networkx as nx
import numpy as np
import copy

BRANCH_P_INDEX = 13

def ppc_to_nx(ppc):
    G = nx.Graph()
    G.add_nodes_from(ppc['bus'][:,0].astype(int))
    G.add_edges_from(ppc['branch'][:,0:2].astype(int))
    return G

def nodeset_to_ppc_subgrid(nodes, ppc):
    new_ppc = copy.deepcopy(ppc)
    # build mask to remove buses not part of the component
    convert_bus_list_to_mask = np.vectorize(lambda x : x in nodes)
    mask = convert_bus_list_to_mask(ppc['bus'][:,0])
    new_ppc['bus'] = ppc['bus'][mask]
    return new_ppc

def nx_to_ppc_components(graph, ppc):
    for component in nx.connected_components(graph):
        sub_ppc = nodeset_to_ppc_subgrid(component, ppc) 
        yield sub_ppc

def get_components(ppc):
    return get_components_as_ppc(ppc_to_nx(ppc), ppc)

def run_simulation(grid, capacities, attack_set, verbose=0, step_limit=-1):
    ppopt = pp.ppoption(VERBOSE=0, OUT_SYS_SUM=0) if verbose else pp.ppoption(VERBOSE=0, OUT_ALL=0)
    failed_lines = []
    failure_history = []
    new_failed_lines = attack_set

    while len(new_failed_lines) > 0 and step_limit:
        # keep track of failed lines
        failure_history.append(new_failed_lines)
        failed_lines.extend(new_failed_lines)
        
        # remove failed lines
        for line in new_failed_lines:
            grid['branch'][line][2], grid['branch'][line][3] = np.inf, np.inf

        sub_grids = get_components(grid)

        # TO BE ADDED
        # - CONVERT GRID TO NETWORKX GRAPH - done
        # - FIND CONNECTED COMPONENTS OF GRAPH - done
        # - CONVERT COMPONENTS BACK INTO PYPOWER CASEFILES - done
        # - REBALANCE POWER GENERATION/LOAD
        # - RUN DC POWER FLOW IN EACH COMPONENT
        # - RECOMBINE COMPONENTS BACK INTO WHOLE GRID

        grid, success = pp.rundcpf(grid, ppopt)
        if not success:
            print("Error: DC Power Flow failed")
            return

        # check for newly failed lines
        new_failed_lines = []
        for i in range(len(grid['branch'])):
            if abs(grid['branch'][i][BRANCH_P_INDEX]) > capacities[i]:
                new_failed_lines.append(i)

        # decrease step counter, if active
        if step_limit > 0:
            step_limit -= 1

    total_flow = sum([grid['branch'][i][BRANCH_P_INDEX] for i in range(len(grid['branch']))])

    output_data = {"failure_history": failure_history,
                   "failed_lines": failed_lines,
                   "total_flow": total_flow,
                   "grid": grid}

    return output_data

def prop_capacity_sim(grid, a, attack_set, verbose=0, step_limit=-1):
    ppopt = pp.ppoption(VERBOSE=0, OUT_SYS_SUM=0) if verbose else pp.ppoption(VERBOSE=0, OUT_ALL=0)
    initial_grid = pp.rundcpf(grid, ppopt)[0]
    capacities = abs(initial_grid['branch'][:,BRANCH_P_INDEX])*(1+a)

    return run_simulation(grid, capacities, attack_set, verbose, step_limit)

def dist_capacity_sim(grid, dist, attack_set, verbose=0, step_limit=-1):
    ppopt = pp.ppoption(VERBOSE=0, OUT_SYS_SUM=0) if verbose else pp.ppoption(VERBOSE=0, OUT_ALL=0)
    initial_grid = pp.rundcpf(grid, ppopt)[0]
    capacities = abs(initial_grid['branch'][:,BRANCH_P_INDEX]) + dist()

    return run_simulation(grid, capacities, attack_set, verbose, step_limit)