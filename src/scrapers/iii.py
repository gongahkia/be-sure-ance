"""
INDIA INTERNATIONAL INSURANCE

https://www.iii.com.sg/ 
https://www.iii.com.sg/products/motor-insurance 
https://www.iii.com.sg/products/home-insurance 
https://www.iii.com.sg/products/travel-insurance 
https://www.iii.com.sg/products/personal-accident-insurance 
https://www.iii.com.sg/products/maid-insurance 
https://www.iii.com.sg/products/pet-insurance 
https://www.iii.com.sg/products/marine-insurance 
https://www.iii.com.sg/products/property-insurance
https://www.iii.com.sg/products/liability-insurance 
https://www.iii.com.sg/products/engineering-insurance
https://www.iii.com.sg/products/surety-insurance
https://www.iii.com.sg/products/motor-fleet-insurance 
https://www.iii.com.sg/products/reinsurance
"""

# ----- required imports -----

import os
import asyncio
from dotenv import load_dotenv
from supabase import create_client, Client
from playwright.async_api import async_playwright

# ----- functions -----


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
        scraped_plans = []
        plan_overview = ""
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, timeout=60000)
        name_el = await page.query_selector(
            "div.col-12.col-lg-6.order-2.z-index-1.padding-10-rem-left.padding-60px-bottom.lg-padding-3-rem-left.md-padding-15px-left h3"
        )
        if name_el:
            plan_name = (await name_el.text_content()).strip()
        else:
            plan_name = ""
        plan_overview_1 = await page.query_selector(
            "p.alt-font.text-white.text-uppercase.text-small"
        )
        if plan_overview_1:
            plan_overview = (await plan_overview_1.text_content()).strip()
        else:
            plan_overview = ""
        plan_description_el = await page.query_selector("section.parallax")
        if plan_description_el:
            plan_description = (await plan_description_el.text_content()).strip()
        else:
            plan_description = ""
        plan_benefits = []
        overall_list_el = await page.query_selector_all(
            "ul.text-start.p-0.list-style-02.margin-20px-left.text-dkblue.alt-font"
        )
        if overall_list_el:
            for list_el in overall_list_el:
                elements = await list_el.query_selector_all("li")
                if elements:
                    for element in elements:
                        plan_benefits.append((await element.text_content()).strip())
        formatted_row = {
            "plan_name": plan_name,
            "plan_benefits": plan_benefits,
            "plan_description": plan_description,
            "plan_overview": plan_overview,
            "plan_url": url,
            "product_brochure_url": url,
        }
        # print(formatted_row)
        scraped_plans.append(formatted_row)
        await browser.close()
        return scraped_plans


async def run_all_tasks(scrape_list):
    tasks = []
    for url in scrape_list:
        tasks.append(scrape_data(url))
    all_data = await asyncio.gather(*tasks)
    return all_data


# ----- sample execution code -----

if __name__ == "__main__":
    scrape_list = [
        "https://www.iii.com.sg/products/motor-insurance",
        "https://www.iii.com.sg/products/home-insurance",
        "https://www.iii.com.sg/products/travel-insurance",
        "https://www.iii.com.sg/products/personal-accident-insurance",
        "https://www.iii.com.sg/products/maid-insurance",
        "https://www.iii.com.sg/products/pet-insurance",
        "https://www.iii.com.sg/products/marine-insurance",
        "https://www.iii.com.sg/products/property-insurance",
        "https://www.iii.com.sg/products/liability-insurance",
        "https://www.iii.com.sg/products/engineering-insurance",
        "https://www.iii.com.sg/products/surety-insurance",
        "https://www.iii.com.sg/products/motor-fleet-insurance",
        "https://www.iii.com.sg/products/reinsurance",
    ]
    initialize_supabase()
    output = asyncio.run(run_all_tasks(scrape_list))
    overwrite_table_data("iii", output)
