'''
This module handles:
    > the main flask application
    > incoming client requests
        (leading to scheduling/cancelling updates)
    > updates to the interface (by passsing values into the template)
'''

## imports
import os
import logging
from json import load
from time import localtime
from flask import Flask, render_template, request
## handler modules
import covid_data_handler
import covid_news_handling

## logging setup
FORMAT = '%(levelname)s @ %(name)s [%(asctime)s]: %(message)s'
logger_main = logging.getLogger('dashboard')
with open('config.json','r') as config:
    logging.basicConfig(filename=os.getcwd()+load(config)['log_file_path'],
                        filemode='w',format=FORMAT,level=logging.INFO)
# debug, info, warning, error, critical

covid_data_handler.update_covid_data()
covid_news_handling.update_news(sch=False)

updates = []
news_articles = []

app = Flask('dashboard',static_folder=os.getcwd()+'\\static')


@app.route('/index')
def index():
    '''Handles incoming client requests, and injects values into the interface'''
    global updates, news_articles
    update_args = request.args # gets request
    ## adding scheduled update to interface
    valid = update_args.get('update') # schedule update time
    if update_args.get('two'): # update label
        if update_args.get('two') in [u['title'] for u in updates]:
            logger_main.warning('label %s already in use')
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
            updates = sorted(updates, key = lambda u : u['content'])
            # sorts updates by time in interface
        else:
            logger_main.warning('invalid update - no sched time or selected target')
    ## scheduling updates
    if valid:
        u = update_args.get('update').split(':')
        update_t_s = (int(u[0])*60 + int(u[1]) - 0.5)*60
        # coverts scheduled update time to seconds
        t = localtime()
        current_t_s = (t[3]*60 + t[4])*60 + t[5] # converts current time to seconds
        time_diff_s = (update_t_s-current_t_s)%(24*60*60)
        # calculates the interval using the difference
        r = bool(update_args.get('repeat'))
        # checks if update should be repeated
        label = update_args.get('two')
        if update_args.get('covid-data'):
            covid_data_handler.schedule_covid_updates(time_diff_s,label,r)
            logger_main.info('covid stats update scheduled')
            # schedules covid data updates
        if update_args.get('news'):
            covid_news_handling.schedule_news_updates(time_diff_s,label,r)
            logger_main.info('covid news update scheduled')
            # schedules covid news story updates
    ## cancelling news stories
    if update_args.get('notif'):
        covid_news_handling.remove_title(update_args.get('notif')) # add title to removed_titles
        logger_main.info('news story removed from interface')
        covid_news_handling.update_news(sch=False) # updates to fill article list
    ## cancelling scheduled updates
    if update_args.get('update_item'):
        s = None
        for scheduler in [covid_data_handler.covid_data_sch,
                          covid_news_handling.covid_news_sch]:
            if update_args.get('update_item') in scheduler:
                s = scheduler[update_args.get('update_item')]
                # get scheduler from list by label
                list(map(s.cancel, s.queue)) # cancels all events in queue
        if s:
            logger_main.info('scheduled update cancelled')
            for i in range(len(updates)): # removes from list of updates in interface
                if updates[i]['title'] == update_args.get('update_item'):
                    updates.pop(i)
                    logging.info('scheduled update removed from interface')
                    break
        else:
            logger_main.warning('scheduler not found')
    ## running (refreshing) all schedulers
    for schedulers in [covid_data_handler.covid_data_sch,
                       covid_news_handling.covid_news_sch]:
        for s in list(schedulers):
            next_event_time = schedulers[s].run(blocking=False)
            if next_event_time:
                logger_main.info('time remaining for %s: %.2f', s, next_event_time)
            else:# removes from list of updates if queue empty (i.e. update done)
                schedulers.pop(s)
                logger_main.info('scheduler %s removed',s)
                i = 0
                while i < len(updates):
                    if updates[i]['title'] == s:
                        updates.pop(i)
                    else:
                        i += 1
            logger_main.info('scheduler %s refreshed',s)
    ## fills interface with values
    area, last7days_cases_local, nation = covid_data_handler.covid_data[:3]
    last7days_cases_nation, hospital_cases, total_deaths = covid_data_handler.covid_data[3:]
    # extracts covid data from covid_data object
    news_articles = covid_news_handling.covid_news
    # extracts covid-related news articles from covid_news object
    return render_template('index_updated.html',title='Covid Dashboard',
                           location=area,
                           local_7day_infections=last7days_cases_local,
                           nation_location=nation,
                           national_7day_infections=last7days_cases_nation,
                           hospital_cases='Hospital Cases: '+str(hospital_cases),
                           deaths_total='Total Deaths: '+str(total_deaths),
                           image='nhs_logo.png', updates=updates,
                           news_articles=news_articles)

if __name__=='__main__':
    app.run()
