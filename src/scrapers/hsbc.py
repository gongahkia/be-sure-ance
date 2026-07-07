"""
HSBC INSURANCE

https://www.insurance.hsbc.com.sg/
https://www.insurance.hsbc.com.sg/claims/
https://www.insurance.hsbc.com.sg/life-and-critical-illness/products/
https://www.insurance.hsbc.com.sg/savings/
https://www.insurance.hsbc.com.sg/investment/
https://www.insurance.hsbc.com.sg/employee-health-benefits/
https://www.insurance.hsbc.com.sg/health/
https://www.insurance.hsbc.com.sg/legacy/
https://www.insurance.hsbc.com.sg/retirement/
https://www.insurance.hsbc.com.sg/personal-accident/
"""

from __future__ import annotations

import argparse
import asyncio
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

TABLE_NAME = "hsbc"
REQUEST_TIMEOUT_SECONDS = 20

PRODUCT_CATALOG = (
    (
        "HSBC Life – Life Treasure III",
        "https://www.insurance.hsbc.com.sg/life-and-critical-illness/products/life-treasure-iii/",
        "A whole life insurance plan with multiplied coverage, cash value accumulation and optional critical illness riders.",
    ),
    (
        "DIRECT – HSBC Life – Term Lite",
        "https://www.insurance.hsbc.com.sg/life-and-critical-illness/products/direct-term-lite/",
        "A direct term life insurance plan with practical, affordable protection.",
    ),
    (
        "HSBC Life Term Protect Advantage",
        "https://www.insurance.hsbc.com.sg/life-and-critical-illness/products/term-protect-advantage/",
        "A term plan with flexible premium and policy terms plus surrender value.",
    ),
    (
        "DIRECT - HSBC Life Protector II",
        "https://www.insurance.hsbc.com.sg/life-and-critical-illness/products/direct-life-protector/",
        "A whole life plan with flexible premiums and direct protection.",
    ),
    (
        "HSBC Life Term Protector / HSBC Life Term Protector Prime",
        "https://www.insurance.hsbc.com.sg/life-and-critical-illness/products/term-protector/",
        "Term life protection with selectable coverage term, payment options and currency.",
    ),
    (
        "HSBC Life ValueLife",
        "https://www.insurance.hsbc.com.sg/life-and-critical-illness/products/value-life/",
        "A life insurance plan with lifetime protection after a limited premium payment period.",
    ),
    (
        "HSBC Life HappyFamily",
        "https://www.insurance.hsbc.com.sg/life-and-critical-illness/products/happy-family/",
        "Bundled prenatal and family protection with an eligible HSBC Life basic plan.",
    ),
    (
        "HSBC Life HappyMummy",
        "https://www.insurance.hsbc.com.sg/life-and-critical-illness/products/happy-mummy/",
        "Prenatal cover for mother and newborn with bundled protection options.",
    ),
    (
        "HSBC Life Cancer ReCover",
        "https://www.insurance.hsbc.com.sg/life-and-critical-illness/products/cancerrecover/",
        "Cancer cover designed for cancer survivors, including recurrent or newly diagnosed cancers.",
    ),
    (
        "HSBC Life CritiCare for Her",
        "https://www.insurance.hsbc.com.sg/life-and-critical-illness/products/criticare-for-her/",
        "Critical illness cover focused on women's health conditions and multiple claims.",
    ),
    (
        "HSBC Life CritiCare for Him",
        "https://www.insurance.hsbc.com.sg/life-and-critical-illness/products/criticare-for-him/",
        "Critical illness cover focused on men's health conditions and multiple claims.",
    ),
    (
        "HSBC Life Super CritiCare",
        "https://www.insurance.hsbc.com.sg/life-and-critical-illness/products/super-criticare/",
        "Critical illness protection with multiple payouts and diabetes care support.",
    ),
    (
        "HSBC Life Wealth Builder",
        "https://www.insurance.hsbc.com.sg/savings/wealth-builder/",
        "A flexible savings plan for long-term wealth accumulation and policy continuity.",
    ),
    (
        "HSBC Life Savings Protector II",
        "https://www.insurance.hsbc.com.sg/savings/savings-protector/",
        "An endowment plan that protects savings while providing potentially higher payouts.",
    ),
    (
        "HSBC Life Goal Focus",
        "https://www.insurance.hsbc.com.sg/investment/products/goal-focus/",
        "An investment-linked plan with flexibility, bonuses, fund choice and built-in protection.",
    ),
    (
        "HSBC Life Wealth Focus",
        "https://www.insurance.hsbc.com.sg/investment/products/wealth-focus/",
        "A regular premium investment-linked plan for wealth growth and protection.",
    ),
    (
        "HSBC Life Goal Builder II",
        "https://www.insurance.hsbc.com.sg/investment/products/goal-builder/",
        "An investment-linked plan combining lifelong protection with wealth growth flexibility.",
    ),
    (
        "HSBC Life Wealth Abundance",
        "https://www.insurance.hsbc.com.sg/investment/products/wealth-abundance/",
        "An investment-linked plan with fund choice, bonuses and life protection.",
    ),
    (
        "HSBC Life Wealth Voyage",
        "https://www.insurance.hsbc.com.sg/investment/products/wealth-voyage/",
        "An investment-linked plan with bonuses for medium- to long-term wealth growth.",
    ),
    (
        "HSBC Life Wealth Harvest",
        "https://www.insurance.hsbc.com.sg/investment/products/wealth-harvest/",
        "A regular-premium investment-linked plan focused on long-term growth.",
    ),
    (
        "HSBC Life Wealth Invest",
        "https://www.insurance.hsbc.com.sg/investment/products/wealth-invest/",
        "Investment-linked protection with managed funds and death or terminal illness cover.",
    ),
    (
        "HSBC Life Wealth Accelerate",
        "https://www.insurance.hsbc.com.sg/investment/products/wealth-accelerate/",
        "An investment-linked plan with bonuses and flexible adaptation over the investment horizon.",
    ),
    (
        "HSBC Life Flexi Protector",
        "https://www.insurance.hsbc.com.sg/investment/products/flexi-protector/",
        "Lifetime protection with savings and investment flexibility.",
    ),
    (
        "HSBC Life Benefits+",
        "https://www.insurance.hsbc.com.sg/employee-health-benefits/products/benefits-plus/",
        "A customisable employee benefits plan for group health protection.",
    ),
    (
        "HSBC Life Benefits+ Business",
        "https://www.insurance.hsbc.com.sg/employee-health-benefits/products/benefits-plus-business/",
        "Corporate health insurance with flexible employee coverage options.",
    ),
    (
        "HSBC Life Benefits+ International",
        "https://www.insurance.hsbc.com.sg/employee-health-benefits/products/group-international-exclusive/",
        "Group healthcare insurance with international medical access.",
    ),
    (
        "HSBC Life Benefits+ International Max",
        "https://www.insurance.hsbc.com.sg/employee-health-benefits/products/group-international-exclusive-plus/",
        "Comprehensive corporate healthcare coverage with worldwide hospital choice.",
    ),
    (
        "HSBC Life Shield",
        "https://www.insurance.hsbc.com.sg/health/products/shield/",
        "Medical reimbursement cover that complements MediShield Life.",
    ),
    (
        "HSBC Life Prime Care",
        "https://www.insurance.hsbc.com.sg/health/products/prime-care/",
        "Additional health insurance for medical and hospitalisation expenses.",
    ),
    (
        "HSBC Life SmartCare Executive",
        "https://www.insurance.hsbc.com.sg/health/products/smartcare-executive/",
        "A flexible health insurance plan tailored to budget and protection needs.",
    ),
    (
        "HSBC Life SmartCare Optimum Enhanced",
        "https://www.insurance.hsbc.com.sg/health/products/smartcare-optimum-enhanced/",
        "Enhanced health insurance with high annual limits and add-on options.",
    ),
    (
        "HSBC Life International Exclusive",
        "https://www.insurance.hsbc.com.sg/health/products/international-exclusive/",
        "International health insurance with private medical access and cashless hospital admissions.",
    ),
    (
        "HSBC Life GlobalCare Health Plan",
        "https://www.insurance.hsbc.com.sg/health/products/globalcare-health-plan/",
        "International medical insurance with geographic coverage choices and high annual limits.",
    ),
    (
        "HSBC Life Diamond Prestige IUL II",
        "https://www.insurance.hsbc.com.sg/legacy/products/diamond-prestige-iul/",
        "Indexed universal life protection for wealth preservation and legacy planning.",
    ),
    (
        "HSBC Life Jade Legacy Universal Life Plans",
        "https://www.insurance.hsbc.com.sg/legacy/jade/",
        "Universal life protection for wealth accumulation and asset preservation.",
    ),
    (
        "HSBC Life Emerald Legacy Life III",
        "https://www.insurance.hsbc.com.sg/legacy/products/emerald-legacy-life/",
        "Single premium whole life cover with guaranteed cash value and lifelong protection.",
    ),
    (
        "HSBC Life Private Wealth VUL",
        "https://www.insurance.hsbc.com.sg/content/dam/hsbc/insn/documents/hsbc-life-private-wealth-vul-brochure.pdf",
        "A variable universal life plan for legacy wealth, liquidity and cash-flow planning.",
    ),
    (
        "HSBC Life Indexed Flexi Income",
        "https://www.insurance.hsbc.com.sg/retirement/products/indexed-flexi-income/",
        "An indexed universal life plan with optional monthly income payouts for life.",
    ),
    (
        "HSBC Life Band Aid",
        "https://www.insurance.hsbc.com.sg/personal-accident/products/band-aid/",
        "Personal accident cover for death or permanent disability due to accident.",
    ),
)

