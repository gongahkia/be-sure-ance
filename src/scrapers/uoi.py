"""
UOI

https://www.uoi.com.sg/index.page 

https://www.uoi.com.sg/personal/travel-insurance.page
https://www.uoi.com.sg/personal/motor-insurance.page 
https://www.uoi.com.sg/personal/home-contents-insurance.page 
https://www.uoi.com.sg/personal/accident-protection.page 

https://www.uoi.com.sg/commercial/general-insurance.page 
https://www.uoi.com.sg/commercial/specialised-insurance.page 
https://www.uoi.com.sg/claims-assistance.page 
https://www.uoi.com.sg/takaful.page 
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
    plan_benefits = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(url)
        plan_name = await page.locator(
            "div.col-12.col-lg-5.p-0 h1.uob-h1.mb-3.mb-md-6"
        ).text_content()
        plan_overview_and_description = await page.locator(
            "div.col-12.col-lg-5.p-0"
        ).text_content()
        plan_overview_and_description = plan_overview_and_description.replace(
            plan_name, ""
        ).strip()
        plan_overview = plan_overview_and_description.split("\n")[0]
        plan_description = "\n".join(plan_overview_and_description.split("\n")[1:])
        benefits_locator = page.locator(
            "div.row.m-0.p-0 div.col-12.col-sm-4.content-block.d-flex.d-sm-block.mt-5.pl-0.pr-0.align-items-center"
        )
        benefit_count = await benefits_locator.count()

        for i in range(benefit_count):
            benefit_text = await benefits_locator.nth(i).text_content()
            plan_benefits.append(benefit_text.strip())

        brochure_url = await page.locator(
            "h2.uob-h2.title.text-center.content-title + img"
        ).get_attribute("src")

        return {
            "plan_name": plan_name.strip(),
            "plan_benefits": plan_benefits,
            "plan_description": plan_description.strip(),
            "plan_overview": plan_overview.strip(),
            "plan_url": url,
            "product_brochure_url": f"https://www.uoi.com.sg{brochure_url}"
            if brochure_url
            else None,
        }


async def run_all_tasks(scrape_list):
    tasks = []
    for url in scrape_list:
        tasks.append(scrape_data(url))
    all_data = await asyncio.gather(*tasks)
    return all_data


# ----- sample execution code -----

if __name__ == "__main__":
    scrape_list = [
        "https://www.uoi.com.sg/personal/travel-insurance.page",
        "https://www.uoi.com.sg/personal/motor-insurance.page",
        "https://www.uoi.com.sg/personal/home-contents-insurance.page",
        "https://www.uoi.com.sg/personal/accident-protection.page",
    ]
    initialize_supabase()
    output = asyncio.run(run_all_tasks(scrape_list))
    overwrite_table_data("uoi", output)
