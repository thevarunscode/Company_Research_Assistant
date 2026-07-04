"""Async website crawler: discovers important pages, dedupes, extracts text."""

import asyncio
import re
from urllib.parse import urljoin, urlparse, urlunparse

import httpx
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Path keywords that mark a page as valuable for research (higher = better).
PRIORITY_KEYWORDS = {
    "about": 10, "company": 9, "product": 10, "service": 10, "solution": 9,
    "pricing": 8, "contact": 8, "feature": 7, "platform": 7, "team": 5,
    "what-we-do": 8, "who-we-are": 8, "overview": 6, "customers": 4,
}

SKIP_PATTERNS = re.compile(
    r"login|log-in|signin|sign-in|signup|sign-up|register|cart|checkout|account"
    r"|privacy|terms|legal|cookie|careers|jobs|press|media|sitemap|search|blog"
    r"|auth|password|download|status|support/ticket|docs/|documentation",
    re.IGNORECASE,
)

ASSET_EXTENSIONS = (
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico", ".css", ".js",
    ".pdf", ".zip", ".mp4", ".webm", ".woff", ".woff2", ".xml", ".json", ".rss",
)

MAX_PAGE_CHARS = 2500


def normalize_url(url: str) -> str:
    """Canonical form used for dedup: no fragment, no query, no trailing slash."""
    p = urlparse(url)
    path = p.path.rstrip("/") or "/"
    return urlunparse((p.scheme, p.netloc.lower(), path, "", "", ""))


def _same_site(url: str, root: str) -> bool:
    host = urlparse(url).netloc.lower().removeprefix("www.")
    root_host = urlparse(root).netloc.lower().removeprefix("www.")
    return host == root_host or host.endswith("." + root_host)


def _score(url: str) -> int:
    path = urlparse(url).path.lower()
    return max((s for kw, s in PRIORITY_KEYWORDS.items() if kw in path), default=0)


def extract_text(html: str) -> tuple[str, str]:
    """Return (title, visible text) with boilerplate removed."""
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(strip=True) if soup.title else ""
    for tag in soup(["script", "style", "noscript", "svg", "iframe", "nav", "footer", "form"]):
        tag.decompose()
    text = re.sub(r"\s+", " ", soup.get_text(separator=" ", strip=True))
    return title, text[:MAX_PAGE_CHARS]


async def _fetch(client: httpx.AsyncClient, url: str) -> str | None:
    try:
        resp = await client.get(url, headers=HEADERS, follow_redirects=True, timeout=12)
        if resp.status_code == 200 and "text/html" in resp.headers.get("content-type", ""):
            return resp.text
    except Exception:
        pass
    return None


def _discover_links(html: str, base_url: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    seen: set[str] = set()
    links: list[str] = []
    for a in soup.find_all("a", href=True):
        href = urljoin(base_url, a["href"].strip())
        if not href.startswith(("http://", "https://")):
            continue
        if not _same_site(href, base_url):
            continue
        if href.lower().endswith(ASSET_EXTENSIONS) or SKIP_PATTERNS.search(href):
            continue
        norm = normalize_url(href)
        if norm not in seen:
            seen.add(norm)
            links.append(norm)
    return links


async def crawl_site(start_url: str, max_pages: int = 8) -> dict:
    """Crawl a company site starting from its homepage.

    Returns {"pages": [{url, title, text}], "crawled": int, "discovered": int}.
    """
    if not start_url.startswith(("http://", "https://")):
        start_url = "https://" + start_url
    root = normalize_url(start_url)

    async with httpx.AsyncClient() as client:
        home_html = await _fetch(client, root)
        if home_html is None and root.startswith("https://"):
            # Some sites only respond on the www. host.
            p = urlparse(root)
            if not p.netloc.startswith("www."):
                alt = root.replace("://", "://www.", 1)
                home_html = await _fetch(client, alt)
                if home_html is not None:
                    root = alt

        pages: list[dict] = []
        if home_html is None:
            return {"pages": pages, "crawled": 0, "discovered": 0}

        title, text = extract_text(home_html)
        pages.append({"url": root, "title": title or "Home", "text": text})

        candidates = [u for u in _discover_links(home_html, root) if u != root]
        candidates.sort(key=_score, reverse=True)
        targets = [u for u in candidates if _score(u) > 0][: max_pages - 1]
        # If keyword scoring found too few, pad with shallow top-level pages.
        if len(targets) < max_pages - 1:
            extras = [
                u for u in candidates
                if u not in targets and urlparse(u).path.count("/") <= 1
            ]
            targets += extras[: max_pages - 1 - len(targets)]

        semaphore = asyncio.Semaphore(5)

        async def fetch_one(url: str) -> dict | None:
            async with semaphore:
                html = await _fetch(client, url)
            if html is None:
                return None
            page_title, page_text = extract_text(html)
            if len(page_text) < 100:  # skip near-empty / js-only shells
                return None
            return {"url": url, "title": page_title, "text": page_text}

        results = await asyncio.gather(*(fetch_one(u) for u in targets))
        pages.extend(r for r in results if r is not None)

    return {"pages": pages, "crawled": len(pages), "discovered": len(candidates) + 1}
