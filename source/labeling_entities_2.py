# -*- coding: utf-8 -*-
"""
Created on Fri Sep  6 09:25:22 2019

@author: Majigsuren Enkhsaikhan

Label the given text according to the typed entities in the text
"""

import fuzzywuzzy as fw
from fuzzywuzzy import process
import re, os, csv
import networkx as nx

DICTIONARY_FOLDER = r"/Users/majiga/Documents/0Domain_Vocabulary/"
#DICTIONARY_FOLDER = r"C:/Users/20230326/0Domain_Vocabulary/"

  
def read_vocabulary(file_name, term_type):
    terms = {}
    with open(file_name, 'r', encoding='latin1') as f:
        lines = f.readlines()
        for t in lines:
            term = t.lower().strip()
            if term:
                terms[term] = term_type
        #print('terms: ', len(terms))
    return terms

# Read domain vocabulary
def read_domain_vocabulary():
    abspath = os.path.abspath('')
    os.chdir(abspath)

    rocks = read_vocabulary(DICTIONARY_FOLDER + "2019_rocks_mindat_gswa.txt", 'ROCK')
    minerals = read_vocabulary(DICTIONARY_FOLDER + "2019_minerals_mindat_gswa.txt", 'MINERAL')
    timescales = read_vocabulary(DICTIONARY_FOLDER + "2019_geological_eras.txt", 'TIMESCALE')
    ore_deps = read_vocabulary(DICTIONARY_FOLDER + "2019_ores_deposits.txt", 'ORE_DEPOSIT')
    strats = read_vocabulary(DICTIONARY_FOLDER + "2019_stratigraphy_gswa.txt", 'STRAT')
    locations = read_vocabulary(DICTIONARY_FOLDER + "2019_locations.txt", 'LOCATION')
    return {**rocks, **minerals, **timescales, **ore_deps, **strats, **locations}



DICTIONARY = read_domain_vocabulary()
#print('\nDOMAIN DICTIONARY is retrieved.')    
#SortedKeyList = sorted(DICTIONARY.keys(), key=len, reverse=True)
#print("sortedKeyList = ", len(sortedKeyList))


# returns the most similar entity name in the dictionary
# False if not found in domain dictionary, True if found in the dictionary
# noun phrase
def correct_name(np, sortedKeyList):
    name, score = process.extractOne(np, sortedKeyList, scorer=fw.fuzz.token_set_ratio) #partial_ratio)
    #for key in dictionary.keys():
    #    if (fuzz.token_set_ratio(entity, key))
    #print(entity, [name], score)
    #print('-- ', np, [name], score)
    if score < 85:
        return np, False, np
    elif len(np) <= len(name):
        return name, True, np
    else:
        return np, False, np

def ignore(mystring):
    CHECK_1 = re.compile('[0-9 ]+m')
    CHECK_2 = re.compile('[0-9 ]+km')
    if CHECK_1.match(mystring):
        return True
    elif CHECK_2.match(mystring):
        return True
    return False

def find_words(term, noun_phrase):    
    match = re.search(r"\b" + re.escape(term + 's') + r"\b", noun_phrase) # plural terms
    if match is not None:
        #print('\n1 - ', [noun_phrase], len(noun_phrase))
        #print('--- Word found: ', match, match.span())
        return True, match.start(), match.end()
    else:
        match = re.search(r"\b" + re.escape(term) + r"\b", noun_phrase) # singular
        if match is not None:
            #print('\n2 - ', [noun_phrase], len(noun_phrase))
            #print('--- Word found: ', match, match.span())
            return True, match.start(), match.end()
    return False, 0, 0

def ent_mentioned(np, selected_keys):
    selected_keys_sorted = sorted(selected_keys, key=len, reverse=True)
    #print('\nNP:\n', np, "\n DICTIONARY:\n", selected_keys_sorted)
    for t in selected_keys_sorted:
        found, start, end = find_words(t, np)
        if found:
            return t, DICTIONARY[t], start, end
    return np, 'OTHER', 0, len(np)


