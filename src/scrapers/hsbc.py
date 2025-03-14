"""
HSBC INSURANCE

https://www.insurance.hsbc.com.sg/
https://www.insurance.hsbc.com.sg/claims/

https://www.insurance.hsbc.com.sg/life-and-critical-illness/products/
https://www.insurance.hsbc.com.sg/savings/
https://www.insurance.hsbc.com.sg/investment/
https://www.insurance.hsbc.com.sg/employee-health-benefits/
https://www.insurance.hsbc.com.sg/health/
https://www.insurance.hsbc.com.sg/legacy/
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
    data = [item for row in data for item in row]
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
        scraped_data = []
        ul_elements = await page.query_selector_all("ul.container-content")
        for ul in ul_elements:
            li_items = await ul.query_selector_all("li")
            for li in li_items:
                name_element = await li.query_selector("div.item-content h3")
                plan_name = (
                    (await name_element.text_content()).strip() if name_element else ""
                )
                link_element = await li.query_selector("div.item-content h3 a")
                plan_url = (
                    await link_element.get_attribute("href") if link_element else ""
                )
                plan_brochure_url = plan_url
                item_content_element = await li.query_selector("div.item-content")
                if item_content_element:
                    item_content_text = (
                        await item_content_element.text_content()
                    ).strip()
                    plan_description = (
                        item_content_text[len(plan_name) :].lstrip()
                        if plan_name
                        else item_content_text
                    )
                else:
                    plan_description = ""
                plan_benefits = [""]
                plan_overview = ""
                formatted_row = {
                    "plan_name": plan_name,
                    "plan_benefits": plan_benefits,
                    "plan_description": plan_description,
                    "plan_overview": plan_overview,
                    "plan_url": plan_url,
                    "product_brochure_url": plan_brochure_url,
                }
                scraped_data.append(formatted_row)
        await browser.close()
        return scraped_data


async def run_all_tasks(scrape_list):
    tasks = []
    for url in scrape_list:
        tasks.append(scrape_data(url))
    all_data = await asyncio.gather(*tasks)
    return all_data


# ----- sample execution code -----

if __name__ == "__main__":
    scrape_list = [
        "https://www.insurance.hsbc.com.sg/life-and-critical-illness/products/",
        "https://www.insurance.hsbc.com.sg/savings/",
        "https://www.insurance.hsbc.com.sg/investment/",
        "https://www.insurance.hsbc.com.sg/employee-health-benefits/",
        "https://www.insurance.hsbc.com.sg/health/",
        "https://www.insurance.hsbc.com.sg/legacy/",
    ]
    initialize_supabase()
    output = asyncio.run(run_all_tasks(scrape_list))
    overwrite_table_data("hsbc", output)
