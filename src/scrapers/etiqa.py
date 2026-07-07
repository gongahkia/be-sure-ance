"""
ETIQA

https://www.etiqa.com.sg/
https://www.etiqa.com.sg/personal/life-critical-illness-protection/
https://www.etiqa.com.sg/personal/premier-solutions/
https://www.etiqa.com.sg/personal/investments/
https://www.etiqa.com.sg/personal/savings-retirement/
https://www.etiqa.com.sg/personal/personal-accident/
https://www.etiqa.com.sg/personal/personal-cyber-insurance/
https://www.etiqa.com.sg/personal/maid-insurance/
https://www.etiqa.com.sg/personal/travel-insurance/
https://www.etiqa.com.sg/personal/home-insurance/
https://www.etiqa.com.sg/personal/fire-insurance/
https://www.etiqa.com.sg/personal/pet-insurance/
https://www.etiqa.com.sg/personal/motor-insurance/
https://www.etiqa.com.sg/business-insurance/accident-health/
https://www.etiqa.com.sg/business-insurance/commercial-vehicle/
https://www.etiqa.com.sg/business-insurance/casualty/
https://www.etiqa.com.sg/business-insurance/corporate-travel/
https://www.etiqa.com.sg/business-insurance/engineering/
https://www.etiqa.com.sg/business-insurance/marine/
https://www.etiqa.com.sg/business-insurance/business-owners-super-suite/
https://www.etiqa.com.sg/business-insurance/miscellaneous/
https://www.etiqa.com.sg/business-insurance/property/
https://www.etiqa.com.sg/claims-and-services/
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

TABLE_NAME = "etiqa"
BASE_URL = "https://www.etiqa.com.sg"
REQUEST_TIMEOUT_SECONDS = 20

PRODUCT_CATALOG = (
    (
        "Life & Critical Illness Protection",
        "https://www.etiqa.com.sg/personal/life-critical-illness-protection/",
        "Whole life, term life and critical illness insurance for family financial protection.",
    ),
    (
        "Premier Solutions",
        "https://www.etiqa.com.sg/personal/premier-solutions/",
        "Premier wealth, retirement and legacy planning insurance solutions.",
    ),
    (
        "Investments",
        "https://www.etiqa.com.sg/personal/investments/",
        "Investment-linked plans for wealth accumulation and life milestones.",
    ),
    (
        "Savings & Retirement",
        "https://www.etiqa.com.sg/personal/savings-retirement/",
        "Savings and retirement insurance plans for future income and goals.",
    ),
    (
        "Personal Accident",
        "https://www.etiqa.com.sg/personal/personal-accident/",
        "Personal accident insurance for injuries, disability and related financial support.",
    ),
    (
        "Personal Cyber Insurance",
        "https://www.etiqa.com.sg/personal/personal-cyber-insurance/",
        "Cyber insurance for digital identity, online risk and fraud exposure.",
    ),
    (
        "Maid Insurance",
        "https://www.etiqa.com.sg/personal/maid-insurance/",
        "Domestic helper insurance for medical, accident and bond needs.",
    ),
    (
        "Travel Insurance",
        "https://www.etiqa.com.sg/personal/travel-insurance/",
        "Travel cover for delays, cancellations, baggage, medical expenses and emergency evacuation.",
    ),
    (
        "Home Insurance",
        "https://www.etiqa.com.sg/personal/home-insurance/",
        "Home insurance for property, contents, mortgage and family protection.",
    ),
    (
        "HDB Fire Insurance",
        "https://www.etiqa.com.sg/personal/fire-insurance/",
        "Fire insurance for HDB flat structures, fixtures and fittings.",
    ),
    (
        "Pet Insurance",
        "https://www.etiqa.com.sg/personal/pet-insurance/",
        "Pet insurance for veterinary care and selected pet health costs.",
    ),
    (
        "Motor Insurance",
        "https://www.etiqa.com.sg/personal/motor-insurance/",
        "Customisable motor insurance for road and vehicle protection.",
    ),
    (
        "Accident & Health Insurance",
        "https://www.etiqa.com.sg/business-insurance/accident-health/",
        "Business accident and health insurance for employee injuries, death and disability.",
    ),
    (
        "Commercial Vehicle Insurance",
        "https://www.etiqa.com.sg/business-insurance/commercial-vehicle/",
        "Commercial vehicle insurance for business vehicle accident exposure.",
    ),
    (
        "Casualty Insurance",
        "https://www.etiqa.com.sg/business-insurance/casualty/",
        "Casualty insurance for accidental damage or injury caused to others.",
    ),
    (
        "Corporate Travel Insurance",
        "https://www.etiqa.com.sg/business-insurance/corporate-travel/",
        "Corporate travel insurance for employees on business trips.",
    ),
    (
        "Engineering Insurance",
        "https://www.etiqa.com.sg/business-insurance/engineering/",
        "Engineering insurance for machinery, equipment, construction and installation risks.",
    ),
    (
        "Marine Insurance",
        "https://www.etiqa.com.sg/business-insurance/marine/",
        "Marine insurance for cargo damage or loss while in transit.",
    ),
    (
        "Business Owners Super Suite",
        "https://www.etiqa.com.sg/business-insurance/business-owners-super-suite/",
        "Packaged business insurance for selected trades and business-owner risks.",
    ),
    (
        "Miscellaneous Insurance",
        "https://www.etiqa.com.sg/business-insurance/miscellaneous/",
        "Miscellaneous business insurance for plate glass, money, burglary and fraud risks.",
    ),
    (
        "Property Insurance",
        "https://www.etiqa.com.sg/business-insurance/property/",
        "Commercial property insurance for damage or loss to business property.",
    ),
)

PRODUCT_URLS = tuple(url for _name, url, _description in PRODUCT_CATALOG)
REJECTED_SOURCE_URLS = (
    "https://www.etiqa.com.sg/",
    "https://www.etiqa.com.sg/claims-and-services/",
)

CHROME_PATTERNS = (
    "claims and services",
    "customer portal",
    "download documents",
    "find products & services",
    "accident & health commercial vehicle",
    "let us help",
    "life & critical illness protection premier solutions",
    "looking for more information",
    "maybank cards",
    "one stop self-help platform",
    "personal cyber insurance maid insurance",
    "privacy policy",
    "security alert",
    "welcome back",
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
    "risk",
)


def normalize_url(url: str) -> str:
    clean_url = urldefrag(str(url or "").strip()).url.rstrip("/")
    return f"{clean_url}/" if clean_url and not clean_url.endswith("/") else clean_url


def normalize_whitespace(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip().lstrip("\ufeff")


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
    description = meta_description(soup) or hero_description(soup) or catalog["plan_description"]
    description = clean_description(catalog["plan_name"], description, catalog["plan_description"])
    benefits = [benefit for benefit in benefit_blocks(soup) if not product_menu_text(benefit)]
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
        "plan_benefits": dedupe_texts(benefits)[:8],
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


def clean_description(plan_name: str, text: str, fallback: str) -> str:
    cleaned = normalize_whitespace(text)
    title_pattern = re.compile(rf"^(?:{re.escape(plan_name)}\s*)+", flags=re.IGNORECASE)
    cleaned = title_pattern.sub("", cleaned).strip()
    cleaned = re.sub(r"^(What you can get|Download Documents)\s+", "", cleaned).strip()
    return cleaned or fallback


def hero_description(soup: BeautifulSoup) -> str:
    for selector in (".elementor-slide-description", ".elementor-widget-theme-post-content p"):
        for element in soup.select(selector):
            text = normalize_whitespace(element.get_text(" ", strip=True))
            if is_content_text(text, max_length=500):
                return text
    return ""


def benefit_blocks(soup: BeautifulSoup) -> list[str]:
    benefits = []
    for element in soup.select(".elementor-widget-container li, .elementor-widget-container p"):
        text = normalize_whitespace(element.get_text(" ", strip=True))
        lowered = text.lower()
        if not is_content_text(text, max_length=260):
            continue
        if any(keyword in lowered for keyword in BENEFIT_KEYWORDS):
            benefits.append(text)
    return dedupe_texts(benefits)


def product_menu_text(text: str) -> bool:
    normalized = normalize_whitespace(text)
    lowered = normalized.lower()
    if normalized == "Motor Insurance Corporate Employee Scheme":
        return True
    if any(
        pattern in lowered
        for pattern in (
            "download etiqa+ sg app",
            "etiqa insurance pte. ltd.",
            "guide from life insurance association",
            "head over to our digital channel",
            "information is accurate",
            "general insurance policy wordings",
            "personal data protection terms",
            "policy terms and conditions",
            "policy owners’ protection scheme",
            "policy owners' protection scheme",
            "this content is for reference",
            "this policy is underwritten",
            "uen:",
            "you have resided in singapore for 182",
        )
    ):
        return True
    if normalized in {name for name, _url, _description in PRODUCT_CATALOG}:
        return True
    if lowered.endswith(" claim") or " claim " in lowered:
        return True
    product_name_hits = sum(
        1 for name, _url, _description in PRODUCT_CATALOG if name.lower() in lowered
    )
    return product_name_hits >= 2


def brochure_url(soup: BeautifulSoup, source_url: str) -> str:
    slug_tokens = {
        token
        for token in source_url.rstrip("/").rsplit("/", 1)[-1].split("-")
        if len(token) >= 4 and token not in {"insurance", "personal", "business"}
    }
    for anchor in soup.select("a[href]"):
        href = anchor.get("href") or ""
        lowered = href.lower()
        if ".pdf" not in lowered:
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
    lowered = normalized.lower()
    if len(normalized) < 20 or len(normalized) > max_length:
        return False
    return not looks_like_chrome(normalized) and lowered not in {"download documents"}


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


def scrape_etiqa(session=requests) -> list[dict]:
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
        raise ValueError(f"Etiqa scraper produced invalid plan rows: {details}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    try:
        rows = scrape_etiqa()
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
