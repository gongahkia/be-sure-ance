"""
CHINA LIFE

https://www.chinalife.com.sg/

https://www.chinalife.com.sg/forms

https://www.chinalife.com.sg/products/endowment-plans
https://www.chinalife.com.sg/products/legacy-planning
https://www.chinalife.com.sg/products/riders
https://www.chinalife.com.sg/products/retirement-annuity-plans
https://www.chinalife.com.sg/products/protection
"""

# ----- required imports -----

import asyncio
import html
import re

from playwright.async_api import async_playwright

from src.backend.helper import initialize_supabase, overwrite_plans_for_insurer
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
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await new_bot_context(browser)
        page = await context.new_page()
        await goto_with_retry(page, url)

        header_element = await page.query_selector("h1.text-center.mt-5.mb-5")
        plan_description = (
            (await header_element.text_content()).strip()
            if (header_element := await page.query_selector("h1.text-center.mt-5.mb-5"))
            else ""
        )

        scraped_plans = []

        plan_elements = await page.query_selector_all("div.col-12.col-lg-4.views-row")

        for plan in plan_elements:
            link_element = await plan.query_selector("span.field-content a")
            if link_element := await plan.query_selector("span.field-content a"):
                plan_name = (
                    (await link_element.text_content()).strip()
                    if (link_element := await plan.query_selector("span.field-content a"))
                    else ""
                )
                plan_url = (
                    await link_element.get_attribute("href")
                    if (link_element := await plan.query_selector("span.field-content a"))
                    else ""
                )
            else:
                plan_name, plan_url = "", ""
            benefit_elements = await plan.query_selector_all("p.h7")
            plan_benefits = (
                [
                    (await benefit.text_content()).strip()
                    for benefit in benefit_elements
                    if benefit_elements
                ]
                if benefit_elements
                else []
            )

            formatted_entry = {
                "plan_name": plan_name,
                "plan_benefits": plan_benefits,
                "plan_description": plan_description,
                "plan_overview": "",
                "plan_url": f"https://www.chinalife.com.sg/{plan_url}" if plan_url else "",
                "product_brochure_url": (
                    f"https://www.chinalife.com.sg/{plan_url}" if plan_url else ""
                ),
            }

            scraped_plans.append(formatted_entry)

    return scraped_plans


async def run_all_tasks(scrape_list):
    return await gather_scrape_results("china_life", scrape_list, scrape_data)


# ----- sample execution code -----

if __name__ == "__main__":
    scrape_list = [
        "https://www.chinalife.com.sg/products/endowment-plans",
        "https://www.chinalife.com.sg/products/legacy-planning",
        "https://www.chinalife.com.sg/products/riders",
        "https://www.chinalife.com.sg/products/retirement-annuity-plans",
        "https://www.chinalife.com.sg/products/protection",
    ]
    initialize_supabase()
    output = asyncio.run(run_all_tasks(scrape_list))
    overwrite_plans_for_insurer("china_life", output)
