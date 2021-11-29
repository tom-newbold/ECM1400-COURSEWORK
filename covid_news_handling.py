from json import load
import requests
import os
import logging

## logging setup
FORMAT = '%(levelname)s @ %(name)s [%(asctime)s]: %(message)s'
logger_cnh = logging.getLogger(__name__)
logging.basicConfig(filename=os.getcwd()+load(open('config.json','r'))['log_file_path'],filemode='w',format=FORMAT,level=logging.INFO)

def news_API_request(covid_terms=load(open('config.json','r'))['news_search_terms'],page_size=20):
    ''' get covid-related news stories from the news api
        > args
            covid_terms[str] : search terms for api request
            page_size[int]   : number of articles fetched from api
        > returns
            [dict] : {
                status[str]          : flag for request successful - ok or error
                ? IF status==ok
                totalResults[int]    : article count
                articles[list][dict] : {
                    source[dict]     : {
                        id[str]   : identifier
                        name[str] : display name
                    }
                    author[str]      : author name
                    title[str]       : article title
                    description[str] : short description of article
                    url[str]         : link to article
                    urlToImage[str]  : link to related image for article
                    publishedAt[str] : [format YYYY-MM-DDtime]
                    content[str]     : article content - max 200 characters
                }
                ? IF staus==error
                code[str]    : see https://newsapi.org/docs/errors - 200, 400, 401, 429, 500
                message[str] : error description
            }
    '''
    _APIkey = load(open('config.json','r'))['api_keys']['news_api'] # get api key from config.json
    logger_cnh.info('API key fetched from config file')
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
def format_news_article(article_json):
    ''' formats news article into a dictionary which can be input into the flask template
        > args
            article_json[dict] : raw json representing a single article
        > returns
            [dict] : {
                title[str]   : title of article
                content[str] : short description and ling (formatted with flask.Markup)
            }
    '''
    return {'title':article_json['title'],'content':Markup(article_json['description']+
            '<a href=\"{url}\">{source}</a>'.format(url=article_json['url'],source=article_json['source']['name']))}

def remove_title(title):
    '''adds article to (global) list of removed articles, so it is not redisplayed when the interface is updated
        > args
            title[str] : title of article to be removed
    '''
    global removed_titles
    if title not in removed_titles:
        removed_titles.append(title)
        logger_cnh.info('news story removed')

def purge_articles():
    '''removes all currently displayed articles (i.e. marked as seen, not redisplayed)'''
    for a in covid_news:
        remove_title(a['title'])

def update_news(covid_terms, article_count=10, sch=True):
    '''updates the covid_news data structure (global) with the latest articles
        > args
            covid_terms[str]   : search terms for news_api request - stored in config.json
            article_count[int] : number of articles to be displayed in the interface
            sch[bool]          : flag for scheduled (over intermittent) updates
    '''
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
def sched_news_update_repeat(sch, search_terms):
    '''uses recursion to implement 24 hour repeating updates
        > args
            sch[sched.scheduler] : associated scheduler
            search_terms[str]    : string containing search terms for news_api request
    '''
    sch.enter(24*60*60, 1, update_news, argument=(search_terms))
    if len(sch.queue) < 30:
        sch.enter(24*60*60, 2, sched_news_update_repeat, argument=(s))

def schedule_news_updates(update_interval, update_name, search_terms, repeating=False):
    '''creates scheduler (stored in covid_news_sch) and schedules news updates
        > args
            update_interval[float] : delay of (initial) scheduled update
            update_name[str]       : label of update in interface - index of scheduler in covid_news_sch
            search_terms[str]      : search terms for news_api request
            repeating[bool]        : flag for repeating updates (every 24 hours)
    '''
    global covid_news_sch
    s = sched.scheduler(time, sleep)
    s.enter(update_interval, 1, update_news, argument=(search_terms))
    if repeating: # schedules a repeating update in 24 hours (this is recursive)
        s.enter(update_interval, 2, sched_news_update_repeat, argument=(s, search_terms))
    covid_news_sch[update_name] = s

if __name__=='__main__':
    print(news_API_request(load(open('config.json','r'))['news_search_terms'])['articles'][0]) # first article