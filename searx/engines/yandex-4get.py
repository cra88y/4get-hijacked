from fourget_hijacker_client import FourgetHijackerClient
import logging

logger = logging.getLogger(__name__)

categories = ['general']
paging = True
engine_type = "online"
time_range_support = True

def request(query, params):
    fourget_params = FourgetHijackerClient.get_4get_params(query, params, engine_name='yandex')

    params['url'] = 'http://4get-hijacked:80/harness.php'
    params['method'] = 'POST'
    params['json'] = {'engine': 'yandex', 'params': fourget_params}
    return params

def response(resp):
    try:
        return FourgetHijackerClient.normalize_results(resp.json())
    except Exception as e:
        logger.error(f'4get yandex response error: {e}')
        return []