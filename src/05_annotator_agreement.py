## Check annotation consistency
import pandas as pd
import numpy as np
import requests
import os
import requests
from time import sleep
from tqdm import tqdm
import re
from ast import literal_eval
import rbo
from statsmodels.stats.inter_rater import fleiss_kappa
from collections import Counter
from sklearn.metrics import cohen_kappa_score, f1_score, accuracy_score



v1 =pd.read_csv('data/annotations/human_annotations/human_annotator_1.csv')
v2 = pd.read_csv('data/annotations/human_annotations/human_annotator_2.csv')

ec = pd.read_csv('data/annotations/GPT_Annotations/annotationsv1/gpt4_engine_comparison.csv')
queries = pd.read_csv('data/annotations/GPT_Annotations/annotationsv1/gpt4_query.csv')
ranks = pd.read_csv('data/annotations/GPT_Annotations/annotationsv1/gpt4_engine_ranks.csv')

# Compare engine comparisons
def compare_engine_binary_annotations(v1,v2,ec):
    v1_trunc = v1[['idx', 'engine_comparison']].copy()
    v1_trunc.columns = ['idx', 'a1_engine_comparison']
    v2_trunc = v2[['idx', 'engine_comparison']].copy()
    v2_trunc.columns = ['idx', 'a2_engine_comparison']
    v1_trunc['a1_engine_comparison'] = v1_trunc['a1_engine_comparison'].str.lower()
    v2_trunc['a2_engine_comparison'] = v2_trunc['a2_engine_comparison'].str.lower()

    ec_trunc = ec[['unique_index', 'engine_comparison']].copy()
    ec_trunc.columns = ['idx', 'gpt4_engine_comparison']
    ec_trunc['gpt4_engine_comparison'] = ec_trunc['gpt4_engine_comparison'].str.lower()

    ec_trunc = ec_trunc.merge(v1_trunc, on='idx', how = 'left')
    ec_trunc = ec_trunc.merge(v2_trunc, on='idx', how = 'left')
    ec_trunc = ec_trunc.dropna()
    
    ecannotators = ec_trunc.drop(columns = 'idx')
    # binarize the matrix
    ecannotators = ecannotators.replace({'yes': 1, 'no': 0})

    # Convert to a format suitable for Fleiss' Kappa
    count_data = ecannotators.apply(pd.Series.value_counts, axis=1).fillna(0)

    # Calculate Fleiss' Kappa
    kappa = fleiss_kappa(count_data, method='fleiss')
    print("Fleiss' Kappa:", kappa)
    
    ## Fleiss' Kappa where humans agree
    ecannotatorsv2 = ecannotators[ecannotators['a1_engine_comparison'] == ecannotators['a2_engine_comparison']].copy()
    count_data = ecannotatorsv2.apply(pd.Series.value_counts, axis=1).fillna(0)
    kappa = fleiss_kappa(count_data, method='fleiss')
    print("Fleiss' Kappa where humans agree:", kappa)

    # check How many rows are identical
    # Convert each row to a tuple (so it's hashable)
    rows_as_tuples = [tuple(row) for row in ecannotators.values]

    # Count the frequency of each unique tuple (row)
    row_counts = Counter(rows_as_tuples)

    # Display how many times each unique row appears
    for row, count in row_counts.items():
        print(f"Row {row} appears {count} times")

    ec2 = ecannotators.copy()
    ec2['total'] = ecannotators.sum(axis=1)
    # drop rows where at least one annotator said no comparison
    disagreement = ec2[ec2['total'].isin([0,1,2])].reset_index()['index'].tolist()

    return ec_trunc, disagreement


