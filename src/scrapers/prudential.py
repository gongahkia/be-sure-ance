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
from src.validation.plan_quality import validate_plan_rows

TABLE_NAME = "prudential"
REQUEST_TIMEOUT_SECONDS = 20

CATEGORY_URLS = (
    "https://www.prudential.com.sg/products/health-insurance",
    "https://www.prudential.com.sg/products/health-insurance/medical-and-accident",
    "https://www.prudential.com.sg/products/health-insurance/medical",
    "https://www.prudential.com.sg/products/health-insurance/accident",
    "https://www.prudential.com.sg/products/health-insurance/critical-illness",
    "https://www.prudential.com.sg/products/life-insurance",
    "https://www.prudential.com.sg/products/life-insurance/whole-and-term-insurance",
    "https://www.prudential.com.sg/products/life-insurance/whole-life-insurance",
    "https://www.prudential.com.sg/products/life-insurance/term-life-insurance",
    "https://www.prudential.com.sg/products/life-insurance/maternity-insurance",
    "https://www.prudential.com.sg/products/life-insurance/mortgage-insurance",
    "https://www.prudential.com.sg/products/wealth-accumulation",
    "https://www.prudential.com.sg/products/wealth-accumulation/savings-and-retirement",
    "https://www.prudential.com.sg/products/wealth-accumulation/savings",
    "https://www.prudential.com.sg/products/wealth-accumulation/retirement",
    "https://www.prudential.com.sg/products/wealth-accumulation/investments",
    "https://www.prudential.com.sg/products/legacy-planning",
    "https://www.prudential.com.sg/products/legacy-planning/all-legacy-plans",
    "https://www.prudential.com.sg/products/srs/play-the-right-cards-with-srs",
)

REJECTED_SOURCE_URLS = (
    "https://www.prudential.com.sg/",
    "https://www.prudential.com.sg/products/buy-online",
    "https://www.prudential.com.sg/products/promotions",
    "https://www.prudential.com.sg/lifestage",
    "https://www.prudential.com.sg/claims-and-support/file-claim",
    "https://www.prudential.com.sg/claims-and-support/payments",
    "https://www.prudential.com.sg/claims-and-support/support",
)

CATEGORY_SEGMENTS = {
    "accident",
    "all-legacy-plans",
    "critical-illness",
    "investments",
    "maternity-insurance",
    "medical",
    "medical-and-accident",
    "mortgage-insurance",
    "retirement",
    "savings",
    "savings-and-retirement",
    "term-life-insurance",
    "whole-and-term-insurance",
    "whole-life-insurance",
}

EXCLUDED_PATH_PARTS = (
    "/buy-online",
    "/claims-and-support",
    "/compare",
    "/funds",
    "/lifestage",
    "/promotions",
    "/srs/",
)

CATEGORY_HERO_PATTERNS = (
    "protect you and your family",
    "provide financial security",
    "grow your wealth",
    "preserve and protect your wealth",
    "insurance for life",
)

CHROME_PATTERNS = (
    "claims & services",
    "contact us",
    "financial tools",
    "login",
    "not what you’re looking for",
    "not what you're looking for",
    "online payment",
    "products",
    "prudential singapore",
    "prurewards",
    "select your goal",
    "take me there",
    "website feedback",
    "we’re here to help",
    "we're here to help",
)

NON_PRODUCT_PATTERNS = (
    "all fields are mandatory",
    "as buying a life insurance policy",
    "by submitting this form",
    "compare plans",
    "declaration",
    "download brochure",
    "important information",
    "need help making a decision",
    "needs analysis calculator",
    "please refer to the exact terms",
    "secondary navigation",
    "speak to a financial advisor",
    "the information on this website",
    "things to consider",
    "useful tools and information",
    "you are recommended to read",
)

