import json
import aiohttp
from typing import Dict, Any, Optional

class FourgetHijackerClient:
    
    def __init__(self, base_url: str = "http://4get-hijacked:80"):
        self.base_url = base_url
        self.session = None
    
    async def get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def get_manifest(self) -> Dict[str, Any]:
        url = f"{self.base_url}/harness.php?action=discover"
        session = await self.get_session()
        
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {}
        except Exception as e:
            print(f"Error fetching manifest: {e}")
            return {}
    
    async def fetch(self, engine: str, params: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/harness.php"
        payload = {
            "engine": engine,
            "params": params
        }
        
        session = await self.get_session()
        
        try:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"status": "error", "message": f"HTTP {response.status}"}
        except Exception as e:
            print(f"Error fetching results: {e}")
            return {"status": "error", "message": str(e)}
    
    @staticmethod
    def normalize_results(response_data: Dict[str, Any], engine_name: str) -> Dict[str, Any]:
        results = []
        
        if response_data.get("status") != "ok":
            return results
        
        for item in response_data.get("web", []):
            results.append({
                "url": item.get("url"),
                "title": item.get("title"),
                "content": item.get("description") or item.get("snippet"),
            })
        
        return results
