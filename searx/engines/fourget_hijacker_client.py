import httpx
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
import time
import json
from urllib.parse import parse_qs, urlparse

logger = logging.getLogger(__name__)

class FourgetHijackerClient:
    MAX_CONTENT_LENGTH = 5000

    def __init__(self, base_url: str = "http://4get-hijacked:80"):
        self.base_url = base_url

    def get_engine_filters(self, engine: str) -> Dict[str, Any]:
        url = f"{self.base_url}/filters.php"
        try:
            response = httpx.post(url, json={"engine": engine, "page": "web"}, timeout=5.0)
            if response.status_code == 200:
                try:
                    return response.json()
                except json.JSONDecodeError:
                    return {}
            return {}
        except Exception as e:
            logger.error(f"Failed to fetch filters for {engine}: {e}")
            return {}

    @staticmethod
    def get_4get_params(query: str, params: Dict[str, Any], engine_filters: Dict[str, Any], engine_name: str = None) -> Dict[str, Any]:
        fourget_params = {"s": query}

        if engine_filters:
            for filter_name, filter_config in engine_filters.items():
                if isinstance(filter_config.get("option"), dict):
                    default = list(filter_config["option"].keys())[0]
                    fourget_params[filter_name] = default

        nsfw_map = {0: "yes", 1: "maybe", 2: "no"}
        if "safesearch" in params:
            fourget_params["nsfw"] = nsfw_map.get(params["safesearch"], "yes")

        if "language" in params:
            lang_full = params["language"]
            lang = lang_full.split("-")[0] if "-" in lang_full else lang_full
            country = lang_full.split("-")[1] if "-" in lang_full else "us"
            
            if engine_name and engine_name.startswith("yandex"):
                yandex_langs = ["en", "ru", "be", "fr", "de", "id", "kk", "tt", "tr", "uk"]
                if lang in yandex_langs:
                    fourget_params["lang"] = lang
            else:
                fourget_params["lang"] = lang
            
            fourget_params["country"] = country.lower()

        if "time_range" in params and params["time_range"]:
            time_range = params["time_range"]
            current_time = int(time.time())
            time_mappings = {'day': 86400, 'week': 604800, 'month': 2592000, 'year': 31536000}
            if time_range in time_mappings:
                fourget_params['newer'] = current_time - time_mappings[time_range]
            if engine_filters and 'older' in engine_filters:
                fourget_params['older'] = current_time

        if "pageno" in params and params["pageno"] > 1:
            fourget_params["offset"] = (params["pageno"] - 1) * 10

        engine_specific_mappings = {
            "google": {"hl": "google_language", "gl": "google_country"},
            "brave": {"spellcheck": "brave_spellcheck", "country": "brave_country"},
            "duckduckgo": {"extendedsearch": "ddg_extendedsearch"},
            "yandex": {"lang": "yandex_language"},
            "marginalia": {"recent": "marginalia_recent", "intitle": "marginalia_intitle"}
        }

        if engine_name:
            base_engine = engine_name.replace("-4get", "").replace("4", "")
            if base_engine in engine_specific_mappings:
                mappings = engine_specific_mappings[base_engine]
                for fourget_param, searxng_param in mappings.items():
                    if searxng_param in params:
                        fourget_params[fourget_param] = params[searxng_param]

        return fourget_params

    def fetch(self, engine: str, params: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/harness.php"
        payload = {"engine": engine, "params": params}
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

    # --- Validation Helpers ---

    @staticmethod
    def _is_valid_url(url: Any) -> bool:
        if not url or not isinstance(url, str):
            return False
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False

    @staticmethod
    def _is_broken_image_url(url: str) -> bool:
        """Check if a specific URL string looks like a broken image placeholder"""
        if not url or not isinstance(url, str):
            return True
        
        broken_patterns = [
            "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP",
            "placeholder", "empty", "broken", "404", "1x1", "0x0", "transparent.gif"
        ]
        return any(pattern in url.lower() for pattern in broken_patterns)

    @staticmethod
    def _parse_date(date_val: Any) -> Optional[datetime]:
        if not date_val:
            return None
        try:
            return datetime.fromtimestamp(int(date_val))
        except (ValueError, TypeError, OverflowError):
            return None

    @staticmethod
    def _truncate_content(content: Any) -> str:
        if not content or not isinstance(content, str):
            return ""
        if len(content) > FourgetHijackerClient.MAX_CONTENT_LENGTH:
            return content[:FourgetHijackerClient.MAX_CONTENT_LENGTH] + "..."
        return content

    # --- Normalization Logic ---

    @staticmethod
    def normalize_results(response_data: Any, engine: str = None):
        results = []
        if not isinstance(response_data, dict):
            return results

        # 1. Spelling
        spelling = response_data.get("spelling")
        if isinstance(spelling, dict) and spelling.get("type") != "no_correction":
            correction = spelling.get("correction")
            if correction and isinstance(correction, str) and correction.strip():
                results.append({"suggestion": correction.strip()})

        # 2. Related
        related_list = response_data.get("related")
        if isinstance(related_list, list):
            for related in related_list:
                if related and isinstance(related, str) and related.strip():
                    results.append({"suggestion": related.strip()})

        # 3. Answers
        answer_list = response_data.get("answer")
        if isinstance(answer_list, list):
            for answer in answer_list:
                if not isinstance(answer, dict): continue
                normalized_answer = FourgetHijackerClient._normalize_answer_result(answer)
                if normalized_answer:
                    results.append(normalized_answer)

        # 4. Standard Results
        for result_type in ["web", "image", "video", "news"]:
            items = response_data.get(result_type)
            if isinstance(items, list):
                for item in items:
                    if not isinstance(item, dict): continue
                    
                    # Global check: Invalid Date (Future/Epoch) -> Discard
                    if FourgetHijackerClient._has_invalid_date(item):
                        continue

                    # NOTE: We removed the global _has_broken_thumbnail check here.
                    # We now handle it inside each method to allow fallback.

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
    def _has_invalid_date(item: Dict[str, Any]) -> bool:
        date_val = item.get("date")
        if not date_val: return False
        try:
            timestamp = int(date_val)
            date_obj = datetime.fromtimestamp(timestamp)
            if date_obj.hour == 0 and date_obj.minute == 0 and date_obj.second == 0:
                if date_obj.year >= datetime.now().year - 1: return True
            if date_obj > datetime.now(): return True
        except (ValueError, TypeError, OverflowError):
            return True
        return False

    @staticmethod
    def _normalize_answer_result(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        desc_list = item.get("description")
        if not desc_list or not isinstance(desc_list, list): return None
        description_parts = []
        for part in desc_list:
            if isinstance(part, dict) and part.get("type") == "text":
                val = part.get("value")
                if val and isinstance(val, str) and val.strip():
                    description_parts.append(val.strip())
        answer_text = " ".join(description_parts)
        if not answer_text: return None
        return {"answer": FourgetHijackerClient._truncate_content(answer_text)}

    @staticmethod
    def _normalize_web_result(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        url = item.get("url")
        title = item.get("title")
        if not FourgetHijackerClient._is_valid_url(url) or not title: return None
            
        result = {
            "title": title,
            "url": url,
            "content": FourgetHijackerClient._truncate_content(item.get("description"))
        }
        date_obj = FourgetHijackerClient._parse_date(item.get("date") or item.get("publishedDate"))
        if date_obj: result["publishedDate"] = date_obj
        return result

    @staticmethod
    def _normalize_image_result(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        # For Image Search, a broken image IS a broken result. We discard it.
        source = item.get("source")
        if not source or not isinstance(source, list) or len(source) < 1: return None

        img_data = source[0]
        thumb_data = source[1] if len(source) > 1 else img_data
        
        if not isinstance(img_data, dict) or not isinstance(thumb_data, dict): return None

        img_url = img_data.get("url")
        thumb_url = thumb_data.get("url")
        
        if not FourgetHijackerClient._is_valid_url(img_url): return None
        
        # Strict check for Image Search: If image is broken placeholder, discard.
        if FourgetHijackerClient._is_broken_image_url(img_url): return None

        # Proxy extraction logic
        if "url=" in img_url and (img_url.startswith("/") or "4get" in img_url):
            try:
                parsed = urlparse(img_url)
                qs = parse_qs(parsed.query)
                if 'url' in qs:
                    candidate = qs['url'][0]
                    if FourgetHijackerClient._is_valid_url(candidate): img_url = candidate
            except Exception: pass

        return {
            "title": item.get("title") or "Image",
            "url": item.get("url") or img_url,
            "img_src": img_url,
            "thumbnail_src": thumb_url or img_url
        }

    @staticmethod
    def _normalize_video_result(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        url = item.get("url")
        title = item.get("title")
        if not FourgetHijackerClient._is_valid_url(url) or not title: return None

        result = {
            "title": title,
            "url": url,
            "content": FourgetHijackerClient._truncate_content(item.get("description")),
            "thumbnail": None
        }
        
        # Fallback Logic: If thumb is broken, keep result but set thumb to None
        raw_thumb = item.get("thumb")
        thumb_url = None
        if isinstance(raw_thumb, dict): thumb_url = raw_thumb.get("url")
        elif isinstance(raw_thumb, str): thumb_url = raw_thumb
        
        if thumb_url and not FourgetHijackerClient._is_broken_image_url(thumb_url):
            result["thumbnail"] = thumb_url
                
        date_obj = FourgetHijackerClient._parse_date(item.get("date") or item.get("publishedDate"))
        if date_obj: result["publishedDate"] = date_obj
        return result

    @staticmethod
    def _normalize_news_result(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        url = item.get("url")
        title = item.get("title")
        if not FourgetHijackerClient._is_valid_url(url) or not title: return None

        result = {
            "title": title,
            "url": url,
            "content": FourgetHijackerClient._truncate_content(item.get("description")),
            "thumbnail": None
        }
        
        # Fallback Logic: If thumb is broken, keep result but set thumb to None
        raw_thumb = item.get("thumb")
        if isinstance(raw_thumb, dict):
            thumb_url = raw_thumb.get("url")
            if thumb_url and not FourgetHijackerClient._is_broken_image_url(thumb_url):
                result["thumbnail"] = thumb_url
            
        date_obj = FourgetHijackerClient._parse_date(item.get("date"))
        if date_obj: result["publishedDate"] = date_obj
        return result