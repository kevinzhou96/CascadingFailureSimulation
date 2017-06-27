import pypower.api as pp
import networkx as nx
import numpy as np
import copy

import pypower.idx_brch as idx_brch
import pypower.idx_bus as idx_bus
import pypower.idx_gen as idx_gen

from get_components import get_components

def rescale_power_linear(ppc):
    """Rescales power generation or load within a component uniformly among all
    buses to balance generation and load. Only scales values downwards.

    ARGUMENTS: ppc: dict (representing a PYPOWER case file)
    RETURNS:   None (does in-place update of ppc)
    """
    total_gen = sum(ppc['gen'][:, idx_gen.PG])
    total_load = sum(ppc['bus'][:, idx_bus.PD])

    if np.isclose(total_gen, total_load):
        # no need to scale
        return
    elif total_gen > total_load:
        # scale generation down
        scale_factor = total_load / total_gen # note total_gen > 0
        ppc['gen'][:, idx_gen.PG] *= scale_factor
    else: # total_load > total_gen
        # scale load down
        scale_factor = total_gen / total_load # note total_load > 0
        ppc['bus'][:, idx_bus.PD] *= scale_factor

def rescale_power_gen(ppc):
    """Rescales power generation only (not load) within a component uniformly
    among all buses to match load. If total generation is zero, we cannot fulfill
    the load and so load is set to 0.

    ARGUMENTS: ppc: dict (representing a PYPOWER case file)
    RETURNS:   None (does in-place update of ppc)
    """
    total_gen = sum(ppc['gen'][:, idx_gen.PG])
    total_load = sum(ppc['bus'][:, idx_bus.PD])

    if np.isclose(total_gen, 0):
        # no power generated, set loads to zero
        ppc['bus'][:, idx_bus.PD] = np.zeros(len(ppc['bus']))
    elif np.isclose(total_gen, total_load):
        # no need to scale
        return
    else:
        # scale generation down
        scale_factor = total_load / total_gen
        ppc['gen'][:, idx_gen.PG] *= scale_factor

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
        output['branch'][line_mask] = component['branch']

    return output


def run_simulation(grid, capacities, attack_set, debug=False, step_limit=-1):
    """Runs a cascading failure simulation.

    addition documentation goes here

    INPUT:  grid: dict (representing a PYPOWER case file),
            capacities: list (of the same length as grid['branch']),
            attack_set: iterable (of line numbers),
            debug: bool,
            step_limit: int
    OUTPUT: dict (containing data about the simulation)
    """
    # initialization
    grid = pp.rundcpf(copy.deepcopy(grid), pp.ppoption(VERBOSE=0, OUT_ALL=0))[0]
    ppopt = pp.ppoption(VERBOSE=0, OUT_SYS_SUM=0) if debug else pp.ppoption(VERBOSE=0, OUT_ALL=0)
    failed_lines = []
    failure_history = []
    new_failed_lines = attack_set

    counter = 0
    while len(new_failed_lines) > 0 and step_limit:
        print("Running loop number %d" % counter)
        # keep track of failed lines
        failure_history.append(new_failed_lines)
        failed_lines.extend(new_failed_lines)
        
        # fail lines
        for line in new_failed_lines:
            grid['branch'][line][idx_brch.BR_R] = np.inf
            grid['branch'][line][idx_brch.BR_X] = np.inf

        # rescale power and run DC power flow in each component
        components = get_components(grid)
        if len(components) > 1:
            print("%d components before PF" % len(components))
        for i, component in enumerate(components):
            rescale_power_gen(component)
            components[i] = pp.rundcpf(grid, ppopt)[0]

            ## debugging stuff, DELETE_ME
            if len(components) > 1:
                print("component bus data")
                busdatamask = np.zeros(13, dtype=bool)
                busdatamask[[0,2]] = True
                print(component['bus'][:,busdatamask])
                print("component branch data")
                buses = component['bus'][:,idx_bus.BUS_I]
                branches = np.array(list(filter(lambda branch : branch[idx_brch.F_BUS] in buses and branch[idx_brch.T_BUS] in buses, component['branch'])))
                branchdatamask = np.zeros(17, dtype=bool)
                branchdatamask[[0,1,3,13]] = True
                print(branches[:,branchdatamask]) if len(branches) > 0 else print(branches)

        # recombine components back to grid
        grid = combine_components(components, grid)
        
        ## debugging stuff, DELETE_ME
        print("whole grid bus data")
        busdatamask = np.zeros(13, dtype=bool)
        busdatamask[[0,2]] = True
        buses = grid['bus'][:,idx_bus.BUS_I]
        branches = np.array(list(filter(lambda branch : branch[idx_brch.F_BUS] in buses and branch[idx_brch.T_BUS] in buses, component['branch'])))
        branchdatamask = np.zeros(17, dtype=bool)
        branchdatamask[[0,1,3,13]] = True
        print(grid['bus'][:,busdatamask])
        print("whole grid branch data")
        print(grid['branch'][:,branchdatamask])
        pp.printpf(grid)
        
        # find failed lines
        new_failed_lines = []
        for i in range(len(grid['branch'])):
            #print("available capacity in branch %d: %f - %s = %s" % (i,capacities[i],abs(grid['branch'][i][idx_brch.PF]), capacities[i]-abs(grid['branch'][i][idx_brch.PF])))
            if abs(grid['branch'][i][idx_brch.PF]) > capacities[i]:
                new_failed_lines.append(i)
        
        ## debugging stuff, DELETE_ME
        print(new_failed_lines)

        # decrease step counter, if active
        if step_limit > 0:
            step_limit -= 1

        counter += 1

    total_flow = sum(grid['branch'][:, idx_brch.PF])

    output_data = {"failure_history": failure_history,
                   "failed_lines": failed_lines,
                   "total_flow": total_flow,
                   "grid": grid}

    return output_data

def prop_capacity_sim(grid, a, attack_set, debug=False, step_limit=-1):
    """Runs a cascading failure simulation, with capacities proportional to
    initial load (i.e. C = (1+a)*L).

    See run_simulation() for more details.
    """
    ppopt = pp.ppoption(VERBOSE=0, OUT_SYS_SUM=0) if debug else pp.ppoption(VERBOSE=0, OUT_ALL=0)
    initial_grid = pp.rundcpf(grid, ppopt)[0]
    capacities = abs(initial_grid['branch'][:, idx_brch.PF])*(1+a)

    return run_simulation(grid, capacities, attack_set, debug, step_limit)

def dist_capacity_sim(grid, dist, attack_set, debug=False, step_limit=-1):
    """Runs a cascading failure simulation, with capacities given by C = L + S, 
    where S is a random variable drawn from a given distribution.

    See run_simulation() for more details.
    """
    ppopt = pp.ppoption(VERBOSE=0, OUT_SYS_SUM=0) if debug else pp.ppoption(VERBOSE=0, OUT_ALL=0)
    initial_grid = pp.rundcpf(grid, ppopt)[0]
    capacities = abs(initial_grid['branch'][:, idx_brch.PF]) + dist()

    return run_simulation(grid, capacities, attack_set, debug, step_limit)
