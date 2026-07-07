"""
CHINA LIFE

https://www.chinalife.com.sg/
https://www.chinalife.com.sg/forms
https://www.chinalife.com.sg/products/endowment-plans
https://www.chinalife.com.sg/products/legacy-planning
https://www.chinalife.com.sg/products/riders
https://www.chinalife.com.sg/products/retirement-annuity-plans
https://www.chinalife.com.sg/products/protection
"""

from __future__ import annotations

import argparse
import html
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

TABLE_NAME = "china_life"
BASE_URL = "https://www.chinalife.com.sg"
REQUEST_TIMEOUT_SECONDS = 20

CATEGORY_URLS = (
    "https://www.chinalife.com.sg/products/endowment-plans",
    "https://www.chinalife.com.sg/products/legacy-planning",
    "https://www.chinalife.com.sg/products/riders",
    "https://www.chinalife.com.sg/products/retirement-annuity-plans",
    "https://www.chinalife.com.sg/products/protection",
)

REJECTED_SOURCE_URLS = (
    "https://www.chinalife.com.sg/",
    "https://www.chinalife.com.sg/forms",
    *CATEGORY_URLS,
)

CHROME_PATTERNS = (
    "alert: please be aware",
    "china life (overseas) – macau",
    "china life (overseas) –hk",
    "customer care hotline",
    "distributed by our agency channel",
    "footer",
    "online enquiry",
    "privacy settings",
    "products legacy planning",
    "we use cookies",
)

BENEFIT_KEYWORDS = (
    "accident",
    "benefit",
    "bonus",
    "capital",
    "cash",
    "coverage",
    "critical",
    "death",
    "guarantee",
    "income",
    "maturity",
    "medical",
    "premium",
    "protection",
    "retirement",
    "waiver",
)


def normalize_url(url: str) -> str:
    return urldefrag(str(url or "").strip()).url.rstrip("/")


def normalize_whitespace(value: str | None) -> str:
    text = html.unescape(value or "")
    text = text.replace("\u00a0", " ").replace("Â", " ")
    text = text.replace("â", "–").replace("â", "'")
    return re.sub(r"\s+", " ", text).strip()


def remove_excess_newlines(inp):
    if not isinstance(inp, str):
        raise TypeError(f"Input must be type <string> but was type <{type(inp).__name__}>")
    return normalize_whitespace(re.sub(r"\n+", "\n", inp))


def remove_html_entities(inp):
    return normalize_whitespace(inp)


def fetch_html(url: str, session=requests) -> str:
    response = session.get(
        url,
        timeout=REQUEST_TIMEOUT_SECONDS,
        headers={"User-Agent": BOT_USER_AGENT},
    )
    response.raise_for_status()
    response.encoding = "utf-8"
    return response.text


def parse_listing_html(html_content: str, source_url: str) -> list[dict]:
    soup = BeautifulSoup(html_content, "html.parser")
    category = category_title(soup)
    rows = []
    for card in soup.select("div.col-12.col-lg-4.views-row"):
        anchor = card.select_one("span.field-content a[href]")
        if not anchor:
            continue
        plan_name = normalize_whitespace(anchor.get_text(" ", strip=True))
        plan_url = normalize_url(urljoin(BASE_URL, anchor.get("href") or ""))
        benefits = clean_blocks(
            item.get_text(" ", strip=True) for item in card.select("p.h7, p.h4, li")
        )
        if plan_name and plan_url:
            rows.append(
                {
                    "plan_name": plan_name,
                    "plan_url": plan_url,
                    "plan_description": category,
                    "plan_benefits": benefits,
                    "source_url": normalize_url(source_url),
                }
            )
    return rows


