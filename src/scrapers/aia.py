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

import asyncio
import html
import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from src.backend.helper import initialize_data_store, overwrite_plans_for_insurer
from src.lib.http_identity import BOT_USER_AGENT
from src.scrapers.navigation import (
    gather_scrape_results,
    goto_with_retry,
    log_url_failure,
    new_bot_context,
)

# ----- functions -----

AIA_BASE_URL = "https://www.aia.com.sg"
REQUEST_TIMEOUT_SECONDS = 8
AIA_DIRECT_PRODUCT_URLS = [
    "https://www.aia.com.sg/en/our-products/health/medical-insurance/aia-healthshield-gold-max",
    "https://www.aia.com.sg/en/our-products/accident-protection/aia-solitaire-personal-accident",
    "https://www.aia.com.sg/en/our-products/accident-protection/aia-centurion-pa",
    "https://www.aia.com.sg/en/our-products/accident-protection/aia-platinum-accidentcare",
    "https://www.aia.com.sg/en/our-products/accident-protection/aia-star-protector-plus",
    "https://www.aia.com.sg/en/our-products/accident-protection/aia-genfit-pa",
    "https://www.aia.com.sg/en/our-products/life-insurance/whole-life-insurance/aia-guaranteed-protect-plus-iv",
    "https://www.aia.com.sg/en/our-products/life-insurance/whole-life-insurance/direct-aia-whole-life-cover-ii",
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
        "plan_description": (
            meta_description.get("content", "") if meta_description else ""
        ),
        "plan_overview": overview_content.get_text(" ", strip=True) if overview_content else "",
        "product_brochure_url": urljoin(AIA_BASE_URL, cta_url) if cta_url else "",
        "plan_benefits": benefits,
    }


def product_title(title_content, meta_title, soup: BeautifulSoup) -> str:
    title = title_content.get_text(" ", strip=True) if title_content else ""
    if not title or title.lower() in {"share", "overview"}:
        title = meta_title.get("content", "") if meta_title else ""
    if not title and soup.title:
        title = soup.title.get_text(" ", strip=True).split("|", 1)[0]
    return title.strip()


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


async def page_content_or_fallback(page, url: str) -> str:
    try:
        await goto_with_retry(page, url)
        return await page.content()
    except Exception as exc:
        log_url_failure("aia", url, exc)
        try:
            return await asyncio.to_thread(fetch_html, url)
        except Exception as fallback_exc:
            log_url_failure("aia", url, fallback_exc)
            return ""


async def scrape_data(target_url):
    scraped_data = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await new_bot_context(browser)
        page = await context.new_page()

        html_content = await page_content_or_fallback(page, target_url)
        if not html_content:
            await browser.close()
            return []

        if await page.query_selector("#productDetailContainer"):  # handle pop-up ad
            await page.wait_for_timeout(2000)
            if await page.query_selector("#div-close"):
                await page.click("#div-close")
                print("Closed popup")

        product_filters_data = parse_listing_html(html_content)
        if not product_filters_data:
            product_data = parse_product_html(html_content)
            row = build_plan_row({"plan_url": target_url}, product_data)
            await browser.close()
            return [row] if row["plan_name"] else []

        for filter in product_filters_data:
            url = filter["plan_url"]
            # print(url)
            product_page = await context.new_page()
            try:
                product_html = await page_content_or_fallback(product_page, url)
                if not product_html:
                    continue
                product_data = parse_product_html(product_html)
                scraped_data.append(build_plan_row(filter, product_data))
            finally:
                await product_page.close()

        await browser.close()

        return scraped_data


async def run_all_tasks(scrape_list):
    return await gather_scrape_results("aia", scrape_list, scrape_data)


# ----- sample execution code -----

if __name__ == "__main__":
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
    overwrite_plans_for_insurer("aia", output)
