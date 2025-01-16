import pandas as pd
import numpy as np
import os
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer

files = os.listdir('./data/raw')
files = ['./data/raw/' + file for file in files if file.endswith('.csv')]

def count_occurrences(sentence, string_list):
    count = sum(1 for word in string_list if word in sentence)
    return count

def total_occurrences(sentence, string_list):
    # Function to count total occurrences of strings in a sentence
    count = sum(sentence.count(word) for word in string_list)
    return count

def clean_4chan(files):
    dfs = []
    for file in files:
        try:
            df = pd.read_csv(file)
            df['qry'] = file.split('/')[-1].split('.')[0]
            dfs.append(df)
        except:
            print(file)

    dfs = pd.concat(dfs)
    engines = dfs.qry.unique().tolist()
    engines.remove('Microsoft Bing')
    engines.remove('You')
    engines += ['You.com']
    engines = [i.lower() for i in engines]

    dfs['comments'] = dfs['comments'].fillna('')
    dfs['title'] = dfs['title'].fillna('')
    dfs.qry = dfs.qry.str.lower()
    dfs['title'] = dfs['title'].str.lower()
    dfs['comments'] = dfs['comments'].str.lower()

    # harmonize search engine names
    dfs.replace('starpage', 'startpage', inplace=True)
    dfs.replace('yandex.com', 'yandex', inplace=True)
    dfs.replace('duckduckgo.com', 'duckduckgo', inplace=True)
    dfs.replace('yahoojapan', 'yahoo', inplace=True)
    dfs.replace('searx.me', 'searx', inplace=True)
    dfs.replace('intelx.io', 'intelx', inplace=True)
    dfs.replace('yahoo.com', 'yahoo', inplace=True)
    dfs.replace('gigablast.com', 'yahoo', inplace=True)
    dfs.replace('bravesearch', 'brave search', inplace=True)
    dfs.replace('brave', 'brave search', inplace=True)
    return dfs, engines


def filter_engines(dfs, engines):
    #filtered_df = dfs[dfs['comments'].apply(lambda x: count_occurrences(x, engines) >= 2)]
    dfs['title'] = dfs['title'].fillna('')
    #comments = dfs[dfs['comments'].apply(lambda x: count_occurrences(x, engines) >= 1)]
    #titles = dfs[dfs['title'].apply(lambda x: count_occurrences(x, engines) >= 1)]
    #se = dfs[dfs['title'].str.contains('search engine')]

    # create 1-hot encoding based on presence of each engine in comments or title
    se_comment_dict = {}
    se_title_dict = {}
    for word in engines:
        se_comment_dict[word] = dfs['comments'].apply(lambda x: 1 if word in x else 0)
    for word in engines:
        se_title_dict[word] = dfs['title'].apply(lambda x: 1 if word in x else 0)


    std = pd.DataFrame(se_title_dict)
    sed = pd.DataFrame(se_comment_dict)

    combined = std.values + sed.values
    final = pd.DataFrame(combined, columns=std.columns)
    filter = final.sum(axis = 1)

    dfs = dfs.copy()

    # only include comments with at least 3 SE mentions
    dfs['filter'] = filter.values
    out = dfs[dfs['filter'] >= 2]
    final['filter'] = filter.values
    finalout = final[final['filter'] >= 2]

    joined = pd.concat([out.reset_index(), finalout.reset_index()], axis=1)
    joined['timestamp'] = joined['timestamp'].astype(int)
    return joined

# Function to get most common n-grams
def get_most_common_ngrams(text_series, n=2, top_k=10):
    # Initialize CountVectorizer for n-grams
    vectorizer = CountVectorizer(ngram_range=(n, n)).fit(text_series)
    # Transform text series to document-term matrix
    transformed_text = vectorizer.transform(text_series)
    # Sum up the counts of each n-gram
    ngram_counts = transformed_text.sum(axis=0).A1
    # Get the feature names (n-grams)
    ngrams = vectorizer.get_feature_names_out()
    # Create a DataFrame with n-grams and their counts
    ngram_freq_df = pd.DataFrame({'ngram': ngrams, 'count': ngram_counts})
    # Sort the DataFrame by count in descending order
    ngram_freq_df = ngram_freq_df.sort_values(by='count', ascending=False)
    # Get the top_k most common n-grams
    return ngram_freq_df.head(top_k)

# Get the most common bigrams
#most_common_bigrams = get_most_common_ngrams(se['title'], n=1, top_k=50)

if __name__ == '__main__':
    #most_common_bigrams = get_most_common_ngrams(comments['comments'], n=2, top_k=50)
    #print(most_common_bigrams)
    dfs, engines = clean_4chan(files)
    joined = filter_engines(dfs, engines)
    joined.to_csv('data/processed/data_with_ec.csv', index=False)
