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

import asyncio
import re

from playwright.async_api import async_playwright

from src.backend.helper import initialize_supabase, overwrite_plans_for_insurer
from src.scrapers.navigation import gather_scrape_results, goto_with_retry, new_bot_context

# ----- functions -----


def remove_excess_newlines(inp):
    if not isinstance(inp, str):
        raise TypeError(f"Input must be type <string> but was type <{type(inp).__name__}>")
    inp = re.sub(r"\n+", "\n", inp)
    inp = re.sub(r"[ \t\u200b]+", " ", inp)
    return inp.strip()


async def scrape_data(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await new_bot_context(browser)
        page = await context.new_page()
        await goto_with_retry(page, url)
        scraped_data = []
        ul_elements = await page.query_selector_all("ul.container-content")
        for ul in ul_elements:
            li_items = await ul.query_selector_all("li")
            for li in li_items:
                name_element = await li.query_selector("div.item-content h3")
                plan_name = (await name_element.text_content()).strip() if name_element else ""
                link_element = await li.query_selector("div.item-content h3 a")
                plan_url = await link_element.get_attribute("href") if link_element else ""
                plan_brochure_url = plan_url
                item_content_element = await li.query_selector("div.item-content")
                if item_content_element:
                    item_content_text = (await item_content_element.text_content()).strip()
                    plan_description = (
                        item_content_text[len(plan_name) :].lstrip()
                        if plan_name
                        else item_content_text
                    )
                else:
                    plan_description = ""
                plan_benefits = []
                plan_overview = ""
                formatted_row = {
                    "plan_name": plan_name,
                    "plan_benefits": plan_benefits,
                    "plan_description": plan_description,
                    "plan_overview": plan_overview,
                    "plan_url": f"https://www.insurance.hsbc.com.sg{plan_url}" if plan_url else "",
                    "product_brochure_url": (
                        f"https://www.insurance.hsbc.com.sg{plan_brochure_url}"
                        if plan_brochure_url
                        else ""
                    ),
                }
                if formatted_row["plan_name"] in [
                    "",
                    "How to file a claim",
                    "Ways to pay your premiums",
                    "Insurance help and support",
                    "Contact us",
                ]:
                    continue
                scraped_data.append(formatted_row)
                # print(formatted_row)
        await browser.close()
        return scraped_data


async def run_all_tasks(scrape_list):
    return await gather_scrape_results("hsbc", scrape_list, scrape_data)


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
    overwrite_plans_for_insurer("hsbc", output)