def extract_annotation_ranks(vlistranks_dict, idx_list):
    dict_cache = []
    for i in range(len(vlistranks_dict)):
        idx = idx_list[i]
        if len(vlistranks_dict[i]) == 0:
            dict_cache.append(pd.DataFrame({'idx': idx, 'engine': None, 'rank': None}, index=[0]))
        tmp = pd.DataFrame(vlistranks_dict[i], index = [0]).T.reset_index()
        tmp['idx'] = idx
        tmp.columns = ['engine', 'rank', 'idx']
        dict_cache.append(tmp)
    annotation_ranks = pd.concat(dict_cache)
    annotation_ranks.columns = ['engine', 'e_rank', 'idx']
    annotation_ranks['engine'] = annotation_ranks['engine'].str.lower()
    return annotation_ranks

def jaccard_similarity(list1, list2):
    set1 = set(list1)
    set2 = set(list2)
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return intersection / union

def clean_engines(ranking_df_trunc):
    ranking_df_trunc['engine'] = ranking_df_trunc['engine'].str.lower()
    ranking_df_trunc.replace('starpage', 'startpage', inplace=True)
    ranking_df_trunc.replace('yandex.com', 'yandex', inplace=True)
    ranking_df_trunc.replace('duckduckgo.com', 'duckduckgo', inplace=True)
    ranking_df_trunc.replace('yahoojapan', 'yahoo', inplace=True)
    ranking_df_trunc.replace('searx.me', 'searx', inplace=True)
    ranking_df_trunc.replace('intelx.io', 'intelx', inplace=True)
    ranking_df_trunc.replace('yahoo.com', 'yahoo', inplace=True)
    ranking_df_trunc.replace('gigablast.com', 'yahoo', inplace=True)
    ranking_df_trunc.replace('bravesearch', 'brave search', inplace=True)
    ranking_df_trunc.replace('brave', 'brave search', inplace=True)
    ranking_df_trunc.replace('jewgle', 'google', inplace=True)
    ranking_df_trunc.replace('ddg', 'duckduckgo', inplace=True)
    return ranking_df_trunc

def jaccard_rankings(v1,v2,ranks,disagreement):
    vlistranks = v1['engine_rankings'].tolist()
    vlistranks = [i.replace('“', '"').replace('”', '"') for i in vlistranks]
    vlistranks_dict = [literal_eval(i) for i in vlistranks]
    vlistranks2 = v2['engine_rankings'].tolist()
    vlistranks_dict2 = [literal_eval(i) for i in vlistranks2]
    idx_list = v1['idx'].tolist()

    ar1 = extract_annotation_ranks(vlistranks_dict, idx_list)
    ar2 = extract_annotation_ranks(vlistranks_dict2, idx_list)
    ar1 = clean_engines(ar1)
    ar2 = clean_engines(ar2)
    ranks = clean_engines(ranks)
    


    # only considering engines that all annotators agreed were engine comparisons
    drop_idx = disagreement

    ar1.columns = ['engine', 'ar1_rank', 'idx']
    ar2.columns = ['engine', 'ar2_rank', 'idx']
    annotated_ranks = ar1.merge(ar2, on = ['idx', 'engine'], how = 'outer')
    annotated_ranks = annotated_ranks.dropna()
    annotated_ranks = annotated_ranks[~annotated_ranks['idx'].isin(drop_idx)]
    gpt4_ranks = ranks[ranks['idx'].isin(annotated_ranks['idx'].unique().tolist())].copy()
    gpt4_ranks = clean_engines(gpt4_ranks)
    # compare rank 1


    #annotation_ranks.merge(ranking_df_trunc, on = ['idx', 'engine'], how = 'left')
    #agreement = validation[validation['engine_comparison'] == validation['gpt4_engine_comparison']]
    #agreement = agreement[agreement['engine_comparison'] == 'yes']
    #agreementidx = agreement.idx.unique().tolist()
    #rbo_cache = []


    #ar = annotation_ranks[annotation_ranks['engine'] != 'google'].copy().dropna()
    #rdt = ranking_df_trunc[ranking_df_trunc['engine'] != 'google'].copy().dropna()


    an_idx_list = annotated_ranks['idx'].unique().tolist()

    A1_A2 = []
    A2_GPT = []
    A1_GPT = []
    for i in an_idx_list:
        #S = ar[ar['idx'] == i]['engine'].tolist()
        try:
            S = annotated_ranks[annotated_ranks['idx'] == i].copy()
            A1 = S[S['ar1_rank'] == 1]['engine'].tolist()
            #T = rdt[rdt['idx'] == i]['engine'].tolist()
            #T = annotated_ranks[annotated_ranks['idx'] == i].copy()
            A2 = S[S['ar2_rank'] == 1]['engine'].tolist()
            GPTR = gpt4_ranks[gpt4_ranks['idx'] == i]['engine'].tolist()
            A1_A2.append(jaccard_similarity(A1, A2))
            A2_GPT.append(jaccard_similarity(GPTR, A2))
            A1_GPT.append(jaccard_similarity(A1, GPTR))
        except:
            print(i)

    print('Between Humans ', np.mean(A1_A2)) #0.85 between humans
    print('Between A2 & GPT ',np.mean(A2_GPT)) #0.70 between A2 & GPT
    print('Between A1 & GPT ',np.mean(A1_GPT)) #0.65 between A1 & GPT
    

