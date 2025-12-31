from fourget_hijacker_client import FourgetHijackerClient  
import logging  
  
logger = logging.getLogger(__name__)  
  
categories = ['general']  
paging = True  
engine_type = "online"  
time_range_support = True  
  
def request(query, params):  
    client = FourgetHijackerClient()  
    filters = client.get_engine_filters('marginalia')  
      
    # Get standard parameter mappings  
    fourget_params = FourgetHijackerClient.get_4get_params(query, params, filters)  
      
    # Handle time range → recent mapping  
    if 'time_range' in params and params['time_range'] not in [None, '']:  
        fourget_params['recent'] = 'no'  
      
    # Apply engine-specific custom parameters from settings.yml  
    if 'marginalia_recent' in params:  
        fourget_params['recent'] = params['marginalia_recent']  
    if 'marginalia_intitle' in params:  
        fourget_params['intitle'] = params['marginalia_intitle']  
      
    params['url'] = 'http://4get-hijacked:80/harness.php'  
    params['method'] = 'POST'  
    params['json'] = {  
        'engine': 'marginalia',  
        'params': fourget_params  
    }  
    return params  
  
def response(resp):  
    try:  
        response_data = resp.json()  
        logger.debug(f'4get marginalia response data: {response_data}')  
        results = FourgetHijackerClient.normalize_results(response_data)  
        logger.debug(f'marginalia-4get results: {len(results)}')  
        return results  
    except Exception as e:  
        logger.error(f'4get marginalia response error: {e}')  
        return []