def entities_mentioned(np):
    entities = {}    
    entity_start_end = []    
    triples = []    
    selected_keys = []
    for term in DICTIONARY:        
        for w in np.split():
            if w in term or w.rstrip('s') in term:
                selected_keys.append(term)
    #print('newList # = ', len(selected_keys))
    
    start = 0
    end = 0
    term, term_group, start, end = ent_mentioned(np, selected_keys)
    entities[term] = [term_group, start, end]
    entity_start_end.append([term, start, end])    
    #print('\n - - - 1: ', np, start, end)
    
    np_new = np[:start] + (end-start)*'0' + np[end:]
    if any(char.isalpha() for char in np_new):
        term, term_group, start, end = ent_mentioned(np_new, selected_keys)
        #print('\n - - - 2: ', np_new, start, end)
        if (term_group != 'OTHER'):
            entities[term] = [term_group, start, end]
            entity_start_end.append([term, start, end])
            
    np_new = np_new[:start] + (end-start)*'0' + np_new[end:]
    #print('\n - - - 3: ', np_new, start, end)
    if any(char.isalpha() for char in np_new):
        term, term_group, start, end = ent_mentioned(np_new, selected_keys)
        #print('\n - - - 3: ', np_new, start, end)
        if (term_group != 'OTHER'):
            entities[term] = [term_group, start, end]
            entity_start_end.append([term, start, end])
            
    np_new = np_new[:start] + (end-start)*'0' + np_new[end:]
    if any(char.isalpha() for char in np_new):
        term, term_group, start, end = ent_mentioned(np_new, selected_keys)
        #print('\n - - - 4: ', np_new, start, end)
        if (term_group != 'OTHER'):
            entities[term] = [term_group, start, end]
            entity_start_end.append([term, start, end])
    
    #print('Term, start, end: \n', entity_start_end, '\n')
    
    if (len(entity_start_end) > 1):
        entity_start_end.sort(key=lambda x: x[1])
        for i in range(1, len(entity_start_end)):
            e1, start1, end1 = entity_start_end[i-1]
            e2, start2, end2 = entity_start_end[i]
            relation = np[end1:start2].strip()
            triples.append([e1, relation, e2])            
            #print('*********** h, r, t = ', e1, relation, e2)

    return entities, triples
    
def entities_mentioned_list(noun_chunks):
    #print("\nLabeling noun chunks with their entity types.\n")
    nps = [np.lower().strip() for np in noun_chunks]
    typed_nps = {}
    typed_triples = []
    for np in nps:
        if np not in typed_nps:
            if np.endswith(' ltd') or np.endswith(' limited') or np.endswith(' pty') or np.endswith(' company'):
                typed_nps[np] = {np: ['OTHER', 0, 0]} # {np: 'ORG'}
                #continue
            elif np.endswith(' project'):
                typed_nps[np] = {np: ['OTHER', 0, 0]} # {np: 'PROJECT'}
                #continue
            elif np.endswith(' prospect') or np.endswith(' prospects'):
                typed_nps[np] = {np: ['OTHER', 0, 0]} # {np: 'PROSPECT'}
                #continue
            elif 'diamond' in np and (' drill' in np or ' hole' in np or ' twin' in np or ' impregnated' in np or ' core' in np):
                typed_nps[np] = {np: ['OTHER', 0, 0]}
                #continue
            elif np.endswith(' diamond'):
                typed_nps[np] = {np: ['OTHER', 0, 0]}                
            elif ' mineralisation' in np:
                typed_nps[np] = {np: ['OTHER', 0, 0]}                
            else:
                typed_noun_chunks, triples = entities_mentioned(np)
                typed_triples += triples
                
                if len(typed_noun_chunks) == 0:
                    typed_nps[np] = {np: ['OTHER', 0, 0]}
                #elif len(typed_noun_chunks) == 1 and 'OTHER' in list(typed_noun_chunks.values())[0]:
                    #print("-- ", np)
                    #if np.endswith(' complex') or np.endswith(' formation') or np.endswith(' member') or np.endswith(' suite') or np.endswith(' supersuite') or np.endswith(' beds') or np.endswith(' subgroup') or np.endswith(' group') or np.endswith(' supergroup'):
                    #    typed_nps[np] = {np: 'STRAT'}
                    #if np.endswith(' rock'):
                    #    typed_nps[np] = {np: ['ROCK', 0, len(np)]}
                    #else:
                    #    typed_nps[np] = {np: ['OTHER', 0, 0]}
                else:
                    typed_nps[np] = typed_noun_chunks
            
    #print('\nENTITES:\n', typed_nps)
    #print("\nTRIPLEs:\n", typed_triples)
    return typed_nps, typed_triples

