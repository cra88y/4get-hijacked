# SPDX-License-Identifier: AGPL-3.0-or-later
"""Google Crab Engine - Structure-Only Version
Bypasses bot detection by mimicking Opera Mini and parsing pure HTML structure.
Ignores CSS class names to prevent breakage when Google updates code.
"""

import typing as t
from urllib.parse import urlencode, unquote, urlparse, parse_qs
from lxml import html
import babel
import babel.core
import babel.languages

from searx.utils import extract_text, eval_xpath, eval_xpath_list, eval_xpath_getindex
from searx.locales import language_tag, region_tag, get_official_locales
from searx.network import get
from searx.exceptions import SearxEngineCaptchaException
from searx.enginelib.traits import EngineTraits
from searx.result_types import EngineResults
from searx import logger

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams

about = {
    "website": 'https://www.google.com',
    "wikidata_id": 'Q9366',
    "official_api_documentation": 'https://developers.google.com/custom-search/',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

categories = ['general', 'web']
paging = True
max_page = 50
time_range_support = True
safesearch = True

time_range_dict = {'day': 'd', 'week': 'w', 'month': 'm', 'year': 'y'}
filter_mapping = {0: 'off', 1: 'medium', 2: 'high'}

# The "Magic" User-Agent (Opera 8.65)
OLD_USER_AGENT = "Mozilla/4.0 (compatible; MSIE 6.0; Windows CE; PPC; 240x320) Opera 8.65 [nl]"

traits: t.Optional[EngineTraits] = None

def get_google_info(params: "OnlineParams", eng_traits: EngineTraits) -> dict[str, t.Any]:
    ret_val: dict[str, t.Any] = {
        'language': None, 'country': None, 'subdomain': None,
        'params': {}, 'headers': {}, 'cookies': {}, 'locale': None,
    }

    sxng_locale = params.get('searxng_locale', 'all')
    try:
        locale = babel.Locale.parse(sxng_locale, sep='-')
    except babel.core.UnknownLocaleError:
        locale = None

    eng_lang = eng_traits.get_language(sxng_locale, 'lang_en')
    lang_code = eng_lang.split('_')[-1]
    
    # --- FIX: Handle NoneType for country ---
    country = eng_traits.get_region(sxng_locale, eng_traits.all_locale)
    if not country:
        country = 'US'  # Default to US if region detection fails

    ret_val['language'] = eng_lang
    ret_val['country'] = country
    ret_val['locale'] = locale
    
    # Defensive coding for missing traits
    supported_domains = eng_traits.custom.get('supported_domains', {})
    ret_val['subdomain'] = supported_domains.get(country.upper(), 'www.google.com')

    ret_val['params']['hl'] = f'{lang_code}-{country}'
    ret_val['params']['lr'] = eng_lang if sxng_locale != 'all' else ''
    ret_val['params']['cr'] = ('country' + country) if len(sxng_locale.split('-')) > 1 else ''
    ret_val['params']['ie'] = 'utf8'
    ret_val['params']['oe'] = 'utf8'

    # Legacy Headers
    ret_val['headers']['Accept'] = 'text/html, application/xml;q=0.9, */*;q=0.8'
    ret_val['headers']['Accept-Language'] = 'en-US,en;q=0.5'
    ret_val['headers']['Connection'] = 'Keep-Alive'
    ret_val['cookies']['CONSENT'] = "YES+"

    return ret_val

def detect_google_sorry(resp):
    if resp.url.host == 'sorry.google.com' or resp.url.path.startswith('/sorry'):
        raise SearxEngineCaptchaException()
    if 'id="captcha-form"' in resp.text:
        raise SearxEngineCaptchaException()

def request(query: str, params: "OnlineParams") -> None:
    start = (params['pageno'] - 1) * 10
    if traits is None: return

    google_info = get_google_info(params, traits)
    query_params = {'q': query, **google_info['params'], 'start': start}

    if params['time_range'] in time_range_dict:
        query_params['tbs'] = 'qdr:' + time_range_dict[params['time_range']]
    if params['safesearch']:
        query_params['safe'] = filter_mapping[params['safesearch']]

    params['url'] = 'https://' + google_info['subdomain'] + '/search?' + urlencode(query_params)
    params['cookies'] = google_info['cookies']
    params['headers'].update(google_info['headers'])
    params['headers']['User-Agent'] = OLD_USER_AGENT

def response(resp: "SXNG_Response"):
    detect_google_sorry(resp)
    results = EngineResults()
    dom = html.fromstring(resp.text)

    # --- PURE STRUCTURE PARSING ---
    # Find all links that contain an h3
    link_nodes = eval_xpath_list(dom, '//a[.//h3]')

    for link in link_nodes:
        try:
            # 1. Extract Title (The text inside the h3)
            title_tag = eval_xpath_getindex(link, './/h3', 0, default=None)
            if title_tag is None: continue
            title = extract_text(title_tag)

            # 2. Extract URL
            raw_url = link.get('href', '')
            url = raw_url
            # Clean Google Redirects
            if '/url?q=' in raw_url:
                parsed = parse_qs(urlparse(raw_url).query)
                if 'q' in parsed:
                    url = parsed['q'][0]
            
            if not url or 'google.com' in urlparse(url).netloc:
                continue

            # 3. Extract Snippet (The text NEXT to the link)
            content = ''
            
            # Go up to the wrapper div of the link
            link_wrapper = link.getparent()
            
            # Go up to the main card div
            card_div = link_wrapper.getparent()
            
            if card_div is not None:
                # Find all divs inside the card
                divs_in_card = card_div.xpath('./div')
                
                for div in divs_in_card:
                    # If this div contains the h3, it's the title block. Skip it.
                    if div.xpath('.//h3'):
                        continue
                    
                    # If it doesn't have the h3, it's likely the snippet.
                    text = extract_text(div)
                    if text:
                        content = text
                        break

            results.append({'url': url, 'title': title, 'content': content})

        except Exception:
            continue

    return results

# Standard Trait Fetching
skip_countries = ['AL', 'AZ', 'BD', 'BN', 'BT', 'ET', 'GE', 'GL', 'KH', 'LA', 'LK', 'ME', 'MK', 'MM', 'MN', 'MV', 'MY', 'NP', 'TJ', 'TM', 'UZ']

def fetch_traits(engine_traits: EngineTraits, add_domains: bool = True):
    # Initialize immediately to prevent KeyError if network fails
    engine_traits.custom['supported_domains'] = {}
    
    try:
        resp = get('https://www.google.com/preferences')
        if not resp.ok:
            engine_traits.languages['en'] = 'lang_en'
            engine_traits.custom['supported_domains']['US'] = 'www.google.com'
            return

        dom = html.fromstring(resp.text.replace('<?xml version="1.0" encoding="UTF-8"?>', ''))
        lang_map = {'no': 'nb'}
        for x in eval_xpath_list(dom, "//select[@name='hl']/option"):
            eng_lang = x.get("value")
            try:
                locale = babel.Locale.parse(lang_map.get(eng_lang, eng_lang), sep='-')
            except babel.UnknownLocaleError: continue
            sxng_lang = language_tag(locale)
            if engine_traits.languages.get(sxng_lang) and engine_traits.languages.get(sxng_lang) != eng_lang: continue
            engine_traits.languages[sxng_lang] = 'lang_' + eng_lang

        engine_traits.languages['zh'] = 'lang_zh-CN'
        for x in eval_xpath_list(dom, "//select[@name='gl']/option"):
            eng_country = x.get("value")
            if eng_country in skip_countries or eng_country == 'ZZ': continue
            sxng_locales = get_official_locales(eng_country, engine_traits.languages.keys(), regional=True)
            for sxng_locale in sxng_locales:
                engine_traits.regions[region_tag(sxng_locale)] = eng_country

        if add_domains:
            resp = get('https://www.google.com/supported_domains')
            if resp.ok:
                for domain in resp.text.split():
                    domain = domain.strip()
                    if not domain or domain in ['.google.com']: continue
                    region = domain.split('.')[-1].upper()
                    engine_traits.custom['supported_domains'][region] = 'www' + domain
    except Exception as e:
        logger.warning(f"Google-Crab: Failed to fetch traits: {e}")
        # Fallback defaults
        engine_traits.languages['en'] = 'lang_en'
        engine_traits.custom['supported_domains']['US'] = 'www.google.com'