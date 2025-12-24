from searx.engines.fourget_bridge import get_engine

categories = ['general', 'web']
paging = True
weight = 100

request, response = get_engine(
    scraper_name='brave',
    target_url_fmt='https://search.brave.com/search?q={query}',
    safe_param='&safesearch=strict'
)