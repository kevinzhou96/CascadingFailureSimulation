import simulation
import random
import numpy as np
import pypower.api as pp
import csv
import sys
import copy
import json
import signal

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

def equal_freespace(case, freespace, minAttack, maxAttack, interval,
                    iterations=200, printProgress=False):
    output = dict()
    output['average'] = dict()
    output['raw'] = dict()

    dist = lambda : freespace
    n_branches = len(case['branch'])
        
    for attack_size in range(minAttack, maxAttack, interval):
        if printProgress:
            progress = attack_size/(maxAttack-minAttack)
            print("\r%d%%... " % round(progress*100), end='', flush=True)

        system_sizes = []
        for i in range(iterations):
            attack_set = random.sample(range(n_branches), attack_size)
            iter_result = simulation.iid_sim(case, dist, attack_set)
            system_sizes.append(iter_result['system_size'])
        avg_size = np.mean(system_sizes)
        output['average'][attack_size] = avg_size
        output['raw'][attack_size] = copy.deepcopy(system_sizes)

    return output


def analyze_csvout(factor, minAttack, maxAttack, interval, fname, iterations=200):
    print('Beginning system size analysis...')

    with open(fname, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)

        #space = lambda case : avg_line_flow(case) * factor
        space = lambda case : 100

        print('  running 30 bus test case... ')
        writer.writerow(['IEEE 30 bus test case'])
        #c30 = equalize_generation(pp.case30())
        c30 = pp.case30()
        out30 = equal_freespace(c30, space(c30), 0, len(c30['branch']), interval,
                                iterations=iterations, printProgress=True)
        print('    finished!')
        for key in sorted(out30['average'].keys()):
            writer.writerow([key, out30[key]])

        print('  running 57 bus test case... ')
        writer.writerow([])
        writer.writerow(['IEEE 57 bus test case'])
        #c57 = equalize_generation(pp.case57())
        c57 = pp.case57()
        out57 = equal_freespace(c57, space(c57), 0, len(c57['branch']), interval,
                                iterations=iterations, printProgress=True)
        print('    finished!')
        for key in sorted(out57['average'].keys()):
            writer.writerow([key, out57[key]])

        print('  running 118 bus test case... ')
        writer.writerow([])
        writer.writerow(['IEEE 118 bus test case'])
        #c118 = equalize_generation(pp.case118())
        c118 = pp.case118()
        out118 = equal_freespace(c118, space(c118), 0, len(c118['branch']), interval,
                                 iterations=iterations, printProgress=True)
        print('    finished!')
        for key in sorted(out118.keys()):
            writer.writerow([key, out118['average'][key]])

        print('  running 300 bus test case... ')
        writer.writerow([])
        writer.writerow(['IEEE 300 bus test case'])
        #c300 = equalize_generation(pp.case300())
        c300 = pp.case300()
        out300 = equal_freespace(c300, space(c300), 0, len(c300['branch']), interval,
                                 iterations=iterations, printProgress=True)
        print('    finished!')
        for key in sorted(out300.keys()):
            writer.writerow([key, out300['average'][key]])

    print('System size analysis complete!')


def analyze_jsonout(space, minAttack, maxAttack, interval, fname, iterations=200):
    print("Beginning system size analysis...")

    results = dict()

    print('  running 30 bus test case... ', end='', flush=True)
    c30 = pp.case30()
    n_b = len(c30['branch'])
    results['30bus'] = equal_freespace(c30, space, int(n_b * minAttack), int(n_b * maxAttack),
                                       interval, iterations=iterations)
    print('finished!')

    print('  running 57 bus test case... ', end='', flush=True)
    c57 = pp.case57()
    n_b = len(c57['branch'])
    results['57bus'] = equal_freespace(c57, space, int(n_b * minAttack), int(n_b * maxAttack),
                                       interval, iterations=iterations)
    print('finished!')

    print('  running 118 bus test case... ', end='', flush=True)
    c118 = pp.case118()
    n_b = len(c118['branch'])
    results['118bus'] = equal_freespace(c118, space, int(n_b * minAttack), int(n_b * maxAttack),
                                       interval, iterations=iterations)
    print('finished!')

    print('  running 300 bus test case... ', end='', flush=True)
    c300 = pp.case300()
    n_b = len(c300['branch'])
    results['300bus'] = equal_freespace(c300, space, int(n_b * minAttack), int(n_b * maxAttack),
                                       interval, iterations=iterations)
    print('finished!')

    with open(fname, 'w') as outfile:
        json.dump(results, outfile)

    print("Full system size analysis complete!")


def json_to_csv(in_fname, out_fname):
    with open(in_fname, 'r') as infile:
        data = json.load(infile)

    with open(out_fname, 'w', newline='') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(['IEEE 30-bus test case'])
        for key in sorted(data['30bus']['average'].keys()):
            writer.writerow([key, data['30bus']['average'][key]])

        writer.writerow([])
        writer.writerow(['IEEE 57-bus test case'])
        for key in sorted(data['57bus']['average'].keys()):
            writer.writerow([key, data['57bus']['average'][key]])
        
        writer.writerow([])
        writer.writerow(['IEEE 118-bus test case'])
        for key in sorted(data['118bus']['average'].keys()):
            writer.writerow([key, data['118bus']['average'][key]])

        writer.writerow([])
        writer.writerow(['IEEE 300-bus test case'])
        for key in sorted(data['300bus']['average'].keys()):
            writer.writerow([key, data['300bus']['average'][key]])

    return


def main(space, minAttack, maxAttack, interval, fname, iterations=200):
    analyze_jsonout(space, minAttack, maxAttack, interval, fname, iterations=iterations)

if __name__ == '__main__':
    if len(sys.argv) == 4:
        iterations = int(sys.argv[3])
    else:
        iterations = 200

    if len(sys.argv) >= 3:
        space = float(sys.argv[2])
    else:
        space = 10

    if len(sys.argv) >= 2:
        fname = sys.argv[1]
    else:
        fname = 'systemsize_analysis.txt'

    main(space=space, fname=fname, iterations=iterations, minAttack=0, maxAttack=1, interval=1)
    #analyze_300_eqspace()
