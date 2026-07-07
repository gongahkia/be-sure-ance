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

from __future__ import annotations

import argparse
import asyncio
import re
from urllib.parse import urldefrag, urljoin

import requests
from bs4 import BeautifulSoup

if __package__ in {None, ""}:
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.backend.helper import (
    format_plan_rows,
    initialize_data_store,
    overwrite_plans_for_insurer,
)
from src.lib.http_identity import BOT_USER_AGENT
from src.lib.scraper_health import record_scraper_failure
from src.scrapers.navigation import gather_scrape_results
from src.validation.plan_quality import validate_plan_rows

TABLE_NAME = "iii"
REQUEST_TIMEOUT_SECONDS = 20

PRODUCT_CATALOG = (
    (
        "Motor Insurance",
        "https://www.iii.com.sg/products/motor-insurance",
        "Comprehensive motor insurance for private and commercial vehicles.",
    ),
    (
        "Home Insurance",
        "https://www.iii.com.sg/products/home-insurance",
        "Home insurance for building, fixtures, fittings and contents.",
    ),
    (
        "Travel Insurance",
        "https://www.iii.com.sg/products/travel-insurance",
        "Travel insurance for overseas trips, medical emergencies and travel inconvenience.",
    ),
    (
        "Personal Accident Insurance",
        "https://www.iii.com.sg/products/personal-accident-insurance",
        "Personal accident cover for disability, death and medical expenses.",
    ),
    (
        "Maid Insurance",
        "https://www.iii.com.sg/products/maid-insurance",
        "Maid insurance and bond package for foreign domestic workers.",
    ),
    (
        "Pet Insurance",
        "https://www.iii.com.sg/products/pet-insurance",
        "Pet insurance for accidents and illness affecting eligible pets.",
    ),
    (
        "Marine Insurance",
        "https://www.iii.com.sg/products/marine-insurance",
        "Marine insurance for hull, cargo, oil and energy risks.",
    ),
    (
        "Property Insurance",
        "https://www.iii.com.sg/products/property-insurance",
        "Commercial property insurance for assets and business property risks.",
    ),
    (
        "Liability Insurance",
        "https://www.iii.com.sg/products/liability-insurance",
        "Liability insurance for professional indemnity, public liability and related risks.",
    ),
    (
        "Engineering Insurance",
        "https://www.iii.com.sg/products/engineering-insurance",
        "Engineering insurance for construction, erection, plant and machinery risks.",
    ),
    (
        "Surety Insurance",
        "https://www.iii.com.sg/products/surety-insurance",
        "Surety insurance for bonds and contractual performance obligations.",
    ),
    (
        "Motor Fleet Insurance",
        "https://www.iii.com.sg/products/motor-fleet-insurance",
        "Motor fleet insurance for commercial vehicle operations.",
    ),
    (
        "Reinsurance",
        "https://www.iii.com.sg/products/reinsurance",
        "Facultative reinsurance for property and regional commercial risks.",
    ),
)

PRODUCT_URLS = tuple(url for _name, url, _description in PRODUCT_CATALOG)
REJECTED_SOURCE_URLS = (
    "https://www.iii.com.sg/",
    "https://www.iii.com.sg/claims",
    "https://www.iii.com.sg/contact",
    "https://www.iii.com.sg/media",
    "https://www.iii.com.sg/about-us/profile",
)

CHROME_PATTERNS = (
    "agent login",
    "blog",
    "buy now",
    "careers",
    "compliance framework",
    "contact us",
    "customer and agent portal",
    "customer login",
    "download forms",
    "get support",
    "login",
    "make an enquiry",
    "quick links",
    'rated "a',
    "still have queries",
    "terms of use",
    "whistle blower",
)

STOP_HEADING_PATTERNS = (
    "customer and agent portal",
    "frequently asked questions",
    "how do i file",
    "how to file",
    "quick links",
    "still have queries",
)

PRICE_PATTERNS = (
    "from as low as",
    "from less than",
    "from s$",
)


def normalize_url(url: str) -> str:
    return urldefrag(str(url or "").strip()).url.rstrip("/")


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


def parse_product_html(html_content: str, source_url: str) -> dict | None:
    source_url = normalize_url(source_url)
    catalog = catalog_row_for_url(source_url)
    if not catalog:
        return None

    soup = BeautifulSoup(html_content, "html.parser")
    content = scoped_content(soup)
    plan_name = plan_title(content) or catalog["plan_name"]
    if plan_name != catalog["plan_name"]:
        plan_name = catalog["plan_name"]

    blocks = content_blocks(content)
    description = first_description(blocks) or catalog["plan_description"]
    benefits = benefit_blocks(content)
    if not benefits:
        benefits = [catalog["plan_description"]]
    overview_blocks = [
        block for block in blocks if block != description and not is_price_text(block)
    ][:4]
    overview = compact_text(" ".join([description, *overview_blocks]), 700)
    row = {
        "plan_name": plan_name,
        "plan_benefits": benefits[:8],
        "plan_description": compact_text(description, 420),
        "plan_overview": overview,
        "plan_url": source_url,
        "product_brochure_url": first_pdf_url(soup, source_url),
    }
    return row if valid_plan_row(row) else None


