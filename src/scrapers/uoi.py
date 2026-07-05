"""
UOI

https://www.uoi.com.sg/index.page

https://www.uoi.com.sg/personal/travel-insurance.page
https://www.uoi.com.sg/personal/motor-insurance.page
https://www.uoi.com.sg/personal/home-contents-insurance.page
https://www.uoi.com.sg/personal/accident-protection.page

https://www.uoi.com.sg/commercial/general-insurance.page
https://www.uoi.com.sg/commercial/specialised-insurance.page
https://www.uoi.com.sg/claims-assistance.page
https://www.uoi.com.sg/takaful.page
"""

# ----- required imports -----

import asyncio
import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from src.backend.helper import initialize_data_store, overwrite_plans_for_insurer
from src.lib.http_identity import BOT_USER_AGENT
from src.scrapers.navigation import gather_scrape_results

# ----- functions -----

REQUEST_TIMEOUT_SECONDS = 20


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


def first_pdf_url(soup: BeautifulSoup, source_url: str) -> str:
    fallback = ""
    for anchor in soup.select("a[href]"):
        href = anchor.get("href") or ""
        if ".pdf" not in href.lower():
            continue
        absolute = urljoin(source_url, href)
        label = normalize_whitespace(anchor.get_text(" ", strip=True)).lower()
        if "brochure" in label:
            return absolute
        fallback = fallback or absolute
    return fallback


def parse_product_html(html_content: str, source_url: str) -> dict:
    soup = BeautifulSoup(html_content, "html.parser")
    title_node = soup.select_one("main h1, h1, title")
    plan_name = normalize_whitespace(title_node.get_text(" ", strip=True) if title_node else "")
    if "|" in plan_name:
        plan_name = normalize_whitespace(plan_name.split("|", 1)[0])

    paragraphs = [
        normalize_whitespace(node.get_text(" ", strip=True))
        for node in soup.select("main p, section p, div.content p")
    ]
    paragraphs = [text for text in paragraphs if text and text != plan_name]
    benefits = [
        normalize_whitespace(node.get_text(" ", strip=True))
        for node in soup.select("main li, section li, div.content-block, div.card-body")
    ]
    benefits = [text for text in benefits if text]
    benefits = list(dict.fromkeys(benefits))[:16]

    return {
        "plan_name": plan_name,
        "plan_benefits": benefits,
        "plan_description": " ".join(paragraphs[:2]),
        "plan_overview": " ".join(paragraphs[:5]),
        "plan_url": source_url,
        "product_brochure_url": first_pdf_url(soup, source_url),
    }


def scrape_page(url: str) -> list[dict]:
    return [parse_product_html(fetch_html(url), url)]


async def scrape_data(url):
    return await asyncio.to_thread(scrape_page, url)


async def run_all_tasks(scrape_list):
    return await gather_scrape_results("uoi", scrape_list, scrape_data)


# ----- sample execution code -----

if __name__ == "__main__":
    scrape_list = [
        "https://www.uoi.com.sg/personal/travel-insurance.page",
        "https://www.uoi.com.sg/personal/motor-insurance.page",
        "https://www.uoi.com.sg/personal/home-contents-insurance.page",
        "https://www.uoi.com.sg/personal/accident-protection.page",
    ]
    initialize_data_store()
    output = asyncio.run(run_all_tasks(scrape_list))
    overwrite_plans_for_insurer("uoi", output)
