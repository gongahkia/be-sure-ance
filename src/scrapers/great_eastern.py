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

import re
import asyncio
from playwright.async_api import async_playwright

from src.backend.helper import initialize_supabase, overwrite_plans_for_insurer

# ----- functions -----


def remove_excess_newlines(inp):
    if not isinstance(inp, str):
        raise TypeError(
            f"Input must be type <string> but was type <{type(inp).__name__}>"
        )
    inp = re.sub(r"\n+", "\n", inp)
    inp = re.sub(r"[ \t\u200b]+", " ", inp)
    return inp.strip()


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
    overwrite_plans_for_insurer("great_eastern", output)
