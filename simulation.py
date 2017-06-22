import pypower.api as pp
import numpy as np

BRANCH_P_INDEX = 13


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