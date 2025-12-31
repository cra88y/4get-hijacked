import httpx
from typing import Dict, Any
import logging
from datetime import datetime
import time
import json

logger = logging.getLogger(__name__)

class FourgetHijackerClient:
    def __init__(self, base_url: str = "http://4get-hijacked:80"):
        self.base_url = base_url

    def get_engine_filters(self, engine: str) -> Dict[str, Any]:
        """Get filters directly from 4get's getfilters() method via the sidecar"""
        url = f"{self.base_url}/filters.php"
        try:
            response = httpx.post(url, json={"engine": engine, "page": "web"}, timeout=5.0)
            if response.status_code == 200:
                try:
                    return response.json()
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON received for {engine} filters. Response: {response.text[:100]}")
                    return {}
            return {}
        except Exception as e:
            logger.error(f"Failed to fetch filters for {engine}: {e}")
            return {}

    @staticmethod
    def get_4get_params(query: str, params: Dict[str, Any], engine_filters: Dict[str, Any], engine_name: str = None) -> Dict[str, Any]:
        """Map SearXNG parameters to 4get engine parameters"""
        fourget_params = {"s": query}

        # Apply 4get's own defaults for each filter
        if engine_filters:
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
            if engine_name and engine_name.startswith("yandex"):
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
            if engine_filters and 'older' in engine_filters:
                fourget_params['older'] = current_time

        # Pagination
        if "pageno" in params and params["pageno"] > 1:
            fourget_params["offset"] = (params["pageno"] - 1) * 10

        # Engine-specific parameter overrides
        engine_specific_mappings = {
            "google": {"hl": "google_language", "gl": "google_country"},
            "brave": {"spellcheck": "brave_spellcheck", "country": "brave_country"},
            "duckduckgo": {"extendedsearch": "ddg_extendedsearch"},
            "yandex": {"lang": "yandex_language"},
            "marginalia": {"recent": "marginalia_recent", "intitle": "marginalia_intitle"}
        }

        # Apply engine-specific overrides
        if engine_name:
            # Extract base engine name (remove -4get suffix)
            base_engine = engine_name.replace("-4get", "").replace("4", "")
            if base_engine in engine_specific_mappings:
                mappings = engine_specific_mappings[base_engine]
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
        
        if isinstance(thumb, dict):
            url = thumb.get("url", "")
        elif isinstance(thumb, str):
            url = thumb
        else:
            return True
            
        broken_patterns = [
            "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP",
            "placeholder",
            "empty",
            "broken",
            "404",
            "1x1",
            "0x0",
            "transparent.gif"
        ]
        return any(pattern in url.lower() for pattern in broken_patterns)

    @staticmethod
    def _has_invalid_date(item: Dict[str, Any]) -> bool:
        """Check if item has invalid date"""
        date_val = item.get("date")
        if not date_val:
            return False
            
        try:
            timestamp = int(date_val)
            date_obj = datetime.fromtimestamp(timestamp)
            
            # Check if exactly midnight (placeholder)
            if date_obj.hour == 0 and date_obj.minute == 0 and date_obj.second == 0:
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
        
        if not isinstance(response_data, dict):
            return results

        # Handle spelling corrections as suggestions - SAFE ACCESS
        spelling = response_data.get("spelling")
        if isinstance(spelling, dict) and spelling.get("type") != "no_correction":
            if spelling.get("correction"):
                results.append({"suggestion": spelling["correction"]})

        # Add related searches as suggestions
        if response_data.get("related"):
            for related in response_data["related"]:
                results.append({"suggestion": related})

        # Process answer boxes
        if response_data.get("answer"):
            for answer in response_data["answer"]:
                results.append(FourgetHijackerClient._normalize_answer_result(answer))

        # Process standard results
        for result_type in ["web", "image", "video", "news"]:
            if result_type in response_data and isinstance(response_data[result_type], list):
                for item in response_data[result_type]:
                    if FourgetHijackerClient._has_broken_thumbnail(item) or \
                       FourgetHijackerClient._has_invalid_date(item):
                        continue

                    result = None
                    if result_type == "web":
                        result = FourgetHijackerClient._normalize_web_result(item)
                    elif result_type == "image":
                        result = FourgetHijackerClient._normalize_image_result(item)
                        if result: result["template"] = "images.html"
                    elif result_type == "video":
                        result = FourgetHijackerClient._normalize_video_result(item)
                        if result: result["template"] = "videos.html"
                    elif result_type == "news":
                        result = FourgetHijackerClient._normalize_news_result(item)
                    
                    if result:
                        results.append(result)

        return results

    @staticmethod
    def _normalize_answer_result(item):  
        result = {"answer": ""}  
        if item.get("description"):  
            description_parts = []  
            for part in item["description"]:  
                if part.get("type") in ["text", "quote", "title"]:  
                    # Preserve formatting for quotes and titles  
                    if part.get("type") == "quote":  
                        description_parts.append(f'"{part.get("value", "")}"')  
                    else:  
                        description_parts.append(part.get("value", ""))  
            result["answer"] = " ".join(description_parts)  
        return result

    @staticmethod
    def _normalize_web_result(item):
        """Normalize web search results"""
        result = {
            "title": item.get("title"),
            "url": item.get("url"),
            "content": item.get("description")
        }
        
        # Add date as datetime object
        date_val = item.get("date") or item.get("publishedDate")
        if date_val:
            try:
                result["publishedDate"] = datetime.fromtimestamp(int(date_val))
            except Exception:
                pass
        
        return result

    @staticmethod
    def _normalize_image_result(item):
        """Normalize image search results"""
        result = {
            "title": item.get("title"),
            "url": item.get("url"),
            "img_src": None,
            "thumbnail_src": None
        }
        
        if item.get("source") and len(item["source"]) >= 2:
            result["img_src"] = item["source"][0]["url"]
            result["thumbnail_src"] = item["source"][1]["url"]
            
        return result

    @staticmethod
    def _normalize_video_result(item):
        """Normalize video search results"""
        result = {
            "title": item.get("title"),
            "url": item.get("url"),
            "content": item.get("description"),
            "thumbnail": None
        }
        
        # Handle thumbnail
        if item.get("thumb"):
            if isinstance(item["thumb"], dict):
                result["thumbnail"] = item["thumb"].get("url")
            elif isinstance(item["thumb"], str):
                result["thumbnail"] = item["thumb"]
                
        # Add date as datetime object
        date_val = item.get("date") or item.get("publishedDate")
        if date_val:
            try:
                result["publishedDate"] = datetime.fromtimestamp(int(date_val))
            except Exception:
                pass
                
        return result

    @staticmethod
    def _normalize_news_result(item):
        """Normalize news search results"""
        result = {
            "title": item.get("title"),
            "url": item.get("url"),
            "content": item.get("description"),
            "thumbnail": None
        }
        
        # Handle thumbnail
        if item.get("thumb") and isinstance(item["thumb"], dict):
            result["thumbnail"] = item["thumb"].get("url")
            
        # Add date as datetime object
        if item.get("date"):
            try:
                result["publishedDate"] = datetime.fromtimestamp(int(item["date"]))
            except Exception:
                pass
                
        return result