PRODUCT_URLS = tuple(url for _name, url, _description in PRODUCT_CATALOG)
REJECTED_SOURCE_URLS = (
    "https://www.insurance.hsbc.com.sg/",
    "https://www.insurance.hsbc.com.sg/claims/",
    "https://www.insurance.hsbc.com.sg/help/",
    "https://www.insurance.hsbc.com.sg/help/make-a-payment/",
    "https://www.insurance.hsbc.com.sg/contact-us/",
    "https://www.insurance.hsbc.com.sg/content/dam/hsbc/insn/documents/life-hnw-legacy-research-report.pdf",
)

CHROME_PATTERNS = (
    "about hsbc insurance",
    "agent and distributor resource",
    "all rights reserved",
    "contact us",
    "document portal",
    "find a branch",
    "forms and documents",
    "fund prices",
    "help and support",
    "how to claim",
    "insurance help and support",
    "make a payment",
    "privacy and security",
    "quick links",
    "resource library",
    "terms of use",
    "ways to pay your premiums",
)

BENEFIT_KEYWORDS = (
    "benefit",
    "bonus",
    "cash",
    "claim",
    "cover",
    "coverage",
    "critical",
    "death",
    "disability",
    "fund",
    "health",
    "hospital",
    "income",
    "investment",
    "medical",
    "payout",
    "premium",
    "protection",
    "rider",
)


