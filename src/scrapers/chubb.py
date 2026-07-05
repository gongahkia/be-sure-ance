"""
CHUBB

https://www.chubb.com/sg-en/individuals-families.html
https://www.chubb.com/sg-en/individuals-families/travel-insurance.html
https://www.chubb.com/sg-en/individuals-families/home-insurance.html
https://www.chubb.com/sg-en/individuals-families/personal-accident-insurance.html
https://www.chubb.com/sg-en/individuals-families/staycation-insurance.html
https://www.chubb.com/sg-en/individuals-families/coach-and-ferry-travel-insurance.html
"""

# ----- required imports -----

import asyncio
import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from src.backend.helper import initialize_data_store, overwrite_plans_for_insurer
from src.lib.http_identity import BOT_USER_AGENT
from src.scrapers.navigation import gather_scrape_results

# ----- functions -----

CHUBB_BASE_URL = "https://www.chubb.com"
REQUEST_TIMEOUT_SECONDS = 20
SKIP_SLUGS = {"individuals-families", "travel-protection", "accident-protection", "personal-protection"}


def normalize_whitespace(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def fetch_html(url: str, session: requests.Session | None = None) -> str:
    client = session or requests
    response = client.get(
        url,
        timeout=REQUEST_TIMEOUT_SECONDS,
        headers={"User-Agent": BOT_USER_AGENT},
    )
    response.raise_for_status()
    return response.text


def is_chubb_product_url(url: str) -> bool:
    parsed = urlparse(url)
    slug = parsed.path.rstrip("/").rsplit("/", 1)[-1].removesuffix(".html")
    return "/sg-en/individuals-families/" in parsed.path and slug not in SKIP_SLUGS


def discover_product_links(html_content: str, source_url: str) -> list[str]:
    soup = BeautifulSoup(html_content, "html.parser")
    links = []
    seen = set()
    for anchor in soup.select("a[href]"):
        href = urljoin(source_url, anchor.get("href") or "")
        if not is_chubb_product_url(href) or href in seen:
            continue
        seen.add(href)
        links.append(href)
    return links


def meta_description(soup: BeautifulSoup) -> str:
    meta = soup.select_one('meta[name="description"]')
    return normalize_whitespace(meta.get("content")) if meta else ""


def first_pdf_url(soup: BeautifulSoup, source_url: str) -> str:
    for anchor in soup.select("a[href]"):
        href = anchor.get("href") or ""
        if ".pdf" in href.lower():
            return urljoin(source_url, href)
    return ""


def parse_product_html(html_content: str, source_url: str) -> dict | None:
    soup = BeautifulSoup(html_content, "html.parser")
    title = normalize_whitespace((soup.select_one("h1") or soup.select_one("title")).get_text(" "))
    if "|" in title:
        title = normalize_whitespace(title.split("|", 1)[0])
    if not title:
        return None

    description = meta_description(soup)
    text_blocks = [
        normalize_whitespace(element.get_text(" ", strip=True))
        for element in soup.select("p, li, div.text-description")
    ]
    text_blocks = [text for text in text_blocks if text and text != title]
    benefits = []
    for text in text_blocks:
        lowered = text.lower()
        if title.lower() in lowered and len(text) > len(title) + 20:
            description = description or text
        if any(keyword in lowered for keyword in ("cover", "benefit", "protection", "insurance")):
            benefits.append(text)
    benefits = list(dict.fromkeys(benefits))[:12]

    return {
        "plan_name": title,
        "plan_benefits": benefits,
        "plan_description": description or " ".join(text_blocks[:2]),
        "plan_overview": " ".join(text_blocks[:4]),
        "plan_url": source_url,
        "product_brochure_url": first_pdf_url(soup, source_url) or source_url,
    }


def scrape_page(url: str) -> list[dict]:
    html_content = fetch_html(url)
    urls = [url] if is_chubb_product_url(url) else discover_product_links(html_content, url)
    rows = []
    for plan_url in urls:
        plan_html = html_content if plan_url == url else fetch_html(plan_url)
        row = parse_product_html(plan_html, plan_url)
        if row:
            rows.append(row)
    return rows


async def scrape_data(url):
    return await asyncio.to_thread(scrape_page, url)


async def run_all_tasks(scrape_list):
    return await gather_scrape_results("chubb", scrape_list, scrape_data)


# ----- sample execution code -----

if __name__ == "__main__":
    scrape_list = [
        "https://www.chubb.com/sg-en/individuals-families.html",
        "https://www.chubb.com/sg-en/individuals-families/travel-insurance.html",
        "https://www.chubb.com/sg-en/individuals-families/home-insurance.html",
        "https://www.chubb.com/sg-en/individuals-families/personal-accident-insurance.html",
        "https://www.chubb.com/sg-en/individuals-families/staycation-insurance.html",
        "https://www.chubb.com/sg-en/individuals-families/coach-and-ferry-travel-insurance.html",
    ]
    initialize_data_store()
    output = asyncio.run(run_all_tasks(scrape_list))
    overwrite_plans_for_insurer("chubb", output)
