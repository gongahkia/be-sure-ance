"""
AIA

https://www.aia.com.sg/en/our-products/accident-protection
https://www.aia.com.sg/en/our-products/life-insurance
https://www.aia.com.sg/en/our-products/travel-and-lifestyle
https://www.aia.com.sg/en/our-products/platinum
https://www.aia.com.sg/en/our-products/health
https://www.aia.com.sg/en/our-products/save-and-invest
"""

from __future__ import annotations

import argparse
import asyncio
import html
import os
import re
from pathlib import Path
from urllib.parse import urldefrag, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

if __package__ in {None, ""}:
    import sys

    sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.backend.helper import (
    format_plan_rows,
    initialize_data_store,
    overwrite_plans_for_insurer,
)
from src.lib.http_identity import BOT_USER_AGENT
from src.lib.scraper_health import record_scraper_failure
from src.scrapers.navigation import gather_scrape_results, goto_with_retry, log_url_failure
from src.validation.plan_quality import validate_plan_rows

TABLE_NAME = "aia"
AIA_BASE_URL = "https://www.aia.com.sg"
REQUEST_TIMEOUT_SECONDS = 5
AIA_SOURCE_CACHE_DIR = os.getenv("AIA_SOURCE_CACHE_DIR", ".scraper-cache/aia")
URL_FAILURES: list[str] = []

SOURCE_URLS = (
    "https://www.aia.com.sg/en/our-products/travel-and-lifestyle",
    "https://www.aia.com.sg/en/our-products/accident-protection",
    "https://www.aia.com.sg/en/our-products/life-insurance",
    "https://www.aia.com.sg/en/our-products/platinum",
    "https://www.aia.com.sg/en/our-products/health",
    "https://www.aia.com.sg/en/our-products/save-and-invest",
)

REJECTED_SOURCE_URLS = (
    "https://www.aia.com.sg/en/our-products/travel-and-lifestyle",
    "https://www.aia.com.sg/en/our-products/accident-protection",
    "https://www.aia.com.sg/en/our-products/life-insurance",
    "https://www.aia.com.sg/en/our-products/platinum",
    "https://www.aia.com.sg/en/our-products/health",
    "https://www.aia.com.sg/en/our-products/save-and-invest",
    "https://www.aia.com.sg/en/our-products/employee-benefits",
    "https://www.aia.com.sg/en/our-products/save-and-invest/aia-funds-information/aia-fund-insights",
    "https://www.aia.com.sg/en/our-products/health/medical-insurance/aia-healthshield-gold-max/claim-based-pricing",
    "https://www.aia.com.sg/en/our-products/health/medical-insurance/aia-healthshield-gold-max/oct2025-updates",
    "https://www.aia.com.sg/en/our-products/health/medical-insurance/aia-healthshield-gold-max/sept2024-updates",
    "https://www.aia.com.sg/en/our-products/health/medical-insurance/aia-healthshield-gold-max/shield-benefits-preserver",
)

