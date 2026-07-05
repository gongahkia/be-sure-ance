"""
AIA

https://www.aia.com.sg/en/our-products/accident-protection
https://www.aia.com.sg/en/our-products/life-insurance
https://www.aia.com.sg/en/our-products/travel-and-lifestyle
https://www.aia.com.sg/en/our-products/platinum
https://www.aia.com.sg/en/our-products/health
https://www.aia.com.sg/en/our-products/save-and-invest
"""

# ----- required imports -----

import argparse
import asyncio
import html
import os
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from src.backend.helper import initialize_data_store, overwrite_plans_for_insurer
from src.lib.http_identity import BOT_USER_AGENT
from src.lib.scraper_health import record_scraper_failure
from src.scrapers.navigation import (
    gather_scrape_results,
    goto_with_retry,
    log_url_failure,
    new_bot_context,
)

# ----- functions -----

AIA_BASE_URL = "https://www.aia.com.sg"
REQUEST_TIMEOUT_SECONDS = 8
AIA_SOURCE_CACHE_DIR = os.getenv("AIA_SOURCE_CACHE_DIR", ".scraper-cache/aia")
URL_FAILURES = []
AIA_DIRECT_PRODUCT_URLS = [
    "https://www.aia.com.sg/en/our-products/health/medical-insurance/aia-healthshield-gold-max",
    "https://www.aia.com.sg/en/our-products/accident-protection/aia-solitaire-personal-accident",
    "https://www.aia.com.sg/en/our-products/accident-protection/aia-centurion-pa",
    "https://www.aia.com.sg/en/our-products/accident-protection/aia-platinum-accidentcare",
    "https://www.aia.com.sg/en/our-products/accident-protection/aia-star-protector-plus",
    "https://www.aia.com.sg/en/our-products/accident-protection/aia-genfit-pa",
    "https://www.aia.com.sg/en/our-products/life-insurance/whole-life-insurance/aia-guaranteed-protect-plus-iv",
    "https://www.aia.com.sg/en/our-products/life-insurance/whole-life-insurance/direct-aia-whole-life-cover-ii",
    "https://www.aia.com.sg/en/our-products/life-insurance/term-insurance/direct-aia-term-cover",
    "https://www.aia.com.sg/en/our-products/accident-protection/aia-prime-assured",
    "https://www.aia.com.sg/en/our-products/life-insurance/whole-life-insurance/aia-pro-lifetime-protector-ii",
    "https://www.aia.com.sg/en/our-products/life-insurance/term-insurance/aia-secure-flexi-term",
    "https://www.aia.com.sg/en/our-products/corporate-medical-insurance/aia-foreign-worker-protector-plus",
]


def remove_excess_newlines(inp):
    if not isinstance(inp, str):
        raise TypeError(f"Input must be type <string> but was type <{type(inp).__name__}>")
    inp = re.sub(r"\n+", "\n", inp)
    inp = re.sub(r"[ \t\u200b]+", " ", inp)
    return inp.strip()


def remove_html_entities(inp):
    inp2 = html.unescape(inp)
    replacements = {
        "\xa0": " ",  # Non-breaking space
        "\u200b": "",  # Zero-width space
        "\u2013": "-",  # En dash
        "\u2014": "--",  # Em dash
        "\u2026": "...",  # Ellipsis
        "\u2018": "'",  # Left single quote
        "\u2019": "'",  # Right single quote
        "\u201c": '"',  # Left double quote
        "\u201d": '"',  # Right double quote
        "\u00ab": '"',  # Left guillemet
        "\u00bb": '"',  # Right guillemet
        "\u02c6": "^",  # Circumflex
        "\u2039": "<",  # Single left angle quote
        "\u203a": ">",  # Single right angle quote
        "\u02dc": "~",  # Small tilde
        "\u00a9": "(c)",  # Copyright symbol
        "\u00ae": "(R)",  # Registered trademark symbol
        "\u2122": "(TM)",  # Trademark symbol
        "\u00b0": "°",  # Degree symbol
        "\u00b7": "*",  # Middle dot
        "\u00b1": "+/-",  # Plus-minus symbol
        "\u00bc": "1/4",  # One-quarter fraction
        "\u00bd": "1/2",  # One-half fraction
        "\u00be": "3/4",  # Three-quarters fraction
        "&lt;": "<",  # Less-than sign (HTML entity)
        "&gt;": ">",  # Greater-than sign (HTML entity)
        "&amp;": "&",  # Ampersand (HTML entity)
        "&quot;": '"',  # Quotation mark (HTML entity)
        "&apos;": "'",  # Apostrophe (HTML entity)
    }
    for old_char, new_char in replacements.items():
        inp2 = inp2.replace(old_char, new_char)
    return inp2


