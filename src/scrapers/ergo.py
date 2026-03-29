"""
https://www.ergo.com.sg/
https://www.ergo.com.sg/claim
https://www.ergo.com.sg/insurance/personal/motor/product-information
https://www.ergo.com.sg/insurance/personal/personal-accident/product-information
https://www.ergo.com.sg/insurance/personal/travel/product-information
https://www.ergo.com.sg/insurance/personal/home/product-information
https://www.ergo.com.sg/insurance/commercial/group-personal-accident/product-information
https://www.ergo.com.sg/insurance/commercial/foreign-worker-medical/product-information
https://www.ergo.com.sg/insurance/commercial/property/product-information
https://www.ergo.com.sg/insurance/commercial/bonds/product-information
https://www.ergo.com.sg/insurance/commercial/public-liability/product-information
https://www.ergo.com.sg/insurance/commercial/travel/product-information
https://www.ergo.com.sg/insurance/commercial/motor/product-information
https://www.ergo.com.sg/insurance/commercial/marine/product-information
https://www.ergo.com.sg/insurance/commercial/work-injury/product-information
https://www.ergo.com.sg/insurance/commercial/contractor-all-risks-engineering/product-information
https://www.ergo.com.sg/insurance/commercial/miscellaneous/product-information
"""

if __package__ in {None, ""}:
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.scrapers._generic_domain import GenericScraperConfig, run_cli_scraper

CONFIG = GenericScraperConfig(table_name="ergo")


if __name__ == "__main__":
    run_cli_scraper(CONFIG, __doc__)
