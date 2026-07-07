"""
https://www.sompo.com.sg/
https://www.sompo.com.sg/products/travel
https://www.sompo.com.sg/products/home
https://www.sompo.com.sg/products/pa-ease
https://www.sompo.com.sg/products/private-car
https://www.sompo.com.sg/products/pa-star
https://www.sompo.com.sg/products/maidease
https://www.sompo.com.sg/products/pa-junior
https://www.sompo.com.sg/products/overseas-travel
https://www.sompo.com.sg/commercial-insurance-products/property
https://www.sompo.com.sg/commercial-insurance-products/burglary
https://www.sompo.com.sg/commercial-insurance-products/money
https://www.sompo.com.sg/commercial-insurance-products/plate-glass
https://www.sompo.com.sg/commercial-insurance-products/fidelity-guarantee
https://www.sompo.com.sg/commercial-insurance-products/group-mediwell-classic
https://www.sompo.com.sg/commercial-insurance-products/group-personal-accident
https://www.sompo.com.sg/commercial-insurance-products/work-injury-compensation
https://www.sompo.com.sg/commercial-insurance-products/public-liability
https://www.sompo.com.sg/commercial-insurance-products/marine-cargo
https://www.sompo.com.sg/commercial-insurance-products/bailees-forwarders-liability-move-@360
https://www.sompo.com.sg/commercial-insurance-products/spectra-office
https://www.sompo.com.sg/commercial-insurance-products/spectra-light-industrial
https://www.sompo.com.sg/commercial-insurance-products/sme
https://www.sompo.com.sg/commercial-insurance-products/spectra-service
https://www.sompo.com.sg/commercial-insurance-products/sme-data-cyber-security
https://www.sompo.com.sg/commercial-insurance-products/spectra-retail
https://www.sompo.com.sg/commercial-insurance-products/pleasurecraft-sail@360
https://www.sompo.com.sg/commercial-insurance-products/spectra-food-beverage
https://www.sompo.com.sg/commercial-insurance-products/commercial-motor
https://www.sompo.com.sg/claims/claims-list
"""

from __future__ import annotations

import argparse
import asyncio
import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from src.backend.helper import format_plan_rows, initialize_data_store, overwrite_plans_for_insurer
from src.lib.http_identity import BOT_USER_AGENT
from src.lib.scraper_health import record_scraper_failure
from src.scrapers.navigation import gather_scrape_results
from src.validation.plan_quality import validate_plan_rows

TABLE_NAME = "sompo"
REQUEST_TIMEOUT_SECONDS = 20

PRODUCT_URLS = [
    "https://www.sompo.com.sg/products/travel",
    "https://www.sompo.com.sg/products/home",
    "https://www.sompo.com.sg/products/pa-ease",
    "https://www.sompo.com.sg/products/private-car",
    "https://www.sompo.com.sg/products/pa-star",
    "https://www.sompo.com.sg/products/maidease",
    "https://www.sompo.com.sg/products/pa-junior",
    "https://www.sompo.com.sg/products/overseas-travel",
    "https://www.sompo.com.sg/commercial-insurance-products/property",
    "https://www.sompo.com.sg/commercial-insurance-products/burglary",
    "https://www.sompo.com.sg/commercial-insurance-products/money",
    "https://www.sompo.com.sg/commercial-insurance-products/plate-glass",
    "https://www.sompo.com.sg/commercial-insurance-products/fidelity-guarantee",
    "https://www.sompo.com.sg/commercial-insurance-products/group-mediwell-classic",
    "https://www.sompo.com.sg/commercial-insurance-products/group-personal-accident",
    "https://www.sompo.com.sg/commercial-insurance-products/work-injury-compensation",
    "https://www.sompo.com.sg/commercial-insurance-products/public-liability",
    "https://www.sompo.com.sg/commercial-insurance-products/marine-cargo",
    "https://www.sompo.com.sg/commercial-insurance-products/bailees-forwarders-liability-move-@360",
    "https://www.sompo.com.sg/commercial-insurance-products/spectra-office",
    "https://www.sompo.com.sg/commercial-insurance-products/spectra-light-industrial",
    "https://www.sompo.com.sg/commercial-insurance-products/sme",
    "https://www.sompo.com.sg/commercial-insurance-products/spectra-service",
    "https://www.sompo.com.sg/commercial-insurance-products/sme-data-cyber-security",
    "https://www.sompo.com.sg/commercial-insurance-products/spectra-retail",
    "https://www.sompo.com.sg/commercial-insurance-products/pleasurecraft-sail@360",
    "https://www.sompo.com.sg/commercial-insurance-products/spectra-food-beverage",
    "https://www.sompo.com.sg/commercial-insurance-products/commercial-motor",
]

REJECTED_SOURCE_URLS = {
    "https://www.sompo.com.sg/",
    "https://www.sompo.com.sg/claims/claims-list",
    "https://www.sompo.com.sg/commercial-insurance-products/sme",
}

