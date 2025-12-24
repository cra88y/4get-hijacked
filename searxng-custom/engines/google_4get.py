from searx.engines.fourget_bridge import generic_request, generic_response

categories = ['general', 'web']
paging = True
weight = 100

# Explicit definitions for SearXNG's static analysis
def request(query, params):
    return generic_request(
        query, params, 
        scraper_name='google', 
        target_url_fmt='https://www.google.com/search?q={query}&gbv=1'
    )

def response(resp):
    return generic_response(resp)