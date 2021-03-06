from flask import Flask, jsonify
from flask_cors import CORS
from flask import request
import threading
import logging
from flask.logging import default_handler


from rake_nltk import Rake

from sklearn.feature_extraction.text import CountVectorizer
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize, sent_tokenize

import numpy as np
import itertools

import bs4 as bs
import urllib.request
import re
import nltk

def summarize_nltk(input_sentence):
  import bs4 as bs
  import urllib.request
  import re
  import nltk


  scraped_data = urllib.request.urlopen('https://en.wikipedia.org/wiki/Severe_acute_respiratory_syndrome_coronavirus_2')
  article = scraped_data.read()
  # article = '''
  # It is actually funny when you think of it, liberals and democrats hated the Georgia voting bill they never read so much they forced the all star game moved to Colorado where it is actually harder to vote, you must have an ID to mail in ballots, and less early voting days than Georgia or Texas...the Georgia and Texas law simply made it harder to cheat which democrats and liberals hate. Because if it was about voting they would be protesting democrat states that actually have the most strict voting laws in the United States!
  # '''
  # article = '''
  # The channel was created by Australian-American media mogul Rupert Murdoch to appeal to a conservative audience, hiring former Republican media consultant and CNBC executive Roger Ailes as its founding CEO. It launched on October 7, 1996, to 17 million cable subscribers. Fox News grew during the late 1990s and 2000s to become the dominant subscription news network in the U.S. As of September 2018, approximately 87,118,000 U.S. households (90.8% of television subscribers) received Fox News. In 2019, Fox News was the top-rated cable network, averaging 2.5 million viewers. Murdoch is the current executive chairman and Suzanne Scott is the CEO.
  # '''
  article = input_sentence

  parsed_article = bs.BeautifulSoup(article,'lxml')

  paragraphs = parsed_article.find_all('p')

  article_text = input_sentence

  for p in paragraphs:
      article_text += p.text
  # Removing Square Brackets and Extra Spaces
  article_text = re.sub(r'\[[0-9]*\]', ' ', article_text)
  article_text = re.sub(r'\s+', ' ', article_text)
  # Removing special characters and digits
  formatted_article_text = re.sub('[^a-zA-Z]', ' ', article_text )
  formatted_article_text = re.sub(r'\s+', ' ', formatted_article_text)
  sentence_list = nltk.sent_tokenize(article_text)
  stopwords = nltk.corpus.stopwords.words('english')

  word_frequencies = {}
  for word in nltk.word_tokenize(formatted_article_text):
      if word not in stopwords:
          if word not in word_frequencies.keys():
              word_frequencies[word] = 1
          else:
              word_frequencies[word] += 1
      maximum_frequncy = max(word_frequencies.values())
  for word in word_frequencies.keys():
      word_frequencies[word] = (word_frequencies[word]/maximum_frequncy)
      sentence_scores = {}
  for sent in sentence_list:
      for word in nltk.word_tokenize(sent.lower()):
          if word in word_frequencies.keys():
              if len(sent.split(' ')) < 30:
                  if sent not in sentence_scores.keys():
                      sentence_scores[sent] = word_frequencies[word]
                  else:
                      sentence_scores[sent] += word_frequencies[word]
  import heapq
  summary_sentences = heapq.nlargest(7, sentence_scores, key=sentence_scores.get)

  summary = ' '.join(summary_sentences)

  # print("input sentence ")
  # print(article)

  # print("input sentence after summarization using NLTK package")
  # print(summary)
  return summary


def summarize_bert(sentence):
  article = sentence
  from summarizer import Summarizer
  model = Summarizer()
  result = model(article, min_length= 1)
  #result = model(article, ratio=0.2)  # Specified with ratio
  #result = model(article, num_sentences=3) 
  summary_bert = "".join(result)
  return summary_bert


def extract_keywords_using_rake(input_sentence):
  summary = input_sentence
  from rake_nltk import Rake
  rake_nltk_var = Rake()
  # text = """spaCy is an open-source software library for advanced natural language processing,
  # written in the programming languages Python and Cython. The library is published under the MIT license
  # and its main developers are Matthew Honnibal and Ines Montani, the founders of the software company Explosion."""
  rake_nltk_var.extract_keywords_from_text(summary)
  keyword_extracted = rake_nltk_var.get_ranked_phrases()
  # print("\n keywords extracted after summarization using RAKE Algorithm")
  # print(keyword_extracted)
  return keyword_extracted

def extract_keywords_using_distil_bert(input_sentence, number_of_words_in_each_keyword, number_of_top_keywords):
  summary = input_sentence
  from sklearn.feature_extraction.text import CountVectorizer
  n_gram_range = (number_of_words_in_each_keyword, number_of_words_in_each_keyword)
  stop_words = "english"
  # Extract candidate words/phrases
  count = CountVectorizer(ngram_range=n_gram_range, stop_words=stop_words).fit([summary])
  candidates = count.get_feature_names()
  candidates
  from sentence_transformers import SentenceTransformer

  model = SentenceTransformer('distilbert-base-nli-mean-tokens')
  doc_embedding = model.encode([summary])
  candidate_embeddings = model.encode(candidates)

  from sklearn.metrics.pairwise import cosine_similarity

  top_n = number_of_top_keywords
  distances = cosine_similarity(doc_embedding, candidate_embeddings)
  keywords = [candidates[index] for index in distances.argsort()[0][-top_n:]]  

  return keywords

