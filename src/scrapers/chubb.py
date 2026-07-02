"""
CHUBB

https://www.chubb.com/sg-en/
https://www.chubb.com/sg-en/claims.html

https://www.chubb.com/sg-en/business/financial-lines.html 
https://www.chubb.com/sg-en/business/marine.html 
https://www.chubb.com/sg-en/business/property.html 
https://www.chubb.com/sg-en/business/risk-engineering-services.html
https://www.chubb.com/sg-en/business/accident-health.html 
https://www.chubb.com/sg-en/business/casualty.html 
https://www.chubb.com/sg-en/business/construction.html
https://www.chubb.com/sg-en/business/cyber.html
https://www.chubb.com/sg-en/business/energy.html 
https://www.chubb.com/sg-en/business/environmental.html
"""

# ----- required imports -----

import re
import html
import asyncio
from playwright.async_api import async_playwright

from src.backend.helper import initialize_supabase, overwrite_plans_for_insurer

# ----- functions -----


def remove_excess_newlines(inp):
    if not isinstance(inp, str):
        raise TypeError(
            f"Input must be type <string> but was type <{type(inp).__name__}>"
        )
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
        page = await browser.new_page()
        await page.goto(url, timeout=60000)

        scraped_plans = []

        content_div = await page.query_selector("div.content")
        if content_div:
            anchor_text = (
                (await (await content_div.query_selector("a")).text_content()).strip()
                if await content_div.query_selector("a")
                else ""
            )
            hero_title = (
                (
                    await (
                        await content_div.query_selector("h1.hero-title")
                    ).text_content()
                ).strip()
                if await content_div.query_selector("h1.hero-title")
                else ""
            )
            text_description = (
                (
                    await (
                        await content_div.query_selector("div.text-description")
                    ).text_content()
                ).strip()
                if await content_div.query_selector("div.text-description")
                else ""
            )
            plan_description = ", ".join(
                filter(None, [anchor_text, hero_title, hero_title and text_description])
            )
        else:
            plan_description = ""

        widget_contents = await page.query_selector_all("div.widget-content")

        for widget in widget_contents:
            h2_element = await widget.query_selector("h2.h4-title")
            description_element = await widget.query_selector("div.text-description")
            cta_buttons_wrap = await widget.query_selector("div.cta-buttons-wrap a")

            if h2_element := await widget.query_selector("h2.h4-title"):
                plan_name = (await h2_element.text_content()).strip()
            else:
                continue

            if desc_element := await widget.query_selector("div.text-description"):
                plan_overview = (await desc_element.text_content()).strip()
            else:
                continue

            if cta_wrap := await widget.query_selector("div.cta-buttons-wrap a"):
                plan_url = await cta_wrap.get_attribute("href")
                product_brochure_url = plan_url
            else:
                continue

            formatted_entry = {
                "plan_name": plan_name,
                "plan_benefits": [],
                "plan_description": plan_overview,
                "plan_overview": plan_description,
                "plan_url": f"https://www.chubb.com{plan_url}",
                "product_brochure_url": f"https://www.chubb.com{plan_url}",
            }
            # print(formatted_entry)
            scraped_plans.append(formatted_entry)
        await browser.close()
        return scraped_plans


async def run_all_tasks(scrape_list):
    tasks = []
    for url in scrape_list:
        tasks.append(scrape_data(url))
    all_data = await asyncio.gather(*tasks)
    return [plan_dict for general in all_data for plan_dict in general]


# ----- sample execution code -----

if __name__ == "__main__":
    scrape_list = [
        "https://www.chubb.com/sg-en/business/financial-lines.html",
        "https://www.chubb.com/sg-en/business/marine.html",
        "https://www.chubb.com/sg-en/business/property.html",
        "https://www.chubb.com/sg-en/business/risk-engineering-services.html",
        "https://www.chubb.com/sg-en/business/casualty.html",
        "https://www.chubb.com/sg-en/business/construction.html",
        "https://www.chubb.com/sg-en/business/cyber.html",
        "https://www.chubb.com/sg-en/business/energy.html",
        "https://www.chubb.com/sg-en/business/environmental.html",
    ]
    initialize_supabase()
    output = asyncio.run(run_all_tasks(scrape_list))
    overwrite_plans_for_insurer("chubb", output)