def parse_product_html(
    html_content: str,
    source_url: str,
    listing_row: dict | None = None,
) -> dict | None:
    url = normalize_url(source_url)
    if url in {normalize_url(rejected) for rejected in REJECTED_SOURCE_URLS}:
        return None
    soup = BeautifulSoup(html_content, "html.parser")
    plan_name = product_title(soup) or normalize_whitespace((listing_row or {}).get("plan_name"))
    if not plan_name or looks_like_chrome(plan_name):
        return None

    listing_benefits = list((listing_row or {}).get("plan_benefits") or [])
    summary = product_summary(soup)
    if not summary:
        summary = direct_product_summary(soup, plan_name)
    if not summary and listing_row:
        summary = f"{plan_name} is a China Life Singapore {listing_row['plan_description']} plan."
    benefits = dedupe_texts([*product_features(soup), *listing_benefits])[:8]
    description = compact_text(summary, 500)
    overview = compact_text(" ".join([summary, *benefits[:4]]), 900)
    row = {
        "plan_name": plan_name,
        "plan_benefits": benefits,
        "plan_description": description,
        "plan_overview": overview,
        "plan_url": url,
        "product_brochure_url": brochure_url(soup, url),
    }
    return row if valid_plan_row(row) else None


def category_title(soup: BeautifulSoup) -> str:
    for heading in soup.select("h1"):
        text = normalize_whitespace(heading.get_text(" ", strip=True))
        text = text.lstrip("– ").strip()
        if text and not looks_like_chrome(text):
            return text
    return ""


def product_title(soup: BeautifulSoup) -> str:
    selectors = (
        "h1.field--name-title",
        ".block-field-blocknodeproducttitle h1",
        "h1",
    )
    for selector in selectors:
        for heading in soup.select(selector):
            text = normalize_whitespace(heading.get_text(" ", strip=True))
            if text and text.lower() not in {"product features", "distributed by"}:
                return text
    if soup.title:
        return normalize_whitespace(soup.title.get_text(" ", strip=True).split("|", 1)[0])
    return ""


def product_summary(soup: BeautifulSoup) -> str:
    element = soup.select_one(".field--name-field-product-summary .field__item")
    if not element:
        return ""
    text = normalize_whitespace(element.get_text(" ", strip=True))
    return strip_prefix(text, "Product Summary")


def direct_product_summary(soup: BeautifulSoup, plan_name: str) -> str:
    main = soup.select_one("main")
    if not main:
        return ""
    text = normalize_whitespace(main.get_text(" ", strip=True))
    if plan_name not in text:
        return ""
    tail = text.split(plan_name, 1)[-1]
    tail = re.split(r"Online Enquiry|Call Us|Email Us|Product Summary", tail, maxsplit=1)[-1]
    sentences = re.split(r"(?<=[.!?])\s+", tail)
    cleaned = clean_blocks(sentences)
    return " ".join(cleaned[:3])


def product_features(soup: BeautifulSoup) -> list[str]:
    selectors = (
        ".field--name-field-product-icons p.h4",
        ".field--name-field-product-icons p",
        ".field--name-field-product-icons li",
    )
    values = []
    for selector in selectors:
        for element in soup.select(selector):
            text = normalize_whitespace(element.get_text(" ", strip=True))
            lowered = text.lower()
            if not is_content_text(text, max_length=220):
                continue
            if any(keyword in lowered for keyword in BENEFIT_KEYWORDS):
                values.append(text)
    return clean_blocks(values)


def brochure_url(soup: BeautifulSoup, source_url: str) -> str:
    candidates = []
    for anchor in soup.select("a[href]"):
        href = normalize_whitespace(anchor.get("href") or "")
        text = normalize_whitespace(anchor.get_text(" ", strip=True)).lower()
        if ".pdf" not in href.lower():
            continue
        absolute = urljoin(source_url, href)
        if "cn" in text or "chinese" in text or "%e4%" in href.lower():
            continue
        candidates.append((text, absolute))
    for text, absolute in candidates:
        domain = urlparse(absolute).netloc
        if "chinalife.com.sg" in domain and ("english" in text or "brochure" in absolute.lower()):
            return absolute
    for _text, absolute in candidates:
        if "chinalife.com.sg" in urlparse(absolute).netloc:
            return absolute
    return ""