# max_sum_sim(doc_embedding, candidate_embeddings, candidates, top_n=5, nr_candidates=10)
# def max_sum_sim(doc_embedding, word_embeddings, words, top_n, nr_candidates):
# def mmr(doc_embedding, word_embeddings, words, top_n, diversity):

def bert_keywords_diversificatin_using_max_sum_similarity_method(input_sentence, number_of_words_in_each_keyword, number_of_top_keywords, nr_candidates):
    summary = input_sentence
    from sklearn.feature_extraction.text import CountVectorizer
    n_gram_range = (number_of_words_in_each_keyword, number_of_words_in_each_keyword)
    stop_words = "english"
    # Extract candidate words/phrases
    count = CountVectorizer(ngram_range=n_gram_range, stop_words=stop_words).fit([summary])
    candidates = count.get_feature_names()    
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer('distilbert-base-nli-mean-tokens')
    doc_embedding = model.encode([summary])
    candidate_embeddings = model.encode(candidates)

    from sklearn.metrics.pairwise import cosine_similarity

    top_n = number_of_top_keywords
    distances = cosine_similarity(doc_embedding, candidate_embeddings)
    keywords = [candidates[index] for index in distances.argsort()[0][-top_n:]] 


    import numpy as np
    import itertools
    # Calculate distances and extract keywords
    distances = cosine_similarity(doc_embedding, candidate_embeddings)
    distances_candidates = cosine_similarity(candidate_embeddings, 
                                            candidate_embeddings)

    # Get top_n words as candidates based on cosine similarity
    words_idx = list(distances.argsort()[0][-nr_candidates:])
    words_vals = [candidates[index] for index in words_idx]
    distances_candidates = distances_candidates[np.ix_(words_idx, words_idx)]

    # Calculate the combination of words that are the least similar to each other
    min_sim = np.inf
    candidate = None
    for combination in itertools.combinations(range(len(words_idx)), top_n):
        sim = sum([distances_candidates[i][j] for i in combination for j in combination if i != j])
        if sim < min_sim:
            candidate = combination
            min_sim = sim

    return [words_vals[idx] for idx in candidate]


def bert_keywords_diversificatin_using_maximal_marginal_relevance_method(input_sentence, number_of_words_in_each_keyword, number_of_top_keywords, diversity):
    summary = input_sentence
    from sklearn.feature_extraction.text import CountVectorizer
    n_gram_range = (number_of_words_in_each_keyword, number_of_words_in_each_keyword)
    stop_words = "english"
    # Extract candidate words/phrases
    count = CountVectorizer(ngram_range=n_gram_range, stop_words=stop_words).fit([summary])
    candidates = count.get_feature_names()    
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer('distilbert-base-nli-mean-tokens')
    doc_embedding = model.encode([summary])
    candidate_embeddings = model.encode(candidates)

    from sklearn.metrics.pairwise import cosine_similarity

    top_n = number_of_top_keywords
    distances = cosine_similarity(doc_embedding, candidate_embeddings)
    keywords = [candidates[index] for index in distances.argsort()[0][-top_n:]] 

    word_embeddings = candidate_embeddings
    words = candidates

    import numpy as np

    # Extract similarity within words, and between words and the document
    word_doc_similarity = cosine_similarity(word_embeddings, doc_embedding)
    word_similarity = cosine_similarity(word_embeddings)

    # Initialize candidates and already choose best keyword/keyphras
    keywords_idx = [np.argmax(word_doc_similarity)]
    candidates_idx = [i for i in range(len(words)) if i != keywords_idx[0]]

    for _ in range(top_n - 1):
        # Extract similarities within candidates and
        # between candidates and selected keywords/phrases
        candidate_similarities = word_doc_similarity[candidates_idx, :]
        target_similarities = np.max(word_similarity[candidates_idx][:, keywords_idx], axis=1)

        # Calculate MMR
        mmr = (1-diversity) * candidate_similarities - diversity * target_similarities.reshape(-1, 1)
        mmr_idx = candidates_idx[np.argmax(mmr)]

        # Update keywords & candidates
        keywords_idx.append(mmr_idx)
        candidates_idx.remove(mmr_idx)

    return [words[idx] for idx in keywords_idx]




app = Flask(__name__)
app.debug = True
config = None

CORS(app, support_credentials=True)
logging.basicConfig(level=logging.DEBUG,
                    format='(%(threadName)-10s) %(message)s',
                    )


# @app.route('/hello/', methods=['GET'])
# def welcome():
#     return "Hello World!"



@app.route('/<string:name>/')
def hello(name):
    extracted_words = extract_keywords_using_rake(summarize_bert(name))
    extracted_words= " ".join(extracted_words)
    print(extracted_words)
    return extracted_words


if __name__ == '__main__':
    extracted_words = extract_keywords_using_distil_bert("Lawton, who was sentenced to 12 years in prison for stealing roughly $12 million in diamonds and gold from jewelers at gunpoint, said the smash-and-grabs happening across the United States are organized and could be related to gang initiations. However, he said, they could be prevented", 3, 5);
    
    app.run(host= '127.0.0.1', port=8090)