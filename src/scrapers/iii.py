"""
INDIA INTERNATIONAL INSURANCE

https://www.iii.com.sg/
https://www.iii.com.sg/products/motor-insurance
https://www.iii.com.sg/products/home-insurance
https://www.iii.com.sg/products/travel-insurance
https://www.iii.com.sg/products/personal-accident-insurance
https://www.iii.com.sg/products/maid-insurance
https://www.iii.com.sg/products/pet-insurance
https://www.iii.com.sg/products/marine-insurance
https://www.iii.com.sg/products/property-insurance
https://www.iii.com.sg/products/liability-insurance
https://www.iii.com.sg/products/engineering-insurance
https://www.iii.com.sg/products/surety-insurance
https://www.iii.com.sg/products/motor-fleet-insurance
https://www.iii.com.sg/products/reinsurance
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

III_BASE_URL = "https://www.iii.com.sg"
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


def page_title_from_url(url: str) -> str:
    slug = url.rstrip("/").rsplit("/", 1)[-1]
    return slug.replace("-", " ").title()


def first_pdf_url(soup: BeautifulSoup, source_url: str) -> str:
    for anchor in soup.select("a[href]"):
        href = anchor.get("href") or ""
        if ".pdf" in href.lower():
            return urljoin(source_url, href)
    return ""


def parse_product_html(html_content: str, source_url: str) -> dict:
    soup = BeautifulSoup(html_content, "html.parser")
    title_node = soup.select_one("h1") or soup.select_one("main h2") or soup.select_one("h2")
    title = normalize_whitespace(title_node.get_text(" ", strip=True) if title_node else "")
    title = title or page_title_from_url(source_url)

    lead_blocks = [
        normalize_whitespace(node.get_text(" ", strip=True))
        for node in soup.select("main p, section p, article p")
    ]
    lead_blocks = [text for text in lead_blocks if text and text != title]
    benefit_nodes = soup.select(
        "main li, section li, ul.text-start li, ul.list-style-02 li, div.card-body"
    )
    benefits = [
        normalize_whitespace(node.get_text(" ", strip=True))
        for node in benefit_nodes
        if normalize_whitespace(node.get_text(" ", strip=True))
    ]
    benefits = list(dict.fromkeys(benefits))[:16]

    return {
        "plan_name": title,
        "plan_benefits": benefits,
        "plan_description": " ".join(lead_blocks[:2]),
        "plan_overview": " ".join(lead_blocks[:5]),
        "plan_url": source_url,
        "product_brochure_url": first_pdf_url(soup, source_url),
    }


def scrape_page(url: str) -> list[dict]:
    return [parse_product_html(fetch_html(url), url)]


async def scrape_data(url):
    return await asyncio.to_thread(scrape_page, url)


async def run_all_tasks(scrape_list):
    return await gather_scrape_results("iii", scrape_list, scrape_data)


# ----- sample execution code -----

if __name__ == "__main__":
    scrape_list = [
        "https://www.iii.com.sg/products/motor-insurance",
        "https://www.iii.com.sg/products/home-insurance",
        "https://www.iii.com.sg/products/travel-insurance",
        "https://www.iii.com.sg/products/personal-accident-insurance",
        "https://www.iii.com.sg/products/maid-insurance",
        "https://www.iii.com.sg/products/pet-insurance",
        "https://www.iii.com.sg/products/marine-insurance",
        "https://www.iii.com.sg/products/property-insurance",
        "https://www.iii.com.sg/products/liability-insurance",
        "https://www.iii.com.sg/products/engineering-insurance",
        "https://www.iii.com.sg/products/surety-insurance",
        "https://www.iii.com.sg/products/motor-fleet-insurance",
        "https://www.iii.com.sg/products/reinsurance",
    ]
    initialize_data_store()
    output = asyncio.run(run_all_tasks(scrape_list))
    overwrite_plans_for_insurer("iii", output)
