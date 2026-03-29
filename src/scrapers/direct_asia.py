"""
https://www.directasia.com/
https://www.directasia.com/car-insurance/promotions
https://www.directasia.com/car-insurance/authorised-workshops
https://www.directasia.com/motorcycle-insurance/cover-types
https://www.directasia.com/motorcycle-insurance/ncd
https://www.directasia.com/motorcycle-insurance/optional-benefits
https://www.directasia.com/motorcycle-insurance/who-rid
https://www.directasia.com/motorcycle-insurance/promotions
https://www.directasia.com/motorcycle-insurance/authorised-workshops
https://www.directasia.com/travel-insurance/plan-limits
https://www.directasia.com/travel-insurance/optional-benefit
https://www.directasia.com/travel-insurance/cover-limits
https://www.directasia.com/travel-insurance/who-we-cover
https://www.directasia.com/travel-insurance/features
https://www.directasia.com/travel-coverage-sport-activities-and-equipment
https://www.directasia.com/travel-insurance/promotions
https://www.directasia.com/student-school-group-travel-insurance
https://www.directasia.com/claims/car-motorcycle
https://www.directasia.com/claims/travel
https://www.directasia.com/car-insurance/cover-types
https://www.directasia.com/car-insurance/ncd60
https://www.directasia.com/car-insurance/drivers-and-usage
https://www.directasia.com/car-insurance/optional-benefits
"""

if __package__ in {None, ""}:
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.scrapers._generic_domain import GenericScraperConfig, run_cli_scraper

CONFIG = GenericScraperConfig(table_name="direct_asia")


if __name__ == "__main__":
    run_cli_scraper(CONFIG, __doc__)
