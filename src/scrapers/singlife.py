"""
SINGLIFE

https://singlife.com/en

https://singlife.com/en/life-insurance
https://singlife.com/en/medical-insurance
https://singlife.com/en/critical-illness-insurance
https://singlife.com/en/disability-insurance
https://singlife.com/en/accident-insurance
https://singlife.com/en/mindef-and-mha/mindef-group-insurance
https://singlife.com/en/mindef-and-mha/mha-group-insurance
https://singlife.com/en/savings
https://singlife.com/en/investment-linked-plan

https://singlife.com/en/maternity-care
https://singlife.com/en/car-insurance
https://singlife.com/en/travel-insurance
https://singlife.com/en/home-insurance
https://singlife.com/en/pogis
https://singlife.com/en/flexi-retirement-ii
https://singlife.com/en/singlife-account
https://singlife.com/en/dollardex
https://singlife.com/en/grow-with-singlife
https://singlife.com/en/business/general-insurance/commercial-vehicle-insurance
https://singlife.com/en/business/general-insurance/corporate-travel-insurance
https://singlife.com/en/business/general-insurance/mybusiness-insurance
https://singlife.com/en/business/corporate-insurance/myglobal-benefits
https://singlife.com/en/business/corporate-insurance/group-term-life
https://singlife.com/en/business/corporate-insurance/group-critical-illness
https://singlife.com/en/business/corporate-insurance/group-preferred-care-plus
https://singlife.com/en/business/corporate-insurance/group-hospital-and-surgical-care
https://singlife.com/en/business/corporate-insurance/group-personal-accident
https://singlife.com/en/business/corporate-insurance/group-disability-protection
https://singlife.com/en/business/corporate-insurance/mybenefits-plus
"""

from __future__ import annotations

import argparse
import re
from urllib.parse import urldefrag, urljoin

import requests
from bs4 import BeautifulSoup, Tag

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

TABLE_NAME = "singlife"
BASE_URL = "https://singlife.com"
REQUEST_TIMEOUT_SECONDS = 20

SOURCE_URLS = (
    "https://singlife.com/en/life-insurance",
    "https://singlife.com/en/medical-insurance",
    "https://singlife.com/en/critical-illness-insurance",
    "https://singlife.com/en/disability-insurance",
    "https://singlife.com/en/accident-insurance",
    "https://singlife.com/en/mindef-and-mha/mindef-group-insurance",
    "https://singlife.com/en/mindef-and-mha/mha-group-insurance",
    "https://singlife.com/en/savings",
    "https://singlife.com/en/investment-linked-plan",
    "https://singlife.com/en/maternity-care",
    "https://singlife.com/en/car-insurance",
    "https://singlife.com/en/travel-insurance",
    "https://singlife.com/en/home-insurance",
    "https://singlife.com/en/pogis",
    "https://singlife.com/en/flexi-retirement-ii",
    "https://singlife.com/en/singlife-account",
    "https://singlife.com/en/business/general-insurance/commercial-vehicle-insurance",
    "https://singlife.com/en/business/general-insurance/corporate-travel-insurance",
    "https://singlife.com/en/business/general-insurance/mybusiness-insurance",
    "https://singlife.com/en/business/corporate-insurance/myglobal-benefits",
    "https://singlife.com/en/business/corporate-insurance/group-term-life",
    "https://singlife.com/en/business/corporate-insurance/group-critical-illness",
    "https://singlife.com/en/business/corporate-insurance/group-preferred-care-plus",
    "https://singlife.com/en/business/corporate-insurance/group-hospital-and-surgical-care",
    "https://singlife.com/en/business/corporate-insurance/group-personal-accident",
    "https://singlife.com/en/business/corporate-insurance/group-disability-protection",
    "https://singlife.com/en/business/corporate-insurance/mybenefits-plus",
)

REJECTED_SOURCE_URLS = (
    "https://singlife.com/en",
    "https://singlife.com/en/dollardex",
    "https://singlife.com/en/grow-with-singlife",
)

DIRECT_PRODUCT_URLS = {
    "https://singlife.com/en/pogis",
    "https://singlife.com/en/flexi-retirement-ii",
    "https://singlife.com/en/singlife-account",
    "https://singlife.com/en/business/general-insurance/commercial-vehicle-insurance",
    "https://singlife.com/en/business/general-insurance/corporate-travel-insurance",
    "https://singlife.com/en/business/general-insurance/mybusiness-insurance",
    "https://singlife.com/en/business/corporate-insurance/myglobal-benefits",
    "https://singlife.com/en/business/corporate-insurance/group-term-life",
    "https://singlife.com/en/business/corporate-insurance/group-critical-illness",
    "https://singlife.com/en/business/corporate-insurance/group-preferred-care-plus",
    "https://singlife.com/en/business/corporate-insurance/group-hospital-and-surgical-care",
    "https://singlife.com/en/business/corporate-insurance/group-personal-accident",
    "https://singlife.com/en/business/corporate-insurance/group-disability-protection",
    "https://singlife.com/en/business/corporate-insurance/mybenefits-plus",
}

