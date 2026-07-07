"""
NTUC INCOME

https://www.income.com.sg/
https://www.income.com.sg/claims/life-insurance
https://www.income.com.sg/claims/health-and-personal-accident
https://www.income.com.sg/claims/i50-insurance-claims
https://www.income.com.sg/claims/motor-insurance
https://www.income.com.sg/claims/travel-claims
https://www.income.com.sg/health-insurance
https://www.income.com.sg/claims/domestic-helper-insurance-claims
https://www.income.com.sg/claims/home-insurance-claims
https://www.income.com.sg/claims/overseas-study-protection-plan-claims
https://www.income.com.sg/claims/golfers-insurance-claims
https://www.income.com.sg/claims/group-insurance
https://www.income.com.sg/claims/commercial-insurance
https://www.income.com.sg/claims/claims-statistics
https://www.income.com.sg/claims/unclaimed-policies
https://www.income.com.sg/health-insurance
https://www.income.com.sg/personal-accident-insurance
https://www.income.com.sg/life-insurance
https://www.income.com.sg/travel-insurance
https://www.income.com.sg/drivo-car-insurance
https://www.income.com.sg/savings-and-investments
https://www.income.com.sg/enhanced-home-insurance
https://www.income.com.sg/domestic-helper-insurance
https://www.income.com.sg/group-insurance-for-employees
https://www.income.com.sg/commercial-insurance
https://www.income.com.sg/group-insurance-for-schools-and-centres-and-moe
https://www.income.com.sg/promotions/motorcycle-insurance-promotion
https://www.income.com.sg/happy-tails-pet-insurance
"""

from __future__ import annotations

import argparse
import asyncio
import re
from urllib.parse import urldefrag, urljoin, urlparse

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

TABLE_NAME = "income"
REQUEST_TIMEOUT_SECONDS = 20

LISTING_URLS = (
    "https://www.income.com.sg/health-insurance",
    "https://www.income.com.sg/personal-accident-insurance",
    "https://www.income.com.sg/life-insurance",
    "https://www.income.com.sg/savings-and-investments",
    "https://www.income.com.sg/group-insurance-for-employees",
    "https://www.income.com.sg/commercial-insurance",
)

DIRECT_PRODUCT_URLS = (
    "https://www.income.com.sg/travel-insurance",
    "https://www.income.com.sg/enhanced-prex-travel-insurance",
    "https://www.income.com.sg/drivo-car-insurance",
    "https://www.income.com.sg/edrivo-car-insurance",
    "https://www.income.com.sg/motorcycle-insurance",
    "https://www.income.com.sg/enhanced-home-insurance",
    "https://www.income.com.sg/domestic-helper-insurance",
    "https://www.income.com.sg/happy-tails-pet-insurance",
    "https://www.income.com.sg/overseas-study-protection-plan",
    "https://www.income.com.sg/home-ultimate-protect",
)

REJECTED_SOURCE_URLS = (
    "https://www.income.com.sg/",
    "https://www.income.com.sg/claims/life-insurance",
    "https://www.income.com.sg/claims/health-and-personal-accident",
    "https://www.income.com.sg/claims/i50-insurance-claims",
    "https://www.income.com.sg/claims/motor-insurance",
    "https://www.income.com.sg/claims/travel-claims",
    "https://www.income.com.sg/claims/domestic-helper-insurance-claims",
    "https://www.income.com.sg/claims/home-insurance-claims",
    "https://www.income.com.sg/claims/overseas-study-protection-plan-claims",
    "https://www.income.com.sg/claims/golfers-insurance-claims",
    "https://www.income.com.sg/claims/group-insurance",
    "https://www.income.com.sg/claims/commercial-insurance",
    "https://www.income.com.sg/claims/claims-statistics",
    "https://www.income.com.sg/claims/unclaimed-policies",
    "https://www.income.com.sg/promotions/motorcycle-insurance-promotion",
)

EXCLUDED_PATH_PARTS = (
    "/buy/",
    "/claims/",
    "/forms/",
    "/fund-prices",
    "/promotions/",
    "/support",
)

