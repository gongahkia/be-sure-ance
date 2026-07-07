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

TABLE_NAME = "raffles_health"
REQUEST_TIMEOUT_SECONDS = 20

DISCOVERY_URLS = (
    "https://www.raffleshealthinsurance.com/",
    "https://www.raffleshealthinsurance.com/products/personal/singapore-medical-cover/",
    "https://www.raffleshealthinsurance.com/products/personal/regional-medical-cover/",
    "https://www.raffleshealthinsurance.com/products/business/singapore-regional-medical-cover/",
)

CANONICAL_PLAN_NAMES = {
    "https://www.raffleshealthinsurance.com/products/raffles-shield/": "Raffles Shield",
    "https://www.raffleshealthinsurance.com/products/raffles-critical-illness-plan/": (
        "Raffles Critical Illness Plan"
    ),
    "https://www.raffleshealthinsurance.com/products/personal/regional-medical-cover/raffles-elite-care/": (
        "Raffles Elite Care"
    ),
    "https://www.raffleshealthinsurance.com/products/personal/global-medical-cover/lifeline-3/": (
        "Lifeline"
    ),
    "https://www.raffleshealthinsurance.com/lifeline/": "Lifeline",
    "https://www.raffleshealthinsurance.com/worldwide-health-options/": (
        "Worldwide Health Options"
    ),
    "https://www.raffleshealthinsurance.com/products/business/singapore-regional-medical-cover/customised-group-insurance/": (
        "Customised Group Insurance"
    ),
    "https://www.raffleshealthinsurance.com/products/business/singapore-regional-medical-cover/raffles-corporate-care-enhanced-iii/": (
        "Raffles Corporate Care Enhanced III"
    ),
    "https://www.raffleshealthinsurance.com/products/business/singapore-regional-medical-cover/foreign-workers-plan/": (
        "Foreign Workers Medical Insurance (FWMI) Enhanced II"
    ),
}

PRODUCT_URLS = tuple(dict.fromkeys(CANONICAL_PLAN_NAMES))
REJECTED_SOURCE_URLS = (
    "https://www.raffleshealthinsurance.com/products/business/third-party-administration/",
    "https://www.raffleshealthinsurance.com/resource-centre/downloads/",
    "https://www.raffleshealthinsurance.com/claims/file-a-claim/personal-insurance-claim/",
    "https://www.raffleshealthinsurance.com/claims/file-a-claim/corporate-insurance-claim/",
)

CHROME_PATTERNS = (
    "products for individuals and families",
    "for businesses and employers singapore",
    "file a personal claim request",
    "file a company claim",
    "forms and downloads",
    "resource centre",
    "contact us",
    "get in touch with us",
    "social media",
    "subscribe to our mailing list",
    "this field is for validation purposes",
    "you can unsubscribe any time",
)

NON_PRODUCT_PATTERNS = (
    "disclaimer and disclosure statement",
    "disclaimer",
    "disclosure statement",
    "things you should know",
    "health insurance can be complex",
    "download a form",
    "find a specialist",
    "make a claim",
    "this brochure is not a contract",
    "waive my hospital admission deposit",
    "policy owners’ protection scheme",
    "policy owners' protection scheme",
)

BENEFIT_KEYWORDS = (
    "benefit",
    "cover",
    "coverage",
    "cash",
    "claim",
    "co-insurance",
    "critical",
    "deductible",
    "employee",
    "health",
    "hospital",
    "medical",
    "maternity",
    "network",
    "rider",
    "specialist",
)

BROCHURE_ALLOW_TERMS = ("brochure", "product summary")
BROCHURE_REJECT_TERMS = (
    "application",
    "authorisation",
    "claim",
    "faq",
    "form",
    "giro",
    "guide",
    "policy conditions",
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


def meta_content(soup: BeautifulSoup, selector: str) -> str:
    element = soup.select_one(selector)
    return normalize_whitespace(element.get("content")) if element else ""


def parse_product_html(html: str, url: str) -> dict | None:
    source_url = normalize_url(url)
    plan_name = CANONICAL_PLAN_NAMES.get(source_url)
    if not plan_name:
        return None

    soup = BeautifulSoup(html, "html.parser")
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
    benefits = benefit_blocks(blocks)

    return {
        "plan_name": plan_name,
        "plan_benefits": benefits,
        "plan_description": description,
        "plan_overview": compact_text(" ".join(overview_blocks)),
        "plan_url": source_url,
        "product_brochure_url": brochure_url(soup, source_url),
    }


def scoped_content(soup: BeautifulSoup) -> BeautifulSoup:
    content = soup.select_one("#content") or soup.select_one(".content-area") or soup
    for element in content.select("script, style, noscript, svg, form, header, footer, nav"):
        element.decompose()
    return content


def first_content_paragraph(content: BeautifulSoup) -> str:
    for element in content.find_all("p"):
        text = normalize_whitespace(element.get_text(" ", strip=True))
        if is_content_text(text):
            return text
    return ""


def content_blocks(content: BeautifulSoup) -> list[str]:
    blocks = []
    seen = set()
    for element in content.find_all(["p", "h2", "h3", "li"], limit=220):
        text = normalize_whitespace(element.get_text(" ", strip=True))
        if not is_content_text(text) or text in seen:
            continue
        seen.add(text)
        blocks.append(text)
    return blocks


def benefit_blocks(blocks: list[str]) -> list[str]:
    benefits = []
    for block in blocks:
        lowered = block.lower()
        if len(block) > 180 or any(pattern in lowered for pattern in NON_PRODUCT_PATTERNS):
            continue
        if any(keyword in lowered for keyword in BENEFIT_KEYWORDS):
            benefits.append(block)
    return benefits[:8]


def is_content_text(text: str) -> bool:
    lowered = text.lower()
    if len(text) < 20 or len(text) > 900:
        return False
    if any(pattern in lowered for pattern in CHROME_PATTERNS):
        return False
    return not any(pattern in lowered for pattern in NON_PRODUCT_PATTERNS)


def compact_text(text: str, limit: int = 900) -> str:
    text = normalize_whitespace(text)
    return text if len(text) <= limit else f"{text[: limit - 1].rstrip()}…"


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
        absolute_url = urljoin(source_url, href)
        score = 0 if "brochure" in haystack else 1
        candidates.append((score, absolute_url))
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


def scrape_raffles_health(session=requests) -> list[dict]:
    rows = []
    for url in PRODUCT_URLS:
        row = parse_product_html(fetch_html(url, session=session), url)
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
        raise ValueError(f"Raffles scraper produced invalid plan rows: {details}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    try:
        rows = scrape_raffles_health()
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