# noun_chunks are SpaCy spans, 
def get_typed_entities(noun_chunks):    
    noun_chunks = [np.lower().strip() for np in noun_chunks]
    #print("\nLabeling: Number of noun chunks = ", len(noun_chunks)) #, noun_chunks)
    entities_typed = {}
    phrases_ents = {}
    
    for chunk in noun_chunks: # noun_chunks_filtered:
        #print(np)
        #np = ' '.join([w for w in chunk.split() if w not in ['a', 'an', 'the']])
        np = ' '.join([w for w in chunk.split()])
        if (np in phrases_ents.keys()):
            for key, value in phrases_ents[np].items():
                entities_typed[key] = value
            continue
        if np.isdigit():
            entities_typed[np] = 'DIGIT'
        if ignore(np):
            entities_typed[np] = 'OTHER'
            continue
        if np.endswith(' ltd') or np.endswith(' limited') or np.endswith(' pty') or np.endswith(' company'):
            #entities_typed[np] = 'ORG'
            entities_typed[np] = 'ORG'
        elif np.endswith(' project'):
            #entities_typed[np] = 'PROJECT'
            entities_typed[np] = 'PROJECT'
        elif np.endswith(' prospect') or np.endswith(' prospects'):
            entities_typed[np] = 'PROSPECT'
        else:
            # get the entities with their types, a noun phrase can have multiple entities
            ents, _ = entities_mentioned(np)

            #print("---------------- ", np, " - ", ents)
            if len(ents) == 1 and list(ents.values())[0] == 'OTHER':
                #print("-- ", np)
                if np.endswith(' complex') or np.endswith(' formation') or np.endswith(' member') or np.endswith(' suite') or np.endswith(' supersuite') or np.endswith(' beds') or np.endswith(' subgroup') or np.endswith(' group') or np.endswith(' supergroup'):
                    entities_typed[np] = 'STRAT'
                    phrases_ents[np] = {np: 'STRAT'}
                elif np.endswith(' rock'):
                    entities_typed[np] = 'ROCK'
                    phrases_ents[np] = {np: 'ROCK'}
                else:
                    phrases_ents[np] = {np: 'OTHER'}
            else:
                for ent, group in ents.items():
                    entities_typed[ent] = group
                    phrases_ents[np] = ents
    
    #print("Typed entities # = ", len(entities_typed), '\n')

    return entities_typed, phrases_ents


# Synonyms and Abbreviations are siolved using a list in synonyms.csv file
def resolve_synonyms(g):
    synonyms = {}
    with open(DICTIONARY_FOLDER + "synonyms.csv", 'r', encoding='latin1') as f:        
        reader = csv.reader(f, delimiter=',')
        for row in reader:            
            synonyms[row[0].lower()] = row[1].lower() # abbreviation and exact words
    #print('synonyms # : ', synonyms)
    
    remove_nodes = []
    add_edges = []
    add_nodes = []

    for s, t, data in g.edges(data=True):
        if s not in remove_nodes:
            if s in synonyms.keys():
                if synonyms[s] not in g.nodes():
                    add_nodes.append([synonyms[s], g.node[s]])
                add_edges.append([synonyms[s], t, data['label']])
                remove_nodes.append(s)
        if t not in remove_nodes:
            if t in synonyms.keys():
                if synonyms[t] not in g.nodes():
                    add_nodes.append([synonyms[t], g.node[t]])
                add_edges.append([s, synonyms[t], data['label']])
                remove_nodes.append(t)
                
    # deal with unconnected nodes
    for n, data in g.nodes(data=True):
        if n not in remove_nodes:
            if n in synonyms.keys():
                if synonyms[n] not in g.nodes():
                    add_nodes.append([synonyms[n], g.node[n]])
                remove_nodes.append(n)
                
    for n, data in add_nodes:
        #print(n, data)
        g.add_node(n, group=data['group'])
    
    for s, t, d in add_edges:
        g.add_edge(s, t, label=d)
        
    print('Synonyms are found. Remove nodes : ', remove_nodes)
    for n in remove_nodes: # remove the merged nodes
        if n in g.nodes():
            g.remove_node(n)
    
    return g    

# 
if __name__ == "__main__":
    
    #resolve_synonyms(nx.Graph())
    
    nps = ['bif', 'quartz', 'dark grey, fresh, high susceptibility rock',
           'the Archaean greenstone belt rocks BIFs', 'large gold deposits in Pilbara',
           'Corboy Formation sediments', 'thinly bedded red and black banded iron formation',
           'the banded iron formation', 'field base metals', 'first hydrothermal']
    
    typed_nps, typed_triples = entities_mentioned_list(nps)
    
    print('\nNPS:\n', typed_nps)
    print('\nTyped_triples:\n', typed_triples)
    
    """
    entities_typed, phrases_ents = get_typed_entities(nps)
    print('\nentities_typed\n', entities_typed)
    print('\nphrases_ents\n', phrases_ents)
    """
    print("\nFinished the process.")