TIER_PAGE_PREFIXES = {
    "https://singlife.com/en/car-insurance": "Singlife Car Insurance",
    "https://singlife.com/en/travel-insurance": "Singlife Travel Insurance",
    "https://singlife.com/en/home-insurance": "Singlife Home Insurance",
}

CHROME_PATTERNS = (
    "access your personal or group insurance policies",
    "access the online sales quotation system",
    "already own an account",
    "articles you might be interested in",
    "ebconnect",
    "financial advisers",
    "find out more terms and conditions apply",
    "for singlife financial advisers",
    "important notes",
    "include other products you're interested in",
    "hr business partners and intermediaries",
    "let's chat about",
    "looking for personal insurance",
    "personal tips, guides and expert advice",
    "pocket sqs",
    "save, invest, earn, be insured",
    "singlife ezsub",
    "singlife online",
    "this site uses cookies",
    "view all logins",
)

NON_PRODUCT_PATTERNS = (
    "all ages mentioned refer",
    "all information provided is",
    "as buying a life insurance policy",
    "cookie policy",
    "download",
    "disclaimers",
    "enjoy these special savings",
    "flip the cards",
    "for singlife account",
    "for singlife third-party",
    "get a quote",
    "image",
    "login",
    "looking for corporate solutions",
    "read more here",
    "rewards and perks",
    "speak to us",
    "submit product quotations",
    "terms and conditions",
    "up to 58% off",
    "we cover trip cancellation",
    "we will get back to you",
)

BENEFIT_KEYWORDS = (
    "accident",
    "benefit",
    "cash",
    "claim",
    "cover",
    "coverage",
    "critical",
    "death",
    "disability",
    "hospital",
    "income",
    "medical",
    "payout",
    "premium",
    "protection",
    "reimbursement",
    "savings",
    "travel",
)

BROCHURE_REJECT_TERMS = (
    "faq",
    "form",
    "map",
    "milestone",
    "nrdo.gov.sg",
    "sdic",
    "terms",
    "tnc",
)


def normalize_url(url: str) -> str:
    return urldefrag(str(url or "").strip()).url.rstrip("/")


