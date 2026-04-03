from __future__ import annotations

from tool_python_stubs.common.types import TextToolResult



import json
import re
from html import unescape
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from tool_python_stubs.common.decorators import tracked_tool
from tool_python_stubs.common.runtime import build_text_result, write_json_output


def _fetch_json(url: str) -> dict | None:
    request = Request(url, headers={"User-Agent": "Multimodal-GeoKG-Agent/0.1"})
    with urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def _fetch_text(url: str) -> str:
    request = Request(url, headers={"User-Agent": "Multimodal-GeoKG-Agent/0.1"})
    with urlopen(request, timeout=15) as response:
        return response.read().decode("utf-8", errors="ignore")


def _strip_html(value: str) -> str:
    text = re.sub(r"<script[\s\S]*?</script>", " ", value, flags=re.IGNORECASE)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", unescape(text))
    return text.strip()


def _fetch_wikipedia(entity_name: str, lang: str) -> tuple[str, str, str] | None:
    url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{quote(entity_name)}"
    data = _fetch_json(url)
    if not data or not data.get("extract"):
        return None
    return (
        data.get("title", entity_name),
        data.get("extract", "").strip(),
        (data.get("content_urls") or {}).get("desktop", {}).get("page", ""),
    )


def _fetch_baidu_baike(entity_name: str) -> tuple[str, str, str] | None:
    url = f"https://baike.baidu.com/item/{quote(entity_name)}"
    html = _fetch_text(url)
    title_match = re.search(r"<title>(.*?)</title>", html, flags=re.IGNORECASE)
    paragraphs = re.findall(r'<div class="para"[^>]*>([\s\S]*?)</div>', html, flags=re.IGNORECASE)
    content = "\n\n".join(filter(None, (_strip_html(item) for item in paragraphs)))
    if not content:
        return None
    title = _strip_html(title_match.group(1)) if title_match else entity_name
    return (title, content, url)


def _fetch_duckduckgo(entity_name: str) -> tuple[str, str, str] | None:
    url = f"https://api.duckduckgo.com/?{urlencode({'q': entity_name, 'format': 'json', 'no_html': 1, 'skip_disambig': 1})}"
    data = _fetch_json(url)
    if not data or not data.get("AbstractText"):
        return None
    return (data.get("Heading") or entity_name, data.get("AbstractText", "").strip(), data.get("AbstractURL", ""))


@tracked_tool
def textual_content_download(
    entity_name: str,
    preferred_sources: list[str] | None = None,
    min_content_chars: int = 200,
) -> TextToolResult:
    """Retrieve descriptive text for a named geographic entity.

    :param entity_name: Entity name in Chinese or English. Must be a non-empty string.
    :type entity_name: str
    :param preferred_sources: Optional ordered source list. Supported values per item: "baidu_baike", "wikipedia_zh", "wikipedia_en", "web". Items must be unique when provided.
    :type preferred_sources: list[str] | None
    :param min_content_chars: Minimum accepted content length in characters. Must be at least 100. Defaults to 200.
    :type min_content_chars: int
    :returns: A TextAsset-compatible dictionary containing retrieved text content and provenance metadata.
    :rtype: TextToolResult
    """
    if not entity_name.strip():
        return {
            "outcome": "error",
            "error_code": "INVALID_ARGUMENT",
            "retryable": False,
            "recovery_hint": "entity_name must be a non-empty string.",
        }

    if min_content_chars < 100:
        return {
            "outcome": "error",
            "error_code": "INVALID_ARGUMENT",
            "retryable": False,
            "recovery_hint": "min_content_chars must be at least 100.",
        }

    allowed_sources = {"baidu_baike", "wikipedia_zh", "wikipedia_en", "web"}
    if preferred_sources is not None:
        if len(set(preferred_sources)) != len(preferred_sources):
            return {
                "outcome": "error",
                "error_code": "INVALID_ARGUMENT",
                "retryable": False,
                "recovery_hint": "preferred_sources items must be unique when provided.",
            }
        invalid_sources = sorted(set(preferred_sources) - allowed_sources)
        if invalid_sources:
            return {
                "outcome": "error",
                "error_code": "INVALID_ARGUMENT",
                "retryable": False,
                "recovery_hint": f"Unsupported preferred_sources values: {', '.join(invalid_sources)}.",
            }

    if preferred_sources is None:
        has_chinese = any("\u4e00" <= char <= "\u9fff" for char in entity_name)
        preferred_sources = ["baidu_baike", "wikipedia_zh", "wikipedia_en", "web"] if has_chinese else ["wikipedia_en", "wikipedia_zh", "baidu_baike", "web"]

    fetchers = {
        "baidu_baike": lambda: _fetch_baidu_baike(entity_name),
        "wikipedia_zh": lambda: _fetch_wikipedia(entity_name, "zh"),
        "wikipedia_en": lambda: _fetch_wikipedia(entity_name, "en"),
        "web": lambda: _fetch_duckduckgo(entity_name),
    }

    for source in preferred_sources:
        fetcher = fetchers.get(source)
        if fetcher is None:
            continue
        try:
            payload = fetcher()
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
            payload = None
        if not payload:
            continue
        title, content, source_url = payload
        if len(content) < min_content_chars:
            continue
        stored = {"title": title, "content": content, "source_type": source, "source_url": source_url}
        file_path = write_json_output("texts", f"text_{quote(entity_name, safe='')}_{source}", stored)
        return build_text_result(
            source_tool="textual_content_download",
            title=title,
            content=content,
            source_type=source,
            source_url=source_url,
            file_path=file_path,
        )

    return {
        "outcome": "empty",
        "error_code": "NO_ENTITY_FOUND",
        "retryable": False,
        "recovery_hint": f"No textual content meeting the minimum length was found for '{entity_name}'.",
    }