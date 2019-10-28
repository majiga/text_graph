# -*- coding: utf-8 -*-
"""
Created on Fri Sep 20 09:15:10 2019

@author: Majigsuren Enkhsaikhan
Build a Knowledge Graph from json graph files.
"""
import glob, os
import re
import csv
import time
import networkx as nx
import simplejson as json

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from networkx.drawing.nx_pydot import read_dot
import seaborn as sns
sns.set(style="white")

count_files = 0
count_files_error = 0
COMM_ = 'iron_ore' # 'gold_deposit' or 'iron_ore'

#FOLDER_GRAPHS = r"C:/Users/20230326/wamex/data/test_gold_graphs/"
FOLDER_GRAPHS = r"/Users/majiga/Documents/wamex/data/test_" + COMM_ + "_graphs/"
#FOLDER_GRAPHS = r"/Users/majiga/Documents/wamex/data/test/"

#FOLDER_KG = r"C:/Users/20230326/wamex/data/KG/"
FOLDER_KG = r"/Users/majiga/Documents/wamex/data/KG/"



files = glob.glob(os.path.join(FOLDER_GRAPHS, '*.json'))
print("Files = ", len(files))

KG = nx.DiGraph(name = "KnowledgeGraph")

def save_graph(graph, fname):
    nodes = [{'id': n, 'group': graph.node[n]['group'], 'degree': str(graph.node[n]['degree'])} for n in graph.nodes()]
    links = [{'source': u, 'target': v, 'label': d['label']} for u, v, d in graph.edges(data=True)]
    with open(fname, 'w') as f:
        json.dump({'nodes': nodes, 'links': links}, f, indent=4,)            
    
def load_graph(filename):
    d = json.load(open(filename))
    #print(d, '\n\n')
    g = nx.DiGraph()    
    
    for n in d['nodes']:
        if n['group'] != 'OTHER':
            g.add_node(n['id'], group = n['group'])
        
    for n in d['links']:
        #print(n['source'], n['target'], n['label'])
        g.add_edge(n['source'], n['target'], label = n['label'])
    """
    print("\nNodes\n")
    for n in g.nodes(True):
        print(n)
    print("\nEdges\n")
    for a, b, c in g.edges(data=True):
        print(a, ' - ', b, ' - ', c)
    """
    return g

def join_graphs(G, graph):
    print("KG:\n", nx.info(G))
    #print("graph:\n", nx.info(graph))
    
    U = nx.DiGraph()
    U.add_edges_from(G.edges(data=True))
    U.add_nodes_from(G.nodes(data=True))
    print("\nG is copied to U:\n", nx.info(U))
    
    # add new nodes
    #print("\nAdd nodes:\n")
    for n in graph.nodes():
        if n not in U.nodes():
            if graph.node[n]['group'] != 'OTHER' or graph.node[n]['group'] != '':
                #print("Add node: ", n, graph.node[n], '\n')
                #U.add_node(n, id = graph.node[n]['id'], group = graph.node[n]['group'])
                U.add_node(n, group = graph.node[n]['group'])

    #print("\nAdd edges:\n")
    # deal with edges and their attributes
    for head, tail, relation in graph.edges(data=True):
        rel = relation['label']
        if U.has_edge(head, tail):
            print('\n- ', [head], [tail], rel, U[head][tail]['label'])
            if rel != [] and rel != ['']:
                if rel in U[head][tail]['label']:
                    continue
                #U[head][tail]['label'] += rel
                U[head][tail]['label'] = list(set(U[head][tail]['label'] + rel))
        else:
            if rel == '[]' or rel == '':
                U.add_edge(head, tail, label=[])
            else:
                U.add_edge(head, tail, label=rel)
    """
    print("\nJoined KG:\n", nx.info(U))
    #print("\n\nNODES:\n")
    #for n in U.nodes(data=True):
    #    print(n)
    print("\n\nEDGES:\n")
    for s,t,a in U.edges(data=True):
        print([s], [t], '  ---  ', [a])
    """ 
    return U


print("Create a KG for " + COMM_ + " ... ")

for filename in files:
    try:
        start_time = time.time()
        print('\n', str(count_files) + " = File name: " + filename)


        graph = load_graph(filename)
        print("Loaded a graph from a json ... \n", nx.info(graph), '\nLength of a graph = ', len(graph), '\n')             
        
        if len(graph) < 2:
            continue
        """
        print("\n\nNODES:\n")
        for n in graph.nodes(data=True):
            print(n)
        print("\n\nEDGES:\n")
        for s,t,a in graph.edges(data=True):
            print([s], [t], [a])
        """
        #KG = nx.compose(KG, graph) # compose do not keep all attributes
        KG = join_graphs(KG, graph)
                
        elapsed_time = time.time() - start_time
        print(str(count_files), " duration = ", time.strftime("%H:%M:%S", time.gmtime(elapsed_time)))
        count_files += 1
        #break

    except Exception as ex:
        print("Error in file: " + filename + ", error msg: " + str(ex))
        count_files_error += 1
        #break
       
print("\nNumber of successful files: ", count_files)
print("Number of files that had errors: ", count_files_error)
print(nx.info(KG))


print("\n\nEDGES:\n")
for s,t,a in KG.edges(data=True):
    print([s], [t], '  ---  ', [a])



# Save graph files
#nx.write_gpickle(KG, FOLDER_KG + "KG_gold_deposit.gpickle")
nx.write_gpickle(KG, FOLDER_KG + "KG_" + COMM_ + ".gpickle")
#G = nx.read_gpickle("KG.gpickle")

# Add degree to the KG
degree_dict = dict(KG.degree(KG.nodes()))
nx.set_node_attributes(KG, degree_dict, 'degree')

#save_graph(KG, FOLDER_KG + "KG_gold_deposit.json")
save_graph(KG, FOLDER_KG + "KG_" + COMM_ + ".json")





"""       
if ('iron ore' in KG.nodes()):
    ego = nx.ego_graph(KG, 'iron ore', radius=2)
    nx.write_gpickle(ego, FOLDER_KG + "iron_ore.gpickle")
    print("Subgraph for iron ore: ", nx.info(ego))

if ('gold deposit' in KG.nodes()):
    ego = nx.ego_graph(KG, 'gold deposit', radius=2)
    nx.write_gpickle(ego, FOLDER_KG + "gold_deposit.gpickle")
    print("Subgraph for gold deposit: ", nx.info(ego))

def draw(G, measures, measure_name):
    plt.figure(figsize=(15,10))
    pos = nx.spring_layout(G)
    #nx.draw(G, pos, with_labels=True)
    nodes = nx.draw_networkx_nodes(G, pos, node_size=250, cmap=plt.cm.plasma, 
                                   node_color=list(measures.values()),
                                   nodelist=measures.keys())
    nodes.set_norm(mcolors.SymLogNorm(linthresh=0.01, linscale=1))    
    nx.draw_networkx_labels(G, pos)
    nx.draw_networkx_edges(G, pos)

    plt.title(measure_name)
    plt.colorbar(nodes)
    #plt.axis('off')
    plt.show()


draw(ego, nx.degree_centrality(ego), 'Degree Centrality')
"""

#plt.figure(figsize=(15,15))
#nx.draw(ego, with_labels=True)

"""
for n in KG.nodes(data=True):
    print(n)
for s,t,a in ego.edges(data=True):
    print([s], [t], [a])
"""
        