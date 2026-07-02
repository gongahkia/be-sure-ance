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

import asyncio
from playwright.async_api import async_playwright

from src.backend.helper import initialize_supabase, overwrite_table_data

# ----- functions -----


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
        plan_overview_1 = await page.query_selector(
            "p.alt-font.text-white.text-uppercase.text-small"
        )
        if plan_overview_1:
            plan_overview = (await plan_overview_1.text_content()).strip()
        plan_description_el = await page.query_selector("section.parallax")
        if plan_description_el:
            plan_overview += f"\n{(await plan_description_el.text_content()).strip()}"
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
        print(formatted_row)
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
