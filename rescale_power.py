import pypower.api as pp
import networkx as nx
import numpy as np
import copy

import pypower.idx_brch as idx_brch
import pypower.idx_bus as idx_bus
import pypower.idx_gen as idx_gen

def rescale_power_down(ppc):
    """Rescales power generation or load within a component uniformly among all
    buses to balance generation and load. Only scales values downwards.

    ARGUMENTS: ppc: dict (representing a PYPOWER case file)
    RETURNS:   None (does in-place update of ppc)
    """
    buses = set(ppc['bus'][:,idx_bus.BUS_I].astype(int))
    genInComponent = lambda gen : int(gen[idx_gen.GEN_BUS]) in buses
    component_generators = np.array(list(filter(genInComponent, ppc['gen'])))

    total_gen = sum(ppc['gen'][:, idx_gen.PG]) if len(component_generators)>0 else 0
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
    buses = set(ppc['bus'][:,idx_bus.BUS_I].astype(int))
    genInComponent = lambda gen : int(gen[idx_gen.GEN_BUS]) in buses
    component_generators = np.array(list(filter(genInComponent, ppc['gen'])))

    total_gen = sum(component_generators[:, idx_gen.PG]) if len(component_generators)>0 else 0
    total_load = sum(ppc['bus'][:, idx_bus.PD])

    if np.isclose(total_gen, 0):
        # no power generated, set loads to zero
        ppc['bus'][:, idx_bus.PD] = np.zeros(len(ppc['bus']))
    elif np.isclose(total_gen, total_load):
        # no need to scale
        return
    else:
        # scale generation to match load
        scale_factor = total_load / total_gen
        ppc['gen'][:, idx_gen.PG] *= scale_factor
