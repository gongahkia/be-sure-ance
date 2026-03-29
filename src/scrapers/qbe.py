"""
https://www.qbe.com/sg
https://www.qbe.com/sg/business-insurance
https://www.qbe.com/sg/personal-insurance
https://www.qbe.com/sg/eclaims
https://www.qbe.com/sg/eservice
"""

if __package__ in {None, ""}:
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.scrapers._generic_domain import GenericScraperConfig, run_cli_scraper

CONFIG = GenericScraperConfig(table_name="qbe")


if __name__ == "__main__":
    run_cli_scraper(CONFIG, __doc__)