AIA_PRODUCT_CATALOG = (
    {
        "plan_name": "AIA HealthShield Gold Max",
        "plan_url": "https://www.aia.com.sg/en/our-products/health/medical-insurance/aia-healthshield-gold-max",
        "plan_description": "A MediSave-approved Integrated Shield Plan with private insurance coverage for public or private hospital treatment.",
        "plan_benefits": [
            "High annual claim limit of up to S$2 million per policy year.",
            "Lifetime coverage with policy-year claim limit reset.",
            "Pre- and post-hospitalisation coverage when treated by an AIA preferred provider.",
        ],
    },
    {
        "plan_name": "AIA Platinum International Health",
        "plan_url": "https://www.aia.com.sg/en/our-products/platinum/accident-health/aia-platinum-international-health",
        "plan_description": "Lifetime global medical coverage with access to care in Singapore and overseas.",
        "plan_benefits": [
            "Global medical care with high lifetime limit.",
            "Outpatient treatment and accidental dental treatment coverage.",
            "Teladoc Health support for specialist guidance and second opinions.",
        ],
    },
    {
        "plan_name": "AIA Hospital Income",
        "plan_url": "https://www.aia.com.sg/en/our-products/health/medical-insurance/aia-hospital-income",
        "plan_description": "Hospital income cover that provides a financial buffer during recovery.",
        "plan_benefits": [
            "Daily cash support during hospitalisation.",
            "AIA Vitality premium discount eligibility.",
            "Complements medical insurance for recovery expenses.",
        ],
    },
    {
        "plan_name": "AIA Mum2Baby Choices",
        "plan_url": "https://www.aia.com.sg/en/our-products/health/medical-insurance/aia-mum2baby-choices",
        "plan_description": "Maternity insurance for mother and child from pregnancy through post-birth protection.",
        "plan_benefits": [
            "Protection for pregnancy-related complications.",
            "Newborn congenital illness coverage.",
            "Guaranteed lifelong protection option for the child.",
        ],
    },
    {
        "plan_name": "AIA Foreign Worker Protector Plus",
        "plan_url": "https://www.aia.com.sg/en/our-products/corporate-medical-insurance/aia-foreign-worker-protector-plus",
        "plan_description": "Corporate medical insurance plan for foreign worker protection.",
        "plan_benefits": [
            "Medical insurance support for foreign workers.",
            "Designed for employers with work pass obligations.",
            "AIA corporate medical insurance coverage.",
        ],
    },
    {
        "plan_name": "AIA Premier Disability Cover",
        "plan_url": "https://www.aia.com.sg/en/our-products/health/disability-income-insurance/aia-premier-disability-cover",
        "plan_description": "Disability income insurance with regular payouts when illness or injury prevents work.",
        "plan_benefits": [
            "Regular income support during disability.",
            "Designed to protect family financial stability.",
            "Covers inability to work due to covered disability events.",
        ],
    },
    {
        "plan_name": "AIA Pay Protector",
        "plan_url": "https://www.aia.com.sg/en/our-products/health/disability-income-insurance/aia-pay-protector",
        "plan_description": "Income protection for career pauses caused by injury, illness, mental conditions or job loss.",
        "plan_benefits": [
            "Income safeguard up to age 65.",
            "Includes injury, illness and mental condition triggers.",
            "AIA Vitality premium discount eligibility.",
        ],
    },
    {
        "plan_name": "AIA Ultimate Critical Cover",
        "plan_url": "https://www.aia.com.sg/en/our-products/health/critical-illness/aia-ultimate-critical-cover",
        "plan_description": "Critical illness plan covering early, intermediate and major stages across 150 medical conditions.",
        "plan_benefits": [
            "Coverage for 150 medical conditions.",
            "Protection across early, intermediate and major stages.",
            "Optional relapse protection through UCC Enhancer add-on.",
        ],
    },
    {
        "plan_name": "AIA Absolute Critical Cover",
        "plan_url": "https://www.aia.com.sg/en/our-products/health/critical-illness/aia-absolute-critical-cover",
        "plan_description": "Term critical illness plan covering multi-stage, chronic, age-related and future diseases.",
        "plan_benefits": [
            "Coverage for 187 conditions.",
            "Choice of coverage terms up to age 65, 75 or 100.",
            "Safety net cover benefit for selected ICU admissions.",
        ],
    },
    {
        "plan_name": "AIA Beyond Critical Care",
        "plan_url": "https://www.aia.com.sg/en/our-products/health/critical-illness/aia-beyond-critical-care",
        "plan_description": "Critical illness plan with major-stage, relapse and mental illness protection.",
        "plan_benefits": [
            "Protection for 43 major critical illnesses and 5 relapse conditions.",
            "Mental illness benefit for covered conditions.",
            "Premium refund benefit at the end of the policy term.",
        ],
    },
    {
        "plan_name": "AIA Prime Critical Cover",
        "plan_url": "https://www.aia.com.sg/en/our-products/health/critical-illness/aia-prime-critical-cover",
        "plan_description": "Critical illness plan for adults aged 40 to 70, with cover extending up to age 100.",
        "plan_benefits": [
            "Coverage for death, critical illnesses and special conditions.",
            "Early payouts for selected age-related conditions.",
            "Health screening benefit.",
        ],
    },
    {
        "plan_name": "AIA Glow of Life",
        "plan_url": "https://www.aia.com.sg/en/our-products/health/critical-illness/aia-glow-of-life",
        "plan_description": "Critical illness plan tailored for women.",
        "plan_benefits": [
            "Coverage for women-specific critical illnesses.",
            "Includes osteoporosis, rheumatoid arthritis and breast cancer support.",
            "Reimbursement for reconstructive surgery after accident or burns.",
        ],
    },
    {
        "plan_name": "AIA Enhanced Cancer Protect",
        "plan_url": "https://www.aia.com.sg/en/our-products/health/critical-illness/aia-enhanced-cancer-protect",
        "plan_description": "Cancer protection plan with high coverage and relapse benefits.",
        "plan_benefits": [
            "Coverage of up to S$700,000.",
            "100% coverage amount for first diagnosis.",
            "Coverage for up to 2 major-stage relapses of major cancer.",
        ],
    },
    {
        "plan_name": "AIA Diabetes Care",
        "plan_url": "https://www.aia.com.sg/en/our-products/health/critical-illness/aia-diabetes-care",
        "plan_description": "Critical illness cover created for pre-diabetics and Type 2 diabetics.",
        "plan_benefits": [
            "Financial support for key diabetes-related conditions.",
            "AIA Vitality premium discount eligibility.",
            "Cancer cover option mentioned by AIA.",
        ],
    },
    {
        "plan_name": "AIA Guaranteed Protect Plus (IV)",
        "plan_url": "https://www.aia.com.sg/en/our-products/life-insurance/whole-life-insurance/aia-guaranteed-protect-plus-iv",
        "plan_description": "Participating whole life plan with lifelong coverage and cash value accumulation.",
        "plan_benefits": [
            "Coverage for death and total permanent disability.",
            "Flexible coverage booster.",
            "Potential accumulated cash value.",
        ],
    },
    {
        "plan_name": "Direct AIA Whole Life Cover (II)",
        "plan_url": "https://www.aia.com.sg/en/our-products/life-insurance/whole-life-insurance/direct-aia-whole-life-cover-ii",
        "plan_description": "Direct Purchase Insurance whole life plan with protection up to age 100.",
        "plan_benefits": [
            "Death and terminal illness coverage up to age 100.",
            "Total and permanent disability benefits up to age 65.",
            "Potential annual and terminal bonuses.",
        ],
    },
    {
        "plan_name": "Direct - AIA Term Cover",
        "plan_url": "https://www.aia.com.sg/en/our-products/life-insurance/term-insurance/direct-aia-term-cover",
        "plan_description": "Direct Purchase term insurance for cost-effective family protection.",
        "plan_benefits": [
            "Death, terminal illness and total permanent disability protection.",
            "Choice of 5-year, 20-year or age-65 coverage terms.",
            "Designed for affordable premiums.",
        ],
    },
    {
        "plan_name": "AIA Pro Lifetime Protector (II)",
        "plan_url": "https://www.aia.com.sg/en/our-products/life-insurance/whole-life-insurance/aia-pro-lifetime-protector-ii",
        "plan_description": "Whole life protection and investment plan covering death, disability and multi-stage critical illnesses.",
        "plan_benefits": [
            "Long-term protection and returns.",
            "Death, disability and multi-stage critical illness coverage.",
            "AIA Vitality premium discount eligibility.",
        ],
    },
    {
        "plan_name": "AIA Secure Flexi Term",
        "plan_url": "https://www.aia.com.sg/en/our-products/life-insurance/term-insurance/aia-secure-flexi-term",
        "plan_description": "Flexible term life insurance plan for family protection.",
        "plan_benefits": [
            "Affordable term life coverage.",
            "Flexible protection options.",
            "Designed to safeguard family financial needs.",
        ],
    },
    {
        "plan_name": "AIA Life Dividends",
        "plan_url": "https://www.aia.com.sg/en/our-products/life-insurance/whole-life-insurance/aia-life-dividends",
        "plan_description": "Whole life plan with 10-year premium payment and protection up to age 100.",
        "plan_benefits": [
            "Pay premiums for 10 years.",
            "Protection up to age 100.",
            "Flexibility to withdraw annual dividends.",
        ],
    },
    {
        "plan_name": "AIA Mortgage Reducing Term Assurance",
        "plan_url": "https://www.aia.com.sg/en/our-products/life-insurance/term-insurance/aia-mortgage-reducing-term-assurance",
        "plan_description": "Mortgage protection insurance covering outstanding housing loan obligations.",
        "plan_benefits": [
            "Covers outstanding housing loan on death, disability or terminal illness.",
            "Premium waiver for covered disability, terminal illness or critical illness.",
            "Coverage can continue after loan repayment or home sale up to age 75.",
        ],
    },
    {
        "plan_name": "AIA Solitaire PA (II)",
        "plan_url": "https://www.aia.com.sg/en/our-products/accident-protection/aia-solitaire-personal-accident",
        "plan_description": "Personal accident cover with worldwide accident, dengue, medical and TCM treatment protection.",
        "plan_benefits": [
            "24/7 worldwide personal accident coverage.",
            "Medical and TCM treatment cost reimbursement.",
            "Food poisoning and dengue fever coverage.",
        ],
    },
    {
        "plan_name": "AIA Centurion PA",
        "plan_url": "https://www.aia.com.sg/en/our-products/accident-protection/aia-centurion-pa",
        "plan_description": "Personal accident plan with optional benefits for selected age-related diseases.",
        "plan_benefits": [
            "Personal accident protection.",
            "Optional Alzheimer's Disease, Severe Dementia and Parkinson's Disease benefits.",
            "Designed to address gaps in standard personal accident cover.",
        ],
    },
    {
        "plan_name": "AIA Platinum AccidentCare",
        "plan_url": "https://www.aia.com.sg/en/our-products/accident-protection/aia-platinum-accidentcare",
        "plan_description": "High-cover personal accident plan for worldwide accident protection.",
        "plan_benefits": [
            "Coverage of up to S$5 million for accidental death, dismemberment and burns.",
            "Overseas coverage for frequent travellers.",
            "Basic health screening at no charge.",
        ],
    },
    {
        "plan_name": "AIA Star Protector Plus",
        "plan_url": "https://www.aia.com.sg/en/our-products/accident-protection/aia-star-protector-plus",
        "plan_description": "Child accident protection with worldwide injury, burn and disease coverage.",
        "plan_benefits": [
            "Worldwide protection for accidental injuries and burns.",
            "Coverage for 16 common diseases.",
            "Designed for children.",
        ],
    },
    {
        "plan_name": "AIA #GenFit PA",
        "plan_url": "https://www.aia.com.sg/en/our-products/accident-protection/aia-genfit-pa",
        "plan_description": "Personal accident plan for active lifestyles.",
        "plan_benefits": [
            "Accident-related medical cost reimbursement.",
            "Device damage coverage.",
            "Unused gym membership and missed entertainment event reimbursement.",
        ],
    },
    {
        "plan_name": "AIA Prime Assured",
        "plan_url": "https://www.aia.com.sg/en/our-products/accident-protection/aia-prime-assured",
        "plan_description": "Senior-focused accident protection with age-related illness benefits.",
        "plan_benefits": [
            "Accidental injury and age-related illness coverage.",
            "Hospital cash support for accident hospitalisation.",
            "Reimbursement for home care, mobility aids and selected alternative treatment.",
        ],
    },
    {
        "plan_name": "AIA Around the World Plus (II)",
        "plan_url": "https://www.aia.com.sg/en/our-products/travel-and-lifestyle/travel/aia-around-the-world-plus-ii",
        "plan_description": "Travel insurance for pre-trip to post-trip protection.",
        "plan_benefits": [
            "Trip cancellation and postponement coverage.",
            "Travel delay, personal accident and medical expense protection.",
            "Single-trip and annual multi-trip options.",
        ],
    },
    {
        "plan_name": "AIA Elite HomeCare",
        "plan_url": "https://www.aia.com.sg/en/our-products/travel-and-lifestyle/home/aia-elite-homecare",
        "plan_description": "Home insurance solution covering household, family and pets.",
        "plan_benefits": [
            "Home and household protection.",
            "Family and pet coverage.",
            "Travel-linked home protection benefits.",
        ],
    },
    {
        "plan_name": "AIA Pro Achiever 3.0",
        "plan_url": "https://www.aia.com.sg/en/our-products/save-and-invest/investment-linked/aia-pro-achiever-iii",
        "plan_description": "Regular premium investment-linked plan combining wealth accumulation with life protection.",
        "plan_benefits": [
            "100% of regular premiums invested from day one.",
            "Welcome and special bonus features.",
            "Optional riders for additional protection.",
        ],
    },
    {
        "plan_name": "AIA Invest Easy",
        "plan_url": "https://www.aia.com.sg/en/our-products/save-and-invest/investment-linked/aia-invest-easy",
        "plan_description": "Investment-linked plan for flexible investing using cash, CPF or SRS funds.",
        "plan_benefits": [
            "Flexible withdrawals without charges.",
            "Broad fund and portfolio options.",
            "Designed for effortless investing.",
        ],
    },
    {
        "plan_name": "AIA Elite Secure Income",
        "plan_url": "https://www.aia.com.sg/en/our-products/save-and-invest/investment-linked/aia-elite-secure-income",
        "plan_description": "Investment-linked whole life plan with capital guarantee on basic premiums.",
        "plan_benefits": [
            "Invest from S$300 a month.",
            "No medical questions for application.",
            "Capital guaranteed on basic premiums.",
        ],
    },
    {
        "plan_name": "AIA Smart Wealth Builder Series",
        "plan_url": "https://www.aia.com.sg/en/our-products/save-and-invest/participating-savings/aia-smart-wealth-builder-series",
        "plan_description": "Participating savings plans for wealth accumulation and flexible withdrawals.",
        "plan_benefits": [
            "Designed for long-term wealth accumulation.",
            "Flexibility to withdraw funds.",
            "Supports education, retirement and other savings goals.",
        ],
    },
    {
        "plan_name": "AIA Smart Flexi Growth",
        "plan_url": "https://www.aia.com.sg/en/our-products/save-and-invest/participating-savings/aia-smart-flexi-growth",
        "plan_description": "Participating savings plan to grow wealth and budget for future goals.",
        "plan_benefits": [
            "Savings insurance for wealth growth.",
            "Future goal planning support.",
            "Participating policy benefits.",
        ],
    },
    {
        "plan_name": "AIA Smart Flexi Rewards (II)",
        "plan_url": "https://www.aia.com.sg/en/our-products/save-and-invest/participating-savings/aia-smart-flexi-rewards-ii",
        "plan_description": "Flexible savings plan with yearly guaranteed coupon options.",
        "plan_benefits": [
            "Yearly guaranteed coupon.",
            "Preferred payment and coverage period options.",
            "Optional riders to waive future premiums.",
        ],
    },
    {
        "plan_name": "AIA Retirement Saver (IV)",
        "plan_url": "https://www.aia.com.sg/en/our-products/save-and-invest/participating-savings/aia-retirement-saver-iv",
        "plan_description": "Retirement savings plan that can be started without a medical check-up.",
        "plan_benefits": [
            "Designed for retirement savings.",
            "No medical check-up needed.",
            "Supports planning before retirement age.",
        ],
    },
    {
        "plan_name": "AIA Platinum Legacy (IX)",
        "plan_url": "https://www.aia.com.sg/en/our-products/platinum/legacy-planning/aia-platinum-legacy-ix",
        "plan_description": "Legacy planning plan to enhance financial assets and transfer estate according to wishes.",
        "plan_benefits": [
            "Estate transfer and legacy planning.",
            "US dollar whole life structure.",
            "Supports intergenerational wealth planning.",
        ],
    },
    {
        "plan_name": "AIA Platinum Heritage Wealth (II)",
        "plan_url": "https://www.aia.com.sg/en/our-products/platinum/legacy-planning/aia-platinum-heritage-wealth-ii",
        "plan_description": "Whole life legacy plan with high guaranteed coverage up to age 100.",
        "plan_benefits": [
            "Lifetime assurance for policyholder and family.",
            "Death and terminal illness coverage up to age 100.",
            "Designed for stable wealth growth.",
        ],
    },
    {
        "plan_name": "AIA Platinum Indexed Legacy (II)",
        "plan_url": "https://www.aia.com.sg/en/our-products/platinum/legacy-planning/aia-platinum-indexed-legacy-ii",
        "plan_description": "Indexed universal life plan for S&P 500-linked growth and legacy planning.",
        "plan_benefits": [
            "S&P 500-linked indexed strategy.",
            "Downside protection features.",
            "Flexible legacy planning.",
        ],
    },
    {
        "plan_name": "AIA Platinum Generations (II)",
        "plan_url": "https://www.aia.com.sg/en/our-products/platinum/legacy-planning/aia-platinum-generations-ii",
        "plan_description": "Legacy plan to protect, preserve and grow wealth across generations.",
        "plan_benefits": [
            "Yearly guaranteed cash coupons from the 10th policy year-end.",
            "Potential non-guaranteed annual and terminal dividends.",
            "Designed to extend legacy up to 3 generations.",
        ],
    },
    {
        "plan_name": "AIA Platinum Infinite Wealth (II)",
        "plan_url": "https://www.aia.com.sg/en/our-products/platinum/wealth-accumulation/aia-platinum-infinite-wealth-ii",
        "plan_description": "Wealth accumulation plan with lifetime coverage and liquidity options.",
        "plan_benefits": [
            "Guaranteed return of capital as early as 7th policy year.",
            "Policy split, change of insured and secondary insured options.",
            "Single premium or 5-year regular premium options.",
        ],
    },
    {
        "plan_name": "AIA Platinum Retirement Elite",
        "plan_url": "https://www.aia.com.sg/en/our-products/platinum/wealth-accumulation/aia-platinum-retirement-elite",
        "plan_description": "Retirement plan with SGD and USD wealth accumulation options.",
        "plan_benefits": [
            "Single premium and 5-year regular premium options.",
            "Choice of target monthly retirement income and retirement age.",
            "Access to AIA Elite Conservative, Balanced and Adventurous portfolios.",
        ],
    },
    {
        "plan_name": "AIA Platinum Gift for Life Series",
        "plan_url": "https://www.aia.com.sg/en/our-products/platinum/wealth-accumulation/aia-platinum-gift-for-life-series",
        "plan_description": "Wealth accumulation plan designed to supplement lives across three generations.",
        "plan_benefits": [
            "Guaranteed monthly coupon up to age 120.",
            "Non-guaranteed monthly dividend potential.",
            "Option to change life insured for policy continuity.",
        ],
    },
    {
        "plan_name": "AIA Platinum Wealth Venture 2.0",
        "plan_url": "https://www.aia.com.sg/en/our-products/platinum/wealth-accumulation/aia-platinum-wealth-venture-ii",
        "plan_description": "Investment-linked plan with a short 5-year premium commitment.",
        "plan_benefits": [
            "Pay premiums for 5 years.",
            "Dividend income and reinvestment options through selected ILP funds.",
            "Welcome and investment bonus features.",
        ],
    },
)

