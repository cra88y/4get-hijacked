from fourget_hijacker_client import FourgetHijackerClient  
import logging  
  
logger = logging.getLogger(__name__)  
  
categories = ['general']  
paging = True  
engine_type = "online"  
time_range_support = True  
  
def request(query, params):  
    client = FourgetHijackerClient()  
    filters = client.get_engine_filters('brave')  
      
    # Get standard parameter mappings  
    fourget_params = FourgetHijackerClient.get_4get_params(query, params, filters)  
      
    # Apply engine-specific custom parameters from settings.yml  
    if 'brave_spellcheck' in params:  
        fourget_params['spellcheck'] = params['brave_spellcheck']  
      
    params['url'] = 'http://4get-hijacked:80/harness.php'  
    params['method'] = 'POST'  
    params['json'] = {  
        'engine': 'brave',  
        'params': fourget_params  
    }  
    return params  
  
def response(resp):  
    try:  
        response_data = resp.json()  
        logger.debug(f'4get brave response data: {response_data}')  
        results = FourgetHijackerClient.normalize_results(response_data)  
        logger.debug(f'brave-4get results: {len(results)}')  
        return results  
    except Exception as e:  
        logger.error(f'4get brave response error: {e}')  
        return []