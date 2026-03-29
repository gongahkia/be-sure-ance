"""
https://www.fwd.com.sg/

https://www.fwd.com.sg/home-insurance/
https://www.fwd.com.sg/fire-insurance/
https://www.fwd.com.sg/maid-insurance/
https://www.fwd.com.sg/car-insurance/
https://www.fwd.com.sg/motorcycle-insurance/
https://www.fwd.com.sg/travel-insurance/
https://www.fwd.com.sg/claim-online/
https://www.fwd.com.sg/forms/#claims
"""

if __package__ in {None, ""}:
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.scrapers._generic_domain import GenericScraperConfig, run_cli_scraper

CONFIG = GenericScraperConfig(table_name="fwd")


if __name__ == "__main__":
    run_cli_scraper(CONFIG, __doc__)
