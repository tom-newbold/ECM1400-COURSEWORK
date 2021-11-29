'''
This module handles:
    > uk-covid-19 api requests
    > fetching up to date stats
    > scheduling these stats updates
[function summary]
covid_data_handler.parse_csv_data() : see below
                  .process_csv_data() : used in conjunction to extract data from a static file
                  .covid_API_request() : utilises the uk_covid19 module to request data
                  .get_stats_from_json() : extracts a specific metric from json returned from the above function
                  .get_covid_stats() : utilises the previous function to get a set of metrics for the interface
                  .update_covid_data() : updates a global data structure with the output of the previous function
                  .sched_covid_update_repeat() : recursively schedules update_covid_data every 24 hours
                  .schedule_covid_updates() : schedules update_covid_data after an interval
'''

from json import load
import os
import logging

## logging setup
FORMAT = '%(levelname)s @ %(name)s [%(asctime)s]: %(message)s'
logger_cdh = logging.getLogger(__name__)
with open('config.json','r') as config:
    logging.basicConfig(filename=os.getcwd()+load(config)['log_file_path'],
                        filemode='w',format=FORMAT,level=logging.INFO)

def parse_csv_data(csv_filename):
    '''return list of strings for rows in the file
        > args
            csv_filename[str] : filename of static csv file
        > returns
            [list] : lines in file
    '''
    return [line.strip('\n') for line in open(csv_filename, 'r').readlines()]

def process_covid_csv_data(covid_csv_data):
    '''extract covid stats from csv format
        > args
            covid_csv_data[list] : list of lines from covid data csv - as returned from parse_csv_data
        > returns
            [tuple] : (
                last7days_cases_total[int]  : summative latest week case count
                current_hospital_cases[int] : current hospital cases
                total_deaths[int]           : latest death toll
            )
    '''
    last7days_cases = []
    i = 1
    prev_empty = True
    # get list of 7 latest daily case counts
    # first non-zero is ignored as not accurate
    while len(last7days_cases) < 7:
        print(i)
        daily_cases = covid_csv_data[i].split(',')[6]
        if(len(daily_cases) > 0):
            if(prev_empty):
                prev_empty = False
            else:
                last7days_cases.append(int(daily_cases))
        i += 1
    last7days_cases_total = sum(last7days_cases)
    ## print('7day cases fetched')
    current_hospital_cases = ''
    i = 1
    # get first non-zero value for hospital case count
    while current_hospital_cases == '':
        current_hospital_cases = covid_csv_data[i].split(',')[5]
        i += 1
    current_hospital_cases = int(current_hospital_cases)
    ## print('hospital cases fetched')
    total_deaths = ''
    i = 1
    # get first non-zero value for total deaths to date
    while total_deaths == '':
        total_deaths = covid_csv_data[i].split(',')[4]
        i += 1
    total_deaths = int(total_deaths)
    ## print('total cases fetched')
    return last7days_cases_total, current_hospital_cases, total_deaths # cases for last 7 days, current hospital cases, cumulative death toll

# arguments will be stored in config file
from uk_covid19 import *
from json import load
def covid_API_request(location=None, location_type=None):
    '''returns a json containing the set of metrics detailed in metrics[dict]
        > args
            location[str]      : area code for api request
            location_type[str] : area type for api request
        > returns
            [dict] : {
                data[list][dict] : {
                    date[str]                     : [format YYYY-MM-DD]
                    areaName[string]              : as specifed in area[list][str]
                    areaType[string]              : see above
                    newCasesByPublishDate[int]    : case count
                    cumDeaths28ByPublishDate[int] : death toll
                    hospitalCases[int]            : hospital cases
                }
                lastUpdate[str]  : time of latest entry [format YYYY-MM-DDtime]
                length[int]      : number of entries fetched from api
                totalPages[int]  : number of pages fetched from api
            }
    '''
    with open('config.json','r') as config:
        config_json = load(config)
        if not location:
            location = config_json['location']
            logger_cdh.info('location fetched from config file')
        if not location_type:
            location_type = config_json['location_type']
            logger_cdh.info('location_type fetched from config file')
    area = ['areaType='+location_type, 'areaName='+location]
    metrics = {
        'date': 'date',
        'areaName': 'areaName',
        'areaType':'areaType',
        'newCasesByPublishDate': 'newCasesByPublishDate',
        'cumDeaths28DaysByPublishDate': 'cumDeaths28DaysByPublishDate',
        'hospitalCases':'hospitalCases'
        }
    api = Cov19API(filters=area, structure=metrics)
    data = api.get_json()
    logger_cdh.info('covid API request')
    return data # dictionary of covid data fetched from api

