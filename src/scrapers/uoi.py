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

from __future__ import annotations

import argparse
import asyncio
import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from src.backend.helper import format_plan_rows, initialize_data_store, overwrite_plans_for_insurer
from src.lib.http_identity import BOT_USER_AGENT
from src.lib.scraper_health import record_scraper_failure
from src.scrapers.navigation import gather_scrape_results
from src.validation.plan_quality import validate_plan_rows

TABLE_NAME = "uoi"
REQUEST_TIMEOUT_SECONDS = 20

PRODUCT_URLS = [
    "https://www.uoi.com.sg/personal/travel-insurance.page",
    "https://www.uoi.com.sg/personal/motor-insurance.page",
    "https://www.uoi.com.sg/personal/home-contents-insurance.page",
    "https://www.uoi.com.sg/personal/accident-protection.page",
]

REJECTED_SOURCE_URLS = {
    "https://www.uoi.com.sg/index.page",
    "https://www.uoi.com.sg/commercial/general-insurance.page",
    "https://www.uoi.com.sg/commercial/specialised-insurance.page",
    "https://www.uoi.com.sg/claims-assistance.page",
    "https://www.uoi.com.sg/takaful.page",
}

PLAN_NAME_BY_PATH = {
    "/personal/travel-insurance.page": "UniTravel Insurance",
    "/personal/motor-insurance.page": "UniCar Insurance",
    "/personal/home-contents-insurance.page": "UniHome Insurance",
    "/personal/accident-protection.page": "UniPA Personal Accident Insurance",
}

STOP_HEADINGS = (
    "coverage",
    "faq",
    "faqs",
    "insurance customer reviews",
    "travel advisory",
    "you may also like",
)

SKIP_TEXT_PATTERNS = (
    "about uob",
    "agent login",
    "buy now",
    "check out the latest promotion",
    "contact us",
    "cookie",
    "credit rating",
    "email your enquiry",
    "get a quote",
    "investor relations",
    "newsroom",
    "promotion",
    "singapore",
    "travel advisory",
    "uob group",
    "you are in",
)


def normalize_whitespace(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def fetch_html(url: str, session=requests) -> str:
    response = session.get(
        url,
        timeout=REQUEST_TIMEOUT_SECONDS,
        headers={"User-Agent": BOT_USER_AGENT},
    )
    response.raise_for_status()
    return response.text


def source_path(source_url: str) -> str:
    return urlparse(source_url).path.rstrip("/") or "/"


def is_accepted_url(source_url: str) -> bool:
    return source_path(source_url) in PLAN_NAME_BY_PATH


def clean_soup(soup: BeautifulSoup) -> BeautifulSoup:
    for element in soup(["script", "style", "noscript", "svg", "header", "footer", "nav"]):
        element.decompose()
    return soup


def should_skip_text(text: str) -> bool:
    lower = text.lower()
    return len(text) < 8 or any(pattern in lower for pattern in SKIP_TEXT_PATTERNS)


def meta_content(soup: BeautifulSoup, selector: str) -> str:
    element = soup.select_one(selector)
    return normalize_whitespace(element.get("content")) if element else ""


def intro_paragraph(soup: BeautifulSoup) -> str:
    candidates: list[str] = []
    for element in soup.find_all(["h2", "p", "li"]):
        text = normalize_whitespace(element.get_text(" ", strip=True))
        if not text:
            continue
        lower = text.lower()
        if element.name == "h2" and "product highlights" in lower:
            break
        if element.name == "p" and not should_skip_text(text):
            candidates.append(text)
    return candidates[-1] if candidates else ""


def highlight_blocks(soup: BeautifulSoup) -> list[str]:
    blocks: list[str] = []
    in_highlights = False
    pending_heading = ""
    seen: set[str] = set()
    for element in soup.find_all(["h2", "h3", "h4", "p", "li"]):
        text = normalize_whitespace(element.get_text(" ", strip=True))
        if not text:
            continue
        lower = text.lower()
        if element.name == "h2" and "product highlights" in lower:
            in_highlights = True
            continue
        if (
            in_highlights
            and element.name == "h2"
            and any(heading in lower for heading in STOP_HEADINGS)
        ):
            break
        if not in_highlights or should_skip_text(text):
            continue
        if element.name in {"h3", "h4"}:
            pending_heading = text
            continue
        block = f"{pending_heading}: {text}" if pending_heading else text
        pending_heading = ""
        if block in seen:
            continue
        seen.add(block)
        blocks.append(block)
        if len(blocks) == 8:
            break
    return blocks


def first_brochure_url(soup: BeautifulSoup, source_url: str) -> str:
    fallback = ""
    for anchor in soup.select("a[href]"):
        href = anchor.get("href") or ""
        if ".pdf" not in href.lower():
            continue
        absolute = urljoin(source_url, href)
        label = normalize_whitespace(anchor.get_text(" ", strip=True)).lower()
        combined = f"{label} {href}".lower()
        if "cookie" in combined or "faq" in combined or "policy" in combined:
            continue
        if "brochure" in combined:
            return absolute
        fallback = fallback or absolute
    return fallback


def parse_product_html(html_content: str, source_url: str) -> dict | None:
    if not is_accepted_url(source_url):
        return None

    soup = clean_soup(BeautifulSoup(html_content, "html.parser"))
    plan_name = PLAN_NAME_BY_PATH[source_path(source_url)]
    description = (
        intro_paragraph(soup)
        or meta_content(soup, 'meta[name="description"]')
        or meta_content(soup, 'meta[property="og:description"]')
    )
    benefits = highlight_blocks(soup)
    overview = " ".join([description, *benefits[:4]]).strip()

    return {
        "plan_name": plan_name,
        "plan_benefits": benefits,
        "plan_description": description[:500],
        "plan_overview": overview[:1200],
        "plan_url": source_url,
        "product_brochure_url": first_brochure_url(soup, source_url),
    }


def scrape_page(url: str, session=requests) -> list[dict]:
    row = parse_product_html(fetch_html(url, session=session), url)
    return [row] if row else []


async def scrape_data(url: str):
    return await asyncio.to_thread(scrape_page, url)


async def run_all_tasks(scrape_list: list[str]) -> list[dict]:
    return await gather_scrape_results(TABLE_NAME, scrape_list, scrape_data)


def assert_semantic_quality(rows: list[dict]) -> None:
    findings = validate_plan_rows(format_plan_rows(TABLE_NAME, rows))
    if findings:
        raise ValueError(findings[0].format())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.parse_known_args()

    rows = asyncio.run(run_all_tasks(PRODUCT_URLS))
    print(f"[{TABLE_NAME}] produced {len(rows)} plan rows")
    assert_semantic_quality(rows)
    if not rows:
        record_scraper_failure(TABLE_NAME, "no plan rows produced")
        return
    initialize_data_store()
    overwrite_plans_for_insurer(TABLE_NAME, rows)


if __name__ == "__main__":
    main()
