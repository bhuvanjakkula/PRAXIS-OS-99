from __future__ import annotations
import httpx

BASE = "https://api.worldbank.org/v2"

async def indicator(country_code: str, indicator_code: str, mrv: int = 10):
    url = f"{BASE}/country/{country_code}/indicator/{indicator_code}"
    params = {"format": "json", "mrv": mrv, "per_page": mrv}
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        payload = response.json()
    if not isinstance(payload, list) or len(payload) < 2:
        return []
    return payload[1] or []
