from covid_news_handling import news_API_request

def test_news_API_request():
    data = news_API_request()
    assert isinstance(data, dict)
    assert data['status']=='ok'
    assert data['totalResults'] > 0
    assert isinstance(data['articles'], list)