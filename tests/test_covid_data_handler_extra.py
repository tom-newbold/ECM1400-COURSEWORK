from covid_data_handler import covid_API_request
from covid_data_handler import get_covid_stats

import re

def test_covid_API_request_code():
    data = covid_API_request()
    assert data['length'] > 0
    assert isinstance(data['data'], list)
    date_format = '[0-9]{4}:(0[1-9])|(1[0-2]):([0-2][1-9])|([1-3]0)|(31)'
    time_format = 'T([01][0-9])|(2[0-4])(:[0-5][0-9]){2}[.][0-9]{6}Z'
    assert bool(re.match('^'+date_format+time_format+'$',data['lastUpdate']))

def test_get_covid_stats():
    data = get_covid_stats()
    assert isinstance(data[0], str)
    assert isinstance(data[2], str)
    assert data[1] > 0
    assert data[3] > 0
    assert data[4] > 0
    assert data[5] > 0