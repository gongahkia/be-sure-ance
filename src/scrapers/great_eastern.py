"""
GREAT EASTERN

https://www.greateasternlife.com/sg/en/about-us.html

https://www.greateasternlife.com/sg/en/personal-insurance/our-products/life-insurance.html
https://www.greateasternlife.com/sg/en/personal-insurance/our-products/health-insurance.html
https://www.greateasternlife.com/sg/en/personal-insurance/our-products/personal-accident-insurance.html
https://www.greateasternlife.com/sg/en/personal-insurance/our-products/retirement-income.html
https://www.greateasternlife.com/sg/en/personal-insurance/our-products/wealth-accumulation.html
https://www.greateasternlife.com/sg/en/personal-insurance/our-products/travel-insurance/travelsmart-premier.html
https://www.greateasternlife.com/sg/en/personal-insurance/our-products/car-insurance.html
https://www.greateasternlife.com/sg/en/personal-insurance/our-products/home-insurance/great-home-protect.html
https://www.greateasternlife.com/sg/en/personal-insurance/our-products/maid-insurance/great-maid-protect.html
https://www.greateasternlife.com/sg/en/personal-insurance/our-products/life-insurance/dependants-protection-scheme.html
https://www.greateasternlife.com/sg/en/campaigns/great-legacy-programme.html
https://www.greateasternlife.com/sg/en/personal-insurance/our-products/prestige-series.html
"""

from __future__ import annotations

import argparse
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

TABLE_NAME = "great_eastern"
BASE_URL = "https://www.greateasternlife.com"
REQUEST_TIMEOUT_SECONDS = 20

CATEGORY_URLS = (
    "https://www.greateasternlife.com/sg/en/personal-insurance/our-products/life-insurance.html",
    "https://www.greateasternlife.com/sg/en/personal-insurance/our-products/health-insurance.html",
    "https://www.greateasternlife.com/sg/en/personal-insurance/our-products/personal-accident-insurance.html",
    "https://www.greateasternlife.com/sg/en/personal-insurance/our-products/retirement-income.html",
    "https://www.greateasternlife.com/sg/en/personal-insurance/our-products/wealth-accumulation.html",
    "https://www.greateasternlife.com/sg/en/personal-insurance/our-products/car-insurance.html",
    "https://www.greateasternlife.com/sg/en/personal-insurance/our-products/prestige-series.html",
)

DIRECT_PRODUCT_URLS = (
    "https://www.greateasternlife.com/sg/en/personal-insurance/our-products/travel-insurance/great-travelcare.html",
    "https://www.greateasternlife.com/sg/en/personal-insurance/our-products/home-insurance/great-home-protect.html",
    "https://www.greateasternlife.com/sg/en/personal-insurance/our-products/maid-insurance/great-maid-protect.html",
    "https://www.greateasternlife.com/sg/en/personal-insurance/our-products/life-insurance/dependants-protection-scheme.html",
    "https://www.greateasternlife.com/sg/en/personal-insurance/our-products/life-insurance/prestige-legacy-index.html",
)

PRODUCT_CATEGORY_SEGMENTS = {
    "car-insurance",
    "health-insurance",
    "home-insurance",
    "life-insurance",
    "maid-insurance",
    "personal-accident-insurance",
    "retirement-income",
    "travel-insurance",
    "wealth-accumulation",
}

REJECTED_SOURCE_URLS = (
    "https://www.greateasternlife.com/sg/en/about-us.html",
    "https://www.greateasternlife.com/sg/en/campaigns/great-legacy-programme.html",
    "https://www.greateasternlife.com/sg/en/personal-insurance/our-products/health-insurance/great-careshield/gcs-benefit.html",
)

CHROME_PATTERNS = (
    "about us",
    "buying a product",
    "contact details",
    "enter contact details",
    "external link notification",
    "financial representative",
    "how can we help",
    "life and health",
    "national schemes",
    "need help buying",
    "personal data protection",
    "prestige series",
    "privacy and security policy",
    "promotions and events",
    "terms of use",
    "view product brochure",
    "wealth accumulation retirement income",
)

