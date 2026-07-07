"""
TOKIO MARINE

https://www.tokiomarine.com/sg/en.html
https://www.tokiomarine.com/sg/en/life/claim/submit-a-claim.html

https://www.tokiomarine.com/sg/en/non-life.html
https://www.tokiomarine.com/sg/en/life.html
"""

from __future__ import annotations

import argparse
import asyncio
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

if __package__ in {None, ""}:
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.backend.helper import (
    format_plan_rows,
    initialize_data_store,
    overwrite_plans_for_insurer,
)
from src.lib.scraper_health import record_scraper_failure
from src.scrapers.navigation import gather_scrape_results, goto_with_retry, new_bot_context
from src.validation.plan_quality import validate_plan_rows

TABLE_NAME = "tokio_marine"
BASE_URL = "https://www.tokiomarine.com"

SCRAPE_LIST = [
    "https://www.tokiomarine.com/sg/en/non-life.html",
    "https://www.tokiomarine.com/sg/en/life.html",
]

NON_PRODUCT_PATTERNS = (
    "accept policy",
    "browse our products",
    "contact us",
    "cookie policy",
    "important information",
    "privacy policy",
    "terms of use",
)

BENEFIT_KEYWORDS = (
    "accident",
    "benefit",
    "building",
    "cover",
    "coverage",
    "damage",
    "death",
    "disablement",
    "expenses",
    "medical",
    "premium",
    "workshop",
)


def normalize_whitespace(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def compact_text(value: str, limit: int = 900) -> str:
    value = normalize_whitespace(value)
    return value if len(value) <= limit else f"{value[: limit - 3].rstrip()}..."


def is_content_text(text: str) -> bool:
    lowered = normalize_whitespace(text).lower()
    if len(lowered) < 12:
        return False
    return not any(pattern in lowered for pattern in NON_PRODUCT_PATTERNS)


def clean_blocks(values: list[str], limit: int = 900) -> list[str]:
    blocks = []
    seen = set()
    for value in values:
        text = compact_text(value, limit=limit)
        if not is_content_text(text) or text in seen:
            continue
        seen.add(text)
        blocks.append(text)
    return blocks


def benefit_blocks(values: list[str]) -> list[str]:
    benefits = []
    for value in clean_blocks(values, limit=220):
        lowered = value.lower()
        if any(keyword in lowered for keyword in BENEFIT_KEYWORDS):
            benefits.append(value)
    return benefits[:8]


def build_plan_record(
    plan_name: str,
    plan_overview: str,
    descriptions: list[str],
    plan_url: str,
    pdf_url: str = "",
) -> dict | None:
    plan_name = normalize_whitespace(plan_name)
    if not plan_name:
        return None
    blocks = clean_blocks(descriptions)
    description = compact_text(plan_overview or (blocks[0] if blocks else ""), limit=500)
    overview = compact_text(" ".join(blocks[:2]))
    return {
        "plan_name": plan_name,
        "plan_benefits": benefit_blocks(descriptions),
        "plan_description": description,
        "plan_overview": overview,
        "plan_url": plan_url,
        "product_brochure_url": pdf_url,
    }


def parse_product_html(html: str, url: str) -> dict | None:
    soup = BeautifulSoup(html, "html.parser")
    title_element = soup.select_one("h2.masthead-colors__title") or soup.select_one("h1")
    overview_element = soup.select_one("h2.masthead-colors__text")
    plan_name = normalize_whitespace(
        title_element.get_text(" ", strip=True) if title_element else ""
    )
    plan_overview = normalize_whitespace(
        overview_element.get_text(" ", strip=True) if overview_element else ""
    )
    descriptions = [
        element.get_text(" ", strip=True) for element in soup.select("div.section-wrap")
    ]
    pdf_url = ""
    for anchor in soup.select("a[href]"):
        href = anchor.get("href") or ""
        if ".pdf" in href.lower():
            pdf_url = urljoin(url, href)
            break
    return build_plan_record(plan_name, plan_overview, descriptions, url, pdf_url)


async def scrape_data(url):
    scraped_plans = []
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True, args=["--disable-http2"])
        context = await new_bot_context(browser)
        page = await context.new_page()
        await goto_with_retry(page, url)

        plan_urls = []
        seen_urls = set()
        for link in await page.query_selector_all("div.quick-help-custom__item a"):
            href = await link.get_attribute("href")
            full_url = urljoin(BASE_URL, href or "")
            if href and full_url not in seen_urls:
                seen_urls.add(full_url)
                plan_urls.append(full_url)

        for plan_url in plan_urls:
            plan_page = await page.context.new_page()
            await goto_with_retry(plan_page, plan_url)
            title_element = await plan_page.query_selector("h2.masthead-colors__title")
            overview_element = await plan_page.query_selector("h2.masthead-colors__text")
            description_elements = await plan_page.query_selector_all("div.section-wrap")
            anchor_tags = await plan_page.query_selector_all("a")

            plan_name = (await title_element.text_content()).strip() if title_element else ""
            plan_overview = (
                (await overview_element.text_content()).strip() if overview_element else ""
            )
            descriptions = [
                (await description.text_content()).strip()
                for description in description_elements
                if description
            ]

            pdf_url = ""
            for anchor in anchor_tags:
                href = await anchor.get_attribute("href")
                if href and ".pdf" in href.lower():
                    pdf_url = urljoin(plan_url, href)
                    break

            row = build_plan_record(plan_name, plan_overview, descriptions, plan_url, pdf_url)
            if row:
                scraped_plans.append(row)
            await plan_page.close()

        await browser.close()
        return scraped_plans


async def run_all_tasks(scrape_list):
    return await gather_scrape_results(TABLE_NAME, scrape_list, scrape_data)


def assert_semantic_quality(rows: list[dict]) -> None:
    findings = validate_plan_rows(format_plan_rows(TABLE_NAME, rows))
    if findings:
        details = "; ".join(finding.format() for finding in findings[:5])
        raise ValueError(f"Tokio Marine scraper produced invalid plan rows: {details}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    try:
        rows = asyncio.run(run_all_tasks(SCRAPE_LIST))
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
