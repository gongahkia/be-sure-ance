from __future__ import annotations

import argparse
import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from src.backend.helper import initialize_data_store, overwrite_plans_for_insurer
from src.lib.http_identity import BOT_USER_AGENT
from src.lib.scraper_health import record_scraper_failure

REQUEST_TIMEOUT_SECONDS = 20
PLAN_KEYWORDS = (
    "accident",
    "benefit",
    "claim",
    "cover",
    "critical",
    "health",
    "home",
    "insurance",
    "life",
    "maid",
    "medical",
    "motor",
    "protection",
    "travel",
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


def meta_content(soup: BeautifulSoup, selector: str) -> str:
    element = soup.select_one(selector)
    return normalize_whitespace(element.get("content")) if element else ""


def clean_title(value: str) -> str:
    title = normalize_whitespace(value)
    for separator in (" | ", " - "):
        if separator in title:
            title = title.split(separator, 1)[0]
    return title


def page_title(soup: BeautifulSoup) -> str:
    title = meta_content(soup, 'meta[property="og:title"]')
    if not title and soup.find("h1"):
        title = soup.find("h1").get_text(" ", strip=True)
    if not title and soup.title:
        title = soup.title.get_text(" ", strip=True)
    return clean_title(title)


def first_pdf_url(soup: BeautifulSoup, source_url: str) -> str:
    for anchor in soup.select("a[href]"):
        href = anchor.get("href") or ""
        if ".pdf" in href.lower():
            return urljoin(source_url, href)
    return ""


def page_blocks(soup: BeautifulSoup) -> list[str]:
    blocks = []
    seen = set()
    for element in soup.find_all(["h2", "h3", "p", "li"], limit=180):
        text = normalize_whitespace(element.get_text(" ", strip=True))
        if len(text) < 8 or text in seen:
            continue
        seen.add(text)
        blocks.append(text)
    return blocks


def parse_static_product_page(url: str, session=requests) -> dict | None:
    soup = BeautifulSoup(fetch_html(url, session=session), "html.parser")
    title = page_title(soup)
    if not title or title.lower() in {"home", "products", "insurance"}:
        return None

    description = (
        meta_content(soup, 'meta[name="description"]')
        or meta_content(soup, 'meta[property="og:description"]')
    )
    blocks = page_blocks(soup)
    benefits = [
        block
        for block in blocks
        if any(keyword in block.lower() for keyword in PLAN_KEYWORDS)
    ][:8]
    overview_blocks = [block for block in blocks if block != title][:4]

    return {
        "plan_name": title,
        "plan_benefits": benefits,
        "plan_description": description or (overview_blocks[0] if overview_blocks else ""),
        "plan_overview": " ".join(overview_blocks),
        "plan_url": url,
        "product_brochure_url": first_pdf_url(soup, url),
    }


def scrape_static_product_pages(urls: list[str], session=requests) -> list[dict]:
    rows = []
    seen = set()
    for url in urls:
        row = parse_static_product_page(url, session=session)
        if not row:
            continue
        key = row["plan_url"]
        if key in seen:
            continue
        seen.add(key)
        rows.append(row)
    return rows


def run_static_product_scraper(table_name: str, urls: list[str]) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args, _ = parser.parse_known_args()
    rows = scrape_static_product_pages(urls)
    print(f"[{table_name}] produced {len(rows)} plan rows")
    if args.dry_run:
        return
    if not rows:
        record_scraper_failure(table_name, "no plan rows produced")
        return
    initialize_data_store()
    overwrite_plans_for_insurer(table_name, rows)
