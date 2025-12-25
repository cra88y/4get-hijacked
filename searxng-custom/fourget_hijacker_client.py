import json
import aiohttp
from typing import Dict, Any, Optional

class FourgetHijackerClient:
    """
    A centralized Python module for all SearXNG stubs to use.
    This avoids code duplication and provides a clean interface to the PHP service.
    """
    
    def __init__(self, base_url: str = "http://4get-hijacked:80"):
        """
        Initialize the client with the base URL of the PHP service.
        
        Args:
            base_url: The base URL of the PHP service (e.g., "http://sidecar:80").
        """
        self.base_url = base_url
        self.session = None
    
    async def get_session(self) -> aiohttp.ClientSession:
        """
        Get or create an aiohttp.ClientSession for making HTTP requests.
        
        Returns:
            An aiohttp.ClientSession instance.
        """
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def get_manifest(self) -> Dict[str, Any]:
        """
        Fetches and caches the manifest from the PHP service.
        
        Returns:
            A dictionary containing the manifest data.
        """
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
        """
        Constructs the JSON payload and makes the POST request to the harness.
        
        Args:
            engine: The name of the engine to use (e.g., "google").
            params: A dictionary of parameters to pass to the engine.
        
        Returns:
            A dictionary containing the parsed JSON response from the harness.
        """
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
        """
        A static method that takes the raw JSON from the harness and maps it to the standard SearXNG result format.
        
        Args:
            response_data: The raw JSON response from the harness.
            engine_name: The name of the engine (e.g., "google").
        
        Returns:
            A dictionary containing the normalized results in the SearXNG format.
        """
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