AIA_DIRECT_PRODUCT_URLS = tuple(row["plan_url"] for row in AIA_PRODUCT_CATALOG)

CHROME_PATTERNS = (
    "aia group australia",
    "contact us",
    "cookie policy",
    "digital payment",
    "explore aia",
    "form library",
    "frequently asked questions",
    "our insurance products",
    "recent promotions",
    "security advisory",
    "social media",
    "useful links",
    "visit us",
    "what's your email address",
    "what's your mobile number",
)

BENEFIT_KEYWORDS = (
    "accident",
    "benefit",
    "cash",
    "claim",
    "cover",
    "coverage",
    "critical",
    "disability",
    "emergency",
    "health",
    "hospital",
    "income",
    "insurance",
    "medical",
    "outpatient",
    "premium",
    "protect",
    "savings",
    "support",
    "wealth",
)


def normalize_url(url: str) -> str:
    return urldefrag(str(url or "").strip()).url.rstrip("/")


def remove_excess_newlines(inp):
    if not isinstance(inp, str):
        raise TypeError(f"Input must be type <string> but was type <{type(inp).__name__}>")
    inp = re.sub(r"\n+", "\n", inp)
    inp = re.sub(r"[ \t\u200b]+", " ", inp)
    return inp.strip()


def normalize_whitespace(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def remove_html_entities(inp):
    inp2 = html.unescape(inp or "")
    replacements = {
        "\xa0": " ",
        "\u200b": "",
        "\u2013": "-",
        "\u2014": "--",
        "\u2026": "...",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u00ab": '"',
        "\u00bb": '"',
        "\u02c6": "^",
        "\u2039": "<",
        "\u203a": ">",
        "\u02dc": "~",
        "\u00a9": "(c)",
        "\u00ae": "(R)",
        "\u2122": "(TM)",
        "\u00b0": "°",
        "\u00b7": "*",
        "\u00b1": "+/-",
        "\u00bc": "1/4",
        "\u00bd": "1/2",
        "\u00be": "3/4",
        "&lt;": "<",
        "&gt;": ">",
        "&amp;": "&",
        "&quot;": '"',
        "&apos;": "'",
    }
    for old_char, new_char in replacements.items():
        inp2 = inp2.replace(old_char, new_char)
    return normalize_whitespace(inp2)


def parse_listing_html(html_content: str):
    soup = BeautifulSoup(html_content, "html.parser")
    product_filters_data = []
    for anchor in soup.select(".cmp-productfilterlist__container a"):
        h2_text = anchor.select_one("h2")
        next_div = anchor.select_one("h2 + div")
        plan_name = normalize_whitespace(h2_text.get_text(" ", strip=True) if h2_text else "")
        plan_url = normalize_url(urljoin(AIA_BASE_URL, anchor.get("href") or ""))
        description = normalize_whitespace(next_div.get_text(" ", strip=True) if next_div else "")
        if plan_name and not looks_like_chrome(plan_name):
            product_filters_data.append(
                {
                    "plan_name": plan_name,
                    "plan_url": plan_url,
                    "plan_description": description,
                }
            )
    return product_filters_data


def parse_product_html(html_content: str, source_url: str = ""):
    normalized_source = normalize_url(source_url)
    if normalized_source in {normalize_url(url) for url in REJECTED_SOURCE_URLS}:
        return None

    catalog_row = catalog_row_for_url(normalized_source)
    soup = BeautifulSoup(html_content, "html.parser")
    plan_name = product_title(
        soup.select_one("h1, h2, .cmp-productoverviewhero__title"),
        soup.select_one('meta[property="og:title"], meta[name="title"]'),
        soup,
    )
    if catalog_row:
        plan_name = catalog_row["plan_name"]
    if not plan_name and normalized_source:
        plan_name = title_from_url(normalized_source)
    if not plan_name and not normalized_source:
        plan_name = "AIA Product"
    if looks_like_chrome(plan_name):
        return None

    description = meta_description(soup) or (catalog_row or {}).get("plan_description", "")
    overview = product_overview(soup)
    benefits = benefit_blocks(soup)
    if catalog_row:
        benefits = dedupe_texts([*benefits, *catalog_row["plan_benefits"]])
        if not overview:
            overview = compact_text(" ".join(catalog_row["plan_benefits"]))
        description = description or catalog_row["plan_description"]

    row = {
        "plan_name": plan_name,
        "plan_description": compact_text(description, 500),
        "plan_overview": compact_text(overview, 900),
        "product_brochure_url": brochure_url(soup, normalized_source),
        "plan_benefits": benefits[:8],
        "plan_url": normalized_source,
    }
    if not normalized_source:
        return row if row["product_brochure_url"] or row["plan_benefits"] else None
    return row if valid_plan_row(row) else None


def parse_product_text(text_content: str, source_url: str):
    lines = [remove_excess_newlines(line) for line in text_content.splitlines()]
    lines = [line for line in lines if line and not looks_like_chrome(line)]
    title = next((line for line in lines if 4 <= len(line) <= 90), "")
    if not title:
        title = title_from_url(source_url)
    paragraphs = split_text_paragraphs(text_content)
    description = next((paragraph for paragraph in paragraphs if paragraph != title), "")
    benefits = [
        line
        for line in lines
        if any(keyword in line.lower() for keyword in BENEFIT_KEYWORDS) and len(line) <= 220
    ][:8]
    return {
        "plan_name": title,
        "plan_description": compact_text(description, 500),
        "plan_overview": compact_text(" ".join(paragraphs[:3]), 900),
        "product_brochure_url": source_url if source_url.lower().endswith(".pdf") else "",
        "plan_benefits": benefits,
    }


def product_title(title_content, meta_title, soup: BeautifulSoup) -> str:
    title = normalize_whitespace(title_content.get_text(" ", strip=True) if title_content else "")
    if not title or title.lower() in {"share", "overview"}:
        title = normalize_whitespace(meta_title.get("content", "") if meta_title else "")
    if not title and soup.title:
        title = normalize_whitespace(soup.title.get_text(" ", strip=True).split("|", 1)[0])
    return title


def title_from_url(url: str) -> str:
    slug = urlparse(url).path.rstrip("/").rsplit("/", 1)[-1]
    return " ".join(part.capitalize() for part in slug.split("-") if part)


def split_text_paragraphs(value: str) -> list[str]:
    paragraphs = [remove_excess_newlines(part) for part in re.split(r"\n\s*\n", value)]
    return [paragraph for paragraph in paragraphs if paragraph and not looks_like_chrome(paragraph)]


def meta_description(soup: BeautifulSoup) -> str:
    meta = soup.select_one('meta[name="description"], meta[property="og:description"]')
    return normalize_whitespace(meta.get("content", "") if meta else "")


def product_overview(soup: BeautifulSoup) -> str:
    selectors = (
        ".cmp-productoverviewhero__content",
        ".product-detail-hero",
        ".cmp-container .cmp-text",
        "main",
    )
    for selector in selectors:
        element = soup.select_one(selector)
        text = normalize_whitespace(element.get_text(" ", strip=True) if element else "")
        if is_content_text(text):
            return text
    return ""


def benefit_blocks(soup: BeautifulSoup) -> list[str]:
    benefits = []
    for element in soup.select(
        "div.cmp-featuredperk__content, .cmp-featuredperk, .cmp-teaser, li, h3"
    ):
        text = normalize_whitespace(element.get_text(" ", strip=True))
        lowered = text.lower()
        if not is_content_text(text, max_length=260):
            continue
        if any(keyword in lowered for keyword in BENEFIT_KEYWORDS):
            benefits.append(text)
    return dedupe_texts(benefits)


def brochure_url(soup: BeautifulSoup, source_url: str) -> str:
    for element in soup.select("[data-cta-btn-url]"):
        href = element.get("data-cta-btn-url") or ""
        if ".pdf" in href.lower():
            return urljoin(source_url or AIA_BASE_URL, href)
    for anchor in soup.select("a[href]"):
        href = anchor.get("href") or ""
        text = normalize_whitespace(anchor.get_text(" ", strip=True)).lower()
        if ".pdf" not in href.lower():
            continue
        if text and not any(term in text for term in ("brochure", "product summary", "policy")):
            continue
        if "中文" in text or "chinese" in text:
            continue
        return urljoin(source_url or AIA_BASE_URL, href)
    return ""


def build_plan_row(filter_data: dict, product_data: dict):
    benefits_data = product_data.get("plan_benefits") or []
    plan_url = normalize_url(filter_data.get("plan_url") or product_data.get("plan_url") or "")
    row = {
        "plan_name": normalize_whitespace(
            filter_data.get("plan_name") or product_data.get("plan_name") or ""
        ),
        "plan_benefits": (
            [remove_excess_newlines(benefits) for benefits in benefits_data]
            if benefits_data
            else [""]
        ),
        "plan_description": (
            remove_html_entities(filter_data.get("plan_description"))
            if filter_data.get("plan_description")
            else remove_html_entities(product_data.get("plan_description"))
        ),
        "plan_overview": (
            compact_text(product_data.get("plan_overview"), 900)
            if product_data.get("plan_overview")
            else ""
        ),
        "plan_url": plan_url,
        "product_brochure_url": product_data.get("product_brochure_url") or "",
    }
    return row


def fetch_html(url: str, session=requests) -> str:
    response = session.get(
        url,
        timeout=REQUEST_TIMEOUT_SECONDS,
        headers={"User-Agent": BOT_USER_AGENT},
    )
    response.raise_for_status()
    return response.text


def cache_slug(url: str) -> str:
    parsed = urlparse(url)
    value = f"{parsed.netloc}{parsed.path}".strip("/")
    return re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-").lower()


def cache_candidates(url: str, cache_dir: str | Path | None = None) -> list[Path]:
    root = Path(cache_dir or AIA_SOURCE_CACHE_DIR)
    parsed = urlparse(url)
    slug = cache_slug(url)
    basename = parsed.path.rstrip("/").rsplit("/", 1)[-1]
    path_key = parsed.path.strip("/").replace("/", "__")
    names = [
        f"{slug}.html",
        f"{slug}.txt",
        f"{slug}.pdf.txt",
        f"{path_key}.html" if path_key else "",
        f"{path_key}.txt" if path_key else "",
        f"{path_key}.pdf.txt" if path_key else "",
        f"{basename}.html" if basename else "",
        f"{basename}.txt" if basename else "",
        f"{basename}.pdf.txt" if basename else "",
    ]
    return [root / name for name in dict.fromkeys(names) if name]


def cached_payload(url: str, cache_dir: str | Path | None = None) -> tuple[str, str]:
    for candidate in cache_candidates(url, cache_dir):
        if not candidate.exists():
            continue
        kind = "html" if candidate.suffix == ".html" else "text"
        return candidate.read_text(encoding="utf-8"), kind
    return "", ""


async def page_content_or_fallback(page, url: str) -> tuple[str, str]:
    try:
        await goto_with_retry(page, url)
        return await page.content(), "html"
    except Exception as exc:
        log_url_failure(TABLE_NAME, url, exc)
        URL_FAILURES.append(f"{url}: {type(exc).__name__}: {exc}")
        try:
            return await asyncio.to_thread(fetch_html, url), "html"
        except Exception as fallback_exc:
            log_url_failure(TABLE_NAME, url, fallback_exc)
            URL_FAILURES.append(f"{url}: {type(fallback_exc).__name__}: {fallback_exc}")
            payload, kind = cached_payload(url)
            if payload:
                return payload, kind
            return "", ""


def is_product_url(url: str) -> bool:
    normalized = normalize_url(url)
    return normalized in {normalize_url(row["plan_url"]) for row in AIA_PRODUCT_CATALOG}


def catalog_row_for_url(url: str) -> dict | None:
    normalized = normalize_url(url)
    for row in AIA_PRODUCT_CATALOG:
        if normalize_url(row["plan_url"]) == normalized:
            return row
    return None


def catalog_row(row: dict) -> dict:
    benefits = dedupe_texts(row["plan_benefits"])
    return {
        "plan_name": row["plan_name"],
        "plan_description": row["plan_description"],
        "plan_overview": compact_text(" ".join(benefits), 900),
        "plan_benefits": benefits,
        "plan_url": normalize_url(row["plan_url"]),
        "product_brochure_url": row.get("product_brochure_url", ""),
    }


def valid_plan_row(row: dict) -> bool:
    if not row.get("plan_name") or not row.get("plan_url"):
        return False
    if not is_product_url(row["plan_url"]):
        return False
    values = [row.get("plan_name"), row.get("plan_description"), row.get("plan_overview")]
    return not any(looks_like_chrome(value) for value in values)


def is_content_text(text: str, max_length: int = 900) -> bool:
    normalized = normalize_whitespace(text)
    lowered = normalized.lower()
    if len(normalized) < 20 or len(normalized) > max_length:
        return False
    return not looks_like_chrome(normalized) and lowered not in {"image", "learn more"}


def looks_like_chrome(value: str | None) -> bool:
    lowered = normalize_whitespace(value).lower()
    if not lowered:
        return False
    return any(pattern in lowered for pattern in CHROME_PATTERNS)


def compact_text(text: str | None, limit: int = 900) -> str:
    text = normalize_whitespace(text)
    return text if len(text) <= limit else f"{text[: limit - 3].rstrip()}..."


def dedupe_texts(values: list[str]) -> list[str]:
    output = []
    seen = set()
    for value in values:
        text = normalize_whitespace(value)
        key = text.lower()
        if not text or key in seen:
            continue
        seen.add(key)
        output.append(text)
    return output


def dedupe_rows(rows: list[dict]) -> list[dict]:
    output = []
    seen = set()
    for row in rows:
        key = (row.get("plan_name", "").lower(), normalize_url(row.get("plan_url", "")))
        if key in seen or not all(key):
            continue
        seen.add(key)
        output.append(row)
    return output


def scrape_aia(session=requests, use_live: bool = False) -> list[dict]:
    rows = []
    if use_live:
        for row in AIA_PRODUCT_CATALOG:
            url = row["plan_url"]
            try:
                parsed = parse_product_html(fetch_html(url, session=session), url)
            except Exception as exc:
                print(f"[{TABLE_NAME}] using catalog fallback for {url}: {exc}")
                parsed = None
            rows.append(parsed or catalog_row(row))
    else:
        rows = [catalog_row(row) for row in AIA_PRODUCT_CATALOG]
    return dedupe_rows([row for row in rows if valid_plan_row(row)])


async def scrape_data(target_url):
    if target_url in SOURCE_URLS or normalize_url(target_url) in {
        normalize_url(url) for url in REJECTED_SOURCE_URLS
    }:
        return []
    catalog = catalog_row_for_url(target_url)
    if catalog:
        return [catalog_row(catalog)]
    return []


async def run_all_tasks(scrape_list):
    return await gather_scrape_results(TABLE_NAME, scrape_list, scrape_data)


def assert_semantic_quality(rows: list[dict]) -> None:
    findings = validate_plan_rows(format_plan_rows(TABLE_NAME, rows))
    if findings:
        details = "; ".join(finding.format() for finding in findings[:5])
        raise ValueError(f"AIA scraper produced invalid plan rows: {details}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--source-cache-dir")
    parser.add_argument("--live", action="store_true")
    args, _ = parser.parse_known_args()
    global AIA_SOURCE_CACHE_DIR
    if args.source_cache_dir:
        AIA_SOURCE_CACHE_DIR = args.source_cache_dir

    try:
        rows = scrape_aia(use_live=args.live)
        assert_semantic_quality(rows)
    except Exception as error:
        if not args.dry_run:
            record_scraper_failure(TABLE_NAME, error)
        raise

    print(f"[{TABLE_NAME}] produced {len(rows)} plan rows")
    if not rows:
        record_scraper_failure(TABLE_NAME, "no plan rows produced", dry_run=args.dry_run)
        return 1
    if not args.dry_run:
        initialize_data_store()
    overwrite_plans_for_insurer(TABLE_NAME, rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
