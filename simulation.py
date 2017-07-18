import pypower.api as pp
import networkx as nx
import numpy as np
import copy

import pypower.idx_brch as idx_brch
import pypower.idx_bus as idx_bus
import pypower.idx_gen as idx_gen

from components import get_components, combine_components
from rescale_power import rescale_power_down, rescale_power_gen


def system_summary(grid, components, capacities):
    out_string = ''

    # print bus data
    out_string += '\nBus Data'
    out_string += '\n' + '=' * 80
    out_string += '\n  Bus #     Gen      Load  '
    out_string += '\n -------  -------  --------'
    for i in range(len(grid['bus'])):
        bus = grid['bus'][i]
        bus_i = bus[idx_bus.BUS_I]
        for gen in grid['gen']:
            if gen[idx_gen.GEN_BUS] == bus_i:
                pg = gen[idx_gen.PG]
            else:
                pg = 0.
        load = bus[idx_bus.PD]
        out_string += '\n%6d%10.3f%10.3f' % (bus_i, pg, load)
    out_string += '\n          -------  --------'
    out_string += '\n Total: %9.3f%10.3f' % (sum(grid['gen'][:, idx_gen.PG]), sum(grid['bus'][:, idx_bus.PD]))
    out_string += '\n'
    # print branch data
    out_string += '\nBranch Data'
    out_string += '\n' + '=' * 80
    out_string += '\n Brch    From     To    Failed     Flow        Cap        Diff       Pct '
    out_string += '\n------  ------  ------  ------  ----------  ---------  ----------  -------'
    for i in range(len(grid['branch'])):
        branch = grid['branch'][i]
        f_bus = branch[idx_brch.F_BUS]
        t_bus = branch[idx_brch.T_BUS]
        is_failed = branch[idx_brch.BR_X] == np.inf
        failed = 'Y' if is_failed else 'N'
        flow = '-' if is_failed else abs(branch[idx_brch.PF])
        cap = capacities[i]
        diff = '-' if is_failed else cap - flow
        pct = '-' if is_failed else (flow / cap) * 100
        if is_failed:
            out_string += '\n%5d%8d%8d      %s        %s%15.3f        %s         %s' % (i, f_bus, t_bus, failed, flow, cap, diff, pct)
        else:
            out_string += '\n%5d%8d%8d      %s  %11.3f%11.3f%12.3f%9.2f' % (i, f_bus, t_bus, failed, flow, cap, diff, pct)
        out_string += '\n'
    # print component data
    out_string += '\nComponent Data'
    out_string += '\n' + '=' * 80
    out_string += '\n Comp     Buses'
    out_string += '\n------  ---------'
    for i in range(len(components)):
        out_string += '\n   %s    %s' % (i, list(components[i]['bus'][:, idx_bus.BUS_I].astype(int)))

    return out_string


"""
simulation.py - main functions for running cascading failure simulation
"""

def run_simulation(grid, capacities, attack_set, detail=False):
    """Runs a cascading failure simulation.

    addition documentation goes here

    INPUT:  grid: dict (representing a PYPOWER case file),
            capacities: list (of the same length as grid['branch']),
            attack_set: list (of line indices),
            verbose: bool,
            step_limit: int
    OUTPUT: dict (containing data about the simulation)
    """
    # initialization
    if 'areas' in grid:
        del grid['areas']
    ppopt = pp.ppoption(VERBOSE=0, OUT_ALL=0)
    grid = pp.rundcpf(grid, ppopt)[0]
    # record initial data
    initial_power = sum(grid['bus'][:, idx_bus.PD])
    initial_size = len(grid['branch'])
    # initialize data structures
    failed_lines = []
    failure_history = []
    new_failed_lines = attack_set
    components = []

    if detail:
        counter = 0
        print("Initial system summary:")
        print(system_summary(grid, [grid], capacities))
        print("Lines to fail: %s" % new_failed_lines)


    while len(new_failed_lines) > 0:
        if detail:
            print()
            temp = input("About to run loop %d. Press enter to continue." % counter)

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

        if detail:
            print(system_summary(grid, components, capacities))
            print("Lines to fail: %s" % new_failed_lines)
            counter += 1
        

    # compute power loss
    final_power = sum(grid['bus'][:, idx_bus.PD])
    power_loss = (initial_power - final_power) / initial_power

    #compute system size
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


def proportional_sim(grid, a, attack_set, detail=False):
    """Runs a cascading failure simulation, with capacities proportional to
    initial load (i.e. C = (1+a)*L).

    See run_simulation() for more details.
    """
    ppopt = pp.ppoption(VERBOSE=0, OUT_ALL=0)
    initial_grid = pp.rundcpf(grid, ppopt)[0]
    capacities = abs(initial_grid['branch'][:, idx_brch.PF])*(1+a)

    return run_simulation(grid, capacities, attack_set, detail)

def iid_sim(grid, dist, attack_set, detail=False):
    """Runs a cascading failure simulation, with capacities given by C = L + S, 
    where S is a random variable drawn from a given distribution.

    See run_simulation() for more details.
    """
    ppopt = pp.ppoption(VERBOSE=0, OUT_ALL=0)
    initial_grid = pp.rundcpf(grid, ppopt)[0]
    capacities = abs(initial_grid['branch'][:, idx_brch.PF]) + dist()

    return run_simulation(grid, capacities, attack_set, detail)
