"""
HL ASSURANCE

https://www.hlas.com.sg/
https://www.hlas.com.sg/personal-insurance/travel-insurance/
https://www.hlas.com.sg/personal-insurance/car-insurance/
https://www.hlas.com.sg/personal-insurance/choice-protect360/
https://www.hlas.com.sg/hlas-corporate-employee-program/
https://www.hlas.com.sg/personal-insurance/critical-illness-insurance/
https://www.hlas.com.sg/personal-insurance/early-critical-illness-insurance/
https://www.hlas.com.sg/personal-insurance/fraud-protect360-plus/
https://www.hlas.com.sg/personal-insurance/fire-insurance/
https://www.hlas.com.sg/personal-insurance/home-protect360/
https://www.hlas.com.sg/personal-insurance/home-protectlite/
https://www.hlas.com.sg/personal-insurance/hospital-protect360/
https://www.hlas.com.sg/personal-insurance/maid-insurance/
https://www.hlas.com.sg/personal-insurance/mobile-phone-insurance/
https://www.hlas.com.sg/personal-insurance/accident-protect360/
https://www.hlas.com.sg/personal-insurance/family-protect360/
https://www.hlas.com.sg/singapore-travel-pass/
https://www.hlas.com.sg/businesspackages/
https://www.hlas.com.sg/casualtyinsurance/
https://www.hlas.com.sg/corporate-travel360/
https://www.hlas.com.sg/engineeringinsurance/
https://www.hlas.com.sg/propertyinsurance/
https://www.hlas.com.sg/check-claim-status/
https://www.hlas.com.sg/claim-forms/
https://www.hlas.com.sg/how-to-claim/
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

TABLE_NAME = "hl_assurance"
REQUEST_TIMEOUT_SECONDS = 20

PRODUCT_CATALOG = (
    (
        "Travel Insurance",
        "https://www.hlas.com.sg/personal-insurance/travel-insurance/",
        "Travel insurance with no-claims discount, pre-existing condition, miles and flight-delay cover options.",
    ),
    (
        "Car Insurance",
        "https://www.hlas.com.sg/personal-insurance/car-insurance/",
        "Car insurance for Singapore drivers with repair, accident and road protection benefits.",
    ),
    (
        "Choice Protect360",
        "https://www.hlas.com.sg/personal-insurance/choice-protect360/",
        "Personal accident protection for accidental death, disability and medical expenses.",
    ),
    (
        "HLAS Corporate Employee Program",
        "https://www.hlas.com.sg/hlas-corporate-employee-program/",
        "Corporate employee insurance programme for discounted personal insurance access.",
    ),
    (
        "Critical Illness Insurance",
        "https://www.hlas.com.sg/personal-insurance/critical-illness-insurance/",
        "Critical illness insurance for major illness financial protection.",
    ),
    (
        "Early Critical Illness Insurance",
        "https://www.hlas.com.sg/personal-insurance/early-critical-illness-insurance/",
        "Early critical illness cover for earlier-stage diagnosis support.",
    ),
    (
        "Fraud Protect360 Plus",
        "https://www.hlas.com.sg/personal-insurance/fraud-protect360-plus/",
        "Fraud insurance for online scams, unauthorised transactions and digital financial risks.",
    ),
    (
        "Fire Insurance",
        "https://www.hlas.com.sg/personal-insurance/fire-insurance/",
        "Fire insurance for HDB structures, fixtures and fittings.",
    ),
    (
        "Home Protect360",
        "https://www.hlas.com.sg/personal-insurance/home-protect360/",
        "Home insurance for contents, renovation, liability and household risks.",
    ),
    (
        "Home ProtectLite",
        "https://www.hlas.com.sg/personal-insurance/home-protectlite/",
        "Lite home insurance for essential home and contents protection.",
    ),
    (
        "Hospital Protect360",
        "https://www.hlas.com.sg/personal-insurance/hospital-protect360/",
        "Hospital cash insurance for hospitalisation and recovery expenses.",
    ),
    (
        "Maid Insurance",
        "https://www.hlas.com.sg/personal-insurance/maid-insurance/",
        "Maid insurance for domestic helper medical, accident and bond needs.",
    ),
    (
        "Mobile Phone Insurance",
        "https://www.hlas.com.sg/personal-insurance/mobile-phone-insurance/",
        "Mobile phone insurance against theft and accidental damage.",
    ),
    (
        "Accident Protect360",
        "https://www.hlas.com.sg/personal-insurance/accident-protect360/",
        "Personal accident insurance for injury, disability and medical reimbursement.",
    ),
    (
        "Family Protect360",
        "https://www.hlas.com.sg/personal-insurance/family-protect360/",
        "Family personal accident protection for household members.",
    ),
    (
        "Singapore Travel Pass",
        "https://www.hlas.com.sg/singapore-travel-pass/",
        "Inbound travel insurance for visitors entering Singapore.",
    ),
    (
        "Business Protect360",
        "https://www.hlas.com.sg/businesspackages/",
        "Business package insurance for offices, retail and small businesses.",
    ),
    (
        "Casualty Insurance",
        "https://www.hlas.com.sg/casualtyinsurance/",
        "Casualty insurance for third-party injury, property damage and employee accident exposures.",
    ),
    (
        "Corporate Travel360",
        "https://www.hlas.com.sg/corporate-travel360/",
        "Corporate travel insurance for business travel disruption and medical risks.",
    ),
    (
        "Engineering Insurance",
        "https://www.hlas.com.sg/engineeringinsurance/",
        "Engineering insurance for construction, installation and machinery risks.",
    ),
    (
        "Property Insurance",
        "https://www.hlas.com.sg/propertyinsurance/",
        "Commercial property insurance for business asset damage and loss.",
    ),
)

PRODUCT_URLS = tuple(url for _name, url, _description in PRODUCT_CATALOG)
REJECTED_SOURCE_URLS = (
    "https://www.hlas.com.sg/",
    "https://www.hlas.com.sg/check-claim-status/",
    "https://www.hlas.com.sg/claim-forms/",
    "https://www.hlas.com.sg/how-to-claim/",
)

CHROME_PATTERNS = (
    "about hl assurance",
    "check claim status",
    "claim forms",
    "contact us",
    "customer portal",
    "how to claim",
    "privacy policy",
    "related articles",
    "terms of use",
)

BENEFIT_KEYWORDS = (
    "accident",
    "benefit",
    "claim",
    "cover",
    "coverage",
    "damage",
    "insurance",
    "medical",
    "protect",
    "protection",
)


def normalize_url(url: str) -> str:
    clean_url = urldefrag(str(url or "").strip()).url.rstrip("/")
    return f"{clean_url}/" if clean_url and not clean_url.endswith("/") else clean_url


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
    if source_url not in {normalize_url(product_url) for product_url in PRODUCT_URLS}:
        return None
    soup = BeautifulSoup(html, "html.parser")
    catalog = catalog_row_for_url(source_url)
    description = meta_description(soup) or catalog["plan_description"]
    benefits = benefit_blocks(soup)
    if not benefits:
        benefits = [catalog["plan_description"]]
    overview_blocks = [
        description,
        *[benefit for benefit in benefits[:3] if benefit != description],
    ]
    row = {
        "plan_name": catalog["plan_name"],
        "plan_description": compact_text(description, 500),
        "plan_overview": compact_text(" ".join(overview_blocks), 900),
        "plan_benefits": benefits[:8],
        "plan_url": source_url,
        "product_brochure_url": brochure_url(soup, source_url),
    }
    return row if valid_plan_row(row) else None


def meta_description(soup: BeautifulSoup) -> str:
    for selector in ('meta[name="description"]', 'meta[property="og:description"]'):
        element = soup.select_one(selector)
        text = normalize_whitespace(element.get("content", "") if element else "")
        if is_content_text(text, max_length=500):
            return text
    return ""


def benefit_blocks(soup: BeautifulSoup) -> list[str]:
    benefits = []
    for element in soup.select("main li, main p, .entry-content li, .entry-content p"):
        text = normalize_whitespace(element.get_text(" ", strip=True))
        lowered = text.lower()
        if not is_content_text(text, max_length=240):
            continue
        if any(keyword in lowered for keyword in BENEFIT_KEYWORDS):
            benefits.append(text)
    return dedupe_texts([benefit for benefit in benefits if not boilerplate_text(benefit)])


def brochure_url(soup: BeautifulSoup, source_url: str) -> str:
    slug_tokens = {
        token
        for token in source_url.rstrip("/").rsplit("/", 1)[-1].split("-")
        if len(token) >= 4 and token not in {"insurance", "protect360", "personal"}
    }
    for anchor in soup.select("a[href]"):
        href = anchor.get("href") or ""
        lowered = href.lower()
        if ".pdf" not in lowered:
            continue
        if "approved_workshop" in lowered or "/portals/0/" in lowered:
            continue
        if not any(term in lowered for term in ("brochure", "policy", "wording", "_pw", "-pw")):
            continue
        if slug_tokens and not any(token in lowered for token in slug_tokens):
            continue
        return urljoin(source_url, href)
    return ""


def catalog_row_for_url(url: str) -> dict:
    source_url = normalize_url(url)
    for name, product_url, description in PRODUCT_CATALOG:
        if normalize_url(product_url) == source_url:
            return {
                "plan_name": name,
                "plan_url": normalize_url(product_url),
                "plan_description": description,
            }
    raise KeyError(url)


def valid_plan_row(row: dict) -> bool:
    if not row.get("plan_name") or not row.get("plan_url") or not row.get("plan_description"):
        return False
    values = (row.get("plan_name"), row.get("plan_description"), row.get("plan_overview"))
    return not any(looks_like_chrome(value) for value in values)


def is_content_text(text: str | None, max_length: int = 900) -> bool:
    normalized = normalize_whitespace(text)
    if len(normalized) < 20 or len(normalized) > max_length:
        return False
    return not looks_like_chrome(normalized) and not boilerplate_text(normalized)


def boilerplate_text(text: str | None) -> bool:
    lowered = normalize_whitespace(text).lower()
    return any(
        pattern in lowered
        for pattern in (
            "all rights reserved",
            "hong leong assurance",
            "personal data",
            "policy owners' protection scheme",
            "this material is for reference only",
        )
    )


def looks_like_chrome(value: str | None) -> bool:
    lowered = normalize_whitespace(value).lower()
    return any(pattern in lowered for pattern in CHROME_PATTERNS)


def compact_text(value: str | None, limit: int = 900) -> str:
    text = normalize_whitespace(value)
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


def scrape_hl_assurance(session=requests) -> list[dict]:
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
    source_url = normalize_url(url)
    if source_url in {normalize_url(rejected) for rejected in REJECTED_SOURCE_URLS}:
        return []
    if source_url not in {normalize_url(product_url) for product_url in PRODUCT_URLS}:
        return []
    row = parse_product_html(fetch_html(source_url), source_url)
    return [row] if row else []


async def run_all_tasks(scrape_list):
    return await gather_scrape_results(TABLE_NAME, scrape_list, scrape_data)


def assert_semantic_quality(rows: list[dict]) -> None:
    findings = validate_plan_rows(format_plan_rows(TABLE_NAME, rows))
    if findings:
        details = "; ".join(finding.format() for finding in findings[:5])
        raise ValueError(f"HL Assurance scraper produced invalid plan rows: {details}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    try:
        rows = scrape_hl_assurance()
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
