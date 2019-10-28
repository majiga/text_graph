#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 10 09:19:24 2019

@author: majiga
"""
import glob, os, json
#import pandas as pd
#import numpy as np
#import csv
import time
import networkx as nx
import matplotlib.pyplot as plt
   
from process_text import process_all


count_files = 0
count_files_error = 0

#FOLDER_ALL_WAMEX = r"C:/Users/20230326/wamex/data/test_1/"
#FOLDER_ALL_WAMEX = r"C:/Users/20230326/wamex/data/wamex_xml/"
#FOLDER_ALL_WAMEX_fix = r"C:/Users/20230326/wamex/data/test_graphs/"

#FOLDER_ALL_WAMEX = r"C:/Users/20230326/wamex/data/wamex_xml/"
#FOLDER_ALL_WAMEX = r"/Users/majiga/Documents/wamex/data/test_iron_ore/"
#FOLDER_ALL_WAMEX_fix = r"/Users/majiga/Documents/wamex/data/test_iron_ore_graphs/"

#FOLDER_ALL_WAMEX = r"/Users/majiga/Documents/wamex/data/test_vms/"
#FOLDER_ALL_WAMEX_fix = r"/Users/majiga/Documents/wamex/data/test_vms_graphs/"

FOLDER_ALL_WAMEX = r"/Users/majiga/Documents/wamex/data/test_gold/"
FOLDER_ALL_WAMEX_fix = r"/Users/majiga/Documents/wamex/data/test_gold_graphs/"

files = glob.glob(os.path.join(FOLDER_ALL_WAMEX, '*.json'))
print("Files = ", len(files))


def create_triples(g):
    triples = []
    ore_deps = []
    print('Creating the triples from the graph\n')
    for s,t,a in g.edges(data=True):
        s_group = g.node[s]['group']
        t_group = g.node[t]['group']
        if (s_group == 'ORE_DEPOSIT' and s_group not in ore_deps):
            ore_deps.append(s)
        if (t_group == 'ORE_DEPOSIT' and t_group not in ore_deps):
            ore_deps.append(t)
        if a:
            triples.append([s, a['label'], t, g.node[s]['group'], g.node[t]['group']])
        else:
            triples.append([s, [], t, g.node[s]['group'], g.node[t]['group']])
    return triples, ore_deps


def create_triples_from_graph(g):
    triples = []
    print('Creating the triples from the graph\n')
    for s,t,a in g.edges(data=True):
        s_group = g.node[s]['group']
        t_group = g.node[t]['group']
        if a:
            triples.append([s, a['label'], t, s_group, t_group])
        else:
            triples.append([s, [], t, s_group, t_group])
    return triples

KG = nx.DiGraph(name = "KnowledgeGraph")
files_ids = []

for filename in files:
    #try:
        start_time = time.time()
        print('\n\n ======= ', str(count_files) + " = File name: " + filename)

        with open(filename, 'r') as f:
            data = f.read()
                
        graph = process_all(data)
        if graph.number_of_nodes() < 2: 
            continue
        
        print("\n\nGRAPH:\n", nx.info(graph))
        """
        print("\n\nNODES:\n")
        for n in graph.nodes(data=True):
            print(n)
        print("\n\nEDGES:\n")
        for s,t,a in graph.edges(data=True):
            print([s], [t], ' --- ', a['label'])
        """
        
        filename_extension = str(filename).split('/')[-1:][0] # for macbook
        #filename_extension = str(filename).split('\\')[-1:][0] # for windows
        filename_new = FOLDER_ALL_WAMEX_fix + str(filename_extension).split('.')[-2:][0]
    
        # Add degree
        degree_dict = dict(graph.degree(graph.nodes()))
        nx.set_node_attributes(graph, degree_dict, 'degree')
    
        # Save graph files
        nodes = [{'id': n, 'group': graph.node[n]['group'], 'degree': graph.node[n]['degree']} for n in graph.nodes()]
        #links = [{'source': u, 'target': v, 'label': data['label'], 'data': data} for u, v, d in graph.edges(data=True)]
        links = [{'source': u, 'target': v, 'label': d['label']} for u, v, d in graph.edges(data=True)]
        with open(filename_new + '.json', 'w') as f:
            json.dump({'nodes': nodes, 'links': links}, f, indent=4,)
            
        #nx.write_gpickle(graph, filename_new + ".gpickle")
        #print(filename_new + ".pickle file saved.")
        #write_dot(graph, filename_new + '.dot')
        #print(".dot file is created. See it on the webgraphviz.com")
    
        """
        # Create triples from the graph
        triples, ore_deps = create_triples_from_graph(graph)
        #print("TRIPLES:\n", triples)
        
        with open(filename_new + '.triples', mode='w', newline='', encoding='utf-8') as file:
            csv_writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            #csv_writer.writerow(['head', 'relation', 'tail', head_group, tail_group])
            csv_writer.writerows(triples)
        print(".triples file is created.")
        
        files_ids.append([count_files, filename_extension, graph.number_of_nodes(), graph.number_of_edges(), ore_deps])
        """
        
        count_files += 1
        elapsed_time = time.time() - start_time
        print(str(count_files), " duration = ", time.strftime("%H:%M:%S", time.gmtime(elapsed_time)), '\n')
        #print(count_files, filename_new)
        #break

    #except Exception as ex:
    #    print("Error in file: " + filename + ", error msg: " + str(ex))
    #    count_files_error += 1
        #break
       
print("Number of successful files: ", count_files)
print("Number of files that had errors: ", count_files_error)

"""
with open('wamex_files.csv', mode='w', newline='', encoding='utf-8') as file:
    csv_writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    #csv_writer.writerow(['head', 'relation', 'tail', head_group, tail_group])
    csv_writer.writerows(files_ids)
print("wamex_files.csv file is created.")
"""
