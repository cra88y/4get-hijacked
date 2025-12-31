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
    def get_4get_params(query: str, params: Dict[str, Any], engine_filters: Dict[str, Any], engine_name: str = None) -> Dict[str, Any]:  
        """Map SearXNG parameters to 4get engine parameters"""  
        fourget_params = {"s": query}  
        
        # Apply 4get's own defaults for each filter  
        for filter_name, filter_config in engine_filters.items():  
            if isinstance(filter_config.get("option"), dict):  
                default = list(filter_config["option"].keys())[0]  
                fourget_params[filter_name] = default  
        
        # Map SearXNG standard parameters  
        nsfw_map = {0: "yes", 1: "maybe", 2: "no"}  
        if "safesearch" in params:  
            fourget_params["nsfw"] = nsfw_map.get(params["safesearch"], "yes")  
        
        # Language mapping with engine-specific handling  
        if "language" in params:  
            lang_full = params["language"]  
            lang = lang_full.split("-")[0] if "-" in lang_full else lang_full  
            country = lang_full.split("-")[1] if "-" in lang_full else "us"  
            
            # Yandex-specific language validation  
            if engine_name == "yandex":  
                yandex_langs = ["en", "ru", "be", "fr", "de", "id", "kk", "tt", "tr", "uk"]  
                if lang in yandex_langs:  
                    fourget_params["lang"] = lang  
            else:  
                fourget_params["lang"] = lang  
                fourget_params["country"] = country.lower()  
        
        # Enhanced time range mapping  
        if "time_range" in params and params["time_range"]:  
            time_range = params["time_range"]  
            current_time = int(time.time())  
            
            time_mappings = {  
                'day': 86400,  
                'week': 604800,   
                'month': 2592000,  
                'year': 31536000  
            }  
            
            if time_range in time_mappings:  
                fourget_params['newer'] = current_time - time_mappings[time_range]  
                # Some engines support both newer and older  
                if 'older' in engine_filters:  
                    fourget_params['older'] = current_time  
        
        # Pagination  
        if "pageno" in params and params["pageno"] > 1:  
            fourget_params["offset"] = (params["pageno"] - 1) * 10  
        
        # Engine-specific parameter overrides with explicit engine matching  
        engine_specific_mappings = {  
            "google": {"hl": "google_language", "gl": "google_country"},  
            "brave": {"spellcheck": "brave_spellcheck", "country": "brave_country"},  
            "duckduckgo": {"extendedsearch": "ddg_extendedsearch"},  
            "yandex": {"lang": "yandex_language"},  
            "marginalia": {"recent": "marginalia_recent", "intitle": "marginalia_intitle"}  
        }  
        
        # Apply engine-specific overrides  
        if engine_name and engine_name in engine_specific_mappings:  
            mappings = engine_specific_mappings[engine_name]  
            for fourget_param, searxng_param in mappings.items():  
                if searxng_param in params:  
                    fourget_params[fourget_param] = params[searxng_param]  
        
        return fourget_params
  
    def fetch(self, engine: str, params: Dict[str, Any]) -> Dict[str, Any]:  
        """Execute search request via the hijacker"""  
        url = f"{self.base_url}/harness.php"  
        payload = {  
            "engine": engine,  
            "params": params  
        }  
        try:  
            response = httpx.post(url, json=payload, timeout=10.0)  
            response.raise_for_status()  
            return response.json()  
        except httpx.HTTPStatusError as e:  
            logger.error(f"HTTP error for {engine}: {e}")  
            return {"status": "error", "message": f"HTTP {e.response.status_code}"}  
        except Exception as e:  
            logger.error(f"Request failed for {engine}: {e}")  
            return {"status": "error", "message": str(e)}  
  
    @staticmethod  
    def _has_broken_thumbnail(item: Dict[str, Any]) -> bool:  
        """Check if item has broken thumbnail"""  
        thumb = item.get("thumb")  
        if not thumb:  
            return False  
          
        # Check for common broken thumbnail patterns  
        if isinstance(thumb, dict):  
            url = thumb.get("url", "")  
        elif isinstance(thumb, str):  
            url = thumb  
        else:  
            return True  
          
        # Common broken thumbnail indicators  
        broken_patterns = [  
            "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP",  
            "placeholder", "empty", "broken", "404",  
            "1x1", "0x0", "transparent.gif"  
        ]  
          
        return any(pattern in url.lower() for pattern in broken_patterns)  
  
    @staticmethod  
    def _has_invalid_date(item: Dict[str, Any]) -> bool:  
        """Check if item has invalid date"""  
        date_val = item.get("date")  
        if not date_val:  
            return False  
          
        try:  
            # Check for placeholder dates  
            timestamp = int(date_val)  
            date_obj = datetime.fromtimestamp(timestamp)  
              
            # Check if it's exactly midnight (placeholder)  
            if date_obj.hour == 0 and date_obj.minute == 0 and date_obj.second == 0:  
                # Check if it's a recent date (likely placeholder)  
                current_year = datetime.now().year  
                if date_obj.year >= current_year - 1:  
                    return True  
              
            # Check for future dates  
            if date_obj > datetime.now():  
                return True  
                  
        except (ValueError, TypeError):  
            return True  
          
        return False  
  
    @staticmethod  
    def normalize_results(response_data: Any, engine: str = None):  
        """Normalize 4get response format to SearXNG expected format"""  
        results = []  
          
        # Handle special content first  
        if isinstance(response_data, dict):  
            # Add spelling corrections as suggestions  
            if response_data.get("spelling", {}).get("type") != "no_correction":  
                spelling = response_data["spelling"]  
                results.append({"suggestion": spelling["correction"]})  
              
            # Add related searches as suggestions  
            if response_data.get("related"):  
                for related in response_data["related"]:  
                    results.append({"suggestion": related})  
              
            # Add instant answers  
            if response_data.get("answer"):  
                for answer in response_data["answer"]:  
                    results.append({  
                        "title": answer.get("title"),  
                        "content": FourgetHijackerClient._format_answer_content(answer.get("description", [])),  
                        "url": answer.get("url")  
                    })  
          
        # Process standard results  
        if isinstance(response_data, dict):  
            for result_type in ["web", "image", "video", "news"]:  
                if result_type in response_data:  
                    for item in response_data[result_type]:  
                        # Skip results with broken data  
                        if FourgetHijackerClient._has_broken_thumbnail(item):  
                            continue  
                        if FourgetHijackerClient._has_invalid_date(item):  
                            continue  
                          
                        # Normalize based on result type  
                        if result_type == "web":  
                            result = FourgetHijackerClient._normalize_web_result(item)  
                        elif result_type == "image":  
                            result = FourgetHijackerClient._normalize_image_result(item)  
                        elif result_type == "video":  
                            result = FourgetHijackerClient._normalize_video_result(item)  
                        elif result_type == "news":  
                            result = FourgetHijackerClient._normalize_news_result(item)  
                          
                        results.append(result)  
          
        return results  
  
    @staticmethod  
    def _format_answer_content(description: list) -> str:  
        """Format answer description array to string"""  
        if not isinstance(description, list):  
            return str(description)  
          
        parts = []  
        for item in description:  
            if isinstance(item, dict) and "value" in item:  
                parts.append(item["value"])  
            elif isinstance(item, str):  
                parts.append(item)  
          
        return " ".join(parts)  
  
    @staticmethod  
    def _normalize_web_result(item: Dict[str, Any]) -> Dict[str, Any]:  
        """Normalize web search results"""  
        result = {  
            "title": item.get("title"),  
            "url": item.get("url"),  
            "content": item.get("description") or item.get("snippet") or item.get("content", "")  
        }  
          
        # Handle thumbnail  
        if isinstance(item.get("thumb"), dict):  
            thumb_url = item["thumb"].get("url")  
            if thumb_url:  
                result["thumbnail"] = thumb_url  
        elif isinstance(item.get("thumb"), str):  
            result["thumbnail"] = item["thumb"]  
          
        # Add date without time portion  
        date_val = item.get("date")  
        if date_val:  
            try:  
                # Convert to date object to strip time  
                date_obj = datetime.fromtimestamp(int(date_val))  
                result["publishedDate"] = date_obj.strftime("%Y-%m-%d")  
            except Exception:  
                pass  
          
        return result  
  
    @staticmethod  
    def _normalize_image_result(item: Dict[str, Any]) -> Dict[str, Any]:  
        """Normalize image search results"""  
        result = {  
            "title": item.get("title"),  
            "url": item.get("url"),  
            "img_src": None,  
            "thumbnail": None,  
            "resolution": None  
        }  
          
        # Handle image sources  
        if item.get("source") and len(item["source"]) > 0:  
            # Use the largest image as source  
            largest = item["source"][0]  
            result["img_src"] = largest.get("url")  
              
            # Use thumbnail if available  
            if len(item["source"]) > 1:  
                thumb = item["source"][-1]  
                result["thumbnail"] = thumb.get("url")  
              
            # Resolution  
            if largest.get("width") and largest.get("height"):  
                result["resolution"] = f"{largest['width']}x{largest['height']}"  
          
        return result  
  
    @staticmethod  
    def _normalize_video_result(item: Dict[str, Any]) -> Dict[str, Any]:  
        """Normalize video search results"""  
        result = {  
            "title": item.get("title"),  
            "url": item.get("url"),  
            "content": item.get("description", ""),  
            "duration": None,  
            "views": None,  
            "thumbnail": None  
        }  
          
        # Duration  
        if item.get("duration"):  
            result["duration"] = item["duration"]  
          
        # Views  
        if item.get("views"):  
            result["views"] = str(item["views"])  
          
        # Thumbnail  
        if isinstance(item.get("thumb"), dict):  
            thumb_url = item["thumb"].get("url")  
            if thumb_url:  
                result["thumbnail"] = thumb_url  
          
        # Date without time portion  
        if item.get("date"):  
            try:  
                date_obj = datetime.fromtimestamp(int(item["date"]))  
                result["publishedDate"] = date_obj.strftime("%Y-%m-%d")  
            except Exception:  
                pass  
          
        return result  
  
    @staticmethod  
    def _normalize_news_result(item: Dict[str, Any]) -> Dict[str, Any]:  
        """Normalize news search results"""  
        result = {  
            "title": item.get("title"),  
            "url": item.get("url"),  
            "content": item.get("description", ""),  
            "thumbnail": None  
        }  
          
        # Thumbnail  
        if isinstance(item.get("thumb"), dict):  
            thumb_url = item["thumb"].get("url")  
            if thumb_url:  
                result["thumbnail"] = thumb_url  
          
        # Date without time portion  
        if item.get("date"):  
            try:  
                date_obj = datetime.fromtimestamp(int(item["date"]))  
                result["publishedDate"] = date_obj.strftime("%Y-%m-%d")  
            except Exception:  
                pass  
          
        return result