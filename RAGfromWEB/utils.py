import curses
import feedparser
import requests
import unicodedata
import json
from newspaper import Article
from bs4 import BeautifulSoup
from nltk.tokenize import sent_tokenize, word_tokenize
import numpy as np
from sklearn.neighbors import NearestNeighbors
from mattsollamatools import chunker

MODEL = "" # Insert model name here

# Create a dictionary to store topics and their URLs
topic_urls = {
    "Skills": "https://www.myskillsfuture.gov.sg/content/portal/en/",
    "Careers": "https://www.mycareersfuture.gov.sg/job/",
}

# Use curses to create a menu of topics
def menu(stdscr):
    chosen_topic = get_url_for_topic(stdscr)  
    url = topic_urls[chosen_topic] if chosen_topic in topic_urls else "Topic not found"
    
    stdscr.addstr(len(topic_urls) + 3, 0, f"Selected URL for {chosen_topic}: {url}")
    stdscr.refresh()
    
    return chosen_topic


'''
IDK what this does but i'll figure it out later
'''
# You have chosen a topic. Now return the url for that topic
def get_url_for_topic(stdscr):
    curses.curs_set(0)  # Hide the cursor
    stdscr.clear()

    stdscr.addstr(0, 0, "Choose a topic using the arrow keys (Press Enter to select):")

    # Create a list of topics
    topics = list(topic_urls.keys())
    current_topic = 0

    while True:
        for i, topic in enumerate(topics):
            if i == current_topic:
                stdscr.addstr(i + 2, 2, f"> {topic}")
            else:
                stdscr.addstr(i + 2, 2, f"  {topic}")

        stdscr.refresh()

        key = stdscr.getch()

        if key == curses.KEY_DOWN and current_topic < len(topics) - 1:
            current_topic += 1
        elif key == curses.KEY_UP and current_topic > 0:
            current_topic -= 1
        elif key == 10:  # Enter key
            return topic_urls[topics[current_topic]]

# Get the last N URLs from an RSS feed
def getUrls(feed_url, n=20):
    feed = feedparser.parse(feed_url)
    entries = feed.entries[-n:]
    urls = [entry.link for entry in entries]
    return urls

# Often there are a bunch of ads and menus on pages for a news article. This uses newspaper3k to get just the text of just the article.
def getArticleText(url):
  article = Article(url)
  article.download()
  article.parse()
  return article.text

def get_best(text):
  systemPrompt = "Write a concise summary of the top 5 most relevant postings, return your responses with 2 relevant key points of the postings given. Include the URL of the respective postings."
  prompt = text
  
  url = "http://localhost:11434/api/generate"

  payload = {
    "model": MODEL,
    "prompt": prompt, 
    "system": systemPrompt,
    "stream": False
  }
  payload_json = json.dumps(payload)
  headers = {"Content-Type": "application/json"}
  response = requests.post(url, data=payload_json, headers=headers)

  return json.loads(response.text)["response"]


'''
Idk what this does so I just left this in
'''
# Perform K-nearest neighbors (KNN) search
def knn_search(question_embedding, embeddings, k=5):
    X = np.array([item['embedding'] for article in embeddings for item in article['embeddings']])
    source_texts = [item['source'] for article in embeddings for item in article['embeddings']]
    
    # Fit a KNN model on the embeddings
    knn = NearestNeighbors(n_neighbors=k, metric='cosine')
    knn.fit(X)
    
    # Find the indices and distances of the k-nearest neighbors
    distances, indices = knn.kneighbors(question_embedding, n_neighbors=k)
    
    # Get the indices and source texts of the best matches
    best_matches = [(indices[0][i], source_texts[indices[0][i]]) for i in range(k)]
    
    return best_matches