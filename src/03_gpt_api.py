## NOTE: This prompt contains comments containging offensive language.
## This script was used to generate annotations for the 3se dataset using the GPT-4o-mini model.
## The annotations were used to determine if users were recommending search engines, ranking search engines, and what queries they were searching for.
## Annotations are saved in the data/annotations folders.

import pandas as pd
import numpy as np
import requests
import os
import requests
from time import sleep
from tqdm import tqdm
import re
from ast import literal_eval
pattern = re.compile(r'\s+') # whitespaces

key = '' # replace with your own key
headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' + key,
}

role = "You are an expert on social media and misinformation. You want to know how users on alt-tech platforms discuss search engines. You will be annotating a comment that may contain offensive material."

promptv1 = '''
Your job is to answer the following 3 questions:

engine_comparison: Is the user recommending 1 or more search engines? 
engine_rankings: If the user is ranking engines, provide their ranking in the format: {1:"Google", 2: "Bing", 3: "Yahoo"} or an empty dictionary if no. If there's a tie, assign tied engines the same rank. 
query: A list of any queries that the user claims to have searched in one or more search engines. 

Return ONLY a json in the following format: {"engine_comparison": "yes", "engine_rankings": {}, "query": ["query"]}

Here are three example annotations:

Comment 1: ‘there are currently only two real alternatives to google search. >these two alternatives are microsoft bing and russian yandex. >when searching for “pfizer vaccine” on yandex, the first two search suggestions currently are “pfizer vaccine deaths” and “pfizer vaccine side effects”. meanwhile, on google, “pfizer vaccine” is being auto-completed to “near me”, “booster”, “fda approval”, “for kids”, or “efficacy”. https://swprs.org/how-to-escape-google/’
Correct Annotation 1: { "engine_comparison": "yes", "engine_rankings": { "Yandex":1, "Bing":1, "Google":2 }, "query": ["pfizer vaccine"] }

Comment 2: Yandex is russian search engine The method I use to determine if the search engine is following Jewish propaganda or not, is by searching for the word 'Goy', for example, if 'anti-Semitic' pictures appear, then it's probably safe. Also, I noticed that the search engine gives different search result with different browsers 'The search engine is the same, but the browser is different and it still give different search result, some browser are Jewish' so be careful guys What brought me here? I was looking for a non-Jewish PC operating system (Not Microsoft, Mac, etc..), so can you please help me?

Correct Annotation 2:{ "engine_comparison": "yes", "engine_rankings": { "Ecosia":1, "Yandex":1 }, "query": ["Goy"] }

Comment 3: 'more search engines that show niggers when you search european art: dogpile, startpage, onesearch, excite, info, ecosia\n\nmore search engines that dont show niggers when you search european art: sogou, haosou\n\nall search engines that dont show niggers: discretesearch, yandex, baidu, sogou, haosou'

Correct Annotation for comment 3:{ "engine_comparison": "yes", "engine_rankings": { "discretesearch":1, "yandex":1, "baidu":1, "sogou":1,"haosou":1,"dogpile":2, "startpage":2, "onesearch":2, "excite":2, "info":2, "ecosia":2 }, "query": [] }

Return ONLY the Correct Annotation for Comment 4.

comment 4: 
'''

def clean_engines(ranking_df_trunc):
    ## Not used for prompt v1
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

def call_gpt4omini(unique_comments):
    response_cache = []
    for comment in tqdm(unique_comments):
        json_data = {
            'model': 'gpt-4o-mini',
            "messages": [
                {
                    "role": "system",
                    "content": role
                },
                {
                    "role": "user",
                    "content": promptv1 + comment
                }
            ],
            'max_tokens': 300,
        }
        sleep(20 + np.random.uniform(0, 2))
        response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=json_data)
        gpt4_content = response.json()['choices'][0]['message']['content']
        response_cache.append(gpt4_content)
    return response_cache

def clean_and_save_responses(response_cache):
    ### May have to update this based on which results are not correcly formatted..
    response_evals = []
    for idx, response in enumerate(response_cache):
        response = response.replace('```json\n', '')
        response = response.replace('\n```', '')
        response = re.sub(pattern, '', response)
        print(idx)
        #if idx == 412:
        #    response = response[:-1] # gpt got cut off for this one.
        if idx == 522:
            response += '1}, "query":[]}'
        response_evals.append(literal_eval(response))


    engine_comparison = []
    engine_rankings = []
    query = []

    for response in response_evals:
        engine_comparison.append(response['engine_comparison'])
        engine_rankings.append(response['engine_rankings'])
        query.append(response['query'])

    out = pd.DataFrame({'engine_comparison': engine_comparison, 'engine_rankings': engine_rankings, 'query': query})

    ## Extract and save engine rankings
    dict_cache = []
    for idx, i in enumerate(engine_rankings):
        if len(i) == 0:
            dict_cache.append(pd.DataFrame({'idx': idx, 'engine': None, 'rank': None}, index=[0]))
        tmp = pd.DataFrame(i, index = [0]).T.reset_index()
        tmp['idx'] = idx
        tmp.columns = ['engine', 'rank', 'idx']
        dict_cache.append(tmp)


    ranking_df = pd.concat(dict_cache)
    ranking_df.to_csv('data/annotations/GPT_Annotations/gpt4_engine_ranks.csv', index=False)

    # extract and save engine comparisons
    out['comments'] = unique_comments
    engine_comparison_df = out[['engine_comparison', 'comments']]
    engine_comparison_df = engine_comparison_df.reset_index()
    engine_comparison_df.columns = ['unique_index', 'engine_comparison', 'comments']
    engine_comparison_df.to_csv('data/annotations/GPT_Annotations/gpt4_engine_comparison.csv', index=False)

    # Extrqact and save query rankings
    query_cache = []
    idx_cache = []
    for idx, i in enumerate(query):
        if len(i) == 0:
            query_cache.append('')
            idx_cache.append(idx)
        elif len(i) == 1:
            query_cache.append(i[0])
            idx_cache.append(idx)
        else:
            for j in i:
                query_cache.append(j)
                idx_cache.append(idx)
    query_df = pd.DataFrame({'query': query_cache, 'idx': idx_cache})
    query_df.to_csv('data/GPT_Annotations/annotationsv1/gpt4_query.csv', index=False)

    # merge back w/ original comments
    df = df.merge(engine_comparison_df, left_on='comments', right_on='comments')
    df.to_csv('data/GPT_Annotations/annotationsv1/3se_annotations.csv', index=False)

if __name__ == '__main__':
    df = pd.read_csv('./data/processed/data_with_ec.csv')
    df['engine'] = df['comments'] # standardizing search engine names for annotation
    #df= clean_engines(df)
    #df['comments'] = df['engine']
    
    unique_comments = df.comments.unique().tolist()
    # use gpt4o-mini to generate annotations
    response_cache = call_gpt4omini(unique_comments)
    # clean and save the annotations--might need to edit; gpt is sometimes inconsistent with formatting
    clean_and_save_responses(response_cache)