def parse_listing_html(html_content: str):
    soup = BeautifulSoup(html_content, "html.parser")
    product_filters_data = []
    for anchor in soup.select(".cmp-productfilterlist__container a"):
        h2_text = anchor.select_one("h2")
        next_div = anchor.select_one("h2 + div")
        product_filters_data.append(
            {
                "plan_name": h2_text.get_text(strip=True) if h2_text else "",
                "plan_url": urljoin(AIA_BASE_URL, anchor.get("href") or ""),
                "plan_description": next_div.get_text(" ", strip=True) if next_div else "",
            }
        )
    return product_filters_data


def parse_product_html(html_content: str):
    soup = BeautifulSoup(html_content, "html.parser")
    overview_content = soup.select_one(".cmp-productoverviewhero__content")
    title_content = soup.select_one("h1, .cmp-productoverviewhero__title")
    meta_description = soup.select_one('meta[name="description"]')
    meta_title = soup.select_one('meta[property="og:title"], meta[name="title"]')
    cta_button = soup.select_one(".cmp-button.cmp-button__primary")
    benefits = [
        benefit.get_text(" ", strip=True)
        for benefit in soup.select("div.cmp-featuredperk__content")
    ]
    if not benefits:
        benefits = [
            benefit.get_text(" ", strip=True)
            for benefit in soup.select("li, div.cmp-text, div.cmp-productdetails__content")
            if benefit.get_text(" ", strip=True)
        ][:12]
    cta_url = cta_button.get("data-cta-btn-url") if cta_button else ""
    if not cta_url and cta_button:
        cta_url = cta_button.get("href") or ""
    if not cta_url:
        for anchor in soup.select("a[href]"):
            href = anchor.get("href") or ""
            if ".pdf" in href.lower():
                cta_url = href
                break
    return {
        "plan_name": product_title(title_content, meta_title, soup),
        "plan_description": (meta_description.get("content", "") if meta_description else ""),
        "plan_overview": overview_content.get_text(" ", strip=True) if overview_content else "",
        "product_brochure_url": urljoin(AIA_BASE_URL, cta_url) if cta_url else "",
        "plan_benefits": benefits,
    }


def parse_product_text(text_content: str, source_url: str):
    lines = [remove_excess_newlines(line) for line in text_content.splitlines()]
    lines = [line for line in lines if line]
    title = next((line for line in lines if 4 <= len(line) <= 90), "")
    if not title:
        title = title_from_url(source_url)
    paragraphs = split_text_paragraphs(text_content)
    description = next((paragraph for paragraph in paragraphs if paragraph != title), "")
    benefits = [
        line
        for line in lines
        if any(
            keyword in line.lower()
            for keyword in (
                "accident",
                "benefit",
                "cover",
                "critical",
                "health",
                "hospital",
                "life",
                "medical",
                "protect",
                "term",
            )
        )
    ][:12]
    return {
        "plan_name": title,
        "plan_description": description,
        "plan_overview": "\n".join(paragraphs[:4]),
        "product_brochure_url": source_url if source_url.lower().endswith(".pdf") else "",
        "plan_benefits": benefits,
    }


def product_title(title_content, meta_title, soup: BeautifulSoup) -> str:
    title = title_content.get_text(" ", strip=True) if title_content else ""
    if not title or title.lower() in {"share", "overview"}:
        title = meta_title.get("content", "") if meta_title else ""
    if not title and soup.title:
        title = soup.title.get_text(" ", strip=True).split("|", 1)[0]
    return title.strip()


def title_from_url(url: str) -> str:
    slug = urlparse(url).path.rstrip("/").rsplit("/", 1)[-1]
    return " ".join(part.capitalize() for part in slug.split("-") if part)


def split_text_paragraphs(value: str) -> list[str]:
    paragraphs = [remove_excess_newlines(part) for part in re.split(r"\n\s*\n", value)]
    return [paragraph for paragraph in paragraphs if paragraph]


def build_plan_row(filter_data: dict, product_data: dict):
    benefits_data = product_data.get("plan_benefits") or []
    return {
        "plan_name": filter_data.get("plan_name") or product_data.get("plan_name") or "",
        "plan_benefits": (
            [remove_excess_newlines(benefits) for benefits in benefits_data]
            if benefits_data
            else [""]
        ),
        "plan_description": (
            remove_html_entities(filter_data.get("plan_description"))
            if filter_data.get("plan_description")
            else remove_html_entities(product_data.get("plan_description"))
        ),
        "plan_overview": (
            remove_excess_newlines(product_data.get("plan_overview"))
            if product_data.get("plan_overview")
            else ""
        ),
        "plan_url": filter_data.get("plan_url") or "",
        "product_brochure_url": product_data.get("product_brochure_url") or "",
    }


