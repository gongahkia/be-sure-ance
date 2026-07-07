"""
SUN LIFE

https://www.sunlife.com.sg/en/

https://www.sunlife.com.sg/en/product-solutions/life-insurance/
https://www.sunlife.com.sg/en/product-solutions/indexed-universal-life/
"""

from __future__ import annotations

import argparse
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

TABLE_NAME = "sunlife"
REQUEST_TIMEOUT_SECONDS = 20

CANONICAL_PLAN_NAMES = {
    "https://www.sunlife.com.sg/en/product-solutions/life-insurance/": ("SunBrilliance Whole Life"),
    "https://www.sunlife.com.sg/en/product-solutions/indexed-universal-life/": (
        "SunBrilliance Indexed Universal Life II"
    ),
}

PRODUCT_URLS = tuple(CANONICAL_PLAN_NAMES)
REJECTED_SOURCE_URLS = ("https://www.sunlife.com.sg/en/",)

CHROME_PATTERNS = (
    "about us",
    "additional details",
    "client complaint",
    "contact us",
    "distributor portal",
    "faqs on",
    "get more bright ideas",
    "insights",
    "personal information collection statement",
    "product solutions",
    "related documents",
)

NON_PRODUCT_PATTERNS = (
    "campaign is valid",
    "download brochure",
    "learn more",
    "peace of mind",
    "premium discount campaign",
    "premium top up campaign",
    "we're looking for",
    "your name",
)

BENEFIT_KEYWORDS = (
    "benefit",
    "cash",
    "coverage",
    "death",
    "flexibility",
    "growth",
    "guaranteed",
    "legacy",
    "lifetime",
    "premium",
    "protection",
)


def normalize_url(url: str) -> str:
    clean_url = urldefrag(str(url or "").strip()).url
    return clean_url if clean_url.endswith("/") else f"{clean_url}/"


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


def parse_product_html(html: str, url: str) -> dict | None:
    source_url = normalize_url(url)
    if source_url in REJECTED_SOURCE_URLS or source_url not in CANONICAL_PLAN_NAMES:
        return None

    soup = BeautifulSoup(html, "html.parser")
    plan_name = CANONICAL_PLAN_NAMES[source_url]
    description = product_description(soup)
    benefits = benefit_blocks(soup)

    return {
        "plan_name": plan_name,
        "plan_benefits": benefits,
        "plan_description": description,
        "plan_overview": compact_text(" ".join(benefits[:3])),
        "plan_url": source_url,
        "product_brochure_url": brochure_url(soup, source_url),
    }


def product_description(soup: BeautifulSoup) -> str:
    for element in soup.select(".text.aem-GridColumn.aem-GridColumn--default--12"):
        text = compact_text(element.get_text(" ", strip=True), limit=500)
        if text.lower().startswith(("key benefits", "related documents", "additional details")):
            continue
        if "sunbrilliance" in text.lower():
            return text
        if is_content_text(text):
            return text
    return ""


def benefit_blocks(soup: BeautifulSoup) -> list[str]:
    benefits = []
    seen = set()
    for element in soup.select("div.card-body"):
        text = normalize_whitespace(element.get_text(" ", strip=True))
        lowered = text.lower()
        if text in seen or not is_content_text(text) or len(text) > 260:
            continue
        if any(keyword in lowered for keyword in BENEFIT_KEYWORDS):
            benefits.append(text)
            seen.add(text)
    return benefits[:8]


def brochure_url(soup: BeautifulSoup, source_url: str) -> str:
    for anchor in soup.select("a[href]"):
        href = anchor.get("href") or ""
        text = normalize_whitespace(anchor.get_text(" ", strip=True)).lower()
        if ".pdf" not in href.lower():
            continue
        if "download brochure" not in text:
            continue
        if "chinese" in text or "simplified" in text:
            continue
        return urljoin(source_url, href)
    return ""


def is_content_text(text: str) -> bool:
    lowered = normalize_whitespace(text).lower()
    if len(lowered) < 20 or len(lowered) > 900:
        return False
    if any(pattern in lowered for pattern in CHROME_PATTERNS):
        return False
    return not any(pattern in lowered for pattern in NON_PRODUCT_PATTERNS)


def compact_text(text: str, limit: int = 900) -> str:
    text = normalize_whitespace(text)
    return text if len(text) <= limit else f"{text[: limit - 3].rstrip()}..."


def dedupe_rows(rows: list[dict]) -> list[dict]:
    deduped = []
    seen = set()
    for row in rows:
        key = (
            normalize_whitespace(row.get("plan_name")).lower(),
            normalize_url(row.get("plan_url")),
        )
        if not all(key) or key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def scrape_sunlife(session=requests) -> list[dict]:
    rows = []
    for url in PRODUCT_URLS:
        try:
            row = parse_product_html(fetch_html(url, session=session), url)
        except Exception as exc:
            print(f"[{TABLE_NAME}] skipping product {url}: {exc}")
            continue
        if row:
            rows.append(row)
    return dedupe_rows(rows)


async def scrape_data(url):
    row = parse_product_html(fetch_html(url), url)
    return [row] if row else []


async def run_all_tasks(scrape_list):
    return await gather_scrape_results(TABLE_NAME, scrape_list, scrape_data)


def assert_semantic_quality(rows: list[dict]) -> None:
    findings = validate_plan_rows(format_plan_rows(TABLE_NAME, rows))
    if findings:
        details = "; ".join(finding.format() for finding in findings[:5])
        raise ValueError(f"Sun Life scraper produced invalid plan rows: {details}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    try:
        rows = scrape_sunlife()
        assert_semantic_quality(rows)
    except Exception as error:
        if not args.dry_run:
            record_scraper_failure(TABLE_NAME, error)
        raise

    print(f"[{TABLE_NAME}] produced {len(rows)} plan rows")
    if args.dry_run:
        overwrite_plans_for_insurer(TABLE_NAME, rows)
        return 0
    if not rows:
        record_scraper_failure(TABLE_NAME, "no plan rows produced")
        return 1

    initialize_data_store()
    overwrite_plans_for_insurer(TABLE_NAME, rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
