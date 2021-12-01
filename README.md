# COVID Dashboard

### ECM1400 Coursework Project

The aim of this coursework was to create a personalised data dashboard which would provide the user with up-to-data COVID statistics, along with relavant news stories.


This was implemented using various modules, including:  
- flask : Used to run the web application, implementing the interface using the *index.html* file provided  
- sched : Used to schedule updates to the interface (statistics and news) at times specified by the user  
- uk_covid19 and requests : Used to fetch data from the relavant APIs  


Along with other backend modules:  
- json : Used to load API responses into a readable dictionary format  
- logging : Used to track the program during runtime  
- pytest : Used to run tests  

---

## Prequisites / Installation

#### Installing Required Modules

A list of modules to be installed can be found in *requirements.txt*. Installing these modules can be done by running *requirements.bat*, or manually by executing `pip install -r requirements.txt` in the project directory

#### API key

In order for news stories to be displayed, a key for the NewsAPI is required.  
Visit <https://newsapi.org/> and create a free account. Open *config_template.json*, and replace `[api-key]` with your key. Once this is done, make sure to rename this file to *config.json*.

#### Running the Dashboard

Now, to start the dashboard, run *dashboard.bat*. This will automatically run the test suite, host the flask application, and open the correct url in the default browser.

---

## Developer Documentation

This project is intended to be run using Python 3.9 (64-bit)

#### Function Summary

A summary of the functions from both supplementary modules is detailed below.


covid_data_handler.
- parse_csv_data() > see process_csv_data
- process_csv_data() > used in conjunction to extract data from a static file
- covid_API_request() > utilises the uk_covid19 module to request data
- get_stats_from_json() > extracts a specific metric from json returned from the above function
- get_covid_stats() > utilises the previous function to get a set of metrics for the interface
- update_covid_data() > updates a global data structure with the output of the previous function
- sched_covid_update_repeat() > recursively schedules update_covid_data every 24 hours
- schedule_covid_updates() > schedules update_covid_data after an interval


covid_news_handling.
- news_API_request()>: utilises the requests module to request news stories
- format_news_article() > injects article information into a format compatible with the interface
- remove_title() > marks an article as "seen"
- purge_articles() > calls remove_title on all currently displayed articles
- update_news() > updates a global data structure with (formatted) news articles
- sched_news_update_repeat() > recursively schedules update_news every 24 hours
- schedule_news_updates() > schedules update_news after an interval

---

## Other Details

#### Author

**Thomas Newbold**  
<tn337@exeter.ac.uk>
