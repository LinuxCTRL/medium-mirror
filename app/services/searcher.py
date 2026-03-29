import asyncio
import random
import json
import httpx
from typing import List, Dict
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]

# Load the large GraphQL query from the file
try:
    with open("medium_search_query.graphql", "r") as f:
        SEARCH_QUERY = f.read()
except:
    SEARCH_QUERY = ""

async def search_medium(query: str, depth: int = 5) -> List[Dict[str, str]]:
    """
    Search Medium using the official GraphQL SearchQuery.
    The 'depth' parameter controls how many additional pages to fetch (1 page = 10 results).
    """
    results_map = {}
    
    # We'll use Playwright to get the initial cookies and state
    # This ensures we have a valid session if Medium requires it.
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=random.choice(USER_AGENTS))
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)

        try:
            # 1. Get initial results from the main search page
            search_url = f"https://medium.com/search/posts?q={query.replace(' ', '+')}"
            print(f"Loading search page: {search_url}")
            await page.goto(search_url, wait_until="domcontentloaded")
            await asyncio.sleep(5)
            
            state = await page.evaluate("window.__APOLLO_STATE__")
            if state:
                for val in state.values():
                    if isinstance(val, dict) and val.get("__typename") == "Post":
                        url = val.get("mediumUrl")
                        title = val.get("title")
                        if url and title:
                            clean_url = url.split("?")[0]
                            author = "Medium Result"
                            creator_ref = val.get("creator", {}).get("__ref")
                            if creator_ref and creator_ref in state:
                                author = state[creator_ref].get("name") or state[creator_ref].get("username") or author
                            
                            results_map[clean_url] = {
                                "title": title.strip(),
                                "url": clean_url,
                                "author": author,
                                "claps": val.get("clapCount", 0)
                            }
            
            print(f"Initial results: {len(results_map)}")

            # 2. Mimic the "Show more" GraphQL calls for subsequent pages
            if depth > 1:
                cookies = await context.cookies()
                cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
                
                headers = {
                    "content-type": "application/json",
                    "accept": "*/*",
                    "user-agent": random.choice(USER_AGENTS),
                    "cookie": cookie_str,
                    "origin": "https://medium.com",
                    "referer": search_url
                }

                async with httpx.AsyncClient() as client:
                    for page_num in range(1, depth): # Fetch subsequent pages
                        print(f"Fetching page {page_num} via GraphQL...")
                        
                        variables = {
                            "query": query,
                            "pagingOptions": {"limit": 10, "page": page_num},
                            "withUsers": False, "withTags": False, "withPosts": True,
                            "withCollections": False, "withLists": False,
                            "searchInCollection": False, "collectionDomainOrSlug": "medium.com",
                            "postsSearchOptions": {
                                "filters": "writtenByHighQualityUser:true",
                                "clickAnalytics": True,
                                "analyticsTags": ["web-main-content"]
                            }
                        }
                        
                        payload = [{
                            "operationName": "SearchQuery",
                            "variables": variables,
                            "query": SEARCH_QUERY
                        }]
                        
                        resp = await client.post("https://medium.com/_/graphql", json=payload, headers=headers)
                        if resp.status_code == 200:
                            data = resp.json()
                            # Navigate deep into the response to find posts
                            try:
                                items = data[0]['data']['search']['posts']['items']
                                for item in items:
                                    # The full post data might be nested or in a fragment
                                    # We'll just look for Post objects in the response data
                                    def find_posts(obj):
                                        if isinstance(obj, dict):
                                            if obj.get("__typename") == "Post":
                                                url = obj.get("mediumUrl")
                                                title = obj.get("title")
                                                if url and title:
                                                    clean_url = url.split("?")[0]
                                                    results_map[clean_url] = {
                                                        "title": title.strip(),
                                                        "url": clean_url,
                                                        "author": obj.get("creator", {}).get("name", "Medium Result"),
                                                        "claps": obj.get("clapCount", 0)
                                                    }
                                            else:
                                                for v in obj.values(): find_posts(v)
                                        elif isinstance(obj, list):
                                            for i in obj: find_posts(i)
                                    
                                    find_posts(item)
                            except:
                                print(f"Failed to parse page {page_num} items")
                        else:
                            print(f"GraphQL Error {resp.status_code}: {resp.text[:200]}")
                        
                        print(f"Results after page {page_num}: {len(results_map)}")
                        await asyncio.sleep(random.uniform(1, 3))

            return list(results_map.values())
        except Exception as e:
            print(f"Search error: {e}")
            return list(results_map.values())
        finally:
            await browser.close()
