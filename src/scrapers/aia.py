"""
AIA

https://www.aia.com.sg/en/our-products/accident-protection
https://www.aia.com.sg/en/our-products/life-insurance
https://www.aia.com.sg/en/our-products/travel-and-lifestyle
https://www.aia.com.sg/en/our-products/platinum
https://www.aia.com.sg/en/our-products/health
https://www.aia.com.sg/en/our-products/save-and-invest
"""

# ----- required imports -----

import asyncio
import lib.sanitise 
from playwright.async_api import async_playwright
import json

# ----- functions -----

async def scrape_data(target_url):

    product_filters_data = []
    scraped_data = []

    async with async_playwright() as p:

        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto(target_url)

        if await page.query_selector('#productDetailContainer'): # handle pop-up ad 
            await page.wait_for_timeout(2000)  
            if await page.query_selector('#div-close'):
                await page.click('#div-close')
                print('Closed popup')

        product_filters = await page.query_selector_all('.cmp-productfilterlist__container a')

        for filter in product_filters:

            href = await filter.get_attribute('href')
            h2_text = await filter.query_selector('h2')
            if h2_text:
                h2_text = await h2_text.text_content()
            else:
                h2_text = None

            next_div = await filter.query_selector('h2 + div')
            if next_div:
                next_div_text = await next_div.text_content()
            else:
                next_div_text = None

            product_filters_data.append({
                'plan_name': h2_text,
                'plan_url': f"https://www.aia.com.sg{href}",
                'plan_description': next_div_text
            })

        print(f"NUM FILTERS: {len(product_filters_data)}FILTERS\n{product_filters_data}")

        for filter in product_filters_data:

            url = filter["plan_url"]
            print(url)
            product_page = await context.new_page()
            await product_page.goto(url)

            overview_content = await product_page.query_selector('.cmp-productoverviewhero__content')
            if overview_content:
                overview_content = await overview_content.text_content()
            else:
                overview_content = None

            cta_button = await product_page.query_selector('.cmp-button.cmp-button__primary')
            if cta_button:
                cta_url = await cta_button.get_attribute('data-cta-btn-url')
            else:
                cta_url = None

            benefits_container = await product_page.query_selector('#benefitsforyou .cardcarousel.carousel.panelcontainer')
            if benefits_container:
                benefits = await benefits_container.query_selector_all('#cmp-featuredperk__content')
                benefits_data = []
                for benefit in benefits:
                    benefits_data.append(await benefit.text_content())
            else:
                benefits_data = None

            scraped_data.append({
                'plan_name': filter['plan_name'],
                'plan_benefits': benefits_data,
                'plan_description': lib.sanitise.remove_html_entities(filter['plan_description']) if filter['plan_description'] else None,
                'plan_overview': lib.sanitise.remove_excess_newlines(overview_content) if overview_content else None,
                'plan_url': filter['plan_url'],
                'product_brochure_url': f"https://www.aia.com.sg{cta_url}"
            })

            await product_page.close()

        print(f"SCRAPED DATA\n{scraped_data}")

        await browser.close()

        return scraped_data

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
    "https://www.aia.com.sg/en/our-products/travel-and-lifestyle",
    "https://www.aia.com.sg/en/our-products/accident-protection",
    "https://www.aia.com.sg/en/our-products/life-insurance",
    "https://www.aia.com.sg/en/our-products/platinum",
    "https://www.aia.com.sg/en/our-products/health",
    "https://www.aia.com.sg/en/our-products/save-and-invest"
]
json_filepath = "./scraped/aia.json"

asyncio.run(main(json_filepath, scrape_list))