import pypower.api as pp
import networkx as nx
import igraph as ig
import numpy as np
from components_ig import ppc_to_ig


def get_vertex_color(gen, load):
    if gen == load:
        return 'black'
    elif gen > load:
        return 'blue'
    else:
        return 'orange'

def get_edge_color(load, cap, isFailed):
    if isFailed:
        return 'black'
    if abs(load) > cap:
        return 'purple'
    else:
        ratio = abs(load) / cap
        if ratio < 0.5:
            red = hex(int(round(255 * (ratio / 0.5))))
            return '#' + red[2:].zfill(2) + 'ff00'
        else:
            # ratio >= 0.5
            green = hex(int(round(255 * ((1-ratio) / 0.5))))
            return '#ff' + green[2:].zfill(2) + '00'

def draw(grid, capacities, fname, layout=None):
    G = ppc_to_ig(grid, includeInactive=True, includeData=True)
    if layout == None:
        layout = G.layout_reingold_tilford()
    vertex_color = [get_vertex_color(G.vs[i]['gen'], G.vs[i]['load']) for i in range(len(G.vs))]
    vertex_size = np.sqrt(abs(np.array(G.vs['gen']) - np.array(G.vs['load'])))*2.5
    edge_color = [get_edge_color(G.es[i]['load'], capacities[i], G.es[i]['isFailed'])
                  for i in range(len(G.es))]
    ig.plot(G, fname, layout=layout, bbox=(2000,2000), margin=100, vertex_color=vertex_color,
            vertex_size=vertex_size, edge_color=edge_color, edge_width=5)


def visualize(grids, capacities, title):
    if type(grids) == list:
        # provided list of grids
        layout = ppc_to_ig(grids[0], includeInactive=True).layout_reingold_tilford()
        for i in range(len(grids)):
            draw(grids[i], capacities, 'ppcvis-' + title + '_iter' + str(i) + '.png', layout=layout)
    else:
        # provided single grid
        layout = ppc_to_ig(grids, includeInactive=True).layout_reingold_tilford()
        draw(grids, capacities, "ppcvis-" + title + '.png')
