"""
CHUBB

https://www.chubb.com/sg-en/individuals-families.html
https://www.chubb.com/sg-en/individuals-families/travel-insurance.html
https://www.chubb.com/sg-en/individuals-families/home-insurance.html
https://www.chubb.com/sg-en/individuals-families/personal-accident-insurance.html
https://www.chubb.com/sg-en/individuals-families/staycation-insurance.html
https://www.chubb.com/sg-en/individuals-families/coach-and-ferry-travel-insurance.html
"""

# ----- required imports -----

import argparse
import asyncio
import re
from urllib.parse import urldefrag, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from src.backend.helper import (
    format_plan_rows,
    initialize_data_store,
    overwrite_plans_for_insurer,
)
from src.lib.http_identity import BOT_USER_AGENT
from src.lib.scraper_health import record_scraper_failure
from src.scrapers.navigation import gather_scrape_results
from src.validation.plan_quality import validate_plan_rows

# ----- functions -----

TABLE_NAME = "chubb"
CHUBB_BASE_URL = "https://www.chubb.com"
REQUEST_TIMEOUT_SECONDS = 20
SOURCE_URLS = (
    "https://www.chubb.com/sg-en/individuals-families.html",
    "https://www.chubb.com/sg-en/individuals-families/travel-insurance.html",
    "https://www.chubb.com/sg-en/individuals-families/home-insurance.html",
    "https://www.chubb.com/sg-en/individuals-families/personal-accident-insurance.html",
    "https://www.chubb.com/sg-en/individuals-families/staycation-insurance.html",
    "https://www.chubb.com/sg-en/individuals-families/coach-and-ferry-travel-insurance.html",
)
REJECTED_SOURCE_URLS = {
    "https://www.chubb.com/sg-en/individuals-families.html",
    "https://www.chubb.com/sg-en/claims.html",
    "https://www.chubb.com/sg-en/contact-us.html",
}
SUPPORT_SOURCE_URLS = {
    "https://www.chubb.com/sg-en/claims.html",
    "https://www.chubb.com/sg-en/contact-us.html",
}
SKIP_SLUGS = {
    "individuals-families",
    "travel-protection",
    "accident-protection",
    "personal-protection",
}
CHROME_PATTERNS = (
    "about chubb",
    "broker login",
    "careers",
    "claims centre",
    "contact us",
    "explore chubb",
    "newsroom",
    "privacy policy",
    "terms of use",
)
BENEFIT_KEYWORDS = ("cover", "benefit", "claim", "insurance", "medical", "protection")


