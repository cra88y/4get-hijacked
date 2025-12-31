import httpx   
from typing import Dict, Any  
import logging  
from datetime import datetime  
import time  
  
logger = logging.getLogger(__name__)  
  
class FourgetHijackerClient:  
    def __init__(self, base_url: str = "http://4get-hijacked:80"):  
        self.base_url = base_url  
  
    def get_engine_filters(self, engine: str) -> Dict[str, Any]:  
        """Get filters directly from 4get's getfilters() method via the sidecar"""  
        url = f"{self.base_url}/filters.php"  
        try:  
            response = httpx.post(url, json={"engine": engine, "page": "web"}, timeout=5.0)  
            return response.json() if response.status_code == 200 else {}  
        except Exception as e:  
            logger.error(f"Failed to fetch filters for {engine}: {e}")  
            return {}  
  
    @staticmethod  
    def get_4get_params(query: str, params: Dict[str, Any], engine_filters: Dict[str, Any]) -> Dict[str, Any]:  
        fourget_params = {"s": query}  
          
        # Apply 4get's own defaults for each filter  
        for filter_name, filter_config in engine_filters.items():  
            if isinstance(filter_config.get("option"), dict):  
                # Use first option as default (same as 4get does)  
                default = list(filter_config["option"].keys())[0]  
                fourget_params[filter_name] = default  
            elif filter_config.get("option") == "_DATE":  
                fourget_params[filter_name] = False  
            elif filter_config.get("option") == "_SEARCH":  
                fourget_params[filter_name] = ""  
          
        # Override with values from SearXNG params if they match filter names  
        for k, v in params.items():  
            if k in engine_filters and v is not None:  
                fourget_params[k] = v  
  
        # Manual mapping for common SearXNG -> 4get translations  
        # Safesearch  
        if 'safesearch' in params:  
            nsfw_map = {0: "yes", 1: "maybe", 2: "no"}  
            fourget_params["nsfw"] = nsfw_map.get(params['safesearch'], "yes")  
              
        # Language/Country  
        if 'language' in params:  
            lang_full = params['language']  
            fourget_params["lang"] = lang_full.split('-')[0] if '-' in lang_full else lang_full  
            fourget_params["country"] = lang_full.split('-')[1].lower() if '-' in lang_full else 'us'  
  
        return fourget_params  
  
    def fetch(self, engine: str, query: str, params: Dict[str, Any]) -> Dict[str, Any]:  
        url = f"{self.base_url}/harness.php"  
          
        # Fetch filters to get defaults  
        filters = self.get_engine_filters(engine)  
        fourget_params = self.get_4get_params(query, params, filters)  
          
        payload = {  
            "engine": engine,  
            "params": fourget_params  
        }  
        try:  
            response = httpx.post(url, json=payload, timeout=15.0)  
              
            if response.status_code == 200:  
                return response.json()  
              
            logger.error(f"HTTP {response.status_code} from sidecar")  
            return {"status": "error", "message": f"HTTP {response.status_code}"}  
              
        except httpx.RequestError as e:  
            logger.error(f"Sidecar connection failed: {e}")  
            return {"status": "error", "message": str(e)}  
        except Exception as e:  
            logger.error(f"Sidecar request failed: {e}")  
            return {"status": "error", "message": str(e)}  
  
    @staticmethod  
    def normalize_results(response_data: Any):  
        results = []  
          
        # 4get usually returns results in 'web', but some like CrowdView use 'results'  
        if isinstance(response_data, dict):  
            if "web" in response_data:  
                data = response_data["web"]  
            elif "results" in response_data:  
                data = response_data["results"]  
            else:  
                data = []  
        else:  
            data = response_data if isinstance(response_data, list) else []  
          
        if not isinstance(data, list):  
            return results  
  
        for item in data:  
            # 4get results can have different keys for content  
            content = item.get("description") or item.get("snippet") or item.get("content") or ""  
              
            result = {  
                "url": item.get("url") or item.get("link"),  
                "title": item.get("title"),  
                "content": content,  
            }  
              
            # Add thumbnail if available  
            thumb = item.get("thumb") or item.get("thumbnail")  
            if isinstance(thumb, dict):  
                thumb_url = thumb.get("url") or thumb.get("original")  
                if thumb_url:  
                    result["thumbnail"] = thumb_url  
            elif isinstance(item.get("thumb"), str):  
                result["thumbnail"] = item["thumb"]  
              
            # Add date if available  
            date_val = item.get("date") or item.get("publishedDate")  
            if date_val:  
                try:  
                    result["publishedDate"] = datetime.fromtimestamp(int(date_val))  
                except Exception:  
                    pass  
            elif item.get("age"):  
                try:  
                    result["publishedDate"] = datetime.fromtimestamp(time.mktime(time.strptime(item["age"], "%Y-%m-%d")))  
                except:  
                    pass  
                      
            results.append(result)  
        return results