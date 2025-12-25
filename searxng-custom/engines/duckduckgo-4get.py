from searxng.fourget_hijacker_client import FourgetHijackerClient

categories = ['general', 'web']
paging = True
weight = 100

# Explicit definitions for SearXNG's static analysis
def request(query, params):
    """
    Request function for the DuckDuckGo engine.
    
    Args:
        query: The search query.
        params: A dictionary of parameters.
    
    Returns:
        A dictionary containing the results.
    """
    client = FourgetHijackerClient()
    
    # Map SearXNG params to 4get params
    fourget_params = {
        's': query,
        'country': params.get('searxng_locale', 'US').split('-')[-1].lower(),
        'lang': params.get('searxng_locale', 'en').split('-')[0],
        'nsfw': 'yes' if params.get('safesearch') == 0 else 'no'
    }
    
    # Call the client to do the work
    response_data = client.fetch('duckduckgo', fourget_params)
    params['results'] = response_data
    return params

def response(params):
    """
    Response function for the DuckDuckGo engine.
    
    Args:
        params: A dictionary of parameters.
    
    Returns:
        A list of results in the SearXNG format.
    """
    response_data = params.get('results')
    if not response_data:
        return []
    
    # Use the shared normalizer
    client = FourgetHijackerClient()
    return client.normalize_results(response_data, 'duckduckgo')