NON_PRODUCT_PATTERNS = (
    "all fields are mandatory",
    "all information provided on this website",
    "by submitting this form",
    "campaign code",
    "check out products that supplement",
    "customer service",
    "download form",
    "enhance your coverage",
    "important notes",
    "learn about product need help",
    "leave us a message",
    "limited time promotion",
    "limited-time promotion",
    "region upgrade campaign",
    "product name i would like",
    "promotion ends",
    "terms and conditions apply",
    "use the great eastern app",
    "your questions answered",
)

SECTION_LABELS = {
    "key benefits",
    "wealth",
    "lifestyle",
    "national schemes",
    "prestige series",
}

BENEFIT_KEYWORDS = (
    "accident",
    "benefit",
    "bonus",
    "capital",
    "cash",
    "claim",
    "cover",
    "coverage",
    "critical",
    "death",
    "disability",
    "guaranteed",
    "home",
    "hospital",
    "income",
    "medical",
    "payout",
    "premium",
    "protection",
    "reimbursement",
    "retirement",
    "savings",
    "travel",
)

BROCHURE_ALLOW_TERMS = (
    "brochure",
    "product brochure",
)

BROCHURE_REJECT_TERMS = (
    "application",
    "authorisation",
    "change-payment",
    "form",
    "guide",
    "lia.org.sg",
    "moh.gov.sg",
    "msf.gov.sg",
    "nomination",
    "proposal",
    "tnc",
)


def normalize_url(url: str) -> str:
    return urldefrag(str(url or "").strip()).url


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


def is_product_detail_url(url: str) -> bool:
    parsed = urlparse(normalize_url(url))
    if parsed.netloc != "www.greateasternlife.com":
        return False
    segments = [segment for segment in parsed.path.split("/") if segment]
    try:
        category_index = segments.index("our-products") + 1
    except ValueError:
        return False
    if category_index >= len(segments):
        return False
    category = segments[category_index]
    if category not in PRODUCT_CATEGORY_SEGMENTS:
        return False
    if len(segments) <= category_index + 1:
        return False
    return segments[-1].endswith(".html")


def discover_product_urls(
    session=requests,
    category_urls: tuple[str, ...] | list[str] = CATEGORY_URLS,
    direct_product_urls: tuple[str, ...] | list[str] = DIRECT_PRODUCT_URLS,
) -> list[str]:
    product_urls = []
    for product_url in direct_product_urls:
        normalized = normalize_url(product_url)
        if is_product_detail_url(normalized) and normalized not in product_urls:
            product_urls.append(normalized)

    for category_url in category_urls:
        try:
            soup = BeautifulSoup(fetch_html(category_url, session=session), "html.parser")
        except Exception as exc:
            print(f"[{TABLE_NAME}] skipping discovery {category_url}: {exc}")
            continue
        for card in soup.select(".leo-card"):
            anchor = card.select_one("a[href]")
            if not anchor:
                continue
            href = normalize_url(urljoin(category_url, anchor.get("href") or ""))
            if is_product_detail_url(href) and href not in product_urls:
                product_urls.append(href)
    return product_urls


def parse_product_html(html: str, url: str) -> dict | None:
    source_url = normalize_url(url)
    if source_url in REJECTED_SOURCE_URLS or not is_product_detail_url(source_url):
        return None

    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    if "404" in title:
        return None

    content = scoped_content(soup)
    plan_name = clean_plan_name(plan_title(soup, content, title))
    if not plan_name:
        return None

    description = (
        clean_description(meta_content(soup, 'meta[name="description"]'))
        or clean_description(meta_content(soup, 'meta[property="og:description"]'))
        or first_content_paragraph(content)
    )
    blocks = content_blocks(content)
    overview_blocks = [
        block for block in blocks if block != description and plan_name.lower() not in block.lower()
    ][:3]

    return {
        "plan_name": plan_name,
        "plan_benefits": benefit_blocks(blocks),
        "plan_description": description,
        "plan_overview": compact_text(" ".join(overview_blocks)),
        "plan_url": source_url,
        "product_brochure_url": brochure_url(soup, source_url),
    }


def scoped_content(soup: BeautifulSoup) -> BeautifulSoup:
    content = soup.select_one("main") or soup
    for element in content.select(
        "script, style, noscript, svg, form, header, footer, nav, [role='navigation']"
    ):
        element.decompose()
    return content


