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

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from src.backend.helper import initialize_data_store, overwrite_plans_for_insurer
from src.scrapers.navigation import (
    gather_scrape_results,
    goto_with_retry,
    log_url_failure,
    new_bot_context,
)

# ----- functions -----

AIA_BASE_URL = "https://www.aia.com.sg"


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
    cta_button = soup.select_one(".cmp-button.cmp-button__primary")
    benefits = [
        benefit.get_text(" ", strip=True)
        for benefit in soup.select("div.cmp-featuredperk__content")
    ]
    cta_url = cta_button.get("data-cta-btn-url") if cta_button else ""
    return {
        "plan_overview": overview_content.get_text(" ", strip=True) if overview_content else "",
        "product_brochure_url": urljoin(AIA_BASE_URL, cta_url) if cta_url else "",
        "plan_benefits": benefits,
    }


def build_plan_row(filter_data: dict, product_data: dict):
    benefits_data = product_data.get("plan_benefits") or []
    return {
        "plan_name": filter_data.get("plan_name") or "",
        "plan_benefits": (
            [remove_excess_newlines(benefits) for benefits in benefits_data]
            if benefits_data
            else [""]
        ),
        "plan_description": (
            remove_html_entities(filter_data.get("plan_description"))
            if filter_data.get("plan_description")
            else ""
        ),
        "plan_overview": (
            remove_excess_newlines(product_data.get("plan_overview"))
            if product_data.get("plan_overview")
            else ""
        ),
        "plan_url": filter_data.get("plan_url") or "",
        "product_brochure_url": product_data.get("product_brochure_url") or "",
    }


async def scrape_data(target_url):
    scraped_data = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await new_bot_context(browser)
        page = await context.new_page()

        await goto_with_retry(page, target_url)

        if await page.query_selector("#productDetailContainer"):  # handle pop-up ad
            await page.wait_for_timeout(2000)
            if await page.query_selector("#div-close"):
                await page.click("#div-close")
                print("Closed popup")

        product_filters_data = parse_listing_html(await page.content())

        for filter in product_filters_data:
            url = filter["plan_url"]
            # print(url)
            product_page = await context.new_page()
            try:
                await goto_with_retry(product_page, url)
                product_data = parse_product_html(await product_page.content())
                scraped_data.append(build_plan_row(filter, product_data))
            except Exception as exc:
                log_url_failure("aia", url, exc)
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
    ]
    initialize_data_store()
    output = asyncio.run(run_all_tasks(scrape_list))
    overwrite_plans_for_insurer("aia", output)
