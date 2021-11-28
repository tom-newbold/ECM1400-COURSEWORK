from json import load
import os
import logging

## logging setup
FORMAT = '%(levelname)s @ %(name)s [%(asctime)s]: %(message)s'
logger_cdh = logging.getLogger(__name__)
logging.basicConfig(filename=os.getcwd()+load(open('config.json','r'))['log_file_path'],filemode='w',format=FORMAT,level=logging.INFO)

def parse_csv_data(csv_filename):
    '''return list of strings for rows in the file'''
    return [line.strip('\n') for line in open(csv_filename, 'r').readlines()]

def process_covid_csv_data(covid_csv_data):
    '''extract covid stats from csv (as returned from the previous function)'''
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
def covid_API_request(location, location_type):
    '''returns a json containing the set of metrics detailed below'''
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
    '''extracts the requested metric from a json (returned from the covid API)'''
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
    '''fetches relevant statistics to be displayed in the interface'''
    location_local = load(open('config.json','r'))['location']
    location_type = load(open('config.json','r'))['location_type']
    logger_cdh.info('location fetched from config file')
    api_local = covid_API_request(location_local,location_type)
    api_nation = covid_API_request('England','nation')
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
    global covid_data
    covid_data = get_covid_stats()
    logger_cdh.info('covid stats updated [covid_data=%s]', covid_data)


# \/ remove this class
class covid_data_:
    '''data structure for storing covid data'''
    def __init__(self):
        self.stats = []

    def update_covid_data(self):
        '''updates the stats data structure with the latest covid stats'''
        self.stats = get_covid_stats()
        logger_cdh.info('covid stats updated')

## extra functions ----------------------------------------

import sched
from time import time, sleep
def sched_covid_update_repeat(sch):
    '''uses recrsion to implement 24 hour repeating updates'''
    sch.enter(24*60*60, 1, update_covid_data)
    if len(sch.queue) < 30:
        sch.enter(24*60*60, 2, sched_covid_update_repeat, argument=(s))

def schedule_covid_updates(update_interval, update_name, repeating=False):
    '''creates scheduler for scheduling updates'''
    global covid_data_sch
    s = sched.scheduler(time, sleep)
    s.enter(update_interval, 1, update_covid_data)
    if repeating: # schedules a repeating update in 24 hours (this is recursive)
        #s.enter(update_interval, 1, s.enter, argument=(24*60*60, 1, update_covid_data, True))
        s.enter(update_interval, 2, sched_covid_update_repeat, argument=(s))
    covid_data_sch[update_name] = s

if __name__=='__main__':
    print(get_covid_stats())    