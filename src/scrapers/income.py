"""
NTUC INCOME

https://www.income.com.sg/
https://www.income.com.sg/claims/life-insurance
https://www.income.com.sg/claims/health-and-personal-accident
https://www.income.com.sg/claims/i50-insurance-claims
https://www.income.com.sg/claims/motor-insurance
https://www.income.com.sg/claims/travel-claims
https://www.income.com.sg/health-insurance
https://www.income.com.sg/claims/domestic-helper-insurance-claims
https://www.income.com.sg/claims/home-insurance-claims
https://www.income.com.sg/claims/overseas-study-protection-plan-claims
https://www.income.com.sg/claims/golfers-insurance-claims
https://www.income.com.sg/claims/group-insurance
https://www.income.com.sg/claims/commercial-insurance
https://www.income.com.sg/claims/claims-statistics
https://www.income.com.sg/claims/unclaimed-policies
https://www.income.com.sg/health-insurance
https://www.income.com.sg/personal-accident-insurance
https://www.income.com.sg/life-insurance
https://www.income.com.sg/travel-insurance
https://www.income.com.sg/drivo-car-insurance
https://www.income.com.sg/savings-and-investments
https://www.income.com.sg/enhanced-home-insurance
https://www.income.com.sg/domestic-helper-insurance
https://www.income.com.sg/group-insurance-for-employees
https://www.income.com.sg/commercial-insurance
https://www.income.com.sg/group-insurance-for-schools-and-centres-and-moe
https://www.income.com.sg/promotions/motorcycle-insurance-promotion
https://www.income.com.sg/happy-tails-pet-insurance
"""

if __package__ in {None, ""}:
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.scrapers._generic_domain import GenericScraperConfig, run_cli_scraper

CONFIG = GenericScraperConfig(table_name="income", max_seed_pages=32)


if __name__ == "__main__":
    run_cli_scraper(CONFIG, __doc__)