def normalize_whitespace(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def text_of(element: Tag | None) -> str:
    return element.get_text(" ", strip=True) if element else ""


def fetch_html(url: str, session=requests) -> str:
    response = session.get(
        url,
        timeout=REQUEST_TIMEOUT_SECONDS,
        headers={"User-Agent": BOT_USER_AGENT},
    )
    response.raise_for_status()
    return response.text


def parse_source_html(html: str, url: str) -> list[dict]:
    source_url = normalize_url(url)
    if source_url in REJECTED_SOURCE_URLS:
        return []

    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("div.relative.product-card-container")
    if cards:
        return [row for card in cards if (row := parse_product_card(card, source_url))]
    row = parse_direct_product_html(soup, source_url) if source_url in DIRECT_PRODUCT_URLS else None
    return [row] if row else []


def parse_product_card(card: Tag, source_url: str) -> dict | None:
    plan_name = normalize_whitespace(
        text_of(card.select_one("h2.product-card-header") or card.select_one("h3"))
    )
    if not plan_name or is_noise_name(plan_name):
        return None

    prefix = TIER_PAGE_PREFIXES.get(source_url)
    if prefix and plan_name.lower() not in prefix.lower():
        plan_name = f"{prefix} - {plan_name}"

    overview = clean_text(text_of(card.select_one("div.product-card-description")), limit=900)
    benefits = [
        clean_text(item.get_text(" ", strip=True), limit=220)
        for item in card.select("ul.product-card-features li")
    ]
    benefits = [benefit for benefit in benefits if benefit and is_content_text(benefit)]

    plan_url = ""
    url_element = card.select_one("a.product-card-button[href]")
    if url_element:
        plan_url = absolute_url(source_url, url_element.get("href"))

    brochure = card_brochure_url(card, source_url)
    if not plan_url and brochure:
        plan_url = brochure

    return {
        "plan_name": clean_plan_name(plan_name),
        "plan_benefits": benefits[:8],
        "plan_description": category_description(card, source_url),
        "plan_overview": overview,
        "plan_url": plan_url or source_url,
        "product_brochure_url": brochure,
    }


def parse_direct_product_html(soup: BeautifulSoup, source_url: str) -> dict | None:
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    plan_name = clean_plan_name(title_name(soup, title))
    if not plan_name:
        return None

    description = clean_text(
        meta_content(soup, 'meta[name="description"]')
        or meta_content(soup, 'meta[property="og:description"]')
        or first_content_paragraph(soup),
        limit=500,
    )
    blocks = content_blocks(soup)
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


def category_description(card: Tag, source_url: str) -> str:
    category = source_url.rsplit("/", 1)[-1].replace("-", " ").title()
    container = card.find_parent("body")
    banner = container.select_one(".sl-banner-content") if container else None
    banner_text = clean_text(text_of(banner), limit=500)
    if banner_text:
        return banner_text
    return category


def card_brochure_url(card: Tag, source_url: str) -> str:
    for anchor in card.select("a[href]"):
        href = anchor.get("href") or ""
        text = normalize_whitespace(anchor.get_text(" ", strip=True))
        haystack = f"{text} {href}".lower()
        if ".pdf" not in href.lower():
            continue
        if any(term in haystack for term in BROCHURE_REJECT_TERMS):
            continue
        return absolute_url(source_url, href)
    return ""


def brochure_url(soup: BeautifulSoup, source_url: str) -> str:
    for anchor in soup.select("a[href]"):
        href = anchor.get("href") or ""
        text = normalize_whitespace(anchor.get_text(" ", strip=True))
        haystack = f"{text} {href}".lower()
        if ".pdf" not in href.lower():
            continue
        if any(term in haystack for term in BROCHURE_REJECT_TERMS):
            continue
        if "brochure" in haystack or "product-summary" in haystack or "summary" in haystack:
            return absolute_url(source_url, href)
    return ""


def absolute_url(source_url: str, href: str | None) -> str:
    href = href or ""
    return normalize_url(urljoin(source_url, href))


def title_name(soup: BeautifulSoup, title: str) -> str:
    title_text = title_product_name(title)
    if title_text and not is_noise_name(title_text):
        return title_text
    h1 = soup.find("h1")
    if h1:
        h1_text = normalize_whitespace(h1.get_text(" ", strip=True))
        if h1_text and not is_noise_name(h1_text):
            return h1_text
    return title_text


def title_product_name(title: str) -> str:
    title = normalize_whitespace(title)
    for separator in (" | ", " – "):
        if separator in title:
            return title.split(separator, 1)[0]
    return title.removesuffix(" I Get a Quote").strip()


def clean_plan_name(name: str) -> str:
    name = normalize_whitespace(name)
    for suffix in (" | Singlife Singapore", " | Singlife", " Singapore"):
        if name.endswith(suffix):
            name = name[: -len(suffix)]
    return name


def clean_text(text: str, limit: int) -> str:
    text = normalize_whitespace(text)
    return compact_text(text, limit=limit) if is_content_text(text) else ""


def meta_content(soup: BeautifulSoup, selector: str) -> str:
    element = soup.select_one(selector)
    return normalize_whitespace(element.get("content")) if element else ""


def first_content_paragraph(soup: BeautifulSoup) -> str:
    for element in soup.find_all("p"):
        text = normalize_whitespace(element.get_text(" ", strip=True))
        if is_content_text(text):
            return text
    return ""


def content_blocks(soup: BeautifulSoup) -> list[str]:
    content = soup.select_one(".root") or soup
    blocks = []
    seen = set()
    for element in content.find_all(["h2", "h3", "p", "li"], limit=260):
        text = normalize_whitespace(element.get_text(" ", strip=True))
        if text in seen or not is_content_text(text):
            continue
        seen.add(text)
        blocks.append(text)
    return blocks


def is_content_text(text: str) -> bool:
    lowered = normalize_whitespace(text).lower()
    if len(lowered) < 14 or len(lowered) > 700:
        return False
    if any(pattern in lowered for pattern in CHROME_PATTERNS):
        return False
    return not any(pattern in lowered for pattern in NON_PRODUCT_PATTERNS)


def is_noise_name(name: str) -> bool:
    lowered = normalize_whitespace(name).lower()
    return lowered in {
        "already own an account with us?",
        "fund centre",
        "invest with us!",
        "more reads",
        "what is pogis?",
    }


def benefit_blocks(blocks: list[str]) -> list[str]:
    benefits = []
    for block in blocks:
        lowered = block.lower()
        if len(block) > 220:
            continue
        if any(keyword in lowered for keyword in BENEFIT_KEYWORDS):
            benefits.append(block)
    return benefits[:8]


def compact_text(text: str, limit: int = 900) -> str:
    text = normalize_whitespace(text)
    return text if len(text) <= limit else f"{text[: limit - 3].rstrip()}..."


def dedupe_rows(rows: list[dict]) -> list[dict]:
    deduped = []
    seen = set()
    for row in rows:
        name = normalize_whitespace(row.get("plan_name")).lower()
        url = normalize_url(row.get("plan_url"))
        if not name or (name, url) in seen:
            continue
        seen.add((name, url))
        deduped.append(row)
    return deduped


def scrape_singlife(
    session=requests,
    source_urls: tuple[str, ...] | list[str] = SOURCE_URLS,
) -> list[dict]:
    rows = []
    for source_url in source_urls:
        try:
            rows.extend(parse_source_html(fetch_html(source_url, session=session), source_url))
        except Exception as exc:
            print(f"[{TABLE_NAME}] skipping {source_url}: {exc}")
            continue
    return dedupe_rows(rows)


async def scrape_data(url):
    return parse_source_html(fetch_html(url), url)


async def run_all_tasks(scrape_list):
    return await gather_scrape_results(TABLE_NAME, scrape_list, scrape_data)


def assert_semantic_quality(rows: list[dict]) -> None:
    findings = validate_plan_rows(format_plan_rows(TABLE_NAME, rows))
    if findings:
        details = "; ".join(finding.format() for finding in findings[:5])
        raise ValueError(f"Singlife scraper produced invalid plan rows: {details}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    try:
        rows = scrape_singlife()
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
