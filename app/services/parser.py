from bs4 import BeautifulSoup
from typing import Dict, Optional
import copy

def parse_medium_article(html: str) -> Optional[Dict[str, str]]:
    """
    Parser specifically for Freedium's rendered output.
    """
    soup = BeautifulSoup(html, "html.parser")
    
    # 1. Target Freedium's main content container
    article_tag = soup.find("div", class_="main-content")
    
    # If not Freedium, fallback to original Medium/General tags
    if not article_tag:
        article_tag = soup.find("article") or soup.find("main") or soup.find("section")

    if not article_tag:
        return None

    # 2. Title extraction (Freedium uses standard h1 or meta)
    title = "Untitled"
    # Check meta tags first (reliable on Freedium too)
    title_meta = soup.find("meta", property="og:title")
    if title_meta:
        title = title_meta.get("content", "").replace(" - Freedium", "").strip()
    
    if title == "Untitled":
        title_tag = soup.find("h1")
        if title_tag:
            title = title_tag.get_text().strip()

    # 3. Author extraction
    author = "Unknown"
    # Freedium typically includes a link with a class like 'ghostyjoe' or inside the author box.
    author_box = soup.find("div", class_=lambda x: x and 'flex' in x and 'items-center' in x and 'space-x' in x)
    if author_box:
        # Looking for the bold name or links with specific author-like classes
        author_link = author_box.find("a", class_=lambda x: x and ('font-semibold' in x or 'ghostyjoe' in x))
        if author_link:
            author = author_link.get_text().strip()

    # Fallback: Check for meta tags (og:author or article:author)
    if author == "Unknown" or not author:
        for attr in ["property", "name"]:
            for val in ["author", "article:author", "og:article:author", "twitter:creator"]:
                author_meta = soup.find("meta", {attr: val})
                if author_meta and author_meta.get("content"):
                    author = author_meta.get("content").strip()
                    break
            if author != "Unknown": break

    # Fallback: Look for "By " text patterns if still unknown
    if author == "Unknown":
        by_tag = soup.find(lambda tag: tag.name in ["p", "span", "div"] and tag.get_text().strip().startswith("By "))
        if by_tag:
            author = by_tag.get_text().replace("By ", "").strip()

    # 4. Content Cleaning (Freedium already does a lot of work for us!)
    content_soup = copy.copy(article_tag)
    
    # Remove any unwanted leftovers (like their problem modal or dark mode toggle)
    for tag in content_soup.find_all(["script", "style", "nav", "footer", "header", "button", "iframe"]):
        tag.decompose()

    # 5. Fix absolute image URLs if needed (Freedium uses Miro direct links)
    for img in content_soup.find_all("img"):
        if img.has_attr("src") and img["src"].startswith("/"):
            # If Freedium uses local paths, we could fix them, but usually they're absolute miro links.
            pass

    content_html = str(content_soup)

    return {
        "title": title,
        "author": author,
        "content_html": content_html
    }
