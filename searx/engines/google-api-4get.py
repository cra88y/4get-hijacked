from fourget_hijacker_client import FourgetHijackerClient
import logging
logger = logging.getLogger(__name__)

categories, paging, engine_type, time_range_support = ['general'], False, "online", True
EID = __name__.split('.')[-1].replace('-4get', '')

def request(q, p): return FourgetHijackerClient.dispatch_request(EID, q, p)
def response(r): return FourgetHijackerClient.dispatch_response(r, EID, logger)
