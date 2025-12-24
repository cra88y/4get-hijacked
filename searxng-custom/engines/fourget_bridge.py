import json
from searx.result_types import EngineResults
from searx.network import get, post

# Service name in Docker Compose
PARSER_URL = "http://4get-hijacked:80"
OPERA_UA = "Mozilla/4.0 (compatible; MSIE 6.0; Windows CE; PPC; 240x320) Opera 8.65 [nl]"

def get_engine(scraper_name, target_url_fmt, safe_param=""):
    """
    Factory: Returns request/response functions for a specific 4get scraper.
    """
    def request(query, params):
        # 1. Build URL
        search_url = target_url_fmt.format(query=query)
        
        # 2. Apply SafeSearch
        if params.get('safesearch') and safe_param:
            search_url += safe_param

        # 3. Fetch HTML (Python)
        headers = {'User-Agent': OPERA_UA}
        resp = get(search_url, headers=headers)
        if not resp.ok: return []

        # 4. Send to Sidecar (PHP)
        payload = {
            'scraper': scraper_name,
            'html': resp.text,
            'params': {
                's': query,
                'country': params.get('searxng_locale', 'US').split('-')[-1].lower(),
                'lang': params.get('searxng_locale', 'en').split('-')[0],
                'nsfw': 'yes' if params.get('safesearch') == 0 else 'no'
            }
        }

        try:
            parser_resp = post(PARSER_URL, json=payload)
            data = json.loads(parser_resp.text)
        except Exception: return []

        return data

    def response(resp):
        results = EngineResults()
        if resp.get('status') != 'ok': return results
        
        for item in resp.get('web', []):
            results.append({
                'url': item.get('url'),
                'title': item.get('title'),
                'content': item.get('description'),
            })
        return results

    return request, response

# Generic functions for explicit engine definitions (SearXNG discovery fix)
def generic_request(query, params, scraper_name, target_url_fmt, safe_param=""):
    """
    Generic request function that can be used by explicit engine definitions.
    This ensures SearXNG's static analysis can discover the engines.
    """
    # Build the actual request function using the factory
    request_func = get_engine(scraper_name, target_url_fmt, safe_param)[0]
    return request_func(query, params)

def generic_response(resp):
    """
    Generic response function that can be used by explicit engine definitions.
    """
    # Build the actual response function using the factory
    response_func = get_engine(None, None)[1]  # scraper_name not needed for response
    return response_func(resp)