PLAN_NAME_BY_PATH = {
    "/products/travel": "Travel Insurance",
    "/products/home": "Home Insurance",
    "/products/pa-ease": "PA Ease Insurance",
    "/products/private-car": "Private Car Insurance",
    "/products/pa-star": "PAStar Insurance",
    "/products/maidease": "MaidEase",
    "/products/pa-junior": "PAJunior",
    "/products/overseas-travel": "Overseas Travel Accident PLUS",
    "/commercial-insurance-products/property": "Property Insurance",
    "/commercial-insurance-products/burglary": "Burglary Insurance",
    "/commercial-insurance-products/money": "Money Insurance",
    "/commercial-insurance-products/plate-glass": "Plate Glass Insurance",
    "/commercial-insurance-products/fidelity-guarantee": "Fidelity Guarantee Insurance",
    "/commercial-insurance-products/group-mediwell-classic": "Group Mediwell Classic Insurance",
    "/commercial-insurance-products/group-personal-accident": "Group Personal Accident Insurance",
    "/commercial-insurance-products/work-injury-compensation": "Work Injury Compensation Insurance",
    "/commercial-insurance-products/public-liability": "Public Liability Insurance",
    "/commercial-insurance-products/marine-cargo": "Marine Cargo Insurance",
    "/commercial-insurance-products/bailees-forwarders-liability-move-@360": (
        "Bailees / Forwarders Liability - Move @360"
    ),
    "/commercial-insurance-products/spectra-office": "Spectra Office Insurance",
    "/commercial-insurance-products/spectra-light-industrial": "Spectra Light Industrial Insurance",
    "/commercial-insurance-products/spectra-service": "Spectra Service Insurance",
    "/commercial-insurance-products/sme-data-cyber-security": (
        "SME Data & Cyber Security Insurance"
    ),
    "/commercial-insurance-products/spectra-retail": "Spectra Retail Insurance",
    "/commercial-insurance-products/pleasurecraft-sail@360": "Pleasurecraft / Sail@360",
    "/commercial-insurance-products/spectra-food-beverage": "Spectra Food & Beverage Insurance",
    "/commercial-insurance-products/commercial-motor": "Commercial Motor Insurance",
}

STOP_SECTION_HEADINGS = (
    "details of coverage",
    "download center",
    "downloads center",
    "find a suitable plan",
    "compare plans",
    "online help",
    "frequently asked questions",
    "faq",
    "faqs",
    "claims journey",
    "blogs",
)

SKIP_TEXT_PATTERNS = (
    "buy now",
    "call 6461",
    "call 65",
    "cheers grow louder",
    "email us at",
    "enjoy peace of mind, for less",
    "football season",
    "important notice",
    "information correct as",
    "policy owners' protection scheme",
    "policy owners’ protection scheme",
    "promotion",
    "promotion terms",
    "privacy policy",
    "product brochures",
    "proposal forms",
    "roam01",
    "score 25%",
    "secure your coverage today",
    "stay protected and connected",
    "travel confidently and share",
    "contact us",
    "copyright",
    "you might also be interested",
    "need more help",
    "online help",
    "download center",
    "downloads center",
)

SECTION_LABELS = (
    "benefits at a glance",
    "building reinstatement cost",
    "coverage",
    "eligibility",
    "features",
    "important notice",
    "occupation classification",
    "optional cover",
    "premium",
    "product / plan type",
    "product highlights",
    "promotion",
    "schedule of benefits",
    "table of compensation",
    "faqs",
)

PDF_REJECT_PATTERNS = (
    "application",
    "claim",
    "declaration",
    "form",
    "giro",
    "panel",
    "payment",
    "proposal",
    "wording",
    "workshop",
)


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


def source_path(source_url: str) -> str:
    return urlparse(source_url).path.rstrip("/") or "/"


def meta_content(soup: BeautifulSoup, selector: str) -> str:
    element = soup.select_one(selector)
    return normalize_whitespace(element.get("content")) if element else ""


def is_rejected_url(source_url: str) -> bool:
    path = source_path(source_url)
    return source_url.rstrip("/") in {url.rstrip("/") for url in REJECTED_SOURCE_URLS} or (
        path not in PLAN_NAME_BY_PATH
    )


def clean_soup(soup: BeautifulSoup) -> BeautifulSoup:
    for element in soup(["script", "style", "noscript", "svg", "header", "footer", "nav"]):
        element.decompose()
    return soup


def first_heading(soup: BeautifulSoup) -> str:
    for element in soup.find_all(["h1", "h2"], limit=8):
        text = normalize_whitespace(element.get_text(" ", strip=True))
        if text and not should_skip_text(text):
            return text
    return ""


