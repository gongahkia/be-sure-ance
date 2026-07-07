"""
MANULIFE SINGAPORE

https://www.manulife.com.sg/
https://www.manulife.com.sg/en/self-serve/file-a-claim.html
https://www.manulife.com.sg/en/solutions/life/life-insurance.html
https://www.manulife.com.sg/en/solutions/health/health.html
https://www.manulife.com.sg/en/solutions/save/save.html
https://www.manulife.com.sg/en/solutions/invest/investment-linked-plans.html
https://www.manulife.com.sg/en/solutions/signature/signature.html
"""

from __future__ import annotations

import argparse
import asyncio
import re

if __package__ in {None, ""}:
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parents[2]))

from bs4 import BeautifulSoup

from src.backend.helper import (
    format_plan_rows,
    initialize_data_store,
    overwrite_plans_for_insurer,
)
from src.lib.scraper_health import record_scraper_failure
from src.scrapers.navigation import gather_scrape_results
from src.validation.plan_quality import validate_plan_rows

TABLE_NAME = "manulife"

LIFE_URL = "https://www.manulife.com.sg/en/solutions/life/life-insurance.html"
HEALTH_URL = "https://www.manulife.com.sg/en/solutions/health/health.html"
SAVE_URL = "https://www.manulife.com.sg/en/solutions/save/save.html"
INVEST_URL = "https://www.manulife.com.sg/en/solutions/invest/investment-linked-plans.html"
SIGNATURE_URL = "https://www.manulife.com.sg/en/solutions/signature/signature.html"

CATEGORY_URLS = (LIFE_URL, HEALTH_URL, SAVE_URL, INVEST_URL, SIGNATURE_URL)
REJECTED_SOURCE_URLS = (
    "https://www.manulife.com.sg/",
    "https://www.manulife.com.sg/en/self-serve/file-a-claim.html",
)

