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

import asyncio
from playwright.async_api import async_playwright
import json

# ----- functions -----


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


async def run_all_tasks(json_filepath, scrape_list):
    tasks = []
    for url in scrape_list:
        tasks.append(scrape_data(url))
    all_data = await asyncio.gather(*tasks)
    with open(json_filepath, "w") as file:
        json.dump(all_data, file, indent=2)


async def main(json_filepath, scrape_list):
    await run_all_tasks(json_filepath, scrape_list)


# ----- sample execution code -----

scrape_list = [
    "https://www.uoi.com.sg/personal/travel-insurance.page",
    "https://www.uoi.com.sg/personal/motor-insurance.page",
    "https://www.uoi.com.sg/personal/home-contents-insurance.page",
    "https://www.uoi.com.sg/personal/accident-protection.page",
]
json_filepath = "./scraped/uoi.json"

asyncio.run(main(json_filepath, scrape_list))