def normalize_url(url: str) -> str:
    clean_url = urldefrag(str(url or "").strip()).url
    if not clean_url or clean_url.lower().endswith(".pdf"):
        return clean_url
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
    catalog = catalog_row_for_url(source_url)
    if not catalog or source_url.lower().endswith(".pdf"):
        return None

    soup = BeautifulSoup(html, "html.parser")
    page_title = soup.title.get_text(" ", strip=True) if soup.title else ""
    if "404" in page_title:
        return None

    content = scoped_content(soup)
    description = meta_description(soup) or first_content_paragraph(content)
    if not is_content_text(description, max_length=500):
        description = catalog["plan_description"]

    benefits = benefit_blocks(content)
    if not benefits:
        benefits = [catalog["plan_description"]]
    overview_blocks = [
        description,
        *[benefit for benefit in benefits[:3] if benefit != description],
    ]
    row = {
        "plan_name": catalog["plan_name"],
        "plan_benefits": benefits[:8],
        "plan_description": compact_text(description, 500),
        "plan_overview": compact_text(" ".join(overview_blocks), 900),
        "plan_url": source_url,
        "product_brochure_url": brochure_url(soup, source_url),
    }
    return row if valid_plan_row(row) else None


def pdf_catalog_row(url: str) -> dict | None:
    catalog = catalog_row_for_url(url)
    if not catalog or not normalize_url(url).lower().endswith(".pdf"):
        return None
    row = {
        "plan_name": catalog["plan_name"],
        "plan_benefits": [catalog["plan_description"]],
        "plan_description": catalog["plan_description"],
        "plan_overview": catalog["plan_description"],
        "plan_url": normalize_url(url),
        "product_brochure_url": normalize_url(url),
    }
    return row if valid_plan_row(row) else None


def scoped_content(soup: BeautifulSoup) -> BeautifulSoup:
    content = soup.select_one("main") or soup.select_one("#main-content") or soup
    for element in content.select("script, style, noscript, svg, form, header, footer, nav"):
        element.decompose()
    return content


def meta_description(soup: BeautifulSoup) -> str:
    for selector in ('meta[name="description"]', 'meta[property="og:description"]'):
        element = soup.select_one(selector)
        text = normalize_whitespace(element.get("content", "") if element else "")
        if is_content_text(text, max_length=500):
            return text
    return ""


def first_content_paragraph(content: BeautifulSoup) -> str:
    for node in content.select("p"):
        text = normalize_whitespace(node.get_text(" ", strip=True))
        if is_content_text(text, max_length=500):
            return text
    return ""


