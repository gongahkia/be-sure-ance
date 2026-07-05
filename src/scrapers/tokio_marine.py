"""
TOKIO MARINE

https://www.tokiomarine.com/sg/en.html
https://www.tokiomarine.com/sg/en/life/claim/submit-a-claim.html

https://www.tokiomarine.com/sg/en/non-life.html
https://www.tokiomarine.com/sg/en/life.html
"""

# ----- required imports -----

import asyncio
import html
import re
from urllib.parse import urljoin

from playwright.async_api import async_playwright

from src.backend.helper import initialize_data_store, overwrite_plans_for_insurer
from src.scrapers.navigation import gather_scrape_results, goto_with_retry, new_bot_context

# ----- functions -----


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


async def scrape_data(url):
    base_url = "https://www.tokiomarine.com"
    scraped_plans = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-http2"])
        context = await new_bot_context(browser)
        page = await context.new_page()
        await goto_with_retry(page, url)
        link_elements = await page.query_selector_all("div.quick-help-custom__item a")
        plan_urls = []
        seen_urls = set()
        for link in link_elements:
            href = await link.get_attribute("href")
            full_url = urljoin(base_url, href or "")
            if href and full_url not in seen_urls:
                seen_urls.add(full_url)
                plan_urls.append(full_url)
        scraped_plans = []
        for plan_url in plan_urls:
            # print(plan_urls)
            plan_page = await page.context.new_page()
            await goto_with_retry(plan_page, plan_url)
            title_element = await plan_page.query_selector("h2.masthead-colors__title")
            plan_name = (await title_element.text_content()).strip() if title_element else ""
            if not plan_name:
                await plan_page.close()
                continue
            overview_element = await plan_page.query_selector("h2.masthead-colors__text")
            plan_overview = (
                (await overview_element.text_content()).strip() if overview_element else ""
            )
            description_elements = await plan_page.query_selector_all("div.section-wrap")
            descriptions = [
                await descriptions.text_content()
                for descriptions in description_elements
                if descriptions
            ]
            plan_description = "\n\n".join([description.strip() for description in descriptions])
            formatted_row = {
                "plan_name": plan_name,
                "plan_benefits": [],
                "plan_description": plan_description,
                "plan_overview": plan_overview,
                "plan_url": plan_url,
                "product_brochure_url": plan_url,
            }
            # print(scraped_plans)
            scraped_plans.append(formatted_row)
            await plan_page.close()
        await browser.close()
        return scraped_plans


async def run_all_tasks(scrape_list):
    return await gather_scrape_results("tokio_marine", scrape_list, scrape_data)


# ----- sample execution code -----

if __name__ == "__main__":
    scrape_list = [
        "https://www.tokiomarine.com/sg/en/non-life.html",
        "https://www.tokiomarine.com/sg/en/life.html",
    ]
    initialize_data_store()
    output = asyncio.run(run_all_tasks(scrape_list))
    overwrite_plans_for_insurer("tokio_marine", output)