def query_evaluation(v1, v2, queries):
    v1q = v1[['idx', 'query']].copy()
    v2q = v2[['idx', 'query']].copy()
    v1q.columns = ['idx', 'a1_query']
    v2q.columns = ['idx', 'a2_query']
    v1q = v1q.merge(v2q, on = 'idx', how = 'left')
    v1q = v1q.merge(queries, on = 'idx', how = 'left')
    v1q.fillna('No', inplace=True)


    v1q['a1_query'] = v1q['a1_query'].apply(lambda x: literal_eval(x) if isinstance(x, str) and x.startswith('[') else x)
    v1q['a2_query'] = v1q['a2_query'].apply(lambda x: literal_eval(x) if isinstance(x, str) and x.startswith('[') else x)
    v1q['query'] = v1q['query'].apply(lambda x: literal_eval(x) if isinstance(x, str) and x.startswith('[') else x)
    v1q = v1q.explode('a1_query')
    v1q = v1q.explode('a2_query')
    v1q['a1_query'] = v1q['a1_query'].str.lower()
    v1q['a2_query'] = v1q['a2_query'].str.lower()
    v1q['query'] = v1q['query'].str.lower()
    v1q['a1_query'] = v1q['a1_query'].str.replace(' ', '')
    v1q['a2_query'] = v1q['a2_query'].str.replace(' ', '')


    agreement_cache = []
    disagree_cache = []

    for i in v1q['idx'].unique():
        S = sorted(list(set(v1q[v1q['idx'] == i]['a1_query'].tolist())))
        T = sorted(list(set(v1q[v1q['idx'] == i]['a2_query'].tolist())))
        Q = sorted(list(set(v1q[v1q['idx'] == i]['query'].tolist())))
        if S == T == Q:
            agreement_cache.append(i)
        else:
            if len(S) > 1:
                for jdx, j in enumerate(S):
                    if (j in T) and (j in Q):
                        agreement_cache.append(i)
                    else:
                        disagree_cache.append(i)
            else:
                disagree_cache.append(i)
    
    out = v1q[v1q['idx'].isin(disagree_cache)]
    out['a1_query'].nunique()
    # precision: TP / (TP + FP)
    # treating annotator 1 as ground truth--minus one to delete the no category
    TP = (out['a1_query'].nunique()- 1)
    # calculate false negatives and false positives
    FP = len(list(set(out['query'].tolist()) - set(out['a1_query'].tolist())))
    FN = len(list(set(out['a1_query'].tolist()) - set(out['query'].tolist())))
    precision = TP / (TP + FP)
    recall = TP / (TP + FN)
    print('Precision, ',precision)
    print('Recall, ', recall)


if __name__ == "__main__":
    ec_trunc, disagreement = compare_engine_binary_annotations(v1,v2,ec) 
    jaccard_rankings(v1,v2,ranks,disagreement)
    query_evaluation(v1, v2, queries)

#2/1 + 3/2 + 4/3