def normalize_whitespace(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def normalize_url(value: str) -> str:
    return urldefrag(str(value or "").strip()).url.rstrip("/")


def fetch_html(url: str, session: requests.Session | None = None) -> str:
    client = session or requests
    response = client.get(
        url,
        timeout=REQUEST_TIMEOUT_SECONDS,
        headers={"User-Agent": BOT_USER_AGENT},
    )
    response.raise_for_status()
    return response.text


def is_chubb_product_url(url: str) -> bool:
    parsed = urlparse(url)
    slug = parsed.path.rstrip("/").rsplit("/", 1)[-1].removesuffix(".html")
    return (
        "/sg-en/individuals-families/" in parsed.path
        and slug not in SKIP_SLUGS
        and normalize_url(url) not in {normalize_url(source) for source in REJECTED_SOURCE_URLS}
    )


def discover_product_links(html_content: str, source_url: str) -> list[str]:
    soup = BeautifulSoup(html_content, "html.parser")
    links = []
    seen = set()
    for anchor in soup.select("a[href]"):
        href = urljoin(source_url, anchor.get("href") or "")
        if not is_chubb_product_url(href) or href in seen:
            continue
        seen.add(href)
        links.append(href)
    return links


def meta_description(soup: BeautifulSoup) -> str:
    meta = soup.select_one('meta[name="description"]')
    return normalize_whitespace(meta.get("content")) if meta else ""


def first_pdf_url(soup: BeautifulSoup, source_url: str) -> str:
    for anchor in soup.select("a[href]"):
        href = anchor.get("href") or ""
        if ".pdf" in href.lower():
            return urljoin(source_url, href)
    return ""


def parse_product_html(html_content: str, source_url: str) -> dict | None:
    if not is_chubb_product_url(source_url):
        return None
    soup = BeautifulSoup(html_content, "html.parser")
    root = content_root(soup)
    title = normalize_whitespace((soup.select_one("h1") or soup.select_one("title")).get_text(" "))
    if "|" in title:
        title = normalize_whitespace(title.split("|", 1)[0])
    if not title or looks_like_chrome(title):
        return None

    description = meta_description(soup)
    text_blocks = [
        normalize_whitespace(element.get_text(" ", strip=True))
        for element in root.select("p, li, div.text-description")
    ]
    text_blocks = [
        text
        for text in text_blocks
        if is_content_text(text) and text != title and not looks_like_chrome(text)
    ]
    benefits = []
    for text in text_blocks:
        lowered = text.lower()
        if title.lower() in lowered and len(text) > len(title) + 20:
            description = description or text
        if any(keyword in lowered for keyword in BENEFIT_KEYWORDS):
            benefits.append(text)
    benefits = list(dict.fromkeys(benefits))[:12]

    row = {
        "plan_name": title,
        "plan_benefits": benefits,
        "plan_description": description or " ".join(text_blocks[:2]),
        "plan_overview": " ".join(text_blocks[:4]),
        "plan_url": source_url,
        "product_brochure_url": first_pdf_url(soup, source_url),
    }
    row["plan_description"] = compact_text(row["plan_description"], 500)
    row["plan_overview"] = compact_text(row["plan_overview"], 900)
    return row if valid_plan_row(row) else None


def content_root(soup: BeautifulSoup):
    return soup.select_one("div.root.container.responsivegrid") or soup


def scrape_page(url: str) -> list[dict]:
    if normalize_url(url) in {normalize_url(source) for source in SUPPORT_SOURCE_URLS}:
        return []
    html_content = fetch_html(url)
    urls = [url] if is_chubb_product_url(url) else discover_product_links(html_content, url)
    rows = []
    for plan_url in urls:
        plan_html = html_content if plan_url == url else fetch_html(plan_url)
        row = parse_product_html(plan_html, plan_url)
        if row:
            rows.append(row)
    return rows


async def scrape_data(url):
    return await asyncio.to_thread(scrape_page, url)


async def run_all_tasks(scrape_list):
    return dedupe_rows(await gather_scrape_results(TABLE_NAME, scrape_list, scrape_data))


def dedupe_rows(rows: list[dict]) -> list[dict]:
    deduped = []
    seen = set()
    for row in rows:
        key = row.get("plan_url") or row.get("plan_name")
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def valid_plan_row(row: dict) -> bool:
    if not row.get("plan_name") or not row.get("plan_url") or not row.get("plan_description"):
        return False
    values = (row.get("plan_name"), row.get("plan_description"), row.get("plan_overview"))
    return not any(looks_like_chrome(value) for value in values)


def looks_like_chrome(value: str | None) -> bool:
    lowered = normalize_whitespace(value).lower()
    return any(pattern in lowered for pattern in CHROME_PATTERNS)


def is_content_text(value: str | None) -> bool:
    text = normalize_whitespace(value)
    lowered = text.lower()
    if len(text) < 18 or len(text) > 900:
        return False
    if lowered in {"learn more", "get a quote", "make a claim"}:
        return False
    return not looks_like_chrome(text)


def compact_text(value: str | None, limit: int) -> str:
    text = normalize_whitespace(value)
    return text if len(text) <= limit else f"{text[: limit - 3].rstrip()}..."


def assert_semantic_quality(rows: list[dict]) -> None:
    findings = validate_plan_rows(format_plan_rows(TABLE_NAME, rows))
    if findings:
        details = "; ".join(finding.format() for finding in findings[:5])
        raise ValueError(f"Chubb scraper produced invalid plan rows: {details}")


# ----- sample execution code -----

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        output = asyncio.run(run_all_tasks(SOURCE_URLS))
        assert_semantic_quality(output)
    except Exception as error:
        if not args.dry_run:
            record_scraper_failure(TABLE_NAME, error)
        raise
    print(f"[{TABLE_NAME}] produced {len(output)} plan rows")
    if not output:
        record_scraper_failure(TABLE_NAME, "no plan rows produced", dry_run=args.dry_run)
        raise SystemExit(1)
    if not args.dry_run:
        initialize_data_store()
    overwrite_plans_for_insurer(TABLE_NAME, output)
