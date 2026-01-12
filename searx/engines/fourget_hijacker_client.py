import re
from typing import Dict, Any, Optional
from datetime import datetime
import time
from urllib.parse import parse_qs, urlparse, unquote_plus
from html import unescape
from searx.result_types import Answer
import logging

logger = logging.getLogger(__name__)

# Pre-compiled regex patterns
_BROKEN_IMAGE_RE = re.compile(
    r'(data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP|transparent\.gif|1x1\.(gif|png)|0x0|broken_image|image_not_found|no_image|placeholder\.(png|jpg|svg))',
    re.IGNORECASE
)
_WHITESPACE_RE = re.compile(r'\s+')

class FourgetHijackerClient:
    MAX_CONTENT_LENGTH = 5000
    DEFAULT_PAGE_SIZE = 10  # 4get engines return ~10 results per page

    # --- Constants ---
    NSFW_MAP = {0: "yes", 1: "maybe", 2: "no"}
    TIME_MAPPINGS = {'day': 86400, 'week': 604800, 'month': 2592000, 'year': 31536000}


    YANDEX_LANGS = frozenset(["en", "ru", "be", "fr", "de", "id", "kk", "tt", "tr", "uk"])

    _NORMALIZERS = {}  # Populated at end of class to avoid undefined references
    _TEMPLATES = {"image": "images.html", "video": "videos.html"}


    @staticmethod
    def dispatch_request(engine_id: str, query: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Centralized request handler for all 4get hijacked engines."""
        fourget_params = FourgetHijackerClient.get_4get_params(query, params, engine_name=engine_id)

        # Extract category from SearXNG params (dict or OnlineParams)
        category = params.get('category', 'general') if hasattr(params, 'get') else 'general'
        
        if category == 'general' and hasattr(params, 'category'):
            category = params.category

        # Translate all SearXNG categories to 4get method names
        if category == 'general':
            category = 'web'
        elif category == 'images':
            category = 'image'
        elif category == 'videos':
            category = 'video'


        params.update({
            'url': 'http://4get-hijacked:80/harness.php',
            'method': 'POST',
            'json': {
                'engine': engine_id,
                'category': category,
                'params': fourget_params
            }
        })
        return params

    @staticmethod
    def dispatch_response(resp: Any, engine_id: str, logger: Any) -> list:
        """Centralized response handler with error logging."""
        try:
            return FourgetHijackerClient.normalize_results(resp.json())
        except Exception as e:
            logger.error(f'4get {engine_id} response error: {e}')
            return []

    @staticmethod
    def get_4get_params(query: str, params: Dict[str, Any], engine_name: str = None) -> Dict[str, Any]:
        """Build 4get params from SearXNG params."""
        fourget_params = {"s": query}

        if "safesearch" in params:
            fourget_params["nsfw"] = FourgetHijackerClient.NSFW_MAP.get(params["safesearch"], "yes")

        if "language" in params:
            lang_full = params["language"]
            lang = lang_full.split("-")[0] if "-" in lang_full else lang_full
            country = lang_full.split("-")[1] if "-" in lang_full else "us"

            if engine_name and engine_name.startswith("yandex"):
                fourget_params["lang"] = lang if lang in FourgetHijackerClient.YANDEX_LANGS else "en"
            else:
                fourget_params["lang"] = lang

            fourget_params["country"] = country.lower()

        if "time_range" in params and params["time_range"]:
            time_range = params["time_range"]
            current_time = int(time.time())
            if time_range in FourgetHijackerClient.TIME_MAPPINGS:
                fourget_params['newer'] = current_time - FourgetHijackerClient.TIME_MAPPINGS[time_range]
                fourget_params['older'] = current_time

        pageno = params.get("pageno", 1)
        if pageno and pageno > 1:
            fourget_params["offset"] = (pageno - 1) * FourgetHijackerClient.DEFAULT_PAGE_SIZE

        prefix = "fg_"
        for k, v in params.items():
            if k.startswith(prefix):
                raw_key = k[len(prefix):]
                fourget_params[raw_key] = v



        return fourget_params

    # --- Validation Helpers ---

    @staticmethod
    def _is_valid_url(url: Any) -> bool:
        if not url or not isinstance(url, str):
            return False
        if len(url) > 15 and url.startswith(("http://", "https://")):
             return True
        return False

    @staticmethod
    def _is_broken_image_url(url: str) -> bool:
        """Check if URL is a broken image placeholder using pre-compiled regex."""
        if not url or not isinstance(url, str):
            return True
        return bool(_BROKEN_IMAGE_RE.search(url))

    @staticmethod
    def _parse_date(date_val: Any) -> Optional[datetime]:
        if not date_val or date_val is False:
            return None
        try:
            return datetime.fromtimestamp(int(date_val))
        except (ValueError, TypeError, OverflowError):
            return None

    @staticmethod
    def _truncate_content(content: Any) -> str:
        if not content or not isinstance(content, str):
            return ""

        if len(content) > FourgetHijackerClient.MAX_CONTENT_LENGTH * 2:
            content = content[:FourgetHijackerClient.MAX_CONTENT_LENGTH * 2]

        # Only unescape if entity markers likely exist (check first 100 chars)
        if '&' in content[:min(100, len(content))]:
            content = unescape(content)

        content = _WHITESPACE_RE.sub(' ', content).strip()

        if len(content) > FourgetHijackerClient.MAX_CONTENT_LENGTH:
            return content[:FourgetHijackerClient.MAX_CONTENT_LENGTH] + "..."
        return content

    @staticmethod
    def _normalize_thumbnail_url(url: Any, context: str = "thumbnail") -> Optional[str]:
        """Normalize and validate thumbnail URL."""
        if not url or not isinstance(url, str):
            return None

        if url.startswith("//"):
            url = "https:" + url

        if not FourgetHijackerClient._is_valid_url(url):
            logger.debug(f"Rejected {context} URL (invalid format): {url[:100]}")
            return None

        if FourgetHijackerClient._is_broken_image_url(url):
            logger.debug(f"Rejected {context} URL (broken image pattern): {url[:100]}")
            return None

        return url

    # --- Normalization Logic ---

    @staticmethod
    def normalize_results(response_data: Any):
        results = []
        if not isinstance(response_data, dict):
            return results

        # propagate 4get error status
        if response_data.get("status") == "error":
            raise RuntimeError(f"4get upstream error: {response_data.get('message', 'Unknown error')}")

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
        if not FourgetHijackerClient._NORMALIZERS:
            FourgetHijackerClient._NORMALIZERS = {
                "web": FourgetHijackerClient._normalize_web_result,
                "image": FourgetHijackerClient._normalize_image_result,
                "video": FourgetHijackerClient._normalize_video_result,
                "news": FourgetHijackerClient._normalize_news_result,
                "livestream": FourgetHijackerClient._normalize_video_result,
                "reel": FourgetHijackerClient._normalize_video_result,
                "song": FourgetHijackerClient._normalize_media_result,
                "podcast": FourgetHijackerClient._normalize_media_result,
                "playlist": FourgetHijackerClient._normalize_web_result,
                "album": FourgetHijackerClient._normalize_web_result,
                "author": FourgetHijackerClient._normalize_web_result,
                "user": FourgetHijackerClient._normalize_web_result,
            }

        current_ts = time.time()

        for result_type, normalizer in FourgetHijackerClient._NORMALIZERS.items():
            items = response_data.get(result_type)
            if not items:
                continue
            for item in items:
                try:
                    if not isinstance(item, dict) or FourgetHijackerClient._has_invalid_date(item, current_ts):
                        continue
                    result = normalizer(item)
                    if result:
                        if result_type in FourgetHijackerClient._TEMPLATES:
                            result["template"] = FourgetHijackerClient._TEMPLATES[result_type]
                        results.append(result)
                except Exception as e:
                    logger.error(f"Failed to normalize {result_type} result: {e}")
                    continue

        return results

    @staticmethod
    def _has_invalid_date(item: Dict[str, Any], current_ts: float) -> bool:
        """Filter future dates using fast timestamp check."""
        if "date" not in item:
            return False
        date_val = item["date"]
        if not date_val:
            return False
        try:
            if int(date_val) > current_ts:
                return True
        except (ValueError, TypeError, OverflowError):
            return True
        return False

    @staticmethod
    def _normalize_answer_result(item: Dict[str, Any]) -> Optional[Answer | Dict[str, Any]]:
        desc_list = item.get("description")
        if not desc_list or not isinstance(desc_list, list):
            return None

        description_parts = [
            part.get("value", "").strip()
            for part in desc_list
            if isinstance(part, dict) and part.get("type") == "text" and part.get("value")
        ]
        answer_text = " ".join(description_parts)
        if not answer_text:
            return None

        if item.get("table") or item.get("sublink"):
            return FourgetHijackerClient._normalize_infobox_from_answer(item, answer_text)

        return Answer(answer=FourgetHijackerClient._truncate_content(answer_text))

    @staticmethod
    def _normalize_infobox_from_answer(item: Dict[str, Any], content_text: str = None) -> Optional[Dict[str, Any]]:
        title = item.get("title", "Infobox")

        if content_text is None:
            content_text = " ".join([
                part.get("value", "")
                for part in item.get("description", [])
                if isinstance(part, dict) and part.get("type") == "text"
            ])

        title = FourgetHijackerClient._truncate_content(title)

        result = {
            'infobox': title,
            'id': item.get("url") or title,
            'content': FourgetHijackerClient._truncate_content(content_text),
            'urls': [],
            'attributes': []
        }

        thumb_url = FourgetHijackerClient._normalize_thumbnail_url(
            item.get("thumb"), context="infobox"
        )
        if thumb_url:
            result["img_src"] = thumb_url

        if item.get("url") and FourgetHijackerClient._is_valid_url(item["url"]):
            result["urls"].append({'title': 'Source', 'url': item["url"]})

        table_data = item.get("table", {})
        if isinstance(table_data, dict):
            for key, value in table_data.items():
                if value and str(value).strip():
                    result["attributes"].append({
                        'label': str(key),
                        'value': FourgetHijackerClient._truncate_content(str(value))
                    })

        sublinks = item.get("sublink", {})
        # Schema: sublink in infobox/answer can be a list of dicts [{"title": "...", "url": "..."}] 
        # OR a dict {"Title": "Url"}
        if isinstance(sublinks, dict):
            for label, url in sublinks.items():
                if url and FourgetHijackerClient._is_valid_url(url):
                    result["urls"].append({'title': label, 'url': url})
        elif isinstance(sublinks, list):
            for link_item in sublinks:
                if isinstance(link_item, dict):
                    sl_title = link_item.get("title")
                    sl_url = link_item.get("url")
                    if sl_title and sl_url and FourgetHijackerClient._is_valid_url(sl_url):
                         result["urls"].append({'title': sl_title, 'url': sl_url})

        return result

    @staticmethod
    def _normalize_web_result(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        url = item.get("url")
        title = item.get("title")

        if url and url.startswith("//"):
            url = "https:" + url

        if not FourgetHijackerClient._is_valid_url(url) or not title: return None

        # Sanity checks
        if url == title: return None
        if '\x00' in url or '\x00' in title: return None

        content = FourgetHijackerClient._truncate_content(item.get("description"))

        # Enrich content with table data if present
        table_data = item.get("table")
        rich_chunks = []

        # Handle explicit Author field (common in Playlists/Albums)
        author = item.get("author")
        if author:
            author_name = author.get("name") if isinstance(author, dict) else str(author)
            if author_name:
                # If author URL is present, we could make it a link, but for now just text
                rich_chunks.append(f"By {author_name}")

        followers = item.get("followers")
        if followers:
            rich_chunks.append(f"{followers} Followers")

        if isinstance(table_data, dict) and table_data:
            # Check for Rating + Votes pair
            rating = None
            votes = None
            other_attributes = []

            for k, v in table_data.items():
                k_lower = k.lower()
                if k_lower == 'rating':
                    rating = str(v).strip()
                elif k_lower == 'votes':
                    votes = str(v).strip()
                elif v and isinstance(v, (str, int, float)):
                    clean_val = str(v).strip()
                    if clean_val:
                        other_attributes.append((k, clean_val))

            # Construct merged rating string
            if rating:
                rating_str = f"Rating: {rating}"
                if votes:
                    rating_str += f" ({votes} votes)"
                rich_chunks.append(rating_str)
            elif votes:
                 rich_chunks.append(f"Votes: {votes}")

            # Add remaining items
            for key, value in other_attributes:
                rich_chunks.append(f"{key}: {value}")

        if rich_chunks:
            # Prepend rich attributes with elegant separators
            snippet_text = " • ".join(rich_chunks)
            if content:
                content = f"{snippet_text} — {content}"
            else:
                content = snippet_text

        # Append Sitelinks (Deep Links) as Minimal HTML Anchors
        # Schema: sublink is nested dict {"Title" => "URL"} or list of dicts
        sublinks = item.get("sublink")
        if sublinks and isinstance(sublinks, dict):
            sitelink_anchors = []
            for sl_title, sl_url in sublinks.items():
                if not sl_title or not sl_url: continue
                # Basic validation
                if not isinstance(sl_url, str) or not FourgetHijackerClient._is_valid_url(sl_url): continue
                
                # HTML Escape Title for Safety
                safe_title = sl_title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                safe_url = sl_url.replace('"', '&quot;') # minimal escaping for href attr
                
                sitelink_anchors.append(f'<a href="{safe_url}">{safe_title}</a>')
            
            if sitelink_anchors:
                # Minimal format: ...description. <br>Link • Link
                links_html = " • ".join(sitelink_anchors)
                if content:
                    content = f"{content}<br>{links_html}"
                else:
                    content = links_html

        result = {
            "title": FourgetHijackerClient._truncate_content(title),
            "url": url,
            "content": content
        }

        # Attempt to extract thumbnail if present (commonly 'thumb' or 'thumbnail')
        raw_thumb = item.get("thumb") or item.get("thumbnail")
        if raw_thumb:
            # Handle potential dict structure (e.g. {"url": "..."}) or direct string
            thumb_url = None
            if isinstance(raw_thumb, dict):
                thumb_url = raw_thumb.get("url")
            elif isinstance(raw_thumb, str):
                thumb_url = raw_thumb
            
            # Normalize
            thumb_url = FourgetHijackerClient._normalize_thumbnail_url(
                thumb_url, context="web thumbnail"
            )
            
            if thumb_url:
                result["thumbnail"] = thumb_url

        date_obj = FourgetHijackerClient._parse_date(item.get("date") or item.get("publishedDate"))
        if date_obj: result["publishedDate"] = date_obj
        return result

    @staticmethod
    def _extract_proxied_url(url: str) -> str:
        """Extract original URL from 4get proxy wrapper if present."""
        if not url or "url=" not in url:
            return url
        # Conservative check
        if not (url.startswith("/") or "4get" in url.lower()):
            return url

        try:
            # Supports ?url=... and &url=...

            # Edge Case: Fragments. We must essentially ignore anything after '#'
            # Splitting is cheaper than full parsing.
            work_url = url.split('#', 1)[0]

            start_idx = work_url.find('?url=')
            if start_idx == -1:
                start_idx = work_url.find('&url=')

            if start_idx != -1:
                # Extract value part (skip ?url= or &url= which is 5 chars)
                val_start = start_idx + 5
                val_end = work_url.find('&', val_start)

                if val_end == -1:
                    raw_val = work_url[val_start:]
                else:
                    raw_val = work_url[val_start:val_end]

                # unquote_plus handles '+' as space, matching parse_qs behavior
                candidate = unquote_plus(raw_val)
                if FourgetHijackerClient._is_valid_url(candidate):
                    return candidate

        except Exception:
            pass

        # Fallback: strict safety return original if extraction failed
        return url

    @staticmethod
    def _normalize_image_result(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        source = item.get("source")
        if not source or not isinstance(source, list) or len(source) < 1:
            return None

        img_data = source[0]
        thumb_data = source[1] if len(source) > 1 else img_data

        if not isinstance(img_data, dict) or not isinstance(thumb_data, dict):
            return None

        img_url = img_data.get("url")
        thumb_url = thumb_data.get("url")

        if not FourgetHijackerClient._is_valid_url(img_url):
            return None

        if FourgetHijackerClient._is_broken_image_url(img_url):
            return None

        # Sanity checks
        if '\x00' in img_url: return None

        img_url = FourgetHijackerClient._extract_proxied_url(img_url)
        thumb_url = FourgetHijackerClient._extract_proxied_url(thumb_url) if thumb_url else None

        title = item.get("title") or "Image"
        if '\x00' in title: return None

        result = {
            "title": FourgetHijackerClient._truncate_content(title),
            "url": item.get("url") or img_url,
            "img_src": img_url,
        }
        thumb_url = FourgetHijackerClient._normalize_thumbnail_url(
            thumb_url, context="image thumbnail"
        )
        if thumb_url and thumb_url != img_url:
            result["thumbnail_src"] = thumb_url
        return result

    @staticmethod
    def _normalize_video_result(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        url = item.get("url")
        title = item.get("title")
        if not FourgetHijackerClient._is_valid_url(url) or not title:
            return None

        # Sanity checks
        if url == title: return None
        if '\x00' in url or '\x00' in title: return None

        result = {
            "title": FourgetHijackerClient._truncate_content(title),
            "url": url,
            "content": FourgetHijackerClient._truncate_content(item.get("description")),
        }

        # Handle Author/Channel
        author = item.get("author")
        if author:
            if isinstance(author, dict):
                result["author"] = author.get("name")
            elif isinstance(author, str):
                result["author"] = author

        raw_thumb = item.get("thumb") or item.get("thumbnail")
        thumb_url = None
        if isinstance(raw_thumb, dict):
            thumb_url = raw_thumb.get("url")
        elif isinstance(raw_thumb, str):
            thumb_url = raw_thumb

        thumb_url = FourgetHijackerClient._normalize_thumbnail_url(
            thumb_url, context="video thumbnail"
        )
        if thumb_url:
            result["thumbnail"] = thumb_url

        date_obj = FourgetHijackerClient._parse_date(item.get("date") or item.get("publishedDate"))
        if date_obj:
            result["publishedDate"] = date_obj

        # Map rich video metadata
        duration_str = item.get("duration")
        if duration_str and (isinstance(duration_str, str) or isinstance(duration_str, (int, float))):
            # SearXNG handles int as seconds, or strings like "12:30"
            result["length"] = int(duration_str) if isinstance(duration_str, (int, float)) else duration_str

        views_val = item.get("views")
        if views_val:
            result["views"] = str(views_val)

        return result

    @staticmethod
    def _normalize_media_result(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Normalize songs and podcasts to Video-like results."""
        res = FourgetHijackerClient._normalize_video_result(item)
        if not res: return None
        
        # Append stream info if available
        stream = item.get("stream")
        if stream and isinstance(stream, dict):
            endpoint = stream.get("endpoint")
            if endpoint:
                extra = f"Source: {endpoint.upper()}"
                if res.get("content"):
                    res["content"] += f" | {extra}"
                else:
                    res["content"] = extra
        
        return res

    @staticmethod
    def _normalize_news_result(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        url = item.get("url")
        title = item.get("title")
        if not FourgetHijackerClient._is_valid_url(url) or not title:
            return None

        # Sanity checks
        if url == title: return None
        if '\x00' in url or '\x00' in title: return None

        result = {
            "title": FourgetHijackerClient._truncate_content(title),
            "url": url,
            "content": FourgetHijackerClient._truncate_content(item.get("description")),
        }

        raw_thumb = item.get("thumb")
        thumb_url = None
        if isinstance(raw_thumb, dict):
            thumb_url = raw_thumb.get("url")
        elif isinstance(raw_thumb, str):
            thumb_url = raw_thumb

        thumb_url = FourgetHijackerClient._normalize_thumbnail_url(
            thumb_url, context="news thumbnail"
        )
        if thumb_url:
            result["thumbnail"] = thumb_url

        date_obj = FourgetHijackerClient._parse_date(item.get("date"))
        if date_obj:
            result["publishedDate"] = date_obj
        
        # Map Author/Source
        author = item.get("author") or item.get("source")
        if author and isinstance(author, str):
            result["author"] = author

        return result