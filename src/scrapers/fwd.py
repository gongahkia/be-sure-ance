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
from src.validation.plan_quality import validate_plan_rows

TABLE_NAME = "fwd"
REQUEST_TIMEOUT_SECONDS = 20

CANONICAL_PLAN_NAMES = {
    "https://www.fwd.com.sg/home-insurance/": "Home insurance",
    "https://www.fwd.com.sg/maid-insurance/": "Maid insurance",
    "https://www.fwd.com.sg/car-insurance/": "Car insurance",
    "https://www.fwd.com.sg/motorcycle-insurance/": "Motorcycle insurance",
    "https://www.fwd.com.sg/travel-insurance/": "Travel insurance",
    "https://www.fwd.com.sg/accident-health/life-pa/": "FWD Life PA insurance",
    "https://www.fwd.com.sg/life-insurance/direct-purchase-term-life-insurance/": (
        "Direct Term Life insurance"
    ),
    "https://www.fwd.com.sg/critical-illness-insurance/critical-illness-plus/": (
        "Critical Illness Plus insurance"
    ),
}

PRODUCT_URLS = tuple(CANONICAL_PLAN_NAMES)
REJECTED_SOURCE_URLS = (
    "https://www.fwd.com.sg/",
    "https://www.fwd.com.sg/fire-insurance/",
    "https://www.fwd.com.sg/claim-online/",
    "https://www.fwd.com.sg/forms/",
    "https://www.fwd.com.sg/contact-us/",
)

INACTIVE_PATTERNS = (
    "no longer offering",
    "no longer available",
)

CHROME_PATTERNS = (
    "accident & health",
    "advisor login",
    "buy online",
    "calculate premium",
    "car motorcycle",
    "check your price",
    "claim online",
    "claims make a claim",
    "contact us",
    "emergency support",
    "frequently asked questions",
    "home & maid",
    "invest & save",
    "life & health",
    "login to fwd",
    "make a claim",
    "motor car motorcycle",
    "policy forms",
    "product highlights",
    "read the policy wording",
    "smart eiris",
    "support faqs",
    "workshop & clinic finder",
)

NON_PRODUCT_PATTERNS = (
    "all content provided on this webpage is for informational",
    "call 6322 2072",
    "disclaimer",
    "download policy wording",
    "fwd singapore pte. ltd.",
    "not to be used or relied upon",
    "privacy policy",
    "promotion terms",
    "terms and conditions",
    "this page is for general information only",
)

BENEFIT_KEYWORDS = (
    "accident",
    "baggage",
    "benefit",
    "cash",
    "claim",
    "co-payment",
    "cover",
    "coverage",
    "critical",
    "death",
    "evacuation",
    "home assistance",
    "hospital",
    "illness",
    "income",
    "medical",
    "premium",
    "reimbursement",
    "travel",
)

BROCHURE_ALLOW_TERMS = (
    "brochure",
    "policy contract",
    "policy wording",
    "product summary",
)

BROCHURE_REJECT_TERMS = (
    "health first",
    "health-first",
    "healthfirst",
    "lia.org.sg",
    "terms-and-conditions",
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
    plan_name = CANONICAL_PLAN_NAMES.get(source_url)
    if not plan_name or source_url in REJECTED_SOURCE_URLS:
        return None

    soup = BeautifulSoup(html, "html.parser")
    full_text = normalize_whitespace(soup.get_text(" ", strip=True)).lower()
    if any(pattern in full_text for pattern in INACTIVE_PATTERNS):
        return None

    content = scoped_content(soup)
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
    content = soup.select_one("main") or soup.select_one("#main") or soup
    for element in content.select(
        "script, style, noscript, svg, form, header, footer, nav, [role='navigation']"
    ):
        element.decompose()
    return content


def meta_content(soup: BeautifulSoup, selector: str) -> str:
    element = soup.select_one(selector)
    return normalize_whitespace(element.get("content")) if element else ""


def first_content_paragraph(content: BeautifulSoup) -> str:
    for element in content.find_all("p"):
        text = normalize_whitespace(element.get_text(" ", strip=True))
        if is_content_text(text):
            return text
    return ""


def content_blocks(content: BeautifulSoup) -> list[str]:
    blocks = []
    seen = set()
    for element in content.find_all(["h2", "h3", "h4", "p", "li"], limit=240):
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
        if len(block) > 190:
            continue
        if any(keyword in lowered for keyword in BENEFIT_KEYWORDS):
            benefits.append(block)
    return benefits[:8]


def compact_text(text: str, limit: int = 900) -> str:
    text = normalize_whitespace(text)
    return text if len(text) <= limit else f"{text[: limit - 3].rstrip()}..."


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
        score = 0 if "brochure" in haystack or "product summary" in haystack else 1
        candidates.append((score, urljoin(source_url, href)))
    if not candidates:
        return ""
    return sorted(candidates, key=lambda item: item[0])[0][1]


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


def scrape_fwd(session=requests) -> list[dict]:
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


def assert_semantic_quality(rows: list[dict]) -> None:
    findings = validate_plan_rows(format_plan_rows(TABLE_NAME, rows))
    if findings:
        details = "; ".join(finding.format() for finding in findings[:5])
        raise ValueError(f"FWD scraper produced invalid plan rows: {details}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    try:
        rows = scrape_fwd()
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
