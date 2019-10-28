# -*- coding: utf-8 -*-
"""
Created on Thu Sep  5 13:57:21 2019

@author: Majigsuren Enkhsaikhan
"""

import glob, os, codecs, json, re, csv, time
import math
import pandas as pd

import networkx as nx
import matplotlib.pyplot as plt
#import pygraphviz
from networkx.drawing.nx_pydot import write_dot
    
from triple_extraction import extract_triples_by_sentences
from labeling_entities_2 import entities_mentioned_list, get_typed_entities, resolve_synonyms
from refinement_stratigraphy_3 import get_stratigraphic_hierarchy
from refinement_locations import get_location_hierarchy

DEBUG = 0

def draw_graph_centrality(G):    
    degree_dict = dict(G.degree(G.nodes()))
    nx.set_node_attributes(G, degree_dict, 'degree')

    plt.figure(figsize=(15,15))
    pos = nx.spring_layout(G)
    #print("\n\n", nx.info(G))
    #print("Nodes\n", G.nodes(True))
    #print("Edges\n", G.edges())
    
    node_sizes = [math.sqrt(v * 10000) for v in degree_dict.values()]
    node_sizes = [n+30 if n == 0 else n for n in node_sizes]
    
    nx.draw_networkx_nodes(G, pos, 
            nodelist=degree_dict.keys(),
            with_labels=False,
            edge_color='black',
            width=1,
            linewidths=1,
            node_size = node_sizes,
            node_color='blue',
            alpha=0.5)
    
    #edge_labels = {(u, v): d["r"] for u, v, d in G.edges(data=True)}
    edge_labels = {}
    for u, v, d in G.edges(data=True):
        #print(u, v, d)
        relation = re.sub("['\[\]]", '', str(d['label']))
        edge_labels[(u, v)] = relation
    #print('\nedge_labels = ', edge_labels)
    
    nx.draw_networkx_edge_labels(G, pos,
                           font_size=10,
                           edge_labels=edge_labels,
                           font_color='blue')
    
    nx.draw(G, pos, with_labels=True, node_size=1, node_color='skyblue')

