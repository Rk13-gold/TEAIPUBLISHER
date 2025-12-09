"""Web search integration using ddgs or duckduckgo-search.

Provides a small search() helper that returns a list of dicts with keys:
  - title
  - snippet
  - url

If `ddgs` is installed it uses it (faster, more robust), otherwise falls back to
duckduckgo_search module.
"""
from __future__ import annotations
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


def search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Run a web search and return results as a list of dicts.

    This tries to use `ddgs` first, then `duckduckgo_search` as a fallback.
    """
    results: List[Dict[str, str]] = []
    if not query:
        return results
    try:
        # Prefer ddgs if available
        import ddgs  # type: ignore
        logger.debug("Using ddgs for web search")
        for r in ddgs.search(query, max_results=max_results):
            try:
                results.append({
                    'title': r.get('title') or r.get('text') or r.get('body') or r.get('header') or '',
                    'snippet': r.get('body') or r.get('text') or r.get('snippet') or '',
                    'url': r.get('href') or r.get('url') or r.get('link') or ''
                })
            except Exception:
                continue
        return results
    except Exception:
        pass

    try:
        from duckduckgo_search import ddg  # type: ignore
        logger.debug("Using duckduckgo_search.ddg for web search")
        items = ddg(query, max_results=max_results)
        for i in items:
            results.append({
                'title': i.get('title', ''),
                'snippet': i.get('body', '') or i.get('snippet', ''),
                'url': i.get('href', '') or i.get('url', '')
            })
        return results
    except Exception as exc:
        logger.debug('Search fallback error: %s', exc)
        return []


def can_search() -> bool:
    """Return True if a supported search backend is available (ddgs or duckduckgo_search)."""
    try:
        import ddgs  # type: ignore
        return True
    except Exception:
        pass
    try:
        from duckduckgo_search import ddg  # type: ignore
        return True
    except Exception:
        return False
