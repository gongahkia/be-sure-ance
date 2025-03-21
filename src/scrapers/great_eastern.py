"""
GREAT EASTERN 

https://www.greateasternlife.com/sg/en/about-us.html

https://www.greateasternlife.com/sg/en/personal-insurance/our-products/life-insurance.html
https://www.greateasternlife.com/sg/en/personal-insurance/our-products/health-insurance.html
https://www.greateasternlife.com/sg/en/personal-insurance/our-products/personal-accident-insurance.html
https://www.greateasternlife.com/sg/en/personal-insurance/our-products/retirement-income.html
https://www.greateasternlife.com/sg/en/personal-insurance/our-products/wealth-accumulation.html
https://www.greateasternlife.com/sg/en/personal-insurance/our-products/travel-insurance/travelsmart-premier.html
https://www.greateasternlife.com/sg/en/personal-insurance/our-products/car-insurance.html
https://www.greateasternlife.com/sg/en/personal-insurance/our-products/home-insurance/great-home-protect.html
https://www.greateasternlife.com/sg/en/personal-insurance/our-products/maid-insurance/great-maid-protect.html
https://www.greateasternlife.com/sg/en/personal-insurance/our-products/life-insurance/dependants-protection-scheme.html
https://www.greateasternlife.com/sg/en/campaigns/great-legacy-programme.html
https://www.greateasternlife.com/sg/en/personal-insurance/our-products/prestige-series.html
"""

# ----- required imports -----

import os
import re
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
        await page.goto(url)
        scraped_plans = []
        related_categories_element = await page.query_selector(
            "div.relatedCategories.aem-GridColumn.aem-GridColumn--default--12"
        )
        product_header_title_element = await page.query_selector(
            "div.product-header-title h1"
        )
        if related_categories_element and product_header_title_element:
            general_plan_description = (
                (await related_categories_element.text_content())
                + " "
                + (await product_header_title_element.text_content())
            )
        else:
            general_plan_description = ""
        cards = await page.query_selector_all(
            ".leo-card.leo-shadow-none.border-gray.d-flex.h-100.card-with-button"
        )
        for card in cards:
            if card:
                title_element = await card.query_selector("h5.leo-card-title")
                if title_element:
                    plan_name = await title_element.text_content()
                else:
                    plan_name = ""
                plan_benefits = []
                benefits1 = await card.query_selector("div.product-banifits")
                benefits2 = await card.query_selector("div.key-benefits")
                if benefits1:
                    benefits1 = await benefits1.text_content()
                    plan_benefits.append(remove_excess_newlines(benefits1.strip()))
                if benefits2:
                    benefits2 = await benefits2.text_content()
                    plan_benefits.append(remove_excess_newlines(benefits2.strip()))
                footer_element = await card.query_selector(
                    ".leo-card-footer.mt-auto.d-flex a"
                )
                if footer_element:
                    plan_url = await footer_element.get_attribute("href")
                else:
                    plan_url = ""
                formatted_row = {
                    "plan_name": plan_name,
                    "plan_benefits": [plan_benefits],
                    "plan_description": remove_excess_newlines(
                        general_plan_description
                    ),
                    "plan_overview": "",
                    "plan_url": f"https://www.greateasternlife.com{plan_url}"
                    if plan_url
                    else "",
                    "product_brochure_url": f"https://www.greateasternlife.com{plan_url}"
                    if plan_url
                    else plan_url,
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
        "https://www.greateasternlife.com/sg/en/personal-insurance/our-products/life-insurance.html",
        "https://www.greateasternlife.com/sg/en/personal-insurance/our-products/health-insurance.html",
        "https://www.greateasternlife.com/sg/en/personal-insurance/our-products/personal-accident-insurance.html",
        "https://www.greateasternlife.com/sg/en/personal-insurance/our-products/retirement-income.html",
        "https://www.greateasternlife.com/sg/en/personal-insurance/our-products/wealth-accumulation.html",
        "https://www.greateasternlife.com/sg/en/personal-insurance/our-products/car-insurance.html",
        "https://www.greateasternlife.com/sg/en/personal-insurance/our-products/prestige-series.html",
    ]
    initialize_supabase()
    output = asyncio.run(run_all_tasks(scrape_list))
    overwrite_table_data("great_eastern", output)
