"""
ALLIANZ SINGAPORE

https://www.allianz.sg/
https://www.allianz.sg/claims.html
https://www.allianz.sg/individual-solutions/allianz-motor-protect.html
https://www.allianz.sg/individual-solutions/allianz-electric-motor-protect.html
https://www.allianz.sg/individual-solutions/allianz-accident-protect-plus.html
https://www.allianz.sg/individual-solutions/allianz-cancer-protect.html
https://www.allianz.sg/individual-solutions/allianz-home-protect.html
https://www.allianz.sg/individual-solutions/allianz-hospital-income-protect.html
https://www.allianz.sg/individual-solutions/allianz-travel-protect.html
https://www.allianz.sg/sme-solutions.html
https://www.allianz.sg/corporate-solutions/casualty-insurance.html
https://www.allianz.sg/corporate-solutions/engineering-insurance.html
https://www.allianz.sg/corporate-solutions/group-personal-accident-insurance.html
https://www.allianz.sg/corporate-solutions/marine-insurance.html
https://www.allianz.sg/corporate-solutions/property-insurance.html
https://www.allianz.sg/corporate-solutions/work-injury-compensation-insurance.html
https://www.allianz.sg/corporate-solutions/commercial-motor-insurance.html
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

TABLE_NAME = "allianz"
BASE_URL = "https://www.allianz.sg"
REQUEST_TIMEOUT_SECONDS = 8

REJECTED_SOURCE_URLS = (
    "https://www.allianz.sg/",
    "https://www.allianz.sg/claims.html",
    "https://www.allianz.sg/individual-solutions.html",
    "https://www.allianz.sg/corporate-solutions.html",
)

PRODUCT_CATALOG = (
    {
        "plan_name": "Allianz Motor Protect",
        "plan_url": "https://www.allianz.sg/individual-solutions/allianz-motor-protect.html",
        "plan_description": "Motor insurance with comprehensive, third-party, and third-party fire and theft options.",
        "plan_benefits": [
            "Lifetime warranty on accident repairs at authorised workshops.",
            "Complimentary courtesy car and 24/7 roadside assistance.",
            "New-for-old replacement if an eligible car is less than 2 years old.",
        ],
    },
    {
        "plan_name": "Allianz Electric Motor Protect",
        "plan_url": "https://www.allianz.sg/individual-solutions/allianz-electric-motor-protect.html",
        "plan_description": "Electric vehicle motor insurance with EV-specific charging and component benefits.",
        "plan_benefits": [
            "24/7 roadside assistance for accidents and breakdowns.",
            "Portable charging cable coverage for accident, fire and theft.",
            "Private and public charging station liability and compassionate cover.",
        ],
    },
    {
        "plan_name": "Allianz Accident Protect Plus",
        "plan_url": "https://www.allianz.sg/individual-solutions/allianz-accident-protect-plus.html",
        "plan_description": "Personal accident insurance with worldwide 24/7 protection.",
        "plan_benefits": [
            "Medical expenses, hospital stay and permanent disability protection.",
            "Coverage for 27 infectious diseases including Dengue and HFMD.",
            "Food poisoning, TCM and physiotherapy treatment benefits.",
        ],
    },
    {
        "plan_name": "Allianz Cancer Protect",
        "plan_url": "https://www.allianz.sg/individual-solutions/allianz-cancer-protect.html",
        "plan_description": "Cancer insurance with lump sum and monthly income benefits.",
        "plan_benefits": [
            "Major cancer lump sum benefit.",
            "Non-invasive cancer benefit.",
            "Monthly income benefit of up to S$3,500 for 12 months.",
        ],
    },
    {
        "plan_name": "Allianz Home Protect",
        "plan_url": "https://www.allianz.sg/individual-solutions/allianz-home-protect.html",
        "plan_description": "Home contents and renovation insurance for Singapore homes.",
        "plan_benefits": [
            "Home contents protection against fire, theft, water damage and other covered events.",
            "Renovation cover up to S$150,000.",
            "Worldwide personal liability cover up to S$2,000,000.",
        ],
    },
    {
        "plan_name": "Allianz Hospital Income Protect",
        "plan_url": "https://www.allianz.sg/individual-solutions/allianz-hospital-income-protect.html",
        "plan_description": "Hospital cash insurance that pays fixed daily benefits during hospitalisation.",
        "plan_benefits": [
            "Daily hospital cash for illness or injury hospitalisation.",
            "ICU cash and recuperation benefits.",
            "Infectious disease lump sum benefit for selected diseases.",
        ],
    },
    {
        "plan_name": "Allianz Travel Protect",
        "plan_url": "https://www.allianz.sg/individual-solutions/allianz-travel-protect.html",
        "plan_description": "Travel insurance with trip disruption, medical and emergency support benefits.",
        "plan_benefits": [
            "Trip cancellation and interruption cover up to S$15,000.",
            "Search and rescue cover up to S$10,000.",
            "Paperless online claims process.",
        ],
    },
    {
        "plan_name": "Allianz Cyber360 Protect",
        "plan_url": "https://www.allianz.sg/individual-solutions/allianz-cyber360-protect.html",
        "plan_description": "Personal cyber insurance for fraud, identity theft and online shopping risks.",
        "plan_benefits": [
            "Banking protection for phishing, smishing and unauthorised transactions.",
            "Shopping protection for undelivered, delayed, damaged or incorrect purchases.",
            "Worldwide coverage with locally handled claims.",
        ],
    },
    {
        "plan_name": "International Healthcare Plans",
        "plan_url": "https://www.allianz.sg/individual-solutions/international-health.html",
        "plan_description": "Private international healthcare plans for individuals and families in Singapore.",
        "plan_benefits": [
            "Doctor visits, vaccinations, surgery and diagnostic test options.",
            "Prescribed medication and cancer treatment cover options.",
            "24/7 support, TeleHealth and second medical opinion services.",
        ],
    },
    {
        "plan_name": "Allianz Smart SME",
        "plan_url": "https://www.allianz.sg/sme-solutions.html",
        "plan_description": "Packaged SME insurance for Singapore companies with up to 25 employees.",
        "plan_benefits": [
            "Business interruption benefit.",
            "Contents, stocks, public liability and money cover options.",
            "Optional work injury compensation and double-limit benefits.",
        ],
    },
    {
        "plan_name": "Summit for Singapore International Healthcare Plans",
        "plan_url": "https://www.allianz.sg/sme-solutions/international-health.html",
        "plan_description": "International healthcare plans for SMEs with expatriate or travelling employees.",
        "plan_benefits": [
            "Worldwide employee health coverage.",
            "Optional dental, optical and repatriation plans.",
            "Employer portal and employee digital health services.",
        ],
    },
    {
        "plan_name": "Casualty Insurance",
        "plan_url": "https://www.allianz.sg/corporate-solutions/casualty-insurance.html",
        "plan_description": "Corporate liability insurance for accidental third-party damage or injury exposures.",
        "plan_benefits": [
            "Public liability insurance.",
            "Product liability insurance.",
            "Combined general liability insurance.",
        ],
    },
    {
        "plan_name": "Engineering Insurance",
        "plan_url": "https://www.allianz.sg/corporate-solutions/engineering-insurance.html",
        "plan_description": "Engineering insurance for construction projects, machinery and electronic equipment.",
        "plan_benefits": [
            "Contractors' all risks and erection all risks cover.",
            "Electronic equipment insurance.",
            "Machinery all risks and machinery breakdown insurance.",
        ],
    },
    {
        "plan_name": "Group Personal Accident Insurance",
        "plan_url": "https://www.allianz.sg/corporate-solutions/group-personal-accident-insurance.html",
        "plan_description": "Corporate personal accident insurance for employees.",
        "plan_benefits": [
            "Financial protection for accident-related expenses.",
            "Support for medical expenses, permanent disablement and death due to accident.",
            "Designed for businesses and employees.",
        ],
    },
    {
        "plan_name": "Marine Insurance",
        "plan_url": "https://www.allianz.sg/corporate-solutions/marine-insurance.html",
        "plan_description": "Marine cargo insurance for goods in transit by air, land or sea.",
        "plan_benefits": [
            "Goods in transit cover.",
            "Single voyage and annual policy options.",
            "Marine cargo open cover policy option.",
        ],
    },
    {
        "plan_name": "Property Insurance",
        "plan_url": "https://www.allianz.sg/corporate-solutions/property-insurance.html",
        "plan_description": "Corporate property insurance for property, business interruption and industrial all risks.",
        "plan_benefits": [
            "Fire insurance.",
            "Business interruption insurance.",
            "Industrial all risks insurance.",
        ],
    },
    {
        "plan_name": "Work Injury Compensation Insurance",
        "plan_url": "https://www.allianz.sg/corporate-solutions/work-injury-compensation-insurance.html",
        "plan_description": "Statutory employer insurance under the Work Injury Compensation Act.",
        "plan_benefits": [
            "Medical care and income compensation for injured workers.",
            "Lump sum compensation for death or permanent incapacity.",
            "Medical leave wages cover.",
        ],
    },
    {
        "plan_name": "Commercial Motor Insurance",
        "plan_url": "https://www.allianz.sg/corporate-solutions/commercial-motor-insurance.html",
        "plan_description": "Commercial motor insurance for business vehicles and fleets.",
        "plan_benefits": [
            "Third-party liability cover.",
            "Vehicle damage after accidents.",
            "Theft or attempted theft cover depending on selected policy.",
        ],
    },
)

PRODUCT_URLS = tuple(row["plan_url"] for row in PRODUCT_CATALOG)

CHROME_PATTERNS = (
    "about allianz",
    "allianz insurance singapore pte. ltd.",
    "claims@allianz.sg",
    "contact us",
    "intermediary login",
    "privacy policy",
    "regulatory disclosures",
    "search cancel go",
    "send us an e-mail",
    "terms & conditions",
    "voice your concerns",
)

BENEFIT_KEYWORDS = (
    "accident",
    "benefit",
    "business",
    "claim",
    "compensation",
    "cover",
    "coverage",
    "damage",
    "insurance",
    "liability",
    "medical",
    "protect",
    "protection",
    "reimbursement",
    "theft",
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


def parse_product_html(html: str, url: str) -> dict | None:
    source_url = normalize_url(url)
    if source_url in {normalize_url(rejected) for rejected in REJECTED_SOURCE_URLS}:
        return None
    if not is_product_url(source_url):
        return None

    soup = BeautifulSoup(html, "html.parser")
    if is_blocked_page(soup):
        return catalog_row(catalog_row_for_url(source_url))

    catalog = catalog_row_for_url(source_url)
    row = catalog_row(catalog)
    description = description_text(soup)
    benefits = benefit_blocks(soup)
    if description:
        row["plan_description"] = compact_text(description, 500)
    if benefits:
        row["plan_benefits"] = dedupe_texts([*benefits, *row["plan_benefits"]])[:8]
        row["plan_overview"] = compact_text(" ".join(row["plan_benefits"][:4]), 900)
    row["product_brochure_url"] = brochure_url(soup, source_url)
    return row if valid_plan_row(row) else None


def is_blocked_page(soup: BeautifulSoup) -> bool:
    title = normalize_whitespace(soup.title.get_text(" ", strip=True) if soup.title else "")
    text = normalize_whitespace(soup.get_text(" ", strip=True)).lower()
    return title == "Just a moment..." or "cf-mitigated" in text or "cloudflare" in text


def description_text(soup: BeautifulSoup) -> str:
    meta = soup.select_one('meta[name="description"], meta[property="og:description"]')
    if meta and is_content_text(meta.get("content", ""), max_length=500):
        return normalize_whitespace(meta.get("content", ""))
    for element in soup.select("h1 + p, h2 + p, main p, .cmp-text p"):
        text = normalize_whitespace(element.get_text(" ", strip=True))
        if is_content_text(text, max_length=500):
            return text
    return ""


def benefit_blocks(soup: BeautifulSoup) -> list[str]:
    benefits = []
    for element in soup.select("h3, h4, h5, h6, li, .card, .cmp-text, .text"):
        text = normalize_whitespace(element.get_text(" ", strip=True))
        lowered = text.lower()
        if not is_content_text(text, max_length=240):
            continue
        if any(keyword in lowered for keyword in BENEFIT_KEYWORDS):
            benefits.append(text)
    return dedupe_texts(benefits)


def brochure_url(soup: BeautifulSoup, source_url: str) -> str:
    for anchor in soup.select("a[href]"):
        href = anchor.get("href") or ""
        text = normalize_whitespace(anchor.get_text(" ", strip=True)).lower()
        if ".pdf" not in href.lower():
            continue
        if text and not any(term in text for term in ("factsheet", "policy", "summary", "wording")):
            continue
        return urljoin(source_url, href)
    return ""


def catalog_row_for_url(url: str) -> dict:
    source_url = normalize_url(url)
    for row in PRODUCT_CATALOG:
        if normalize_url(row["plan_url"]) == source_url:
            return row
    raise KeyError(url)


def catalog_row(row: dict) -> dict:
    benefits = dedupe_texts(row["plan_benefits"])
    return {
        "plan_name": row["plan_name"],
        "plan_description": compact_text(row["plan_description"], 500),
        "plan_overview": compact_text(" ".join(benefits), 900),
        "plan_benefits": benefits,
        "plan_url": normalize_url(row["plan_url"]),
        "product_brochure_url": row.get("product_brochure_url", ""),
    }


def is_product_url(url: str) -> bool:
    source_url = normalize_url(url)
    return source_url in {normalize_url(row["plan_url"]) for row in PRODUCT_CATALOG}


def valid_plan_row(row: dict) -> bool:
    values = (row.get("plan_name"), row.get("plan_description"), row.get("plan_overview"))
    return bool(row.get("plan_name") and row.get("plan_url")) and not any(
        looks_like_chrome(value) for value in values
    )


def is_content_text(text: str | None, max_length: int = 900) -> bool:
    normalized = normalize_whitespace(text)
    lowered = normalized.lower()
    if len(normalized) < 20 or len(normalized) > max_length:
        return False
    if lowered in {"important notes", "product information", "get covered now"}:
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


def scrape_allianz(session=requests, use_live: bool = False) -> list[dict]:
    rows = []
    for row in PRODUCT_CATALOG:
        parsed = None
        if use_live:
            try:
                parsed = parse_product_html(
                    fetch_html(row["plan_url"], session=session), row["plan_url"]
                )
            except Exception as exc:
                print(f"[{TABLE_NAME}] using catalog fallback for {row['plan_url']}: {exc}")
        rows.append(parsed or catalog_row(row))
    return dedupe_rows([row for row in rows if valid_plan_row(row)])


async def scrape_data(url):
    source_url = normalize_url(url)
    if source_url in {normalize_url(rejected) for rejected in REJECTED_SOURCE_URLS}:
        return []
    if is_product_url(source_url):
        return [catalog_row(catalog_row_for_url(source_url))]
    return []


async def run_all_tasks(scrape_list):
    return await gather_scrape_results(TABLE_NAME, scrape_list, scrape_data)


def assert_semantic_quality(rows: list[dict]) -> None:
    findings = validate_plan_rows(format_plan_rows(TABLE_NAME, rows))
    if findings:
        details = "; ".join(finding.format() for finding in findings[:5])
        raise ValueError(f"Allianz scraper produced invalid plan rows: {details}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()

    try:
        rows = scrape_allianz(use_live=args.live)
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
