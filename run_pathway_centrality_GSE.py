import pandas
import numpy as np
from matplotlib import pyplot as plt
import graph_tools_construction as gt





def make_network(pathway_name, all_edge_dataframe, undirected):
    '''
    Make a network from the known edges.

    Inputs:
        pathway_name: a string for the name of a pathway, corresponds to 'pathway_id' in all_edge_dataframe
        all_edge_dataframe: a dataframe with network data. The columns are:
                            'pathway_id': identifier of the pathway
                            'src': source node identifier
                            'dest': destination node identifier
                            'weight': the edge weight
                            'direction': 'undirected' for undirected edge
        undirected: a boolean, True for undirected and False for directed

    
    Outputs:
        A: a numpy array of the adjacency matrix (directed)
        node_eids: a list of EntrezIDs whose indices correspond to the entries of A
    '''

    edge_dataframe = all_edge_dataframe[all_edge_dataframe['pathway_id'] == pathway_name]

    node_eids = np.array(list(set(edge_dataframe['src']).union(set(edge_dataframe['dest']))))

    if 'weight' in list(edge_dataframe.columns):
        weighted = True
    else:
        weighted = False

    n_nodes = len(node_eids)

    A = np.zeros((n_nodes, n_nodes))

    for _,row in edge_dataframe.iterrows():
        i = np.where(node_eids == row['src'])[0][0]
        j = np.where(node_eids == row['dest'])[0][0]
        if weighted:
            A[i,j] = row['weight'].item()
        else:
            A[i,j] = 1
            if undirected or row['direction'] == 'undirected':
                A[j,i] = A[i,j].copy()
    

    return A, node_eids

def calc_pathway_scores(centrality_measure, undirected, pathway_edges, featureset_eids, outfile = 'output.csv'):
    '''
    '''
    # load names of the pathways and init pathway dataframe
    pathway_names = np.unique(np.array(pathway_edges['pathway_id']))

    pathway_scores = pandas.DataFrame(columns = ['pathway_id', 'unnormalized', 'path norm', 'feature path norm', 'avg degree norm', 'max degree norm', 'feature path count', 'path count'])

    lengths = []

    scores_list = []

    ii=0
    # go through every pathway name
    for pathway_name in pathway_names:

        #make adjacency matrix
        A, n_eids = make_network(pathway_name, pathway_edges, undirected)

        #node eids as strings
        string_node_eids = [str(int(node)) for node in n_eids]

        #find the featureset nodes in the pathway
        discriminatory_nodes = list(set(featureset_eids).intersection(set(string_node_eids)))

        #calculate pathway scores
        scores = gt.centrality_scores(A, centrality_measure)

        #degrees
        degrees = np.sum(A,axis = 0)

        #find the indices of the nodes in the adjacency matrix that correspond to nodes in the featureset
        idx = [string_node_eids.index(r) for r in discriminatory_nodes]

        #calculate pathway scores
        node_scores = scores[idx]

        if len(node_scores) > 0:
            pathway_score = np.sum(node_scores)

            # pathway_score = np.sum(node_scores)

            pathway_scores = pathway_scores.append({'pathway_id': pathway_name, 
                                                    'unnormalized': pathway_score, 
                                                    'path norm': pathway_score/len(scores), 
                                                    'feature path norm': pathway_score/len(node_scores), 
                                                    'avg degree norm': pathway_score/np.mean(degrees), 
                                                    'max degree norm': pathway_score/np.max(degrees),
                                                    'feature path count': len(node_scores),
                                                    'path count' : len(scores)},
                                                    ignore_index = True)

            scores_list.append(pathway_score)
            lengths.append(len(scores))

        if ii % 200 == 0:
            print('pathway '+str(ii)+' done')

        ii+=1

    pathway_scores.sort_values(by = 'unnormalized', ascending=False).dropna()

    pathway_scores.to_csv(outfile, index = False)
    
    # plt.figure()
    # plt.scatter(lengths, scores_list)
    # plt.xlabel('Pathway Size')
    # plt.ylabel('Centrality Score')




#load the data

# metadata = pandas.read_csv('/data4/kehoe/GSE73072/GSE73072_metadata.csv')
# vardata = pandas.read_csv('/data4/kehoe/GSE73072/GSE73072_vardata.csv')

pathway_edges = pandas.read_csv('/data3/darpa/omics_databases/ensembl2pathway/reactome_edges_overlap_fixed_isolated.csv').drop('other_genes', 1).dropna()
pathway_edges['dest'] = pandas.to_numeric(pathway_edges['dest'], downcast='integer') 
pathway_edges['src'] = pandas.to_numeric(pathway_edges['src'], downcast='integer') 

# featureset = pandas.read_csv('/data4/mankovic/GSE73072/network_centrality/featuresets/diffgenes_gse73072_pval_and_lfc.csv', index_col=0)

#####################

#do this only for train_best_probe_ids.csv file
# featureset = pandas.read_csv('/data4/mankovic/GSE73072/network_centrality/featuresets/train_best_probe_ids.csv', index_col=0)
# pid_2_eid = pandas.read_csv('/data4/mankovic/GSE73072/probe_2_entrez.csv')
# featureset_pids = list(featureset.index)
# featureset_eids = []
# #load eids from the probeids in the featureset
# for p in featureset_pids:
#     if p in list(pid_2_eid['ProbeID']):
#         featureset_eids.append(str(pid_2_eid[pid_2_eid['ProbeID'] == p]['EntrezID'].item()))
# suffix = 'best_probe_ids'

#####################

#ssvm features
featureset = pandas.read_csv('/data4/mankovic/GSE73072/network_centrality/featuresets/ssvm_ranked_features.csv', index_col=0)
#do this for top 316 ssvm features with frequency greater than 8
featureset_eids = [str(f) for f in list(featureset.query("Frequency>8").index)]
suffix = 'train_ssvm8'

#####################



print('starting degree directed')
outfile = '/data4/mankovic/GSE73072/network_centrality/simple_rankings/gse73072_directed_degree_train_'+suffix+'.csv'
calc_pathway_scores('degree', False, pathway_edges, featureset_eids, outfile)

print('starting page rank directed')
outfile = '/data4/mankovic/GSE73072/network_centrality/simple_rankings/gse73072_directed_pagerank_train_'+suffix+'.csv'
calc_pathway_scores('page_rank', False, pathway_edges, featureset_eids, outfile)

print('starting degree undirected')
outfile = '/data4/mankovic/GSE73072/network_centrality/simple_rankings/gse73072_undirected_degree_train_'+suffix+'.csv'
calc_pathway_scores('degree', True, pathway_edges, featureset_eids, outfile)

print('starting page rank undirected')
outfile = '/data4/mankovic/GSE73072/network_centrality/simple_rankings/gse73072_undirected_pagerank_train_'+suffix+'.csv'
calc_pathway_scores('page_rank', True, pathway_edges, featureset_eids, outfile)
