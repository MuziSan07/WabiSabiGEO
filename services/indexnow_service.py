"""
services/indexnow_service.py
Ping IndexNow API after content generation.
"""
import httpx
from config import INDEXNOW_KEY


async def ping_indexnow(client_url: str) -> dict:
    """Send a POST request to IndexNow to notify of updated content."""
    from urllib.parse import urlparse
    parsed = urlparse(client_url)
    host = parsed.netloc or parsed.path

    payload = {
        "host": host,
        "key": INDEXNOW_KEY,
        "keyLocation": f"https://{host}/{INDEXNOW_KEY}.txt",
        "urlList": [client_url],
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                "https://api.indexnow.org/indexnow",
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            return {
                "success": resp.status_code in (200, 202),
                "status_code": resp.status_code,
                "message": f"IndexNow pinged — HTTP {resp.status_code}",
            }
    except Exception as e:
        return {"success": False, "status_code": 0, "message": str(e)}
