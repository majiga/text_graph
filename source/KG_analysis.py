#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Oct 13 12:38:14 2019

@author: majiga
"""
import re
import csv
import json
import networkx as nx
import matplotlib.pyplot as plt

"""
# SemEval relations
from models import KerasTextClassifier
semEval_model = KerasTextClassifier(input_length=50, n_classes=10, max_words=15000)
semEval_model.load('SemEval_relation_model')
# Prepare relation labels (int to string)
label_idx_to_use = [i for i, c in enumerate(list(semEval_model.encoder.classes_))]
label_to_use = list(semEval_model.encoder.classes_)
#label_to_use.remove("Other")
for i in range(len(label_to_use)):
    print(label_idx_to_use[i], ' = ', label_to_use[i])
"""

#FOLDER_KG = r"C:/Users/20230326/wamex/data/KG/"
FOLDER_KG = r"/Users/majiga/Documents/wamex/data/KG/"
COMMODITY = 'iron ore' # 'gold deposit' or 'iron ore'
COMM_ = 'iron_ore' # 'gold_deposit' or 'iron_ore'


def draw(G):
    plt.figure(figsize=(15,10))
    pos = nx.spring_layout(G)
    #nx.draw(G, pos, with_labels=True)
    #nodes = nx.draw_networkx_nodes(G, pos, node_size=250, cmap=plt.cm.plasma, node_color = 'r')    
    nx.draw_networkx_labels(G, pos)
    nx.draw_networkx_edges(G, pos)
    edge_labels = {}
    for u, v, d in G.edges(data=True):
        relation = re.sub("['\[\]]", '', str(d))
        edge_labels[(u, v)] = relation
    #print('\nedge_labels = ', edge_labels)
    
    nx.draw_networkx_edge_labels(G, pos,
                           font_size=10,
                           edge_labels=edge_labels,
                           font_color='blue')
    plt.title("Graph Visualisation")
    #plt.axis('off')
    plt.show()

#KG = nx.read_gpickle(FOLDER_KG + "KG_gold.gpickle")
KG = nx.read_gpickle(FOLDER_KG + "KG_" + COMM_ + ".gpickle")

#draw(KG)


if (COMMODITY in KG.nodes()):
    ego = nx.ego_graph(KG, COMMODITY, radius=2)
    # Add degree to the KG
    degree_dict = dict(ego.degree(ego.nodes()))
    nx.set_node_attributes(ego, degree_dict, 'degree')
    # save the ego graph
    nodes = [{'id': n, 'group': ego.node[n]['group'], 'degree': str(ego.node[n]['degree'])} for n in ego.nodes()]
    links = [{'source': u, 'target': v, 'label': d['label']} for u, v, d in ego.edges(data=True)]
    with open(FOLDER_KG + "EGO_" + COMM_ + ".json", 'w') as f:
        json.dump({'nodes': nodes, 'links': links}, f, indent=4,)            

    ego = nx.ego_graph(KG, COMMODITY, radius=1)
    # Add degree to the KG
    degree_dict = dict(ego.degree(ego.nodes()))
    nx.set_node_attributes(ego, degree_dict, 'degree')
    # save the ego graph
    nodes = [{'id': n, 'group': ego.node[n]['group'], 'degree': str(ego.node[n]['degree'])} for n in ego.nodes()]
    links = [{'source': u, 'target': v, 'label': d['label']} for u, v, d in ego.edges(data=True)]
    with open(FOLDER_KG + "EGO_" + COMM_ + "_1hop.json", 'w') as f:
        json.dump({'nodes': nodes, 'links': links}, f, indent=4,)            


"""
# Add SemEval relations
head_tail_list = [] # head, tail, head_group, tail_group
SemEval_data_format = []
for head, tail, a in KG.edges(data=True):
    if not a or len(a) == 0:
        continue
    relations = str(a['label']).split(',')
    for rel in relations:
        #print(rel)
        r = re.sub("[\[\\]\'{}]", '', rel)
        r = r.replace('label: ', '')
        r = r.strip()
        if r == '':
            continue    
        SemEval_data_format.append('<e1>' + head + '</e1> ' + r + ' <e2>' + tail + '</e2>')
        head_tail_list.append([head, tail, KG.node[head]['group'], KG.node[tail]['group']])
semEval_prediction = semEval_model.predict(SemEval_data_format)

data_label = []
for data, pred in zip(SemEval_data_format, semEval_prediction):
    #print(data, ' - ', pred, label_to_use[pred])
    print(data, ' - ', label_to_use[pred])
    data_label.append([data, str(label_to_use[pred])])
    


edges_SemEval = []
for ht, pred in zip(head_tail_list, semEval_prediction):
    #h, t, h_group, t_hroup = ht
    item = ht + [label_to_use[pred]]
    if item not in edges_SemEval:
        edges_SemEval.append(item)
        print(item)

#print(len(SemEval_data_format))
#print(len(edges_SemEval))

#with open(FOLDER_KG + 'SemEval_Relations_gold.csv', 'w', newline = '') as myfile:
with open(FOLDER_KG + 'SemEval_Relations_' + COMM_ + '.csv', 'w', newline = '') as myfile:
     wr = csv.writer(myfile, delimiter=',') #, quoting=csv.QUOTE_ALL)
     wr.writerows(data_label)
#with open(FOLDER_KG + 'SemEval_Triples_gold.csv', 'w', newline = '') as myfile:
with open(FOLDER_KG + 'SemEval_Triples_' + COMM_ + '.csv', 'w', newline = '') as myfile:
     wr = csv.writer(myfile, delimiter=',') #, quoting=csv.QUOTE_ALL)
     wr.writerows(edges_SemEval)
"""

#print(G.nodes(True))
#print(G.edges(data=True))



