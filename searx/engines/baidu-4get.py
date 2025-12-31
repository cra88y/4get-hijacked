from fourget_hijacker_client import FourgetHijackerClient  
import logging  
  
logger = logging.getLogger(__name__)  
  
categories = ['general']  
paging = True  
engine_type = "online"  
time_range_support = True  
  
def request(query, params):  
    client = FourgetHijackerClient()  
    filters = client.get_engine_filters('baidu')  
      
    # Get standard parameter mappings  
    fourget_params = FourgetHijackerClient.get_4get_params(query, params, filters)  
      
    # Apply engine-specific custom parameters from settings.yml  
    if 'baidu_category' in params:  
        fourget_params['category'] = params['baidu_category']  
      
    params['url'] = 'http://4get-hijacked:80/harness.php'  
    params['method'] = 'POST'  
    params['json'] = {  
        'engine': 'baidu',  
        'params': fourget_params  
    }  
    return params  
  
def response(resp):  
    try:  
        response_data = resp.json()  
        logger.debug(f'4get baidu response data: {response_data}')  
        results = FourgetHijackerClient.normalize_results(response_data)  
        logger.debug(f'baidu-4get results: {len(results)}')  
        return results  
    except Exception as e:  
        logger.error(f'4get baidu response error: {e}')  
        return []