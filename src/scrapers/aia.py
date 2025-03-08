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

import os
import json
import asyncio
from dotenv import load_dotenv
from supabase import create_client, Client
from playwright.async_api import async_playwright

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


def initialize_supabase():
    load_dotenv()
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Supabase URL or Key is missing. Check your .env file.")
    global supabase
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("Supabase client initialized successfully.")


def overwrite_table_data(table_name, data):
    query = f"DELETE FROM {table_name} WHERE 1=1;"
    try:
        response = supabase.rpc("execute_sql", {"query": query}).execute()
        if response.data is None or response.data == []:
            print(f"Data cleared from {table_name}: No data returned")
        else:
            print(f"Data cleared from {table_name}: {response.data}")
    except Exception as e:
        print(f"An error occurred while clearing data from {table_name}: {e}")
    insert_data(table_name, data)


def insert_data(table_name, data):
    formatted_data = []
    for row in data:
        plan_benefits = row.get("plan_benefits", [])
        if isinstance(plan_benefits, str):
            plan_benefits = [plan_benefits]
        formatted_row = {
            "plan_name": row.get("plan_name"),
            "plan_benefits": plan_benefits,
            "plan_description": row.get("plan_description"),
            "plan_overview": row.get("plan_overview"),
            "plan_url": row.get("plan_url"),
            "product_brochure_url": row.get("product_brochure_url"),
        }
        formatted_data.append(formatted_row)
    try:
        response_insert = supabase.table(table_name).insert(formatted_data).execute()
        if response_insert.data is None:
            print(f"Error inserting data into {table_name}: No data returned")
        else:
            print(f"Data inserted successfully into {table_name}.")
    except Exception as e:
        print(f"An error occurred while inserting data into {table_name}: {e}")


async def scrape_data(target_url):
    product_filters_data = []
    scraped_data = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto(target_url)

        if await page.query_selector("#productDetailContainer"):  # handle pop-up ad
            await page.wait_for_timeout(2000)
            if await page.query_selector("#div-close"):
                await page.click("#div-close")
                print("Closed popup")

        product_filters = await page.query_selector_all(
            ".cmp-productfilterlist__container a"
        )

        for filter in product_filters:
            href = await filter.get_attribute("href")
            h2_text = await filter.query_selector("h2")
            if h2_text:
                h2_text = await h2_text.text_content()
            else:
                h2_text = None

            next_div = await filter.query_selector("h2 + div")
            if next_div:
                next_div_text = await next_div.text_content()
            else:
                next_div_text = None

            product_filters_data.append(
                {
                    "plan_name": h2_text,
                    "plan_url": f"https://www.aia.com.sg{href}",
                    "plan_description": next_div_text,
                }
            )

        for filter in product_filters_data:
            url = filter["plan_url"]
            print(url)
            product_page = await context.new_page()
            await product_page.goto(url)

            overview_content = await product_page.query_selector(
                ".cmp-productoverviewhero__content"
            )
            if overview_content:
                overview_content = await overview_content.text_content()
            else:
                overview_content = None

            cta_button = await product_page.query_selector(
                ".cmp-button.cmp-button__primary"
            )
            if cta_button:
                cta_url = await cta_button.get_attribute("data-cta-btn-url")
            else:
                cta_url = None

            benefits_container = await product_page.query_selector_all(
                "div.cmp-featuredperk__content"
            )
            if benefits_container:
                benefits_data = []
                for benefit in benefits_container:
                    benefits_data.append(await benefit.text_content())
            else:
                benefits_data = None

            scraped_data.append(
                {
                    "plan_name": filter["plan_name"] if filter["plan_name"] else "",
                    "plan_benefits": [
                        lib.sanitise.remove_excess_newlines(benefits)
                        for benefits in benefits_data
                    ]
                    if benefits_data
                    else [""],
                    "plan_description": lib.sanitise.remove_html_entities(
                        filter["plan_description"]
                    )
                    if filter["plan_description"]
                    else "",
                    "plan_overview": lib.sanitise.remove_excess_newlines(
                        overview_content
                    )
                    if overview_content
                    else "",
                    "plan_url": filter["plan_url"] if filter["plan_url"] else "",
                    "product_brochure_url": f"https://www.aia.com.sg{cta_url}"
                    if cta_url
                    else "",
                }
            )

            await product_page.close()

        await browser.close()

        return scraped_data


async def run_all_tasks(scrape_list):
    tasks = []
    for url in scrape_list:
        tasks.append(scrape_data(url))
    all_data = await asyncio.gather(*tasks)
    return [plan_dict for general in all_data for plan_dict in general]


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
    initialize_supabase()
    output = asyncio.run(run_all_tasks(scrape_list))
    overwrite_table_data("aia", output)
