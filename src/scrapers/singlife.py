"""
SINGLIFE

https://singlife.com/en

https://singlife.com/en/life-insurance 
https://singlife.com/en/medical-insurance 
https://singlife.com/en/critical-illness-insurance 
https://singlife.com/en/disability-insurance
https://singlife.com/en/accident-insurance
https://singlife.com/en/mindef-and-mha/mindef-group-insurance 
https://singlife.com/en/mindef-and-mha/mha-group-insurance
https://singlife.com/en/savings 
https://singlife.com/en/investment-linked-plan 

https://singlife.com/en/maternity-care 
https://singlife.com/en/car-insurance
https://singlife.com/en/travel-insurance
https://singlife.com/en/home-insurance 
https://singlife.com/en/pogis 
https://singlife.com/en/flexi-retirement-ii 
https://singlife.com/en/singlife-account 
https://singlife.com/en/dollardex 
https://singlife.com/en/grow-with-singlife 
https://singlife.com/en/business/general-insurance/commercial-vehicle-insurance
https://singlife.com/en/business/general-insurance/corporate-travel-insurance 
https://singlife.com/en/business/general-insurance/mybusiness-insurance 
https://singlife.com/en/business/corporate-insurance/myglobal-benefits 
https://singlife.com/en/business/corporate-insurance/group-term-life
https://singlife.com/en/business/corporate-insurance/group-critical-illness 
https://singlife.com/en/business/corporate-insurance/group-preferred-care-plus 
https://singlife.com/en/business/corporate-insurance/group-hospital-and-surgical-care
https://singlife.com/en/business/corporate-insurance/group-personal-accident 
https://singlife.com/en/business/corporate-insurance/group-disability-protection 
https://singlife.com/en/business/corporate-insurance/mybenefits-plus 
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
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, timeout=60000)
        scraped_plans = []
        description_element = await page.query_selector("div.sl-banner-content")
        plan_description = (
            (await description_element.text_content()).strip()
            if description_element
            else ""
        )
        product_cards_container = await page.query_selector(
            "div.products-card-container.container.product-card-wrapper"
        )
        if product_cards_container:
            product_cards = await product_cards_container.query_selector_all(
                "div.relative.product-card-container"
            )
            for card in product_cards:
                name_element = await card.query_selector("h2.product-card-header")
                plan_name = (
                    (await name_element.text_content()).strip() if name_element else ""
                )
                overview_element = await card.query_selector(
                    "div.product-card-description"
                )
                plan_overview = (
                    (await overview_element.text_content()).strip()
                    if overview_element
                    else ""
                )
                benefits_elements = await card.query_selector_all(
                    "ul.product-card-features li"
                )
                plan_benefits = [
                    (await benefit.text_content()).strip()
                    for benefit in benefits_elements
                ]
                brochure_element = await card.query_selector(
                    "div.product-card-action-container a"
                )
                plan_brochure_url = (
                    await brochure_element.get_attribute("href")
                    if brochure_element
                    else ""
                )
                url_element = await card.query_selector("a.product-card-button")
                plan_url = (
                    await url_element.get_attribute("href") if url_element else ""
                )
                if not plan_benefits:
                    print("fuck")
                formatted_row = {
                    "plan_name": plan_name,
                    "plan_benefits": plan_benefits,
                    "plan_description": plan_description,
                    "plan_overview": plan_overview,
                    "plan_url": f"https://singlife.com{plan_url}" if plan_url else "",
                    "product_brochure_url": f"https://singlife.com{plan_brochure_url}"
                    if plan_brochure_url
                    else "",
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
        "https://singlife.com/en/life-insurance",
        "https://singlife.com/en/medical-insurance",
        "https://singlife.com/en/critical-illness-insurance",
        "https://singlife.com/en/disability-insuranc",
        "https://singlife.com/en/accident-insuranc",
        "https://singlife.com/en/mindef-and-mha/mindef-group-insurance",
        "https://singlife.com/en/mindef-and-mha/mha-group-insuranc",
        "https://singlife.com/en/savings",
        "https://singlife.com/en/investment-linked-plan",
    ]
    initialize_supabase()
    output = asyncio.run(run_all_tasks(scrape_list))
    overwrite_table_data("singlife", output)
