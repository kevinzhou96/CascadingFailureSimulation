import simulation
import random
import numpy as np
import pypower.api as pp
import csv
import sys

import pypower.idx_bus as idx_bus
import pypower.idx_brch as idx_brch
import pypower.idx_gen as idx_gen

def equalize_generation(ppc):
    n_gen = len(ppc['gen'])
    total_load = sum(ppc['bus'][:,idx_bus.PD])
    ppc['gen'][:, idx_gen.PG] = total_load / n_gen
    return ppc

def avg_line_flow(ppc):
    ppc = pp.rundcpf(ppc, pp.ppoption(VERBOSE=0, OUT_ALL=0))[0]
    return np.mean(abs(ppc['branch'][:, idx_brch.PF]))

def equal_freespace(case, freespace, iterations=200, printProgress=1):
    output = dict()

    dist = lambda : freespace
    n_branches = len(case['branch'])
    for k in range(20):
        if printProgress:
            if k % 4 == 0:
                print("%d%%... " % (k*5), end='', flush=True)
        p = k/20
        system_sizes = []
        for i in range(iterations):
            attack_set = random.sample(range(n_branches), round(p*n_branches))
            iter_result = simulation.iid_sim(case, dist, attack_set)
            system_sizes.append(iter_result['system_size'])
        avg_size = np.mean(system_sizes)
        output[p] = avg_size

    return output

def vary_freespace(case, p, iterations=200):
    output = dict()

    n_branches = len(case['branch'])
    avg_line_flow = np.mean(abs((pp.rundcpf(case, pp.ppoption(VERBOSE=0, OUT_ALL=0))[0])['branch'][:,13]))
    for k in range(int(avg_line_flow+1)*2):
        dist = lambda : k+1
        system_sizes = []
        for i in range(iterations):
            attack_set = random.sample(range(n_branches), round(p*n_branches))
            iter_result = simulation.iid_sim(case, dist, attack_set)
            system_sizes.append(iter_result['system_size'])
        avg_size = np.mean(system_sizes)
        output[k+1] = avg_size
    return output

def main(factor, iterations=200, fname='systemsize_analysis.csv'):
    print('Beginning system size analysis...')

    with open(fname, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)

        space = lambda case : avg_line_flow(case) * factor
       # space = lambda case : 10

        print('  running 30 bus test case... ', end='', flush=True)
        writer.writerow(['IEEE 30 bus test case'])
        c30 = equalize_generation(pp.case30())
        out30 = equal_freespace(c30, space(c30), iterations)
        print('finished!')
        for key in sorted(out30.keys()):
            writer.writerow([key, out30[key]])

        print('  running 57 bus test case... ', end='', flush=True)
        writer.writerow([])
        writer.writerow(['IEEE 57 bus test case'])
        c57 = equalize_generation(pp.case57())
        out57 = equal_freespace(c57, space(c57), iterations)
        print('finished!')
        for key in sorted(out57.keys()):
            writer.writerow([key, out57[key]])

        print('  running 118 bus test case... ', end='', flush=True)
        writer.writerow([])
        writer.writerow(['IEEE 118 bus test case'])
        c118 = equalize_generation(pp.case118())
        out118 = equal_freespace(c118, space(c118), iterations)
        print('finished!')
        for key in sorted(out118.keys()):
            writer.writerow([key, out118[key]])

        print('  running 300 bus test case... ', end='', flush=True)
        writer.writerow([])
        writer.writerow(['IEEE 300 bus test case'])
        c300 = equalize_generation(pp.case300())
        out300 = equal_freespace(c300, space(c300), iterations)
        print('finished!')
        for key in sorted(out300.keys()):
            writer.writerow([key, out300[key]])

    print('System size analysis complete!')

if __name__ == '__main__':
    if len(sys.argv) == 4:
        iterations = int(sys.argv[3])
    else:
        iterations = 200

    if len(sys.argv) >= 3:
        factor = float(sys.argv[2])
    else:
        factor = 1

    if len(sys.argv) >= 2:
        fname = sys.argv[1]
    else:
        fname = 'systemsize_analysis.csv'

    main(factor=factor, fname=fname, iterations=iterations)
    