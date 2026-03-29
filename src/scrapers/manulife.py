"""
https://www.manulife.com.sg/

https://www.manulife.com.sg/en/self-serve/file-a-claim.html

https://www.manulife.com.sg/en/solutions/life/life-insurance.html
https://www.manulife.com.sg/en/solutions/health/health.html
https://www.manulife.com.sg/en/solutions/save/save.html
https://www.manulife.com.sg/en/solutions/invest/investment-linked-plans.html
https://www.manulife.com.sg/en/solutions/signature/signature.html
"""

if __package__ in {None, ""}:
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.scrapers._generic_domain import GenericScraperConfig, run_cli_scraper

CONFIG = GenericScraperConfig(table_name="manulife")


if __name__ == "__main__":
    run_cli_scraper(CONFIG, __doc__)
