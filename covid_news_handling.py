'''This module handles: news-api requests; fetching (and formatting) new news stories; scheduling these news updates.

Below is a summary of the functions defined within this module

covid_news_handling
    .news_API_request()
        > utilises the requests module to request news stories
    .format_news_article()
        > injects article information into a format compatible with the interface
    .remove_title()
        > marks an article as "seen"
    .purge_articles()
        > calls remove_title on all currently displayed articles
    .update_news()
        > updates a global data structure with (formatted) news articles
    .sched_news_update_repeat()
        > recursively schedules update_news every 24 hours
    .schedule_news_updates()
        > schedules update_news after an interval
'''

from json import load
import requests
import os
import logging

## logging setup
FORMAT = '%(levelname)s @ %(name)s [%(asctime)s]: %(message)s'
logger_cnh = logging.getLogger(__name__)
with open('config.json','r') as config:
    logging.basicConfig(filename=os.getcwd()+load(config)['log_file_path'],
                        filemode='w',format=FORMAT,level=logging.INFO)

def news_API_request(covid_terms: str=None,page_size: int=20) -> dict:
    '''Fetches covid-related news stories from the news api.

    Args:
        covid_terms: search terms for api request
        page_size: number of articles fetched from api

    Returns:
        A dictionary containing news articles returned from the api.
        The format of the returned dictionary, along with types, it detailed below.
        
        Expected (i.e. no error):
        {
            status[str]: flag for request successful, "ok"
            totalResults[int]: article count
            articles[list][dict]: {
                source[dict]: {
                    id[str]: identifier
                    name[str]: display name
                }
                author[str]: author name
                title[str]: article title
                description[str]: short description of article
                url[str]: link to article
                urlToImage[str]: link to related image for article
                publishedAt[str]: %format YYYY-MM-DDtime
                content[str]: article content, max 200 characters
            }
        }

        Exception (i.e. error):
        {
            staus[str]: as before, "error"
            code[str]: see https://newsapi.org/docs/errors, (200, 400, 401, 429, 500)
            message[str]: error description
        }
    '''
    with open('config.json','r') as config:
        config_json = load(config)
        if not covid_terms:
            covid_terms = config_json['news_search_terms']
        _APIkey = config_json['api_keys']['news_api'] # get api key from config.json
        logger_cnh.info('API key fetched from config file')
    if not isinstance(covid_terms,str) or _APIkey=='[api-key]': return
    keywords = covid_terms.split(' ')
    url = 'https://newsapi.org/v2/everything?q='+'+OR+'.join(keywords)+'&pageSize='+str(page_size)+'&apiKey='+_APIkey
    response = requests.get(url, auth=('user','pass')) # request related stories from newsAPI
    logger_cnh.info('news API request [url=%s]',url)
    return response.json()

global covid_news, removed_titles, covid_news_sch
covid_news = []
removed_titles = []
covid_news_sch = {}
logger_cnh.info('covid news globals initialized')

from flask import Markup
def format_news_article(article_json: dict) -> dict:
    '''Formats news article into a dictionary which can be input into the flask template.

    Args:
        article_json: raw json representing a single article

    Returns:
        A dictionary representing a news article.
        The format of the returned dictionary, along with types, it detailed below.

        {
            title[str]: title of article
            content[str]: short description and ling (formatted with flask.Markup)
        }
    '''
    if not isinstance(article_json,dict): return
    for key in ['title','description','url','source']:
        if key not in article_json: return
    if 'name' not in article_json['source']: return
    return {'title':article_json['title'],'content':Markup(article_json['description']+
            '<a href=\"{url}\">{source}</a>'.format(url=article_json['url'],source=article_json['source']['name']))}

def remove_title(title: str) -> type(None):
    '''Adds article to (global) list of removed articles, so it is not redisplayed when the interface is updated.

    Args:
        title: title of article to be removed
    '''
    if not isinstance(title,str): return
    global removed_titles
    if title not in removed_titles:
        removed_titles.append(title)
        logger_cnh.info('news story removed')

def purge_articles() -> type(None):
    '''Removes all currently displayed articles (i.e. marked as seen, not redisplayed).'''
    for a in covid_news:
        remove_title(a['title'])

def update_news(covid_terms: str=None, article_count: int=10, sch: bool=True) -> type(None):
    '''Updates the covid_news data structure (global) with the latest articles.

    Args:
        covid_terms: search terms for news_api request - stored in config.json
        article_count: number of articles to be displayed in the interface
        sch: flag for scheduled (over intermittent) updates
    '''
    with open('config.json','r') as config:
        if not covid_terms:
            covid_terms = load(config)['news_search_terms']
    if not isinstance(covid_terms,str): return
    global covid_news, removed_titles
    if sch:
        purge_articles()
    api = news_API_request(covid_terms,article_count+len(removed_titles))['articles']
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
def sched_news_update_repeat(sch: sched.scheduler) -> type(None):
    '''Uses recursion to implement 24 hour repeating updates.

    Args:
        sch: associated scheduler
    '''
    if not isinstance(sch, sched.scheduler): return
    sch.enter(24*60*60, 1, update_news)
    sch.enter(24*60*60, 2, sched_news_update_repeat, argument=(sch,))
    logger_cnh.info('repeat update scheduled')

def schedule_news_updates(update_interval: float, update_name: str, repeating: bool=False) -> type(None):
    '''Creates scheduler (stored in covid_news_sch) and schedules news updates.

    Args:
        update_interval: delay of (initial) scheduled update
        update_name: label of update in interface, index of scheduler in covid_news_sch
        repeating: flag for repeating updates (every 24 hours)
    '''
    if not (update_interval > 0 or isinstance(update_name,str)): return
    global covid_news_sch
    s = sched.scheduler(time, sleep)
    s.enter(update_interval, 1, update_news)
    if repeating: # will schedule a repeating update in after the interval
        s.enter(update_interval, 2, sched_news_update_repeat, argument=(s,))
        logger_cnh.info('repeat update scheduled')
    covid_news_sch[update_name] = s

if __name__=='__main__':
    print(news_API_request(load(open('config.json','r'))['news_search_terms'])['articles'][0]) # first article