LISTING_PATHS = {urlparse(url).path.rstrip("/") for url in LISTING_URLS}

CHROME_PATTERNS = (
    "about income",
    "advisor icon",
    "back to top",
    "buy now",
    "compare plans",
    "contact us",
    "download my income app",
    "filter",
    "income representative search",
    "let us help you",
    "log in",
    "make a claim",
    "my income",
    "promotions",
    "security advisory",
    "select category",
    "speak with an advisor",
    "useful links",
    "vulnerability disclosure",
    "what would you like to compare",
)

STOP_HEADING_PATTERNS = (
    "back to top",
    "by needs",
    "exclusions",
    "filter",
    "footnotes",
    "frequently asked questions",
    "important notes",
    "learn more about",
    "let us help you",
    "understand the details",
    "what would you like to compare",
    "your policy toolkit",
    "your queries answered",
)

BROCHURE_REJECT_PATTERNS = (
    "claim",
    "emergency",
    "forms",
    "handbook",
    "policy-condition",
    "policy conditions",
    "policy wording",
    "renewal bonus",
    "service",
    "table",
    "terms",
    "workshop",
)

CATEGORY_LABELS = (
    "car insurance",
    "commercial insurance",
    "health insurance",
    "home insurance",
    "life insurance",
    "maid insurance",
    "motorcycle insurance",
    "personal accident insurance",
    "pet insurance",
    "savings & investments",
    "travel insurance",
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


def is_income_product_url(url: str) -> bool:
    parsed = urlparse(normalize_url(url))
    if parsed.netloc != "www.income.com.sg":
        return False
    path = parsed.path.rstrip("/")
    if not path or path in LISTING_PATHS:
        return False
    if any(part in path for part in EXCLUDED_PATH_PARTS):
        return False
    return True


def discover_product_urls(
    session=requests,
    listing_urls: tuple[str, ...] | list[str] = LISTING_URLS,
) -> list[str]:
    urls = []
    for direct_url in DIRECT_PRODUCT_URLS:
        if is_income_product_url(direct_url):
            urls.append(normalize_url(direct_url))
    for listing_url in listing_urls:
        try:
            soup = BeautifulSoup(fetch_html(listing_url, session=session), "html.parser")
        except Exception as exc:
            print(f"[{TABLE_NAME}] skipping discovery {listing_url}: {exc}")
            continue
        for anchor in soup.select("a[href]"):
            label = normalize_whitespace(anchor.get_text(" ", strip=True)).lower()
            href = normalize_url(urljoin(listing_url, anchor.get("href") or ""))
            if label != "learn more" or not is_income_product_url(href):
                continue
            if href not in urls:
                urls.append(href)
    return urls


def parse_product_html(html: str, url: str) -> dict | None:
    source_url = normalize_url(url)
    if not is_income_product_url(source_url):
        return None

    soup = BeautifulSoup(html, "html.parser")
    if is_404(soup):
        return None

    title = plan_title(soup)
    if not title:
        return None
    blocks = content_blocks_after_title(soup)
    description = meta_description(soup) or first_description(blocks)
    if not description:
        return None
    benefits = benefit_blocks(blocks, description)
    row = {
        "plan_name": title,
        "plan_benefits": benefits[:8] or [description],
        "plan_description": compact_text(description, 420),
        "plan_overview": compact_text(" ".join([description, *benefits[:4]]), 760),
        "plan_url": source_url,
        "product_brochure_url": brochure_url(soup, source_url),
    }
    return row if valid_plan_row(row) else None


def is_404(soup: BeautifulSoup) -> bool:
    title = normalize_whitespace(soup.title.get_text(" ", strip=True) if soup.title else "")
    h1 = normalize_whitespace(
        soup.select_one("h1").get_text(" ", strip=True) if soup.select_one("h1") else ""
    )
    return title == "404" or h1 == "404" or "page not found" in title.lower()


def plan_title(soup: BeautifulSoup) -> str:
    node = soup.select_one("h1")
    title = normalize_whitespace(node.get_text(" ", strip=True) if node else "")
    if title.lower() == "life insurance":
        return "Life Insurance"
    return title


def meta_description(soup: BeautifulSoup) -> str:
    for selector in ('meta[name="description"]', 'meta[property="og:description"]'):
        element = soup.select_one(selector)
        text = normalize_whitespace(element.get("content", "") if element else "")
        if is_content_text(text, max_length=500):
            return text
    return ""


def content_blocks_after_title(soup: BeautifulSoup) -> list[str]:
    title = plan_title(soup)
    h1 = soup.select_one("h1")
    nodes = h1.find_all_next(["h2", "h3", "h4", "p", "li"]) if h1 else []
    blocks = []
    for node in nodes:
        text = normalize_whitespace(node.get_text(" ", strip=True))
        if node.name in {"h2", "h3", "h4"} and is_stop_heading(text):
            break
        if not is_content_text(text):
            continue
        if text == title or text.lower() in CATEGORY_LABELS:
            continue
        if text not in blocks:
            blocks.append(text)
    return blocks


def first_description(blocks: list[str]) -> str:
    for block in blocks:
        if len(block) >= 35:
            return block
    return blocks[0] if blocks else ""


def benefit_blocks(blocks: list[str], description: str) -> list[str]:
    benefits = []
    for block in blocks:
        if block == description:
            continue
        if len(block) < 12:
            continue
        if block not in benefits:
            benefits.append(block)
    return benefits


def brochure_url(soup: BeautifulSoup, source_url: str) -> str:
    for anchor in soup.select("a[href]"):
        href = anchor.get("href") or ""
        absolute = urljoin(source_url, href)
        lowered = f"{href} {anchor.get_text(' ', strip=True)}".lower()
        if ".pdf" not in absolute.lower():
            continue
        if any(pattern in lowered for pattern in BROCHURE_REJECT_PATTERNS):
            continue
        if "brochure" in lowered or "flyer" in lowered:
            return absolute
    return ""


def is_stop_heading(text: str) -> bool:
    lowered = text.lower()
    return any(pattern in lowered for pattern in STOP_HEADING_PATTERNS)


def is_content_text(text: str, max_length: int = 320) -> bool:
    if not text or len(text) > max_length:
        return False
    lowered = text.lower()
    if any(pattern in lowered for pattern in CHROME_PATTERNS):
        return False
    if lowered.startswith(("image", "select ", "i want to compare", "with")):
        return False
    if "©" in text or "uen " in lowered:
        return False
    return True


def compact_text(text: str, limit: int = 760) -> str:
    compacted = normalize_whitespace(text)
    if len(compacted) <= limit:
        return compacted
    return normalize_whitespace(compacted[:limit].rsplit(" ", 1)[0])


def valid_plan_row(row: dict) -> bool:
    if not row.get("plan_name") or not row.get("plan_url"):
        return False
    formatted = format_plan_rows(TABLE_NAME, [row])
    return validate_plan_rows(formatted) == []


def dedupe_rows(rows: list[dict]) -> list[dict]:
    seen = set()
    deduped = []
    for row in rows:
        key = normalize_url(row["plan_url"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def scrape_income(session=requests) -> list[dict]:
    rows = []
    for url in discover_product_urls(session=session):
        try:
            row = parse_product_html(fetch_html(url, session=session), url)
        except Exception as exc:
            print(f"[{TABLE_NAME}] skipping product {url}: {exc}")
            continue
        if row:
            rows.append(row)
    return dedupe_rows(rows)


def scrape_product_url(url: str, session=requests) -> list[dict]:
    row = parse_product_html(fetch_html(url, session=session), url)
    return [row] if row else []


async def scrape_data(url):
    return await asyncio.to_thread(scrape_product_url, url)


async def run_all_tasks(scrape_list):
    return await gather_scrape_results(TABLE_NAME, scrape_list, scrape_data)


def assert_semantic_quality(rows: list[dict]) -> None:
    findings = validate_plan_rows(format_plan_rows(TABLE_NAME, rows))
    if findings:
        details = "; ".join(finding.format() for finding in findings[:5])
        raise ValueError(f"Income scraper produced invalid plan rows: {details}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    try:
        rows = scrape_income()
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