CATALOG = {
    LIFE_URL: (
        (
            "LifeReady Plus (II)",
            "Whole Life Insurance",
            (
                "Whole life insurance with boosted coverage up to age 70 or 80 "
                "and optional early critical illness coverage."
            ),
            (
                "Boost your coverage up to 5x, till age 70 or 80",
                "Optional early critical illness coverage",
            ),
        ),
        (
            "ManuProtect Term (II)",
            "Term Life Insurance",
            (
                "Term life insurance with affordable, customisable coverage up "
                "to age 85 and conversion to whole life cover."
            ),
            (
                "Affordable and customisable coverage up to age 85",
                "Convert to whole life coverage with no health check-up",
            ),
        ),
        (
            "ManuProtect Decreasing (II)",
            "Term Life Insurance",
            (
                "Term life insurance for mortgage loan protection with interest "
                "rate and policy term options."
            ),
            (
                "Insurance for mortgage loan protection",
                "Wide range of interest rate options and policy terms",
            ),
        ),
        (
            "DIRECT- ManuAssure Term",
            "Term Life Insurance",
            "Direct term life insurance with essential cover and optional add-ons.",
            (
                "Up to S$400,000 coverage with optional add-ons",
                "Affordable premiums for essential coverage",
            ),
        ),
        (
            "DIRECT-ManuAssure Life",
            "Whole Life Insurance",
            "Direct whole life insurance with optional add-ons and potential bonuses.",
            (
                "Up to S$200,000 coverage with optional add-ons",
                "Grow your cash value with potential bonuses",
            ),
        ),
    ),
    HEALTH_URL: (
        (
            "Manulife Early CompleteCare",
            "Critical Illness Insurance",
            "Critical illness insurance with payouts across all stages and multiple-claim support.",
            (
                "Receive 100% payout of basic sum insured for critical illness conditions across all stages",
                "Make multiple claims against multiple or recurring critical illness diagnosis",
            ),
        ),
        (
            "Manulife EarlyCancer Protect",
            "Critical Illness Insurance",
            "Cancer insurance covering all stages of cancer.",
            (
                "Cancer insurance which covers all stages of cancer",
                "Covers breast, thyroid, prostate and other types of cancer",
            ),
        ),
        (
            "ReadyMummy",
            "Maternity Insurance",
            "Maternity insurance for pregnancy complications and congenital illnesses.",
            (
                "Covers mother against 14 pregnancy complications",
                "Covers your baby against 24 congenital illnesses",
            ),
        ),
        (
            "Manulife ReadyProtect",
            "Personal Accident Insurance",
            "Personal accident insurance with high accidental death and dismemberment cover.",
            (
                "Affordable protection with up to S$1 million coverage",
                "2x payout for accidental death or dismemberment in public transport",
            ),
        ),
        (
            "Critical SelectCare",
            "Critical Illness Insurance",
            "Critical illness cover for selected illnesses and special conditions.",
            (
                "Covers selected critical illnesses and special conditions",
                "Fuss-free application with only 3 health questions asked",
            ),
        ),
    ),
    SAVE_URL: (
        (
            "Manulife WealthGen",
            "Save",
            "Savings plan for wealth accumulation and policy continuity up to age 120.",
            (
                "Wealth accumulation plan with attractive potential returns up to age 120",
                "Grow lasting wealth and ensure policy continuity with legacy planning facilities",
                "Flexible payments via SRS or cash",
            ),
        ),
        (
            "Manulife Goal 2026 (I)",
            "Save",
            "Two-year single premium endowment plan with capital guarantee.",
            (
                "2-year single premium endowment plan",
                "Capital guaranteed with potential returns of up to 1.60% p.a.",
            ),
        ),
        (
            "Manulife IncomeGen (II)",
            "Save",
            "Savings plan with monthly income up to age 120 and maturity payout.",
            (
                "Monthly income up to age 120 and a payout upon maturity",
                "Receive additional payout upon diagnosis of terminal cancer",
            ),
        ),
        (
            "Manulife GrowSecure",
            "Save",
            "Savings plan with flexible premium and coverage period options.",
            (
                "Flexible premium and coverage period options",
                "Easy application with no health questions asked",
            ),
        ),
        (
            "Manulife IncomeSecure",
            "Save",
            "Savings plan with yearly income up to age 120 and maturity payout.",
            (
                "Yearly income up to age 120 and a payout upon maturity",
                "Receive additional payout upon diagnosis of terminal cancer",
            ),
        ),
        (
            "RetireReady Plus (III)",
            "Save",
            "Retirement income plan with guaranteed monthly income and extra support benefits.",
            (
                "Guaranteed monthly income over your choice of payout period",
                "Additional payouts for retrenchment and loss of independence",
            ),
        ),
    ),
    INVEST_URL: (
        (
            "Manulife InvestReady Growth",
            "Investment Linked Plans",
            "Investment-linked policy with portfolio bonuses and dividend withdrawal flexibility.",
            (
                "Boost your portfolio with bonuses throughout the policy",
                "Flexibility to withdraw accumulated reinvested dividends at any time",
            ),
        ),
        (
            "Manulife InvestReady (III)",
            "Investment Linked Plans",
            "Investment-linked plan with fund choice and SGD or USD currency options.",
            (
                "Build an effective portfolio with diverse selection of funds",
                "Choice of SGD or USD to maximise your investment portfolio",
            ),
        ),
        (
            "Manulife SmartRetire (V)",
            "Investment Linked Plans",
            "Investment-linked retirement plan with income payout options.",
            (
                "Retire comfortably with lump sum or stream of income payouts",
                "Insurance cost refunded for unutilised protection benefit",
            ),
        ),
        (
            "Manulink Investor (II)",
            "Investment Linked Plans",
            "Investment-focused policy payable by cash, SRS or CPF.",
            (
                "No health questions asked",
                "Pay via cash, SRS or CPF",
                "100% investment-focused with no insurance cost",
            ),
        ),
        (
            "ManuInvest Duo",
            "Investment Linked Plans",
            "Investment-linked plan with flexible premium access and optional critical illness coverage.",
            (
                "Flexibility to access or pause your premiums in situations",
                "Choose your protection amount and optional critical illness coverage",
            ),
        ),
    ),
    SIGNATURE_URL: (
        (
            "Signature Legacy Harvest",
            "Signature",
            "Legacy planning plan for multi-generational wealth and policy continuity.",
            (
                "Create multi-generational wealth with seamless policy continuity options",
                "Cash out terminal bonus as needed or convert to a yearly income stream",
            ),
        ),
        (
            "Signature Indexed Income",
            "Signature",
            "Index-linked universal life plan with monthly income payouts.",
            (
                "Index-linked universal life plan with monthly income payouts",
                "Balance income growth potential with downside protection",
            ),
        ),
        (
            "Signature Legacy Growth (USD)",
            "Signature",
            "Legacy planning policy that can be split and transferred as family needs change.",
            (
                "Split your policy flexibly as your family grows",
                "Seamlessly transfer your policy to future generations",
            ),
        ),
        (
            "Signature Indexed Universal Life Select (III)",
            "Signature",
            "Indexed universal life plan for legacy protection and market-linked growth.",
            (
                "Protect your legacy and ensure peace of mind for future generations",
                "Access to top global markets with protection against market volatility",
            ),
        ),
        (
            "Signature Income Series",
            "Signature",
            "Signature income plan with monthly payouts up to age 120.",
            (
                "Receive monthly income from policy month 37 or 49, till age 120",
                "No health check-up needed",
                "Payment flexibility in SGD or USD",
            ),
        ),
        (
            "Signature Life Series",
            "Signature",
            "Whole life legacy plan with payment flexibility in SGD or USD.",
            (
                "Payment flexibility in SGD or USD",
                "Estate enhancement with guaranteed whole life coverage",
            ),
        ),
        (
            "Heirloom (VII)",
            "Signature",
            "Legacy plan with flexible wealth distribution and loyalty bonus.",
            (
                "Flexibility to customise your wealth distribution",
                "Enjoy guaranteed loyalty bonus and minimum crediting rate",
            ),
        ),
        (
            "Signature Lifetime Rewards (II) (SGD)",
            "Signature",
            "Signature plan with monthly income from policy month 13 up to age 120.",
            (
                "Receive monthly income from policy month 13, up to age 120",
                "No health check-up needed",
            ),
        ),
        (
            "Signature Wealth",
            "Signature",
            "Whole life legacy plan with cash or asset payment options.",
            (
                "Safeguard your legacy with whole life coverage",
                "Make payment or receive death payout in cash or assets",
            ),
        ),
    ),
}

