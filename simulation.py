import pypower.api as pp
import networkx as nx
import numpy as np
import copy

import pypower.idx_brch as idx_brch
import pypower.idx_bus as idx_bus
import pypower.idx_gen as idx_gen

from components import get_components, combine_components
from rescale_power import rescale_power_down, rescale_power_gen

import pdb

DEBUG = 0

"""
simulation.py - main functions for running cascading failure simulation
"""

def run_simulation(grid, capacities, attack_set, verbose=False, step_limit=-1):
    """Runs a cascading failure simulation.

    addition documentation goes here

    INPUT:  grid: dict (representing a PYPOWER case file),
            capacities: list (of the same length as grid['branch']),
            attack_set: iterable (of line numbers),
            verbose: bool,
            step_limit: int
    OUTPUT: dict (containing data about the simulation)
    """
    # initialization
    grid = pp.rundcpf(copy.deepcopy(grid), pp.ppoption(VERBOSE=0, OUT_ALL=0))[0]
    initial_grid = copy.deepcopy(grid)
    ppopt = pp.ppoption(VERBOSE=0, OUT_SYS_SUM=0) if verbose else pp.ppoption(VERBOSE=0, OUT_ALL=0)
    failed_lines = []
    failure_history = []
    new_failed_lines = attack_set

    if DEBUG: counter = 0

    while len(new_failed_lines) > 0 and step_limit:
        if DEBUG: pdb.set_trace()

        # keep track of failed lines
        failure_history.append(new_failed_lines)
        failed_lines.extend(new_failed_lines)
        
        # fail lines
        for line in new_failed_lines:
            grid['branch'][line][idx_brch.BR_R] = np.inf
            grid['branch'][line][idx_brch.BR_X] = np.inf

        # rescale power and run DC power flow in each component
        components = get_components(grid)
        for i, component in enumerate(components):
            rescale_power_gen(component)
            if len(component['branch']) > 0:
                components[i] = pp.rundcpf(component, ppopt)[0]

        # recombine components back to grid
        grid = combine_components(components, grid)
               
        # find failed lines
        new_failed_lines = []
        for i in range(len(grid['branch'])):
            if abs(grid['branch'][i][idx_brch.PF]) > capacities[i]:
                new_failed_lines.append(i)
        

        # decrease step counter, if active
        if step_limit > 0:
            step_limit -= 1

        if DEBUG: counter += 1

    # compute power loss
    initial_power = sum(initial_grid['bus'][:, idx_bus.PD])
    final_power = sum(grid['bus'][:, idx_bus.PD])
    power_loss = (initial_power - final_power) / initial_power

    #compute system size
    initial_size = len(initial_grid['branch'])
    final_size = initial_size - len(failed_lines)
    system_size = final_size / initial_size

    # find isolated (no power generated) components and buses
    isolated_components = []
    isolated_buses = []
    for component in components:
        component_gen = sum(component['gen'][:, idx_gen.PG])
        if component_gen == 0:
            isolated_components.append(component)
            for bus in component['bus']:
                isolated_buses.append(bus)

    output_data = {"failure_history": failure_history,
                   "failed_lines": failed_lines,
                   "system_size": system_size,
                   "power_loss": power_loss,
                   "components": components,
                   "isolated_components": isolated_components,
                   "isolated_buses": isolated_buses,
                   "grid": grid}

    return output_data


def proportional_sim(grid, a, attack_set, verbose=False, step_limit=-1):
    """Runs a cascading failure simulation, with capacities proportional to
    initial load (i.e. C = (1+a)*L).

    See run_simulation() for more details.
    """
    ppopt = pp.ppoption(VERBOSE=0, OUT_SYS_SUM=0) if verbose else pp.ppoption(VERBOSE=0, OUT_ALL=0)
    initial_grid = pp.rundcpf(grid, ppopt)[0]
    capacities = abs(initial_grid['branch'][:, idx_brch.PF])*(1+a)

    return run_simulation(grid, capacities, attack_set, verbose, step_limit)

def iid_sim(grid, dist, attack_set, verbose=False, step_limit=-1):
    """Runs a cascading failure simulation, with capacities given by C = L + S, 
    where S is a random variable drawn from a given distribution.

    See run_simulation() for more details.
    """
    ppopt = pp.ppoption(VERBOSE=0, OUT_SYS_SUM=0) if verbose else pp.ppoption(VERBOSE=0, OUT_ALL=0)
    initial_grid = pp.rundcpf(grid, ppopt)[0]
    capacities = abs(initial_grid['branch'][:, idx_brch.PF]) + dist()

    return run_simulation(grid, capacities, attack_set, verbose, step_limit)
