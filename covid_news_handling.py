from json import load
import requests
import os
import logging

## logging setup
FORMAT = '%(levelname)s @ %(name)s [%(asctime)s]: %(message)s'
logger_cnh = logging.getLogger(__name__)
logging.basicConfig(filename=os.getcwd()+load(open('config.json','r'))['log_file_path'],filemode='w',format=FORMAT,level=logging.INFO)

# covid_terms = definition in docstring <<
def news_API_request(covid_terms,page_size=20):
    '''get covid-related news stories from the news api'''
    _APIkey = load(open('config.json','r'))['api_keys']['news_api'] # get api key from config.json
    logger_cnh.info('API key fetched from config file')
    keywords = covid_terms.split(' ')
    url = 'https://newsapi.org/v2/everything?q='+'+OR+'.join(keywords)+'&pageSize='+str(page_size)+'&apiKey='+_APIkey
    ## fix this
    response = requests.get(url, auth=('user','pass')) # request related stories from newsAPI
    logger_cnh.info('news API request [url=%s]',url)
    return response.json()['articles']

global covid_news, removed_titles, covid_news_sch
covid_news = []
removed_titles = []
covid_news_sch = {}
logger_cnh.info('covid news globals initialized')

from flask import Markup
def format_news_article(article_json):
    '''formats news article from json to dictionary which can be input into flask template'''
    return {'title':article_json['title'],'content':Markup(article_json['description']+
            '<a href=\"{url}\">{source}</a>'.format(url=article_json['url'],source=article_json['source']['name']))}

def remove_title(title):
    '''adds article to list of removed, so it is not redisplayed'''
    global removed_titles
    if title not in removed_titles:
        removed_titles.append(title)
        logger_cnh.info('news story removed')

def purge_articles():
    for a in covid_news: # remove all currently displayed articles
        remove_title(a['title'])

def update_news(covid_terms, article_count=10, sch=True):
    '''updates the news data structure with the latest articles'''
    global covid_news, removed_titles
    if sch:
        purge_articles()
    api = news_API_request(covid_terms,article_count+len(removed_titles))
    covid_news = []
    i = 0
    while len(covid_news) < article_count:
        if i >= len(api):
            logger_cnh.warning('articles list exhasted')
            break
        if api[i]['title'] not in removed_titles:
            covid_news.append(format_news_article(api[i]))
        i += 1
    logger_cnh.info('covid news updated')

import sched
from time import time, sleep
def sched_news_update_repeat(sch, search_terms):
    '''uses recrsion to implement 24 hour repeating updates'''
    sch.enter(24*60*60, 1, update_news, argument=(search_terms))
    if len(sch.queue) < 30:
        sch.enter(24*60*60, 2, sched_news_update_repeat, argument=(s))

def schedule_news_updates(update_interval, update_name, search_terms, repeating=False):
    '''creates scheduler for scheduling updates'''
    global covid_news_sch
    s = sched.scheduler(time, sleep)
    s.enter(update_interval, 1, update_news, argument=(search_terms))
    if repeating: # schedules a repeating update in 24 hours (this is recursive)
        #s.enter(update_interval, 1, s.enter, argument=(24*60*60, 1, update_news), kwargs={'argument':search_terms})
        s.enter(update_interval, 2, sched_news_update_repeat, argument=(s, search_terms))
    covid_news_sch[update_name] = s


# \/ remove this class
class covid_news_:
    '''data structure for storing news stories'''
    def __init__(self):
        self.articles = []
        self.removed_titles = []

    def format_news_article(self, article_json):
        '''formats news article from json to dictionary which can be input into flask template'''
        return {'title':article_json['title'],'content':Markup(article_json['description']+
            '<a href=\"{url}\">{source}</a>'.format(url=article_json['url'],source=article_json['source']['name']))}

    def remove_title(self, title):
        '''adds article to list of removed, so it is not redisplayed'''
        if title not in self.removed_titles:
            self.removed_titles.append(title)
            logger_cnh.info('news story removed')

    def purge_articles(self):
        for a in self.articles: # remove all currently displayed articles
            self.remove_title(a['title'])

    def update_news(self, article_count=10, sch=True):
        '''updates the news data structure with the latest articles'''
        if sch:
            self.purge_articles()
        api = news_API_request('Covid COVID-19 coronavirus',article_count+len(self.removed_titles))
        self.articles = []
        i = 0
        while len(self.articles) < article_count:
            if i >= len(api):
                logger_cnh.warning('articles list exhasted')
                break
            if api[i]['title'] not in self.removed_titles:
                self.articles.append(self.format_news_article(api[i]))
            i += 1
        logger_cnh.info('covid news updated')

if __name__=='__main__':
    print(news_API_request('Covid COVID-19 coronavirus')[0]) # print first result