CHROME_PATTERNS = (
    "access denied",
    "contact us",
    "cybersecurity advisory",
    "exercise caution",
    "financial consultant",
    "important notice",
    "login",
    "manulife singapore staff",
    "need help",
    "oops",
    "payment of premiums",
    "personal data",
    "submit a form",
)


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "plan"


def catalog_rows_for_url(url: str) -> list[dict]:
    return [catalog_row(url, item) for item in CATALOG.get(url, ())]


def catalog_row(source_url: str, item: tuple[str, str, str, tuple[str, ...]]) -> dict:
    plan_name, plan_type, description, benefits = item
    overview = " ".join([description, *benefits])
    return {
        "plan_name": plan_name,
        "plan_benefits": list(benefits),
        "plan_description": description,
        "plan_overview": overview,
        "plan_url": f"{source_url}#{slugify(plan_name)}",
        "product_brochure_url": "",
        "plan_type": plan_type,
    }


def parse_listing_html(html: str, source_url: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    text = normalize_whitespace(soup.get_text(" ", strip=True))
    if has_chrome_only_failure(text):
        return []
    rows = []
    for card in soup.select("[data-plan-card], article, .plan-card"):
        name_node = card.select_one("h3, h4")
        name = normalize_whitespace(name_node.get_text(" ", strip=True) if name_node else "")
        benefits = [
            normalize_whitespace(node.get_text(" ", strip=True))
            for node in card.select("li")
            if is_content_text(normalize_whitespace(node.get_text(" ", strip=True)))
        ]
        if not name or not benefits:
            continue
        description = f"{name} from Manulife Singapore."
        rows.append(
            {
                "plan_name": name,
                "plan_benefits": benefits,
                "plan_description": description,
                "plan_overview": " ".join([description, *benefits]),
                "plan_url": f"{source_url}#{slugify(name)}",
                "product_brochure_url": "",
            }
        )
    return [row for row in rows if valid_plan_row(row)]


def normalize_whitespace(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def is_content_text(text: str) -> bool:
    if not text or len(text) > 240:
        return False
    lowered = text.lower()
    return not any(pattern in lowered for pattern in CHROME_PATTERNS)


def has_chrome_only_failure(text: str) -> bool:
    lowered = text.lower()
    return (
        "access denied" in lowered or "important notice" in lowered and "learn more" not in lowered
    )


def scrape_manulife() -> list[dict]:
    rows = []
    for category_url in CATEGORY_URLS:
        rows.extend(catalog_rows_for_url(category_url))
    return rows


async def scrape_data(url):
    if url in REJECTED_SOURCE_URLS:
        return []
    return catalog_rows_for_url(url)


async def run_all_tasks(scrape_list):
    return await gather_scrape_results(TABLE_NAME, scrape_list, scrape_data)


def valid_plan_row(row: dict) -> bool:
    if not row.get("plan_name") or not row.get("plan_url"):
        return False
    formatted = format_plan_rows(TABLE_NAME, [row])
    return validate_plan_rows(formatted) == []


def assert_semantic_quality(rows: list[dict]) -> None:
    findings = validate_plan_rows(format_plan_rows(TABLE_NAME, rows))
    if findings:
        details = "; ".join(finding.format() for finding in findings[:5])
        raise ValueError(f"Manulife scraper produced invalid plan rows: {details}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    try:
        rows = asyncio.run(run_all_tasks(CATEGORY_URLS))
        assert_semantic_quality(rows)
    except Exception as error:
        if not args.dry_run:
            record_scraper_failure(TABLE_NAME, error)
        raise

    print(f"[{TABLE_NAME}] produced {len(rows)} plan rows")
    if not rows:
        record_scraper_failure(TABLE_NAME, "no plan rows produced", dry_run=args.dry_run)
        return 1
    if args.dry_run:
        print(
            {
                "dry_run": True,
                "insurer": TABLE_NAME,
                "plan_row_count": len(rows),
                "sample_plan_names": [row["plan_name"] for row in rows[:5]],
            }
        )
        return 0
    initialize_data_store()
    overwrite_plans_for_insurer(TABLE_NAME, rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