BENEFIT_KEYWORDS = (
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
    "flexibility",
    "guarantee",
    "health",
    "hospital",
    "income",
    "medical",
    "payout",
    "premium",
    "protection",
    "retirement",
    "savings",
    "waiver",
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


def is_product_detail_url(url: str) -> bool:
    parsed = urlparse(normalize_url(url))
    if parsed.netloc != "www.prudential.com.sg" or not parsed.path.startswith("/products/"):
        return False
    if any(part in parsed.path for part in EXCLUDED_PATH_PARTS):
        return False
    segments = [segment for segment in parsed.path.split("/") if segment]
    if not segments or segments[-1] in CATEGORY_SEGMENTS:
        return False
    if len(segments) >= 4:
        return True
    return len(segments) == 3 and segments[1] == "legacy-planning"


def discover_product_urls(
    session=requests,
    discovery_urls: tuple[str, ...] | list[str] = CATEGORY_URLS,
) -> list[str]:
    product_urls = []
    for discovery_url in discovery_urls:
        try:
            soup = BeautifulSoup(fetch_html(discovery_url, session=session), "html.parser")
        except Exception as exc:
            print(f"[{TABLE_NAME}] skipping discovery {discovery_url}: {exc}")
            continue
        for anchor in soup.select("a[href]"):
            href = normalize_url(urljoin(discovery_url, anchor.get("href") or ""))
            if is_product_detail_url(href) and href not in product_urls:
                product_urls.append(href)
    return product_urls


def meta_content(soup: BeautifulSoup, selector: str) -> str:
    element = soup.select_one(selector)
    return normalize_whitespace(element.get("content")) if element else ""


def parse_product_html(html: str, url: str) -> dict | None:
    source_url = normalize_url(url)
    if not is_product_detail_url(source_url):
        return None

    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    if "404" in title:
        return None

    content = scoped_content(soup)
    plan_name = plan_title(content, title)
    if not plan_name or is_category_hero(plan_name):
        return None

    description = (
        meta_content(soup, 'meta[name="description"]')
        or meta_content(soup, 'meta[property="og:description"]')
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
    content = soup.select_one("main") or soup.select_one("#main-content") or soup
    for element in content.select("script, style, noscript, svg, form, header, footer, nav"):
        element.decompose()
    return content


def plan_title(content: BeautifulSoup, fallback_title: str) -> str:
    h1 = content.find("h1")
    if h1:
        return normalize_whitespace(h1.get_text(" ", strip=True))
    title = normalize_whitespace(fallback_title)
    for separator in (" | ", " - ", " – "):
        if separator in title:
            title = title.split(separator, 1)[0]
    return title


def is_category_hero(text: str) -> bool:
    lowered = text.lower()
    return any(pattern in lowered for pattern in CATEGORY_HERO_PATTERNS)


def first_content_paragraph(content: BeautifulSoup) -> str:
    for element in content.find_all("p"):
        text = normalize_whitespace(element.get_text(" ", strip=True))
        if is_content_text(text):
            return text
    return ""


def content_blocks(content: BeautifulSoup) -> list[str]:
    blocks = []
    seen = set()
    for element in content.find_all(["h2", "h3", "h4", "p", "li"], limit=220):
        text = normalize_whitespace(element.get_text(" ", strip=True))
        if not is_content_text(text) or text in seen:
            continue
        seen.add(text)
        blocks.append(text)
    return blocks


def is_content_text(text: str) -> bool:
    lowered = text.lower()
    if len(text) < 18 or len(text) > 700:
        return False
    if any(pattern in lowered for pattern in CHROME_PATTERNS):
        return False
    return not any(pattern in lowered for pattern in NON_PRODUCT_PATTERNS)


def benefit_blocks(blocks: list[str]) -> list[str]:
    benefits = []
    for block in blocks:
        lowered = block.lower()
        if len(block) > 190 or is_category_hero(block):
            continue
        if any(keyword in lowered for keyword in BENEFIT_KEYWORDS):
            benefits.append(block)
    return benefits[:8]


def compact_text(text: str, limit: int = 900) -> str:
    text = normalize_whitespace(text)
    return text if len(text) <= limit else f"{text[: limit - 1].rstrip()}…"


def brochure_url(soup: BeautifulSoup, source_url: str) -> str:
    for anchor in soup.select("a[href]"):
        href = anchor.get("href") or ""
        href_text = normalize_whitespace(anchor.get_text(" ", strip=True))
        haystack = f"{href_text} {href}".lower()
        if ".pdf" in href.lower() and ("brochure" in haystack or "ebrochure" in haystack):
            return urljoin(source_url, href)
    return ""


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


def scrape_prudential(
    session=requests,
    discovery_urls: tuple[str, ...] | list[str] = CATEGORY_URLS,
) -> list[dict]:
    rows = []
    for product_url in discover_product_urls(session=session, discovery_urls=discovery_urls):
        try:
            row = parse_product_html(fetch_html(product_url, session=session), product_url)
        except Exception as exc:
            print(f"[{TABLE_NAME}] skipping product {product_url}: {exc}")
            continue
        if row:
            rows.append(row)
    return dedupe_rows(rows)


def assert_semantic_quality(rows: list[dict]) -> None:
    findings = validate_plan_rows(format_plan_rows(TABLE_NAME, rows))
    if findings:
        details = "; ".join(finding.format() for finding in findings[:5])
        raise ValueError(f"Prudential scraper produced invalid plan rows: {details}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    try:
        rows = scrape_prudential()
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