def process_all(text):    
    # Extract all possible triples for the text (using noun chunks); No entity types are defined yet
    sentences_triples, DF, np_chunks = extract_triples_by_sentences(text)
    print("\nNumber of Noun_chunks = ", len(np_chunks))
    print("Number of Sentences = ", len(sentences_triples))
    
    # Print chunked document
    for index, row in DF.iterrows():
        _, s, i, w, ent, iob, l, pos, tag, s, e, dep = row
        if DEBUG: print(i, ' & ', w, ' & ', ent, ' & ', s, ' & ', e)
    
    if DEBUG: 
        print("\n\nEntities:", len(np_chunks), "\n")
        for e in np_chunks:
            print(e, e.ent_type_)   
    
    text_triples = []
    if DEBUG: print('\n\nSentences and their triples for ', len(sentences_triples), ' sentences.')
    for k,v in sentences_triples.items():
        if DEBUG: print('\n--- Sentence: ', k, '\nTriples:')        
        for val in v:
            text_triples.append(val)
            if DEBUG: print(val)
    if DEBUG: print('\nNumber of all text_triples = ', len(text_triples))
    
    ############## NOUN CHUNKS ######################
    
    nps = set([np.text.lower() for np in np_chunks])
    typed_nps, typed_nps_triples = entities_mentioned_list(nps)
    
    if DEBUG:
        print("\n------ TYPED NP_CHUNKS: ", len(typed_nps))
        for e,t in typed_nps.items():
            print(e, ' - ', t)

    # Create a graph
    G = nx.DiGraph(name="ProcessGraph")

    # Create all the nodes with their types from typed_nps list
    for np, ents in typed_nps.items():
        #print(np, ents)
        for ent, group in ents.items():
            if (not G.has_node(ent)):
                G.add_node(ent, group = group[0]) 
                #print(ent, group)
    if DEBUG: print("\nEntities are added = ", nx.info(G), '\n', G.nodes(True))

    for head, relation, tail in typed_nps_triples:
        G.add_edge(head, tail, label=[relation])
    if DEBUG: print("\nRelation between Entities in the same noun chunks are added = ", nx.info(G), '\n', G.edges(data=True))
        
    
    ############## TRIPLES ######################
    
    if DEBUG: print('\n----- TEXT TRIPLES to TYPED TRIPLES:\n')
    for h, r, t in text_triples:        
        try:
            heads = typed_nps[h]
            heads_sorted_by_start = sorted(heads.items(), key=lambda kv: kv[1][1], reverse=False)
            e1_last_entity = heads_sorted_by_start[-1][0]
            #print('e1_last_entity = ', e1_last_entity)
            #for k, v in sorted(heads.items(), key=lambda kv: kv[1][1], reverse=False):
            #    print("%s => %s" % (k,v))
            tails = typed_nps[t]
            tails_sorted_by_start = sorted(tails.items(), key=lambda kv: kv[1][1], reverse=False)
            e2_1st_entity = tails_sorted_by_start[0][0]
            #print('e2_1st_entity = ', e2_1st_entity)
            #for k, v in sorted(tails.items(), key=lambda kv: kv[1][1], reverse=False):
            #    print("%s => %s" % (k,v))        
            G.add_edge(e1_last_entity, e2_1st_entity, label=[r])
        except:
            print('--- Error: ', [h], [r], [t])
    
    """
    # Connect every node on the same path # Add edges if a path exists between nodes
    nodes = G.nodes(data=True)
    for s, sd in nodes:
        for t, st in nodes:
            if not G.has_edge(s,t):
                if (nx.has_path(G, s, t)):
                    if (s != t):                        
                        G.add_edge(s, t, label=[])
    print("\n------ PATH connection => all pairs on the same path connected: ", nx.info(G), '\n')
    """
    
    print("\n------ GRAPH: ", nx.info(G), '\n')
    
    # Remove the nodes with the type of 'OTHER'
    remove_nodes = []
    for n, d in G.nodes(data=True):
        #print('\nNode: ', n, d)
        if 'OTHER' == d['group']:
            #print('- removed ', n)
            remove_nodes.append(n)
    #print('\nNodes to remove:\n', remove_nodes, '\n\n')
    
    edges_to_add = []
    edges_to_remove = []
    for n in remove_nodes:
        node_successors = G.successors(n)        
        node_predecessors = G.predecessors(n)        
        for np in node_predecessors:            
            for ns in node_successors:
                edges_to_remove.append([np, n])
                edges_to_remove.append([n, ns])
                #print('\nn = ' , n, G.node[n])
                #print('np = ' , np, G.node[np])
                #print('ns = ' , ns, G.node[ns])                
                if 'OTHER' not in G.node[ns]['group'] and 'OTHER' not in G.node[np]['group']:
                    edges_to_add.append([np, ns])
                """
                #print(G[np][n], n, G[n][ns])
                #l = str(G.get_edge_data(np, n, 'label', default=0)) + n + str(G.get_edge_data(n, ns, 'label', default=0))
                #l = str(G[np][n]['label']) + n + str(G[n][ns]['label'])
                #print(l)
                if (G.has_edge(np, ns)):
                    G[np][ns].append(l)
                else:                    
                    G.add_edge(ns, np, label=[l])
                """
            
    for s, t in edges_to_add:
        if not G.has_edge(s,t):
            G.add_edge(s, t, label = [])
    
    for s, t in edges_to_remove:
        if G.has_edge(s, t):
            G.remove_edge(s, t)
    
    #G.in_edges(node)
    #G.out_edges(node) 
    
    for n in remove_nodes:
        G.remove_node(n) 
    print("\n------ REMOVED NODES with the 'OTHER' type ", nx.info(G), '\n')
    
        
    ############## STRAT ######################
    # Add Stratigraphic Hierarchical information
    stratList = set([e for e,d in G.nodes(data=True) if d['group'] == 'STRAT'])    
    print('\nSTRATS\n', stratList)
    StratG = get_stratigraphic_hierarchy(stratList)
    print("\n------ STRATIGRAPHY graph is retrieved: \n", nx.info(StratG))
    
    # Merge main graph G with the straigraphic graph StratG
    F = nx.compose(G, StratG)
    #print("\nStratigraphy hierarchy added = ", nx.info(F))
    #F has all nodes & edges of both graphs, including attributes
    #Where the attributes conflict, it uses the attributes of StratG.

    """
    ############## LOCATION ######################
    # Add Location Hierarchical information
    location_names = set([e[0] for e in entities_triples if e[1] == 'LOCATION'])
    #print('\nLOCATION\n', location_names)
    LocationG = get_location_hierarchy(location_names)
    #print("\n------ Strat graph\n", nx.info(StratG))
    
    # Merge main graph G with the straigraphic graph StratG
    H = nx.compose(F, LocationG)
    """

    if DEBUG: print("\n------ SYNONYMS resolving on the graph ... ")
    M = resolve_synonyms(F)
    
    if DEBUG: print("\n------ SELF LOOP removal on the graph ... \n")
    M.remove_edges_from(M.selfloop_edges())    
    
    return M

