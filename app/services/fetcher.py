import httpx
import random
import asyncio
from typing import Optional

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]

async def fetch_html(url: str) -> Optional[str]:
    """
    Fetch HTML via Freedium Mirror to bypass Medium's paywall and lazy-loading.
    """
    # Freedium mirror URL structure
    freedium_url = f"https://freedium-mirror.cfd/{url}"
    
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://freedium-mirror.cfd/",
    }

    async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=30.0) as client:
        try:
            print(f"Fetching via Freedium: {freedium_url}")
            response = await client.get(freedium_url)
            response.raise_for_status()
            return response.text
        except httpx.HTTPError as e:
            print(f"Error fetching from Freedium: {e}")
            # If Freedium fails, we could potentially fallback to our Playwright scraper
            return None
