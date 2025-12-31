import httpx 
from typing import Dict, Any
import logging
from datetime import datetime
import time

logger = logging.getLogger(__name__)

class FourgetHijackerClient:
    def __init__(self, base_url: str = "http://4get-hijacked:80"):
        self.base_url = base_url

    def fetch(self, engine: str, params: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/harness.php"
        payload = {
            "engine": engine,
            "params": params
        }
        try:
            # We use httpx.post instead of requests.post
            # httpx handles timeouts and json exactly like requests does here
            response = httpx.post(url, json=payload, timeout=15.0)
            
            if response.status_code == 200:
                return response.json()
            
            logger.error(f"HTTP {response.status_code} from sidecar")
            return {"status": "error", "message": f"HTTP {response.status_code}"}
            
        except httpx.RequestError as e:
            # Catch network-related errors specifically
            logger.error(f"Sidecar connection failed: {e}")
            return {"status": "error", "message": str(e)}
        except Exception as e:
            logger.error(f"Sidecar request failed: {e}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    def normalize_results(response_data: Any):
        results = []
        data = response_data.get("web") if isinstance(response_data, dict) else response_data
        
        if not isinstance(data, list):
            return results

        for item in data:
            result = {
                "url": item.get("url"),
                "title": item.get("title"),
                "content": item.get("description") or item.get("snippet") or "",
            }
            
            # Add thumbnail if available
            if item.get("thumbnail") and item["thumbnail"].get("original"):
                result["thumbnail"] = item["thumbnail"]["original"]
            
            # Add date if available
            if item.get("age"):
                try:
                    # Cleaned up imports to be at top of file or inside try block
                    result["publishedDate"] = datetime.fromtimestamp(time.mktime(time.strptime(item["age"], "%Y-%m-%d")))
                except:
                    pass
                    
            results.append(result)
        return results