def strip_prefix(text: str, prefix: str) -> str:
    if text.lower().startswith(prefix.lower()):
        return normalize_whitespace(text[len(prefix) :])
    return text


def clean_blocks(values) -> list[str]:
    output = []
    seen = set()
    for value in values:
        text = normalize_whitespace(value)
        key = text.lower()
        if not is_content_text(text, max_length=320) or key in seen:
            continue
        seen.add(key)
        output.append(text)
    return output


def valid_plan_row(row: dict) -> bool:
    if not row.get("plan_name") or not row.get("plan_url") or not row.get("plan_description"):
        return False
    values = (row.get("plan_name"), row.get("plan_description"), row.get("plan_overview"))
    return not any(looks_like_chrome(value) for value in values)


def is_content_text(text: str | None, max_length: int = 900) -> bool:
    normalized = normalize_whitespace(text)
    lowered = normalized.lower()
    if len(normalized) < 10 or len(normalized) > max_length:
        return False
    if lowered in {"product summary", "product features", "distributed by"}:
        return False
    return not looks_like_chrome(normalized)


def looks_like_chrome(value: str | None) -> bool:
    lowered = normalize_whitespace(value).lower()
    if not lowered:
        return False
    return any(pattern in lowered for pattern in CHROME_PATTERNS)


def compact_text(text: str | None, limit: int = 900) -> str:
    text = normalize_whitespace(text)
    return text if len(text) <= limit else f"{text[: limit - 3].rstrip()}..."


def dedupe_texts(values: list[str]) -> list[str]:
    output = []
    seen = set()
    for value in values:
        text = normalize_whitespace(value)
        key = text.lower()
        if not text or key in seen:
            continue
        seen.add(key)
        output.append(text)
    return output


def dedupe_rows(rows: list[dict]) -> list[dict]:
    output = []
    seen = set()
    for row in rows:
        key = (row.get("plan_name", "").lower(), normalize_url(row.get("plan_url", "")))
        if key in seen or not all(key):
            continue
        seen.add(key)
        output.append(row)
    return output


def scrape_category_url(url: str, session=requests) -> list[dict]:
    listing_rows = parse_listing_html(fetch_html(url, session=session), url)
    rows = []
    for listing_row in listing_rows:
        try:
            row = parse_product_html(
                fetch_html(listing_row["plan_url"], session=session),
                listing_row["plan_url"],
                listing_row=listing_row,
            )
        except Exception as exc:
            print(f"[{TABLE_NAME}] skipping detail {listing_row['plan_url']}: {exc}")
            row = None
        if row:
            rows.append(row)
    return rows


def scrape_china_life(session=requests) -> list[dict]:
    rows = []
    for url in CATEGORY_URLS:
        try:
            rows.extend(scrape_category_url(url, session=session))
        except Exception as exc:
            print(f"[{TABLE_NAME}] skipping category {url}: {exc}")
    return dedupe_rows(rows)


async def scrape_data(url):
    if normalize_url(url) not in {normalize_url(category) for category in CATEGORY_URLS}:
        return []
    return scrape_category_url(url)


async def run_all_tasks(scrape_list):
    return await gather_scrape_results(TABLE_NAME, scrape_list, scrape_data)


def assert_semantic_quality(rows: list[dict]) -> None:
    findings = validate_plan_rows(format_plan_rows(TABLE_NAME, rows))
    if findings:
        details = "; ".join(finding.format() for finding in findings[:5])
        raise ValueError(f"China Life scraper produced invalid plan rows: {details}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    try:
        rows = scrape_china_life()
        assert_semantic_quality(rows)
    except Exception as error:
        if not args.dry_run:
            record_scraper_failure(TABLE_NAME, error)
        raise

    print(f"[{TABLE_NAME}] produced {len(rows)} plan rows")
    if not rows:
        record_scraper_failure(TABLE_NAME, "no plan rows produced", dry_run=args.dry_run)
        return 1
    if not args.dry_run:
        initialize_data_store()
    overwrite_plans_for_insurer(TABLE_NAME, rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
