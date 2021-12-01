from json import load
import os.path

def test_config_json_validity():
    assert os.path.exists('config.json'), 'config.json does not exist'
    with open('config.json') as config:
        config_json = load(config)
        assert isinstance(config_json['location'], str)
        assert isinstance(config_json['location_type'], str)
        assert isinstance(config_json['news_search_terms'].split(' '), list)
        assert isinstance(config_json['api_keys']['news_api'], str)
        assert not config_json['api_keys']['news_api']=='[api-key]'