def plan_title(soup: BeautifulSoup, content: BeautifulSoup, fallback_title: str) -> str:
    h1 = content.find("h1") or soup.find("h1")
    if h1:
        return normalize_whitespace(h1.get_text(" ", strip=True))
    title = normalize_whitespace(fallback_title)
    for separator in (" | ", " - ", " – "):
        if separator in title:
            return title.split(separator, 1)[0]
    return title


def clean_plan_name(name: str) -> str:
    parts = [part.strip() for part in normalize_whitespace(name).split("|")]
    parts = [part for part in parts if part and "great eastern" not in part.lower()]
    return " | ".join(parts)


def meta_content(soup: BeautifulSoup, selector: str) -> str:
    element = soup.select_one(selector)
    return normalize_whitespace(element.get("content")) if element else ""


def clean_description(description: str) -> str:
    description = compact_text(description, limit=500)
    return description if is_content_text(description) else ""


def first_content_paragraph(content: BeautifulSoup) -> str:
    for element in content.find_all("p"):
        text = normalize_whitespace(element.get_text(" ", strip=True))
        if is_content_text(text):
            return text
    return ""


def content_blocks(content: BeautifulSoup) -> list[str]:
    blocks = []
    seen = set()
    for element in content.find_all(["h2", "h3", "h4", "p", "li"], limit=260):
        text = normalize_whitespace(element.get_text(" ", strip=True))
        if not is_content_text(text) or text in seen:
            continue
        seen.add(text)
        blocks.append(text)
    return blocks


def is_content_text(text: str) -> bool:
    lowered = normalize_whitespace(text).lower()
    if len(text) < 18 or len(text) > 700:
        return False
    if lowered in SECTION_LABELS:
        return False
    if any(pattern in lowered for pattern in CHROME_PATTERNS):
        return False
    return not any(pattern in lowered for pattern in NON_PRODUCT_PATTERNS)


def benefit_blocks(blocks: list[str]) -> list[str]:
    benefits = []
    for block in blocks:
        lowered = block.lower()
        if len(block) > 190:
            continue
        if any(keyword in lowered for keyword in BENEFIT_KEYWORDS):
            benefits.append(block)
    return benefits[:8]


def brochure_url(soup: BeautifulSoup, source_url: str) -> str:
    candidates = []
    for anchor in soup.select("a[href]"):
        href = anchor.get("href") or ""
        href_text = normalize_whitespace(anchor.get_text(" ", strip=True))
        haystack = f"{href_text} {href}".lower()
        if ".pdf" not in href.lower():
            continue
        if not any(term in haystack for term in BROCHURE_ALLOW_TERMS):
            continue
        if any(term in haystack for term in BROCHURE_REJECT_TERMS):
            continue
        score = 0 if "product brochure" in haystack else 1
        candidates.append((score, urljoin(source_url, href)))
    if not candidates:
        return ""
    return sorted(candidates, key=lambda item: item[0])[0][1]


def compact_text(text: str, limit: int = 900) -> str:
    text = normalize_whitespace(text)
    return text if len(text) <= limit else f"{text[: limit - 3].rstrip()}..."


def dedupe_rows(rows: list[dict]) -> list[dict]:
    deduped = []
    seen_urls = set()
    seen_names = set()
    for row in rows:
        key = normalize_url(row.get("plan_url"))
        name = normalize_whitespace(row.get("plan_name")).lower()
        if not key or key in seen_urls or name in seen_names:
            continue
        seen_urls.add(key)
        seen_names.add(name)
        deduped.append(row)
    return deduped


def scrape_great_eastern(
    session=requests,
    category_urls: tuple[str, ...] | list[str] = CATEGORY_URLS,
    direct_product_urls: tuple[str, ...] | list[str] = DIRECT_PRODUCT_URLS,
) -> list[dict]:
    rows = []
    for product_url in discover_product_urls(
        session=session,
        category_urls=category_urls,
        direct_product_urls=direct_product_urls,
    ):
        try:
            row = parse_product_html(fetch_html(product_url, session=session), product_url)
        except Exception as exc:
            print(f"[{TABLE_NAME}] skipping product {product_url}: {exc}")
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
        raise ValueError(f"Great Eastern scraper produced invalid plan rows: {details}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    try:
        rows = scrape_great_eastern()
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
