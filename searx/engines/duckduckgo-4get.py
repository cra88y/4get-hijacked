from fourget_hijacker_client import FourgetHijackerClient  
import logging  
  
logger = logging.getLogger(__name__)  
  
categories = ['general']  
paging = True  
  
def request(query, params):  
    client = FourgetHijackerClient()  
    filters = client.get_engine_filters('duckduckgo')  
      
    # Get standard parameter mappings  
    fourget_params = FourgetHijackerClient.get_4get_params(query, params, filters)  
      
    # Apply engine-specific custom parameters  
    if 'ddg_extendedsearch' in params:  
        fourget_params['extendedsearch'] = params['ddg_extendedsearch']  
    if 'ddg_region' in params:  
         fourget_params['country'] = params['ddg_region'] 
    params['url'] = 'http://4get-hijacked:80/harness.php'  
    params['method'] = 'POST'  
    params['json'] = {  
        'engine': 'duckduckgo',  
        'params': fourget_params  
    }  
    return params  
  
def response(resp):  
    try:  
        response_data = resp.json()  
        logger.debug(f'4get duckduckgo response data: {response_data}')  
        results = FourgetHijackerClient.normalize_results(response_data, 'duckduckgo')  
        logger.debug(f'duckduckgo-4get results: {len(results)}')  
        return results  
    except Exception as e:  
        logger.error(f'4get duckduckgo response error: {e}')  
        return []