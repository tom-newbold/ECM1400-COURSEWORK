##### COVID Dashboard

## ECM1400 Coursework Project

The aim of this coursework was to create a personalised data dashboard which would provide the user with up-to-data COVID statistics, along with relavant news stories.

This was implemented using various modules, including:
	> flask : Used to run the web application, implementing the interface using the *index.html* file provided
	> sched : Used to schedule updates to the interface (statistics and news) at times specified by the user
	> uk_covid19 and requests : Used to fetch data from the relavant APIs

Along with other backend modules:
	> json : Used to load API responses into a readable dictionary format
	> logging : Used to track the program during runtime
	> pytest : Used to run tests

---

### Prequisites / Installation

# Installing Required Modules

A list of modules to be installed can be found in *requirements.txt*. Installing these modules can be done by running *requirements.bat*, or manually by executing `pip install -r requirements.txt` in the project directory

# API key

In order for news stories to be displayed, a key for the NewsAPI is required.
Visit https://newsapi.org/ and create a free account. Open *config_template.json*, and replace `[api-key]` with your key. Once this is done, make sure to rename this file to *config.json*.

# Running the Dashboard

Now, to start the dashboard, run *dashboard.bat*. This will automatically run the test suite, host the flask application, and open the correct url in the default browser.

---

### Developer Documentation

This project is intended to be run using Python 3.9 (64-bit)

---

### Other Details

# Author

**Thomas Newbold**