def benefit_blocks(content: BeautifulSoup) -> list[str]:
    benefits = []
    for node in content.select("main li, li, main p, p"):
        text = normalize_whitespace(node.get_text(" ", strip=True))
        if not is_content_text(text, max_length=220):
            continue
        lowered = text.lower()
        if not any(keyword in lowered for keyword in BENEFIT_KEYWORDS):
            continue
        if text not in benefits:
            benefits.append(text)
    return benefits


def brochure_url(soup: BeautifulSoup, source_url: str) -> str:
    fallback = ""
    for anchor in soup.select("main a[href], a[href]"):
        href = anchor.get("href") or ""
        absolute = urljoin(source_url, href)
        lowered = f"{href} {anchor.get_text(' ', strip=True)}".lower()
        if ".pdf" not in absolute.lower():
            continue
        if "brochure" not in lowered:
            continue
        if "report" in lowered or "transcript" in lowered:
            continue
        fallback = fallback or absolute
        if "product brochure" in lowered or "download brochure" in lowered:
            return absolute
    return fallback


def is_content_text(text: str, max_length: int = 260) -> bool:
    if not text or len(text) > max_length:
        return False
    lowered = text.lower()
    if any(pattern in lowered for pattern in CHROME_PATTERNS):
        return False
    if lowered.startswith(("image", "download link", "find out how")):
        return False
    if "©" in text or "copyright" in lowered:
        return False
    return True


def compact_text(text: str, limit: int = 900) -> str:
    compacted = normalize_whitespace(text)
    if len(compacted) <= limit:
        return compacted
    return normalize_whitespace(compacted[:limit].rsplit(" ", 1)[0])


def valid_plan_row(row: dict) -> bool:
    if not row.get("plan_name") or not row.get("plan_url"):
        return False
    formatted = format_plan_rows(TABLE_NAME, [row])
    return validate_plan_rows(formatted) == []


def catalog_row_for_url(url: str) -> dict | None:
    normalized_url = normalize_url(url)
    for plan_name, plan_url, plan_description in PRODUCT_CATALOG:
        if normalize_url(plan_url) == normalized_url:
            return {
                "plan_name": plan_name,
                "plan_url": normalize_url(plan_url),
                "plan_description": plan_description,
            }
    return None


def scrape_product_url(url: str, session=requests) -> list[dict]:
    source_url = normalize_url(url)
    if source_url in {normalize_url(rejected) for rejected in REJECTED_SOURCE_URLS}:
        return []
    if source_url.lower().endswith(".pdf"):
        row = pdf_catalog_row(source_url)
        return [row] if row else []
    row = parse_product_html(fetch_html(source_url, session=session), source_url)
    return [row] if row else []


def scrape_hsbc(session=requests) -> list[dict]:
    rows = []
    for url in PRODUCT_URLS:
        try:
            rows.extend(scrape_product_url(url, session=session))
        except Exception as exc:
            print(f"[{TABLE_NAME}] skipping product {url}: {exc}")
            continue
    return dedupe_rows(rows)


def dedupe_rows(rows: list[dict]) -> list[dict]:
    seen = set()
    deduped = []
    for row in rows:
        key = normalize_url(row["plan_url"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


async def scrape_data(url):
    return await asyncio.to_thread(scrape_product_url, url)


async def run_all_tasks(scrape_list):
    return await gather_scrape_results(TABLE_NAME, scrape_list, scrape_data)


def assert_semantic_quality(rows: list[dict]) -> None:
    findings = validate_plan_rows(format_plan_rows(TABLE_NAME, rows))
    if findings:
        details = "; ".join(finding.format() for finding in findings[:5])
        raise ValueError(f"HSBC scraper produced invalid plan rows: {details}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    try:
        rows = asyncio.run(run_all_tasks(PRODUCT_URLS))
        assert_semantic_quality(rows)
    except Exception as error:
        if not args.dry_run:
            record_scraper_failure(TABLE_NAME, error)
        raise

    print(f"[{TABLE_NAME}] produced {len(rows)} plan rows")
    if not rows:
        record_scraper_failure(TABLE_NAME, "no plan rows produced", dry_run=args.dry_run)
        return 1
    if args.dry_run:
        print(
            {
                "dry_run": True,
                "insurer": TABLE_NAME,
                "plan_row_count": len(rows),
                "sample_plan_names": [row["plan_name"] for row in rows[:5]],
            }
        )
        return 0
    initialize_data_store()
    overwrite_plans_for_insurer(TABLE_NAME, rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
