"""
services/firecrawl_service.py
Scrape competitor URLs using Firecrawl API.
"""
import httpx
from config import FIRECRAWL_API_KEY


async def scrape_url(url: str) -> dict:
    """Scrape a single URL via Firecrawl and return markdown content."""
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://api.firecrawl.dev/v1/scrape",
            headers={
                "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
                "Content-Type": "application/json",
            },
            json={"url": url, "formats": ["markdown"]},
        )
        resp.raise_for_status()
        data = resp.json()
        return {
            "url": url,
            "content": data.get("data", {}).get("markdown", ""),
            "title": data.get("data", {}).get("metadata", {}).get("title", url),
        }


async def scrape_multiple(urls: list[str]) -> list[dict]:
    """Scrape multiple URLs concurrently."""
    import asyncio
    tasks = [scrape_url(u) for u in urls if u.strip()]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    output = []
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            output.append({"url": urls[i], "content": f"[SCRAPE ERROR: {r}]", "title": urls[i]})
        else:
            output.append(r)
    return output