def text_blocks_until_stop(soup: BeautifulSoup) -> list[str]:
    blocks: list[str] = []
    seen: set[str] = set()
    has_h1 = soup.find("h1") is not None
    started = False
    for element in soup.find_all(["h1", "h2", "h3", "h4", "p", "li", "td", "th"]):
        text = normalize_whitespace(element.get_text(" ", strip=True))
        if not text:
            continue
        lower = text.lower()
        if element.name in {"h1", "h2", "h3", "h4"} and any(
            heading in lower for heading in STOP_SECTION_HEADINGS
        ):
            break
        if not started and (
            element.name == "h1" or (not has_h1 and element.name == "h2" and "highlight" in lower)
        ):
            started = True
        if not started:
            continue
        if should_skip_text(text) or text in seen:
            continue
        seen.add(text)
        blocks.append(text)
    return blocks


def should_skip_text(text: str) -> bool:
    lower = text.lower()
    return (
        len(text) < 4
        or any(pattern in lower for pattern in SKIP_TEXT_PATTERNS)
        or lower.startswith("protected up to specified limits")
        or "%" in text
    )


def build_benefits(blocks: list[str], plan_name: str) -> list[str]:
    benefits: list[str] = []
    for text in blocks:
        if text == plan_name or is_section_label(text):
            continue
        if len(text) < 20:
            continue
        if len(text) > 260:
            text = text[:257].rstrip() + "..."
        benefits.append(text)
        if len(benefits) == 8:
            break
    return benefits


def is_section_label(text: str) -> bool:
    return text.lower() in SECTION_LABELS


def first_brochure_url(soup: BeautifulSoup, source_url: str) -> str:
    candidates: list[tuple[int, str]] = []
    for anchor in soup.select("a[href]"):
        href = anchor.get("href") or ""
        text = normalize_whitespace(anchor.get_text(" ", strip=True))
        combined = f"{text} {href}".lower()
        if ".pdf" not in href.lower():
            continue
        if "download" in combined and ".pdf" not in combined:
            continue
        if (
            any(pattern in combined for pattern in PDF_REJECT_PATTERNS)
            and "brochure" not in combined
        ):
            continue
        score = 0
        if "brochure" in combined:
            score -= 10
        if ".pdf" in href.lower():
            score -= 2
        if any(pattern in combined for pattern in PDF_REJECT_PATTERNS):
            score += 5
        candidates.append((score, urljoin(source_url, href)))
    if not candidates:
        return ""
    candidates.sort(key=lambda item: item[0])
    return candidates[0][1]


def parse_product_html(html: str, source_url: str) -> dict | None:
    if is_rejected_url(source_url):
        return None

    soup = clean_soup(BeautifulSoup(html, "html.parser"))
    title = first_heading(soup)
    if "404" in title or "page not found" in title.lower():
        return None

    plan_name = PLAN_NAME_BY_PATH[source_path(source_url)]
    blocks = [block for block in text_blocks_until_stop(soup) if block != title]
    meaningful_blocks = [
        block for block in blocks if block != plan_name and not is_section_label(block)
    ]
    description = (
        meta_content(soup, 'meta[name="description"]')
        or meta_content(soup, 'meta[property="og:description"]')
        or next(
            (block for block in meaningful_blocks if len(block) > 40),
            next(iter(meaningful_blocks), plan_name),
        )
    )
    benefits = build_benefits(blocks, plan_name)
    overview_parts = [description, *benefits[:4]]

    return {
        "plan_name": plan_name,
        "plan_description": description[:500],
        "plan_overview": " ".join(overview_parts)[:1200],
        "plan_benefits": benefits,
        "plan_url": source_url,
        "product_brochure_url": first_brochure_url(soup, source_url),
    }


def scrape_sompo(session=requests, product_urls: list[str] | None = None) -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()
    for url in product_urls or PRODUCT_URLS:
        row = parse_product_html(fetch_html(url, session=session), url)
        if not row or row["plan_url"] in seen:
            continue
        seen.add(row["plan_url"])
        rows.append(row)
    return rows


def scrape_product_url(url: str, session=requests) -> dict | None:
    return parse_product_html(fetch_html(url, session=session), url)


async def scrape_data(url: str) -> dict | None:
    return await asyncio.to_thread(scrape_product_url, url)


async def run_all_tasks(scrape_list: list[str]) -> list[dict]:
    return await gather_scrape_results(TABLE_NAME, scrape_list, scrape_data)


def assert_semantic_quality(rows: list[dict]) -> None:
    findings = validate_plan_rows(format_plan_rows(TABLE_NAME, rows))
    if findings:
        raise ValueError(findings[0].format())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.parse_known_args()

    rows = asyncio.run(run_all_tasks(PRODUCT_URLS))
    print(f"[{TABLE_NAME}] produced {len(rows)} plan rows")
    assert_semantic_quality(rows)
    if not rows:
        record_scraper_failure(TABLE_NAME, "no plan rows produced")
        return
    initialize_data_store()
    overwrite_plans_for_insurer(TABLE_NAME, rows)


if __name__ == "__main__":
    main()
