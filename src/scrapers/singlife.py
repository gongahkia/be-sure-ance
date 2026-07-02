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

import asyncio
from playwright.async_api import async_playwright

from src.backend.helper import initialize_supabase, overwrite_table_data

# ----- functions -----


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
