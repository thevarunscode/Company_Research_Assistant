"""Serper.dev search client: official-site resolution and research enrichment."""

import re
from urllib.parse import urlparse

import httpx

SERPER_URL = "https://google.serper.dev/search"

# Domains that are never a company's own website.
AGGREGATOR_DOMAINS = {
    "wikipedia.org", "linkedin.com", "facebook.com", "instagram.com",
    "twitter.com", "x.com", "youtube.com", "crunchbase.com", "glassdoor.com",
    "indeed.com", "bloomberg.com", "reuters.com", "forbes.com", "reddit.com",
    "g2.com", "capterra.com", "trustpilot.com", "yelp.com", "medium.com",
    "github.com", "pitchbook.com",
    "zoominfo.com", "owler.com", "tracxn.com", "britannica.com",
}


def _is_aggregator(domain: str) -> bool:
    # Exact / subdomain match only — substring matching would wrongly flag
    # e.g. spacex.com because of x.com.
    return any(domain == agg or domain.endswith("." + agg) for agg in AGGREGATOR_DOMAINS)


def _root_domain(url: str) -> str:
    host = (urlparse(url).netloc or "").lower().removeprefix("www.")
    parts = host.split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else host


async def search(query: str, api_key: str, num: int = 10) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            SERPER_URL,
            headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
            json={"q": query, "num": num},
        )
        resp.raise_for_status()
        return resp.json()


async def resolve_website(company_name: str, api_key: str) -> tuple[str | None, dict]:
    """Find the official website for a company name.

    Returns (url, knowledge_graph_info). Skips aggregator/news domains and
    prefers the knowledge-graph website when Google provides one.
    """
    data = await search(f"{company_name} official website", api_key)
    kg = data.get("knowledgeGraph") or {}

    info = {
        "title": kg.get("title", ""),
        "description": kg.get("description", ""),
        "phone": (kg.get("attributes") or {}).get("Phone", ""),
        "address": (kg.get("attributes") or {}).get("Headquarters", ""),
        "type": kg.get("type", ""),
    }

    if kg.get("website"):
        return kg["website"], info

    normalized_name = re.sub(r"[^a-z0-9]", "", company_name.lower())
    fallback: str | None = None
    for result in data.get("organic", []):
        link = result.get("link", "")
        domain = _root_domain(link)
        if not domain or _is_aggregator(domain):
            continue
        # Use the root of the site, not a deep article/link.
        parsed = urlparse(link)
        site = f"{parsed.scheme}://{parsed.netloc}"
        # An exact company-name ↔ domain match (spacex → spacex.com) beats an
        # earlier-ranked near-miss (spacexnow.com).
        if domain.split(".")[0] == normalized_name:
            return site, info
        fallback = fallback or site
    return fallback, info


async def enrich(company_name: str, domain: str, api_key: str) -> dict:
    """Extra public-source research: contact details and competitors."""
    snippets: dict[str, list[str]] = {"contact": [], "competitors": [], "pricing": []}

    try:
        contact = await search(f"{company_name} headquarters address phone contact", api_key, num=6)
        kg = contact.get("knowledgeGraph") or {}
        attrs = kg.get("attributes") or {}
        if attrs.get("Phone"):
            snippets["contact"].append(f"Phone (Google): {attrs['Phone']}")
        if attrs.get("Headquarters"):
            snippets["contact"].append(f"Headquarters (Google): {attrs['Headquarters']}")
        for r in contact.get("organic", [])[:5]:
            if r.get("snippet"):
                snippets["contact"].append(f"{r.get('title', '')}: {r['snippet']}")
    except Exception:
        pass

    try:
        comp = await search(f"{company_name} competitors alternatives", api_key, num=8)
        for r in comp.get("organic", [])[:6]:
            if r.get("snippet"):
                snippets["competitors"].append(f"{r.get('title', '')}: {r['snippet']}")
        related = [s.get("query", "") for s in comp.get("relatedSearches", [])]
        if related:
            snippets["competitors"].append("Related searches: " + ", ".join(related[:6]))
    except Exception:
        pass

    try:
        pricing = await search(f"{company_name} pricing plans price", api_key, num=6)
        for r in pricing.get("organic", [])[:4]:
            if r.get("snippet"):
                snippets["pricing"].append(f"{r.get('title', '')}: {r['snippet']}")
    except Exception:
        pass

    return snippets