# Process the data and creates the .csv file
if __name__ == "__main__":
    #text =
    """The Archaean greenstone belt contains gold sediments. Someone likes her.
    The Nammuldi Member within the exploration area is characterised by extensive, thick and podded iron rich Banded Iron Formation (BIF),
    separated by equally extensive units of siliceous and carbonate rich chert and shale.
    Underlying the Nammuldi Member rocks are black shales and volcanic rocks belonging to the Jeerinah Formation."""
    
    #text = """Iron enrichment in the Pincunah Hills Formation is found at 'all stratigraphic levels in the formation and forms irregular pods with a distinct orientation to the bedding of the BIF."""
   
    #text = """["Davis Tube Recovery (DTR) tests on composite samples of the unweathered magnetic BIF are summarised in Table 3 and Figure 17 shows the feed % results.","Drill intersections of up to 15 m at 36.2% Fe in magnetite BIF produced DTR concentrate grades of 65.6 69.5% Fe at a 75 micron grind.","The DTR results indicate iron recoveries ranging from 45.0 to 70.3% and mass recoveries ranging from 16.8 to 33.4%.","Analysis by XRF methods.","Reconnaissance surface sampling confirmed the presence of weathered, iron-enriched magnetite banded iron-formation at the southern end of Magnetics exploration licence with grades ranging from 40.1% Fe and 23.7% SiO2 to 57.3% Fe and 7.0% SiO2.","Ground magnetic surveys conducted over four lines defined drilling targets across high-amplitude magnetic targets over a 6 km strike length.","RC drilling was carried out along three traverses with a total of 9 RC drillholes (CAR0019) completed for 662 m depth and 198 samples assayed.","Airborne and ground magnetic anomalies identified in seven of the nine holes drilled relate to BIF rocks.","The targeted BIF rocks are weathered to between 35 and 50 m vertical depth where drilled.","Iron grades range from 34.2 to 36.2% Fe over intersected widths of 1016 m in the southern part of the tenement.","DTR results indicated iron recoveries ranging from 45.0 to 70.3% and mass recoveries ranging from 16.8 to 33.4%.","DTR test work demonstrated that the magnetic rocks are related to BIF rocks and up to 26 m of downhole BIF (3 lenses, CAR005) was encountered.","Weathered Fe-rich caprock rock at surface is considered a reflection of a BIF environment close by.","If a weathered Fe caprock is encountered but not associated with a magnetic anomaly it will not be underlain with BIF, but will represent a relict of BIF erosion from a close by BIF also mixed within saprolite.","The thickness of the saprolite overburden had overriding negative commercial implications which led to the tenement being surrendered on 19 August 2013.","Reference Wilde, SA, and Low, GH, 1975, Explanatory notes on the Perth 1:250 000 geological sheet, Western Australia: Geological Survey of Western Australia, Record 1975\/6, 67p.","Five lenses of weathered to fresh fine- to medium-grained BIF were encountered in three drillholes CARC1, 2 and 5 over the larger southern magnetic anomaly (Figs 9 and 10), representing a total approximately true width of BIF of about 46 m+ across 90 m extent between the three holes over a lateral surface extent of 50 m. The estimated true thickness as shown in Figure 13 ranged from 5 to 15 m. Apparent dip was about 5060 with an expected northwestsoutheast strike (from surface rock outcropping 50 m southwest of drilling).","Quartz and sulphides were observed in drillhole CAR005 at depth (8794 m open ended).","Quartz sulphide BIF at the base of CAR005 and micaceous and quartz-rich micas in a number of metasediments downhole may be prospective for gold.","A smaller 3 m approximately true width of fresh fine- to medium-grained BIF was confirmed in drillhole CAR004 to the east of CAR001, 2 and 5.","In the 201112 reporting year 40 reconnaissance rock chip samples were collected from roadsides or paddocks across areas with anomalous magnetic responses.","Detailed sample locations are shown on Figure 6.","Composite samples CA16 (Figs 5 and 6) were collected in early 2011 as being representative of outcropping and subcropping roadside material where a road crosses the southernmost magnetic feature.","The samples were assayed at Ultra Trace Pty Ltd in Perth for Fe, SiO2, Al2O3, TiO2, CaO, MnO, P, S, MgO, K2O, Na2O and LOI by XRF and for Au, Pt, Cu, Co, Ni, Cr, and As by ICP-MS and ICP-OES.","Sample analysis results of these initial sampling are summarised in Table 1, with a photograph of part of sample CA1 shown in Figure 7.","The samples gave grades ranging from 36.1% to 57.3% Fe, indicating that the magnetite-rich units interpreted to underlie the magnetic anomalies have been enriched in some areas and suggesting the possibility of direct shipping (DSO) type ores being present.","The sampling indicated the presence of high iron contents in ferruginous outcrops\/subcrops coincident with one of the major magnetic trends.","The strike length of the significant magnetic anomalies in the southern half of the tenement totalled about 8.5 km.","Further sampling was carried out in November 2011 of samples CA00737, CAGRNT and CABAS (as shown on Figures 5 and 8), which were assayed with a hand-held Delta Dynamic XRF machine for Fe Si, Al, Ti, Zr, As and Co.","In addition, samples CA2637 were assayed at Ultra Trace for Fe, SiO2, Al2O3, TiO2 by XRF and for Au, Pt, Cu, Co, Ni, Cr, As, Mn, Zn, Pb, U, Sb, Mo, and Tl by ICP-MS and ICP-OES.","Associated elevated arsenic and chrome indicate that a lateriticvolcanic interaction with granite is the most likely scenario.","Sample CA34 (a laterite) produced elevated Al2O3 at 28% indicating bauxite potential.","Results provided by hand-held XRF and laboratory varied.","Hand-held XRF assay is a point tool at specific points on the surface of the rock, whereas the laboratory assayed the whole rock.","This confirmed to a greater degree that the surface iron enrichment was biased in the XRF versus the whole rock sample, being less iron rich and indicating a granitic composition.","Sediments indicating ancient channels with alluvial gravels overlap and intermix with laterite.","Magnetic was encouraged by these early reconnaissance sampling results and planned a programme of ground magnetic surveys and surface sampling to define drilling targets.","The previous surface sampling confirmed the presence of weathered, iron-enriched magnetite banded iron-formation at the southern end of E70\/3921.","Aeromagnetic data shows that high-amplitude magnetic anomalies, interpreted to reflect magnetite BIF, extend for a strike length of at least 8.5 km in the southern half of the tenement, as shown in Figure 8.","Magnetics reconnaissance sampling showed grades ranging from 40.1% Fe and 23.7% SiO2 to 57.3% Fe and 7.0% SiO2, showing potential for enrichment of the underlying BIF.","Significantly, the Calingiri project was situated about 10 km south of Cliffs Yerecoin magnetite project where a resource of 186.8 Mt at 30.9% Fe (DTR concentrate 70.1% Fe and 2.1% SiO2, mass recovery 32.8%) has been reported (Giralia Resources ASX release 7 July 2010).","The Yerecoin resource is notable in that the mineralisation has exceptionally favourable magnetite separation characteristics likely to result in a premium magnetite product at a coarse grind size, similar to Magnetics Jubuk deposit near Corrigin and possibly similar to Magnetics recent coarse-grained magnetite discoveries at Ragged Rock near Northam.","Such premium-quality magnetite continues to be a sought-after product because of its low impurities, making it suitable for both blending and as feed for direct reduction furnaces.","The magnetic target extent at Calingiri is similar to the strike extent of the Yerecoin deposits suggesting potential for similar-sized deposits at Calingiri.","Situated about 100 km northeast of Perth, Calingiri formed part of Magnetics extensive southwest WA iron ore holdings, targeting both DSO-grade hematite and premium-quality magnetite deposits close to rail and port infrastructure.","Calingiri was particularly well located with the BIF targets situated within 4 km of an existing railway.","Two lenses of mostly weathered BIF (CAR0067; Fig.","11) occurred about 4 km to the north of the southern line of drilling (CAR001, 2, 5).","The collective down dip width was about 27 m but was regarded acute to the drilling across 40 m down dip width drilled.","True width was not determinable.","This would confirm the extension of BIF further north in relation to the continuity of the magnetic anomaly trend north and south.","Ground magnetic surveys totalling 4 km were conducted over four lines (Fig.","9) to define drilling targets across the high-amplitude magnetic targets, which occur in soil-covered areas under crop.","The discrete high-amplitude magnetic anomalies outlined by the airborne magnetic data were confirmed.","Magnetic anomalies are considered to be caused by coarse-grained magnetite in a high-grade gneissic metamorphic terrain.","Reverse circulation drilling was conducted on three sections to assess the nature and extent of the magnetic target horizon and the drillhole locations are shown on Figure 9.","Figures 10 to 12 illustrate the ground magnetic profiles and drillhole locations on geophysical imagery.","A single lens of about 3 m true width of fresh fine to medium BIF was encountered downhole in drillhole CAR009 in the northeast central line (Fig.","At drillhole CAR009 bulldozed caprock next to the drillhole contained large fragments of ironstone which further upslope form an iron capstone ridge.","This caprock (Fig.","15) is similar to the anomalous iron samples from the southern line and artificially represents as BIF when it is probably an ironweathered ironstone emanating from localised BIF.","The drilling was carried out along three traverses over a 6 km strike length of the interpreted magnetite BIF, as shown in Figure 9, over three magnetic targets on three roadways in the south, central and northeast-central parts of the tenement aiming to confirm BIF downhole and as a coarse magnetite metamorphosed BIF.","A total of 9 RC drillholes (CAR0019) were completed for 662 m depth by Orbit Drilling using a Hydco 350 RC drill rig with auxiliary booster.","Water was prominent downhole at about 4550 m, fresh in the southern anomaly and trending to brackish in the northeast central line.","Good quantities of water made drilling conditions difficult, with a more powerful booster required to prevent drillhole collapse, sample losses and wet samples.","The drilling confirmed magnetite banded iron-formation in seven of the nine holes drilled.","Detailed sample sites are shown on Figure 6.","Figure 13 shows the downhole lithology versus magnetic susceptibility and Figure 14 shows the downhole Fe versus SiO2.","Geology: The area contains Archean granitegneisses of the South West Terrane of the Yilgarn Craton as well as mylonite and gneiss, quartzmica schist, banded iron-formation, granulite and migmatite of the Jimperding Metamorphic Belt Work done: Aeromagnetic data showed that high-amplitude magnetic anomalies, interpreted to reflect magnetite BIF, extended for a strike length of at least 8.5 km in the southern half of the tenement.","40 reconnaissance rock chip samples were collected from roadsides or paddocks across areas with anomalous magnetic responses.","A ground magnetic survey was carried out over four lines in the southern part of the tenement and RC drilling was carried out along the three traverses with 9 RC drillholes (CAR0019) completed for 662 m depth and 198 samples assayed.","Results: Reconnaissance surface sampling confirmed the presence of weathered, ironenriched magnetite banded iron-formation at the southern end of Magnetics exploration licence with grades ranging from 40.1% Fe and 23.7% SiO2 to 57.3% Fe and 7.0% SiO2.","Airborne and ground magnetic anomalies identified in seven of the nine holes drilled relate to BIF rocks.","The targeted BIF rocks are weathered to between 35 and 50 m vertical depth where drilled.","Iron grades range from 34.2 to 36.2% Fe over intersected widths of 1016 m in the southern part of the tenement.","DTR results indicated iron recoveries ranging from 45.0 to 70.3% and mass recoveries ranging from 16.8 to 33.4%, and demonstrated that the magnetic rocks are related to BIF rocks and up to 26 m of downhole BIF (3 lenses, CRA005) was encountered.","Conclusions: The drilling confirmed magnetic BIF in seven of the nine holes drilled.","Aeromagnetic data showed that high-amplitude magnetic anomalies, interpreted to reflect magnetic BIF, extended for a strike length of at least 8.5km in the southern half of the tenement.","The thickness of the saprolite overburden had overriding negative commercial implications which led to the tenement being surrendered on 19 August 2013. iii CONTENTS Tenement details and location .","1 Regional geology .","3 Previous work .","4 Exploration by Magnetic Resources NL .","9 Ground magnetic surveys .","9 RC drilling .","Calingiri E70\/3921 Tenement location plan 3.","Calingiri E70\/3921 Sample and RC drillhole sites 7.","Calingiri E70\/3921 Aeromagnetic image showing ground magnetic profiles and RC drilling 10.","Calingiri E70\/3921 Southern Line showing 5 drillholes (CAR0015) in relation to spatial image and ground magnetic traverse 11.","Calingiri E70\/3921 Central drill line north of southern line showing 2 drillholes (CAR0056) in relation to spatial image and ground magnetic traverse iv","2 drillholes (CAR0089) in relation to spatial image and ground magnetic traverse","The commodity sought was iron ore and the tenement was acquired for magnetite-rich BIF based on the expression of targeted geophysical data generated from 200609 airborne geophysical survey at 200 m line spacing and earlier 1000 m line spaced GSWA airborne data.","The tenement was centred on the village of Calingiri about 110 km northeast of Perth, 80 km northeast of the town of Gingin and 30 km southwest of Wongon Hills (Fig.","The tenement ran northsouth parallel to the Bindi Bindi Toodyay Road (Fig.","2), and roads running west off this provided good access to the tenement.","Native Title determination boundary.","Enclosed Pastoral Lease land and Pre 1994 mining confined to Nharnuwangga Wajarri and Ngarlawangga ILUA and composition of any Native Title Claims should be sought from the Native Title Spatial Services Landgate.","the data in its unaltered form should contact Geoscience Australia at www.ga.gov.au.","Confirmation of the extent copyright over those parts of the topographic data it has provided for display in TENGRAPH.","Users wishing to use Commonwealth of Australia (c) 2002, through Geoscience Australia and the Department of Defence, maintains supplied by applicants for mining tenements.","No responsibility is accepted for any error or omission.","3) mostly used for agricultural purposes (dairy farming).","A major railway network and road system exists with power and a viable telecommunications network.","Regional geology The area contains Archean granitegneisses of the South West Terrane of the Yilgarn Craton as well as mylonite and gneiss, quartzmica schist, banded iron-formation, granulite and migmatite of the Jimperding Metamorphic Belt (Fig.","The layered rocks of the South West Terrane, as described by Wilde and Low (1975) are notable for the abundance of metasediments, the complete lack of felsic volcanic rocks, the subordinate amount of mafic ?volcanic rocks and the high grade of regional metamorphism.","BIF outcrops within the tenement are strongly deformed and highly metamorphosed.","4 Geological reconnaissance of the area has shown it to be essentially covered by a thin cover of Cenozoic sediments (mainly laterite and colluvium), rarely more than 23 m thick.","The aeromagnetic image shows a series of strong aeromagnetic anomalies and an essentially northnorthwesterly trending system (Fig.","5) which was targeted for banded iron-formation.","The basement of the area is interpreted to be mafic with zones of granite.","Previous work The area was previously explored for iron by Polaris Metals NL and Giralia Resources NL who conducted exploration on E70\/2784 since 2006 including an aeromagnetic survey.","Further to the northwest Giralia explored on E70\/2733 at Yerecoin with BIF sampling giving up to 46% Fe.","They 5 subsequently sold to Cliffs who have announced a JORC resource of magnetite BIF.","The area to the northwest of this is now held by Mt Gibson Iron.","6 Exploration by Magnetic Resources NL The Calingiri project was situated about 10 km south of Atlas Irons Yerecoin project where a substantial magnetite resource, with high concentrate grades similar to Magnetics Jubuk project, has been reported.","Weathering was to about 4050 m down dip to BOCO (base of complete oxidation) 5 to 10 m. Weathered saprolite (BIF) was green-brown and micaceous with low susceptibility <10 10-3 SI units.","BIF quickly transitioned into a dark-grey, fresh, high-susceptibility rock (hundreds 10-3 SI units) passing from BOCO to BOPO (base of partial oxidation), which extended to about 510 m beyond BOCO in most holes apart from where granite was bedrock such as CAR004 where transition to fresh rock was shallower and quicker.","Susceptibility readings (several hundreds 10-3 SI units) were diagnostic in fresh BIF.","Surface-weathered Fe caprock was purple-red with hematite alteration, lightweight and siliceous.","It was not commonly bedded, and was considered a horizontal deposition over saprolite.","Any future drilling in paddocks will have to consider sumps and a bigger auxiliary compressor for the drill rig to handle the water flow and maintain dry samples respectively."]"""
    text = """The Mt Webber Project and surrounding area has been explored for various commodities (Cu Pb Ni Zn) since late in the nineteenth century.","Exploration has primarily focused on the greenstone belts and has produced a number of gold and base metal deposits.","Within the Shaw Batholith are numerous mining centres, which constitute the Shaw River tin field.","This field was historically one of the Pilbaras largest producers of tin and tantalum (Crossing, 2008).","Throughout the twentieth century companies have been actively exploring for iron deposits with varying success.","Mt Webber has three areas of iron enrichment that occur in the synclinal fold closures where the Pincunah Hills Formation BIFs are thickened up by extensive intraformational folding.","The largest areas of high-grade enrichment occur on the westernmost (Ibanez) and easternmost synclines.","The latter is divided into two zones, Fender and Gibson, which are separated by a low-grade neck.","Gibson extends off the tenement to the northeast and is part of a resource which has been defined by Giralia.","Both Ibanez and Fender are striking in a NE direction; Ibanez is the larger of the two named deposits with a strike length of 900m and varying widths from 20m at its southernmost tip to 600m within the centre of the deposit.","Fenders strike length is 1.4 km with a strike width averaging 100m throughout and is currently open to the NE.","Iron enrichment is predominantly goethite which has replaced chert in the BIF to varying degrees.","Judging by appearance of a purple colour and the elevated iron grades there is also the presence of hematitic shale.","The iron enrichment outcrops as irregular pods in the BIF where the chert in the BIF has been replaced leaving the enriched zone depleted in quartz.","Areas where enrichment is not outcropping tend to be zones of ferruginous grit or pisolitic and nodular laterite.","This layer is indicative of Mesozoic to Cainozoic weathering that would have contributed to the formation of the iron enrichment pods and is generally 1 to 3m thick.","The enrichment pods are thought to be remnants of an ancient weathering horizon, the pods forming as a result of supergene enrichment of iron in the BIF during the weathering process.","The edges of the enrichment pods are moderately sharp, less than 2-5m wide.","Depths of enrichment are generally 30m but can be as much as 60m as seen in the eastern side of the Ibanez deposit.","The iron enrichment at the surface is generally in the 55 to 60% range but some values in excess of 60% have been encountered.","A hydrated cap of approximately 1 to 10m is present and this is demonstrated in the elevated silica values of plus 10%.","MT WEBBER PROJECT E45\/2312-I FINAL SURRENDER REPORT Page 11 of 20","Review of the results of all of the exploration data and activities failed to identify any further potential for significant iron mineralisation within E45\/2312 I and thus the tenure was recommended for surrender.","MT WEBBER PROJECT E45\/2312-I FINAL SURRENDER REPORT Page 17 of 20","List of Tables Table 1: Tenement Status as at 11 December 2015 .","7 Table 2: Stratigraphy of Pilbara Supergroup, East Pilbara (after Van Kranendonk, 2003) .","10 Table 3: Significant Intercepts from MW08 Prospect RC drilling 2011 .","The tenement covers a portion of Pastoral Lease 3114\/1265, Hillside.","Access to the tenement is via the Great Northern Highway and thence via tracks along the Hillside Woodstock Road and various station tracks.","Geology: The greater Mt Webber Project occupies a portion of the Eastern Pilbara Block of WA and falls predominantly within the Gorge Creek and Sulphur Springs Groups of the Pilbara Supergroup, although the large tenement area includes Fortescue, De Grey and Warrawoona Group rocks.","It overlies three greenstone belts and the Emerald Mine Greenstone Complex (Van Kranendonk, 1998).","Currently the defined resources sit in the eastern side of the Emerald Mine Greenstone Complex.","MT WEBBER PROJECT E45\/2312-I FINAL SURRENDER REPORT Page 5 of 20 MT WEBBER PROJECT E45\/2312-I FINAL SURRENDER REPORT Page 6 of 20 MT WEBBER PROJECT E45\/2312-I FINAL SURRENDER REPORT Page 7 of 20","The tenements form part of Atlas Mt Webber Project and are located approximately 150 km southeast of Port Hedland (Figure 2), in the East Pilbara Shire of Western Australia.","The tenement covers a portion of Pastoral Lease 3114\/1265, Hillside.","The tenements are situated in the Pilbara Block of Western Australia on the Marble Bar SF50-8 1:250K; and Tambourah 2754 1:100K geological map sheets respectively.","Access to the project is via the Great Northern Highway and thence via tracks along the Hillside Woodstock Road and various station tracks.","On 15th January 2008 Atlas Iron Limited announced an option over iron ore rights for a package of tenements held by Haddington Resources (now Altura Exploration Pty Ltd).","Exploration Licence E45\/2312 formed part of this tenement package.","Exploration licence E45\/2312, originally of twenty-seven (27) blocks was granted to Australian Tantalum Ltd (Altura) on 29 September 2006.","The first statutory partial surrender of fourteen (14) blocks and a subsequent partial surrender of six (6) blocks was effected on E45\/2312 in March 2010 and September 2010 respectively.","Exploration undertaken throughout the first reporting period by Altura included a review of existing exploration data in conjunction with observations taken from field reconnaissance visits to develop a first stage exploration program.","It was considered immediate potential for economic mineralisation to lie within favourable structural features and contacts with ultramafic-mafic volcanic sequences of the greenstone terrane.","A first-phase exploration program for the tenement was developed by Altura taking into account the lack of pre-existing exploration data and limited vehicle access.","Over the reporting year the field program involved a combination of soil and rock chip sampling of rock types suitable for base metal mineralisation.","Initial rock chip sampling was aimed at establishing the most suitable rock types for exploration.","A series of sampling traverses was planned and conducted across the predominantly north-south trend of the greenstone rock sequences.","Soil sampling was also utilised to identify surface anomalies of economic and pathfinder elements, respective MT WEBBER PROJECT E45\/2312-I FINAL SURRENDER REPORT Page 12 of 20 of intermittent water courses throughout the tenement.","Exploration completed over the 2007 to 2008 reporting year identified significant dispersion anomalies in both the shallow soil horizon covering greenstone bedrock and exposed volcanic rock sequences.","Present indications suggest that the strongest base metal anomalism is associated with layered mafic-ultramafic sills surrounding banded-iron formation on the tenement.","Atlas Iron Limited and Haddington Resources conducted exploration activities over the tenements E45\/2312 including Helicopter and ground reconnaissance to ascertain the best access to the area.","Two rock chips were collected within the tenement and analysed by Ultratrace Laboratories Perth recording values of 57.57% Fe and 60.31% Fe (Figure 5 below).","MT WEBBER PROJECT E45\/2312-I FINAL SURRENDER REPORT Page 13 of 20","During the period Atlas Iron Limited conducted field reconnaissance and a surface sampling program.","Three (3) rock traverse samples were collected along with a single rock chip.","Samples were analysed at ALS Laboratory Perth for Atlas Irons Iron Ore Suite.","All samples returned values >57 Fe%.","In October an archaeological heritage survey was undertaken prior to any further work being carried out.","MT WEBBER PROJECT E45\/2312-I FINAL SURRENDER REPORT Page 14 of 20","Exploration comprised: Geological reconnaissance 1:10,000 scale prospect (MW08) geological mapping Targeting and RC drill programme proposal Heritage and land access permissions finalized An RC drilling programme was proposed to test the potential of iron mineralization identified during ground reconnaissance in early 2008 of the Pincunah Hill Formation which is a known host of iron enrichment.","After initial targeting and delineation of zones of enrichment, follow up work involved prospect scale mapping and rock chip sampling.","Results returned from this work included samples ranging from 57.6% Fe to 60.3% Fe.","From field mapping and using nominal depths and density, a target resource of potentially 2 Mt was outlined at the MW08 prospect.","The prospect is an isolated zone of mineralization which lies approximately 9km to the south west of the Ibanez iron ore deposit, however, MW08 is located within 200m of the proposed haul road to the Turner River hub and thus the potential of this prospect can be realized (Figure 7 below).","Land access negotiations restricted field work on the tenement during 2011 thus the proposed drilling programme was postponed and will commence in the next reporting period.","MT WEBBER PROJECT E45\/2312-I FINAL SURRENDER REPORT Page 15 of 20","Exploration comprised an RC drilling programme whereby twenty-six (26) angled (-600) and vertical (-900) holes (MWRC878 MWRC903) were drilled for 1152m.","The programme was undertaken at the MW08 prospect by Egan drilling.","RC drilling recorded significant intercepts in fourteen (14) of the twenty-six (26) holes drilled on the MW08 prospect predominantly within goethite and goethitic haematite.","The Mt Webber Project occupies a portion of the Eastern Pilbara Block of WA and falls predominantly within the Gorge Creek and Sulphur Springs Groups of the Pilbara Supergroup, although the large tenement area includes Fortescue, De Grey and Warrawoona Group rocks (Table 2).","The Gorge Creek Group is subdivided into six formations: the sediment dominated Paddy Market, Corboy, and Pincunah Formations of the MT WEBBER PROJECT E45\/2312-I FINAL SURRENDER REPORT Page 8 of 20 Soansville Subgroup, and Honeyeater Basalt, and Pyramid Hill Formation.","The sedimentary formations of the Gorge Creek Group consist of mainly clastic meta-sedimentary rocks, which are characterised by large internal variations in thickness and by major facies changes, which suggest accumulation in an unstable tectonic environment.","Indirect isotopic dating suggests that the age of the Gorge Creek Group is between 3.3 and 3.0 Ga.","The greater Mt Webber Project overlies three greenstone belts and the Emerald Mine Greenstone Complex (Van Kranendonk, 1998) which is an interaction of the greenstones with granitoid rocks resulting in more strongly deformed rocks.","Currently the defined resources sit in the eastern side of the Emerald Mine Greenstone Complex where the focus of exploration has been.","The Emerald Mine Greenstone Complex comprises sediments of the Gorge Creek Formation which are tightly folded and lie within a sheared contact with the Euro Basalts of the Warrawoona Group.","Unassigned ultramafics have also intruded into the complex in the form of peridotites.","The formation has been metamorphosed predominately to greenschist facies, but the rocks adjacent to the Shaw Granitoid complex have been metamorphosed to amphibolites facies.","This is a direct result of contact metamorphism and structural domaining.","The most prospective unit mapped by the GSWA in the tenement is the Pincunah Hill Formation which is part of the Gorge Creek Group.","The lowest units of the Pincunah Hill Formation in the Emerald Mine Greenstone Complex, contains thinly bedded red and black banded iron formation, black and white layered chert and shales.","The shales locally pass gradationally up into felsic volcanic.","The main structural component of the project area is the two granitoid complexes and the Lalla Rookh Western Shaw Structural Corridor.","Through these elements there is deemed to be five generations of structural events which involve magmatic phases in granitoid domes and subsequent structural elements such as faulting, folding and shearing.","The predominant structural feature of the project area is the Mulgandinnah Shear Zone found inside the Lalla Rookh Western Shaw Structural Corridor.","This shear zone is approximately 4km wide striking in a northerly direction with sinistral movement and is located on the western margin of the Shaw Granitoid Complex.","This fault also has numerous splays coming from it.","The Gorge Creek Group has been folded and refolded in to tight, sometimes isoclinal folds, especially within the BIF (Figure 3 and Figure 4).","The physiography consists of two erosional domains which are strongly controlled by the underlying bedrock.","The greenstone terranes are characterized by strike ridges of resistant rock separated by valleys underlain by less resistant units.","Surrounding granitic rocks are more deeply eroded and the region is generally characterized by low hills separated by colluvial, alluvial, and eluvial sand plains.","This report describes exploration activities for iron ore undertaken by Atlas Iron Limited (Atlas) on E45\/2312-I for the period 29 September 2006 to final surrender on 11 December 2015.","The Mt Webber area is a structurally complex portion of a large greenstone belt flanked by the Shaw Batholith to the east and south.","Gorge Creek sediments unconformable overly Warrawoona Group mafic-ultramafics, sometimes separated by Corboy Formation sediments.","The greenstones are folded into a series of tight NE trending folds, which become more open further to the NW and SE.","These synclines are cored by Pincunah Hill Formation BIFs, sometimes overlain by massive quartzite.","Near the southern margin the folding is much more MT WEBBER PROJECT E45\/2312-I FINAL SURRENDER REPORT Page 9 of 20 open and northerly plunging, paralleling the surface of the migmatitic granite.","The contact between these distinct structural domains is sharp and marked by a decollement fault.","The terrain is rugged, consisting of steep sided hills and mesas containing weathering resistant BIFs and cherts of the Pincunah Hill Formation and quartzite, separated by valleys containing pelitic sediments and maficultramafics of the Warrawoona Group.","Generally outcrop is excellent, with minimal overburden.","Mostly the cover consists of scree and shallow colluviums (Crossing, 2008).","For the most part outcropping lithologies are unoxidised.","Chemical weathering and\/or lateralisation are generally restricted to a few small areas located on the areas of iron enrichment hosted by the Pincunah Hill Formation, and small areas of thin transported laterite.","Iron enrichment in the Pincunah Hills Formation is found at all stratigraphic levels in the formation and forms irregular pods with a distinct orientation to the bedding of the BIF.","The pods vary in size from lenses 10-15m wide to pods several hundred meters wide and over a kilometre long.","These enrichment zones occur at Ibanez, Fender and Gibson prospects found in the Emerald Mine Greenstone Complex.","Crossing, J., 2008 Geological Mapping of the Mt Webber Project Pilbara WA for Atlas Iron.","In-house report commissioned by Atlas Iron Limited.","Atlas Iron Internal Report Gunther, L. 2009.","Atlas Iron Limited Internal Report Gunther, L., 2009.","Atlas Iron Internal Report.","Atlas Iron Limited Internal Report Hickman, A.H. 1983.","Geology of the Pilbara Block and its Environs.","GSWA Bulletin No.","Atlas Iron Internal Report.","Kranendonk van, M. J.","Litho-tectonic and Structural Components of the North Shaw 1:100,000 Sheet, Archaean Pilbara Craton.","Mt Webber Project E45\/2312-I Annual Technical Report to DMP Period ending 28 September 2012.","Atlas Internal Report No.","Mt Webber Project E45\/2268 Annual Technical Report to the DMP Period Ending 29 January 2011.","Atlas Iron Limited Internal Report CR563.","Geology of the Tambourah 1:100 000 sheet: Western Australia Geological Survey, 1:100 000 Geological Series Explanatory Notes, 57p.","MT WEBBER PROJECT E45\/2312-I FINAL SURRENDER REPORT Page 18 of 20","The Mt Webber Project tenements are subject to Native Title Claim by the Njamal People NTC WC99\/008."""
    
    graph = process_all(text)
    """
    print("\n\nNODES:")
    for n in graph.nodes(data=True):
        print(n)
    print("\n\nEDGES:")
    for s,t,a in graph.edges(data=True):
        print([s], [t], ' --- ', a['label'])
    """ 
    print("\nTyped grap - ", nx.info(graph))
    
    draw_graph_centrality(graph)
    
    print("\nFinished the process.")