## extra functions ----------------------------------------

def get_stats_from_json(covid_stats_json, metric, count=1, skip=False):
    '''extracts the specified metric from a json (returned from the covid API)
        > args
            covid_stats_json[dict] : raw json - as returned from covid_API_request
            metric[str]            : stat to extract
            count[int]             : number of entries to cache (used for 7 day sums)
            skip[bool]             : flag for skiping first entry (more accurate for certain metrics)
        > returns
            [str] : area code associated with api request
            [int] : extracted value
    '''
    csj = covid_stats_json['data']
    data = []
    i = 0
    while len(data) < count:
        val = csj[i][metric]
        if val != None:
            if skip:
                skip = not skip
            else:
                data.append(val)
        i += 1
        if i >= len(csj): break
    return csj[0]['areaName'], sum(data)

def get_covid_stats():
    '''fetches relevant statistics to be displayed in the interface
        > returns
            [tuple] : (
                area[str]                   : local area code - stored in config.json
                last7days_cases_local[int]  : summative previous week case count (local)
                nation[str]                 : nation area code - stored in config.json
                last7days_cases_nation[int] : summative previous week case count (nation)
                hospital_cases[int]         : current hospital cases
                total_deaths[int]           : cumulative death toll
            )
    '''
    api_local = covid_API_request()
    api_nation = covid_API_request('England','nation')
    logger_cdh.info('api requests complete')
    area, last7days_cases_local = get_stats_from_json(api_local, 'newCasesByPublishDate', 7, True)
    nation, last7days_cases_nation = get_stats_from_json(api_nation, 'newCasesByPublishDate', 7, True)
    hospital_cases = get_stats_from_json(api_nation, 'hospitalCases')[1]
    total_deaths = get_stats_from_json(api_nation,'cumDeaths28DaysByPublishDate')[1]
    return area, last7days_cases_local, nation, last7days_cases_nation, hospital_cases, total_deaths

global covid_data, covid_data_sch
covid_data = []
covid_data_sch = {}
logger_cdh.info('covid data globals initialized')

def update_covid_data():
    '''updates the covid_data data structure (global) with the latest stats'''
    global covid_data
    covid_data = get_covid_stats()
    logger_cdh.info('covid stats updated [covid_data=%s]', covid_data)

import sched
from time import time, sleep
def sched_covid_update_repeat(sch):
    '''uses recursion to implement 24 hour repeating updates
        > args
            sch[sched.scheduler] : associated scheduler
    '''
    sch.enter(24*60*60, 1, update_covid_data)
    if len(sch.queue) < 30:
        sch.enter(24*60*60, 2, sched_covid_update_repeat, argument=(s))

def schedule_covid_updates(update_interval, update_name, repeating=False):
    '''creates scheduler (stored in covid_data_sch) and schedules news updates
        > args
            update_interval[float] : delay of (initial) scheduled update
            update_name[str]       : label of update in interface - index of scheduler in covid_data_sch
            repeating[bool]        : flag for repeating updates (every 24 hours)
    '''
    global covid_data_sch
    s = sched.scheduler(time, sleep)
    s.enter(update_interval, 1, update_covid_data)
    if repeating: # schedules a repeating update in 24 hours (this is recursive)
        #s.enter(update_interval, 1, s.enter, argument=(24*60*60, 1, update_covid_data, True))
        s.enter(update_interval, 2, sched_covid_update_repeat, argument=(s))
    covid_data_sch[update_name] = s

if __name__=='__main__':
    print(get_covid_stats()) # current covid stats