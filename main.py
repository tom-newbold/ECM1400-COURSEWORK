'''
This module handles:
    > the main flask application
    > incoming client requests
        (leading to scheduling/cancelling updates)
    > updates to the interface (by passsing values into the template)
'''

## imports
from json import load
import os
from time import localtime, time, sleep
import sched
from flask import Flask, render_template, request, redirect, url_for
import logging

## logging setup
FORMAT = '%(levelname)s @ %(name)s [%(asctime)s]: %(message)s'
logger_main = logging.getLogger('dashboard')
with open('config.json','r') as config:
    logging.basicConfig(filename=os.getcwd()+load(config)['log_file_path'],
                        filemode='w',format=FORMAT,level=logging.INFO)
# debug, info, warning, error, critical

## from handler modules
from covid_data_handler import update_covid_data, schedule_covid_updates
import covid_data_handler # for globals
from covid_news_handling import update_news, remove_title, schedule_news_updates
import covid_news_handling # for globals

update_covid_data()
update_news(sch=False)

updates = []
news_articles = []

app = Flask('dashboard',static_folder=os.getcwd()+'\\static')

@app.route('/index')
def index():
    global updates, news_articles
    area, last7days_cases_local, nation, last7days_cases_nation, hospital_cases, total_deaths = covid_data_handler.covid_data
    # extracts covid data from covid_data object
    news_articles = covid_news_handling.covid_news
    # extracts covid-related news articles from covid_news object
    update_args = request.args # gets request
    ## adding scheduled update to interface
    valid = update_args.get('update') # schedule update time
    if update_args.get('two'): # update label
        if update_args.get('two') in [u['title'] for u in updates]:
            logger_main.warning('label %s already in use')
            return redirect(url_for('index'))
        content = ':'.join(update_args.get('update').split(':')) + ' ~ '
        if update_args.get('covid-data'):
            content += 'Covid Data'
            if update_args.get('news'):
                 content += ' and News'
        elif update_args.get('news'):
            content += 'News'
        else:
            valid = False # invalid if neither data or news update
        content += ' Updates'
        if update_args.get('repeat'):
            content += ' (repeating)'
        if valid:
            update = {'title':update_args.get('two'),'content':content}
            updates.append(update) # adds to list of updates in interface
            updates = sorted(updates, key = lambda u : u['content']) # sorts updates by time in interface
        else:
            logger_main.warning('invalid update - no sched time or selected target')
            return redirect(url_for('index'))
    ## scheduling updates
    if valid:
        u = update_args.get('update').split(':')
        update_t_s = (int(u[0])*60 + int(u[1]) - 0.5)*60 # coverts scheduled update time to seconds
        t = localtime()
        current_t_s = (t[3]*60 + t[4])*60 + t[5] # converts current time to seconds
        time_diff_s = (update_t_s-current_t_s)%(24*60*60) # calculates the interval using the difference
        r = True if update_args.get('repeat') else False # checks if update should be repeated
        if update_args.get('covid-data'):
            covid_data_handler.schedule_covid_updates(time_diff_s,update_args.get('two'),r)
            logger_main.info('covid stats update scheduled')
            # schedules covid data updates
        if update_args.get('news'):
            covid_news_handling.schedule_news_updates(time_diff_s,update_args.get('two'),r)
            logger_main.info('covid news update scheduled')
            # schedules covid news story updates
        return redirect(url_for('index')) # refreshes interface
    ## cancelling news stories
    if update_args.get('notif'):
        remove_title(update_args.get('notif')) # add title to removed_titles (so not displayed)
        logger_main.info('news story removed from interface')
        update_news(sch=False) # updates to fill article list
        return redirect(url_for('index')) # refreshes interface
    ## cancelling scheduled updates
    if update_args.get('update_item'):
        s = None
        for scheduler in [covid_data_handler.covid_data_sch,covid_news_handling.covid_news_sch]:
            if update_args.get('update_item') in scheduler.keys():
                s = scheduler[update_args.get('update_item')] # get scheduler from list by label
                list(map(s.cancel, s.queue)) # cancels all events in queue
        if s:
            logger_main.info('scheduled update cancelled')
            for i in range(len(updates)): # removes from list of updates in interface
                if updates[i]['title'] == update_args.get('update_item'):
                    updates.pop(i)
                    logging.info('scheduled update removed from interface')
                    break
            return redirect(url_for('index')) # refreshes interface
        else:
            logger_main.warning('scheduler not found')
    ## running (refreshing) all schedulers
    for schedulers in [covid_data_handler.covid_data_sch,covid_news_handling.covid_news_sch]: # botch to save me rewriting this bit
        for s in list(schedulers):
            if not schedulers[s].empty():
                schedulers[s].run(blocking=False)
            else: # removes from list of updates if queue empty (i.e. update done)
                schedulers[s].run(blocking=False)
                if schedulers[s].empty():
                    schedulers.pop(s)
                    logger_main.info('scheduler %s removed',s)
                    i = 0
                    while i < len(updates):
                        if updates[i]['title'] == s:
                            updates.pop(i)
                        else:
                            i += 1
                    return redirect(url_for('index')) # refreshes interface
            logger_main.info('scheduler %s refreshed',s)
    ## fills interface with values
    return render_template('index_updated.html',title='Covid Dashboard', location=area, local_7day_infections=last7days_cases_local,
                            nation_location=nation, national_7day_infections=last7days_cases_nation, hospital_cases='Hospital Cases: '+str(hospital_cases),
                            deaths_total='Total Deaths: '+str(total_deaths), image='nhs_logo.png', updates=updates, news_articles=news_articles)

if __name__=='__main__':
    app.run()