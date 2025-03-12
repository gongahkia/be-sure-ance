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

        # Get general plan description
        header_element = await page.query_selector("h1.text-center.mt-5.mb-5")
        plan_description = (
            (await header_element.text_content()).strip()
            if (header_element := await page.query_selector("h1.text-center.mt-5.mb-5"))
            else ""
        )

        scraped_plans = []

        plan_elements = await page.query_selector_all("div.col-12.col-lg-4.views-row")

        for plan in plan_elements:
            # Plan Name and URL
            link_element = await plan.query_selector("span.field-content a")
            if link_element := await plan.query_selector("span.field-content a"):
                plan_name = (
                    (await link_text.text_content()).strip()
                    if (
                        link_element := await plan.query_selector(
                            "span.field-content a"
                        )
                    )
                    else ""
                )
                plan_url = (
                    await link_element.get_attribute("href")
                    if (
                        link_element := await plan.query_selector(
                            "span.field-content a"
                        )
                    )
                    else ""
                )
            else:
                plan_name, plan_url = "", ""

            # Plan benefits
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
                "plan_url": plan_url,
                "product_brochure_url": "",
            }

            scraped_plans.append(formatted_entry)

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
        "https://www.chinalife.com.sg/products/endowment-plans",
        "https://www.chinalife.com.sg/products/legacy-planning",
        "https://www.chinalife.com.sg/products/riders",
        "https://www.chinalife.com.sg/products/retirement-annuity-plans",
        "https://www.chinalife.com.sg/products/protection",
    ]
    initialize_supabase()
    output = asyncio.run(run_all_tasks(scrape_list))
    overwrite_table_data("china_life", output)
