"""
SUN LIFE

https://www.sunlife.com.sg/en/ 

https://www.sunlife.com.sg/en/product-solutions/life-insurance/
https://www.sunlife.com.sg/en/product-solutions/indexed-universal-life/ 
"""

# ----- required imports -----

import os
import re
import html
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


async def scrape_data(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, timeout=60000)
        scraped_plans = []
        title_element = await page.query_selector(
            "div.bright.card-content-overlay h1.h1.card-title"
        )
        plan_name = (
            (await title_element.text_content()).strip() if title_element else ""
        )
        description_elements = [
            await page.query_selector("div.bright.card-content-overlay div.card_text"),
            await page.query_selector(
                "div.text.aem-GridColumn.aem-GridColumn--default--12"
            ),
        ]
        plan_description = " ".join(
            [
                (await desc.text_content()).strip()
                for desc in description_elements
                if desc
            ]
        )
        benefit_elements = await page.query_selector_all("div.card-body")
        plan_benefits = [
            (await benefit.text_content()).strip() for benefit in benefit_elements
        ]
        overview_elements = await page.query_selector_all("h3.h3.accordion-header")
        plan_overview = ""
        for overview in overview_elements:
            button_element = await overview.query_selector("button")
            if button_element:
                header_text = (await overview.text_content()).strip()
                plan_overview += header_text + "\n"
                await button_element.click()
                accordion_content = await overview.evaluate_handle(
                    "(header) => header.nextElementSibling"
                )
                if accordion_content:
                    accordion_text = (await accordion_content.text_content()).strip()
                    plan_overview += accordion_text + "\n"
        anchor_tags = await page.query_selector_all("a")
        plan_brochure_url = ""
        for anchor in anchor_tags:
            href = await anchor.get_attribute("href")
            if href and href.endswith(".pdf"):
                plan_brochure_url = href
                break
        formatted_row = {
            "plan_name": plan_name,
            "plan_benefits": plan_benefits,
            "plan_description": plan_description,
            "plan_overview": plan_overview.strip(),
            "plan_url": url,
            "product_brochure_url": f"https://www.sunlife.com.sg{plan_brochure_url}"
            if plan_brochure_url
            else "",
        }
        scraped_plans.append(formatted_row)
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
        "https://www.sunlife.com.sg/en/product-solutions/life-insurance/",
        "https://www.sunlife.com.sg/en/product-solutions/indexed-universal-life/",
    ]
    initialize_supabase()
    output = asyncio.run(run_all_tasks(scrape_list))
    overwrite_table_data("sunlife", output)