def scoped_content(soup: BeautifulSoup) -> BeautifulSoup:
    content = soup.select_one("#block-iii-content") or soup.select_one("main") or soup
    for element in content.select("script, style, noscript, svg, form, nav, footer, header"):
        element.decompose()
    for heading in list(content.find_all(["h2", "h3"])):
        text = normalize_whitespace(heading.get_text(" ", strip=True)).lower()
        if any(pattern in text for pattern in STOP_HEADING_PATTERNS):
            remove_from_here(heading)
            break
    return content


def remove_from_here(node) -> None:
    parent = node.parent
    if not parent:
        node.decompose()
        return
    children = list(parent.children)
    try:
        start_index = children.index(node)
    except ValueError:
        node.decompose()
        return
    for child in children[start_index:]:
        if getattr(child, "decompose", None):
            child.decompose()
        else:
            child.extract()


def plan_title(content: BeautifulSoup) -> str:
    node = content.select_one("h1")
    return normalize_whitespace(node.get_text(" ", strip=True) if node else "")


def content_blocks(content: BeautifulSoup) -> list[str]:
    blocks = []
    for node in content.select("h2, h3, p"):
        text = normalize_whitespace(node.get_text(" ", strip=True))
        if not is_content_text(text):
            continue
        if text == plan_title(content):
            continue
        if text not in blocks:
            blocks.append(text)
    return blocks


def first_description(blocks: list[str]) -> str:
    for text in blocks:
        if is_price_text(text):
            continue
        if len(text) < 10:
            continue
        return text
    return ""


def benefit_blocks(content: BeautifulSoup) -> list[str]:
    benefits = []
    for node in content.select("li"):
        text = normalize_whitespace(node.get_text(" ", strip=True))
        if not is_content_text(text, max_length=180):
            continue
        if text not in benefits:
            benefits.append(text)
    return benefits


def first_pdf_url(soup: BeautifulSoup, source_url: str) -> str:
    for anchor in soup.select("a[href]"):
        href = anchor.get("href") or ""
        absolute = urljoin(source_url, href)
        lowered = f"{href} {anchor.get_text(' ', strip=True)}".lower()
        if ".pdf" not in absolute.lower():
            continue
        if "claim" in lowered or "form" in lowered:
            continue
        return absolute
    return ""


def is_content_text(text: str, max_length: int = 320) -> bool:
    if not text or len(text) > max_length:
        return False
    lowered = text.lower()
    if any(pattern in lowered for pattern in CHROME_PATTERNS):
        return False
    if lowered in {"home", "products", "other products", "india international insurance"}:
        return False
    if lowered.startswith(("image:", "skip to main content")):
        return False
    return True


def is_price_text(text: str) -> bool:
    lowered = text.lower()
    return any(pattern in lowered for pattern in PRICE_PATTERNS)


def compact_text(text: str, limit: int = 700) -> str:
    compacted = normalize_whitespace(text)
    if len(compacted) <= limit:
        return compacted
    return normalize_whitespace(compacted[:limit].rsplit(" ", 1)[0])


def valid_plan_row(row: dict) -> bool:
    if not row.get("plan_name") or not row.get("plan_url"):
        return False
    formatted = format_plan_rows(TABLE_NAME, [row])
    return validate_plan_rows(formatted) == []


def catalog_row_for_url(url: str) -> dict | None:
    normalized_url = normalize_url(url)
    for plan_name, plan_url, plan_description in PRODUCT_CATALOG:
        if normalize_url(plan_url) == normalized_url:
            return {
                "plan_name": plan_name,
                "plan_url": normalize_url(plan_url),
                "plan_description": plan_description,
            }
    return None


def scrape_page(url: str, session=requests) -> list[dict]:
    source_url = normalize_url(url)
    if source_url in {normalize_url(rejected) for rejected in REJECTED_SOURCE_URLS}:
        return []
    row = parse_product_html(fetch_html(source_url, session=session), source_url)
    return [row] if row else []


def scrape_iii(session=requests) -> list[dict]:
    rows = []
    for url in PRODUCT_URLS:
        try:
            rows.extend(scrape_page(url, session=session))
        except Exception as exc:
            print(f"[{TABLE_NAME}] skipping product {url}: {exc}")
            continue
    return rows


async def scrape_data(url):
    return await asyncio.to_thread(scrape_page, url)


async def run_all_tasks(scrape_list):
    return await gather_scrape_results(TABLE_NAME, scrape_list, scrape_data)


def assert_semantic_quality(rows: list[dict]) -> None:
    findings = validate_plan_rows(format_plan_rows(TABLE_NAME, rows))
    if findings:
        details = "; ".join(finding.format() for finding in findings[:5])
        raise ValueError(f"III scraper produced invalid plan rows: {details}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    try:
        rows = asyncio.run(run_all_tasks(PRODUCT_URLS))
        assert_semantic_quality(rows)
    except Exception as error:
        if not args.dry_run:
            record_scraper_failure(TABLE_NAME, error)
        raise

    print(f"[{TABLE_NAME}] produced {len(rows)} plan rows")
    if not rows:
        record_scraper_failure(TABLE_NAME, "no plan rows produced", dry_run=args.dry_run)
        return 1
    if args.dry_run:
        print(
            {
                "dry_run": True,
                "insurer": TABLE_NAME,
                "plan_row_count": len(rows),
                "sample_plan_names": [row["plan_name"] for row in rows[:5]],
            }
        )
        return 0
    initialize_data_store()
    overwrite_plans_for_insurer(TABLE_NAME, rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
