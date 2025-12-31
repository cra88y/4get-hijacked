from fourget_hijacker_client import FourgetHijackerClient  
import logging  
logger = logging.getLogger(__name__)
categories = ['general']  
paging = True  
  
def request(query, params):  
    params['url'] = 'http://4get-hijacked:80/harness.php'  
    params['method'] = 'POST'  
    params['json'] = {  
        "engine": "yandex",   
        "params": {"s": query}  
    }  
    return params  
  
def response(resp):  
    try:  
        response_data = resp.json()  
        logger.debug(f"4get response data: {response_data}") 
        results = FourgetHijackerClient.normalize_results(response_data)  
        logger.debug(f"Normalized results: {results}") 
        return results  
    except Exception as e:  
        logger.error(f"4get response error: {e}") 
        return []