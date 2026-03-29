"""
https://www.prudential.com.sg/

https://www.prudential.com.sg/products/health-insurance
https://www.prudential.com.sg/products/life-insurance
https://www.prudential.com.sg/products/wealth-accumulation
https://www.prudential.com.sg/products/legacy-planning
https://www.prudential.com.sg/products/buy-online
https://www.prudential.com.sg/products/promotions
https://www.prudential.com.sg/products/srs/play-the-right-cards-with-srs
https://www.prudential.com.sg/lifestage
https://www.prudential.com.sg/claims-and-support/file-claim
https://www.prudential.com.sg/claims-and-support/payments
https://www.prudential.com.sg/claims-and-support/support
https://www.prudential.com.sg/
"""

if __package__ in {None, ""}:
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.scrapers._generic_domain import GenericScraperConfig, run_cli_scraper

CONFIG = GenericScraperConfig(table_name="prudential")


if __name__ == "__main__":
    run_cli_scraper(CONFIG, __doc__)