def fetch_html(url: str) -> str:
    response = requests.get(
        url,
        timeout=REQUEST_TIMEOUT_SECONDS,
        headers={"User-Agent": BOT_USER_AGENT},
    )
    response.raise_for_status()
    return response.text


def cache_slug(url: str) -> str:
    parsed = urlparse(url)
    value = f"{parsed.netloc}{parsed.path}".strip("/")
    return re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-").lower()


def cache_candidates(url: str, cache_dir: str | Path | None = None) -> list[Path]:
    root = Path(cache_dir or AIA_SOURCE_CACHE_DIR)
    parsed = urlparse(url)
    slug = cache_slug(url)
    basename = parsed.path.rstrip("/").rsplit("/", 1)[-1]
    path_key = parsed.path.strip("/").replace("/", "__")
    names = [
        f"{slug}.html",
        f"{slug}.txt",
        f"{slug}.pdf.txt",
        f"{path_key}.html" if path_key else "",
        f"{path_key}.txt" if path_key else "",
        f"{path_key}.pdf.txt" if path_key else "",
        f"{basename}.html" if basename else "",
        f"{basename}.txt" if basename else "",
        f"{basename}.pdf.txt" if basename else "",
    ]
    return [root / name for name in dict.fromkeys(names) if name]


def cached_payload(url: str, cache_dir: str | Path | None = None) -> tuple[str, str]:
    for candidate in cache_candidates(url, cache_dir):
        if not candidate.exists():
            continue
        kind = "html" if candidate.suffix == ".html" else "text"
        return candidate.read_text(encoding="utf-8"), kind
    return "", ""


async def page_content_or_fallback(page, url: str) -> tuple[str, str]:
    try:
        await goto_with_retry(page, url)
        return await page.content(), "html"
    except Exception as exc:
        log_url_failure("aia", url, exc)
        URL_FAILURES.append(f"{url}: {type(exc).__name__}: {exc}")
        try:
            return await asyncio.to_thread(fetch_html, url), "html"
        except Exception as fallback_exc:
            log_url_failure("aia", url, fallback_exc)
            URL_FAILURES.append(f"{url}: {type(fallback_exc).__name__}: {fallback_exc}")
            payload, kind = cached_payload(url)
            if payload:
                return payload, kind
            return "", ""


async def scrape_data(target_url):
    scraped_data = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await new_bot_context(browser)
        page = await context.new_page()

        source_content, source_kind = await page_content_or_fallback(page, target_url)
        if not source_content:
            await browser.close()
            return []
        if source_kind == "text":
            product_data = parse_product_text(source_content, target_url)
            row = build_plan_row({"plan_url": target_url}, product_data)
            await browser.close()
            return [row] if row["plan_name"] else []

        if await page.query_selector("#productDetailContainer"):  # handle pop-up ad
            await page.wait_for_timeout(2000)
            if await page.query_selector("#div-close"):
                await page.click("#div-close")
                print("Closed popup")

        product_filters_data = parse_listing_html(source_content)
        if not product_filters_data:
            product_data = parse_product_html(source_content)
            row = build_plan_row({"plan_url": target_url}, product_data)
            await browser.close()
            return [row] if row["plan_name"] else []

        for filter in product_filters_data:
            url = filter["plan_url"]
            # print(url)
            product_page = await context.new_page()
            try:
                product_content, product_kind = await page_content_or_fallback(product_page, url)
                if not product_content:
                    continue
                product_data = (
                    parse_product_html(product_content)
                    if product_kind == "html"
                    else parse_product_text(product_content, url)
                )
                scraped_data.append(build_plan_row(filter, product_data))
            finally:
                await product_page.close()

        await browser.close()

        return scraped_data


async def run_all_tasks(scrape_list):
    return await gather_scrape_results("aia", scrape_list, scrape_data)


# ----- sample execution code -----

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--source-cache-dir")
    args, _ = parser.parse_known_args()
    if args.source_cache_dir:
        AIA_SOURCE_CACHE_DIR = args.source_cache_dir
    scrape_list = [
        "https://www.aia.com.sg/en/our-products/travel-and-lifestyle",
        "https://www.aia.com.sg/en/our-products/accident-protection",
        "https://www.aia.com.sg/en/our-products/life-insurance",
        "https://www.aia.com.sg/en/our-products/platinum",
        "https://www.aia.com.sg/en/our-products/health",
        "https://www.aia.com.sg/en/our-products/save-and-invest",
        *AIA_DIRECT_PRODUCT_URLS,
    ]
    initialize_data_store()
    output = asyncio.run(run_all_tasks(scrape_list))
    if not output:
        record_scraper_failure(
            "aia",
            "; ".join(URL_FAILURES[-8:]) or "no AIA source payloads",
            dry_run=args.dry_run,
        )
    overwrite_plans_for_insurer("aia", output)
