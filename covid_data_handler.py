'''This module handles: uk-covid-19 api requests; fetching up to date stats; scheduling stats updates.

Below is a summary of the functions defined within this module

covid_data_handler
    .parse_csv_data()
        > extracts lines from a csv file
    .process_csv_data()
        > used in conjunction with the above function to extract data from a static file
    .covid_API_request()
        > utilises the uk_covid19 module to request data
    .get_stats_from_json()
        > extracts a specific metric from json returned from the above function
    .get_covid_stats()
        > utilises the previous function to get a set of metrics for the interface
    .update_covid_data()
        > updates a global data structure with the output of the previous function
    .sched_covid_update_repeat()
        > recursively schedules update_covid_data every 24 hours
    .schedule_covid_updates()
        > schedules update_covid_data after an interval
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

def parse_csv_data(csv_filename: str) -> list:
    '''Returns list of strings for rows in the file.
    
    Args:
        csv_filename: Filename of static csv file

    Returns:
        Lines from file
    '''
    if not isinstance(csv_filename,str): return
    if not os.path.exists(csv_filename): return
    return [line.strip('\n') for line in open(csv_filename, 'r').readlines()]

def process_covid_csv_data(covid_csv_data: list) -> tuple[int, int, int]:
    '''Extracts covid stats from csv format.
    
    Args:
        covid_csv_data : List of lines from covid data csv - as returned from parse_csv_data

    Returns:
        Three metrics, detailed below, from the csv lines list.

        last7days_cases_total: Summative latest week case count
        current_hospital_cases: Current hospital cases
        total_deaths: Latest death toll
    '''
    if not isinstance(covid_csv_data,list): return
    if len(covid_csv_data)==0: return
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
def covid_API_request(location: str=None, location_type: str=None) -> dict:
    '''Returns a json containing the set of metrics.

    Args:
        location: Area code for api request
        location_type: Area type for api request

    Returns:
        A dictionary containing the metrics specified in the metrics[dict] variable.
        The format of the returned dictionary, along with types, is detailed below.

        {
            data[list][dict] : {
                date[str]: %format YYYY-MM-DD
                areaName[str]: as specifed in area[list][str]
                areaType[str]: see above
                newCasesByPublishDate[int]: case count
                cumDeaths28ByPublishDate[int]: death toll
                hospitalCases[int]: hospital cases
            }
            lastUpdate[str]: time of latest entry, %format YYYY-MM-DDtime
            length[int]: number of entries fetched from api
            totalPages[int]: number of pages fetched from api
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
    if not (isinstance(location,str) or isinstance(location_type,str)): return
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

def get_stats_from_json(covid_stats_json: dict, metric: str, count: int=1, skip: bool=False) -> tuple[str, int]:
    '''Extracts the specified metric from a json.

    Args:
        covid_stats_json: raw json - as returned from covid_API_request
        metric: stat to extract
        count: number of entries to cache (used for 7 day sums)
        skip: flag for skiping first entry (more accurate for certain metrics)

    Returns:
        The area code associated with the api request, along with the value requested.
    '''
    if not isinstance(covid_stats_json,dict): return
    covid_stats_list = covid_stats_json['data']
    if not isinstance(metric,str) or metric not in covid_stats_list[0].keys(): return
    data = []
    i = 0
    while len(data) < count:
        val = covid_stats_list[i][metric]
        if val != None:
            if skip:
                skip = not skip
            else:
                data.append(val)
        i += 1
        if i >= len(covid_stats_list): break
    return covid_stats_list[0]['areaName'], sum(data)

def get_covid_stats() -> tuple[str, int, str, int, int, int]:
    '''Fetches relevant statistics to be displayed in the interface.

    Returns:
        Area codes (local and national), along with 4 statistics.
        Detailed below.
        
        area: local area code - stored in config.json
        last7days_cases_local: summative previous week case count (local)
        nation: nation area code
        last7days_cases_nation: summative previous week case count (nation)
        hospital_cases: current hospital cases
        total_deaths: cumulative death toll
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

def update_covid_data() -> type(None):
    '''Updates the covid_data data structure (global) with the latest stats.'''
    global covid_data
    covid_data = get_covid_stats()
    logger_cdh.info('covid stats updated [covid_data=%s]', covid_data)

import sched
from time import time, sleep
def sched_covid_update_repeat(sch: sched.scheduler) -> type(None):
    '''Uses recursion to implement 24 hour repeating updates.

    Args:
        sch: associated scheduler
    '''
    if not isinstance(sch, sched.scheduler): return
    sch.enter(24*60*60, 1, update_covid_data)
    sch.enter(24*60*60, 2, sched_covid_update_repeat, argument=(sch,))
    logger_cdh.info('repeat update scheduled')

def schedule_covid_updates(update_interval: float, update_name: str, repeating: bool=False) -> type(None):
    '''Creates scheduler (stored in covid_data_sch) and schedules news updates.

    Args:
        update_interval: delay of (initial) scheduled update
        update_name: label of update in interface - index of scheduler in covid_data_sch
        repeating: flag for repeating updates (every 24 hours)
    '''
    if not (update_interval > 0 or isinstance(update_name,str)): return
    global covid_data_sch
    s = sched.scheduler(time, sleep)
    s.enter(update_interval, 1, update_covid_data)
    if repeating: # will schedule a repeating update in after the interval
        s.enter(update_interval, 2, sched_covid_update_repeat, argument=(s,))
        logger_cdh.info('repeat update scheduled')
    covid_data_sch[update_name] = s

if __name__=='__main__':
    print(get_covid_stats()) # current covid stats