from fourget_hijacker_client import FourgetHijackerClient, about
import logging
logger = logging.getLogger(__name__)

categories, paging, engine_type, time_range_support = ['images'], True, "online", False
fourget_url = "http://4get-hijacked:80"
EID = __name__.rsplit('/', 1)[-1].split('.')[-1].replace('-4get', '')

def request(q, p): return FourgetHijackerClient.dispatch_request(EID, q, p, fourget_url)
def response(r): return FourgetHijackerClient.dispatch_response(r, EID, logger)



