"""
https://alliedworldinsurance.com/singapore/

https://alliedworldinsurance.com/products_category/accident-health/
https://alliedworldinsurance.com/products/bespoke/
https://alliedworldinsurance.com/products/europe-uk-fine-art-specie/

https://alliedworldinsurance.com/products_category/casualty/
https://alliedworldinsurance.com/products_category/commercial-division/
https://alliedworldinsurance.com/products_category/commercial-motor/
https://alliedworldinsurance.com/products_category/construction-engineering/
https://alliedworldinsurance.com/products_category/crisis-management/
https://alliedworldinsurance.com/products_category/environmental-liability/

https://alliedworldinsurance.com/products_category/healthcare-liability/
https://alliedworldinsurance.com/products_category/management-financial-lines/
https://alliedworldinsurance.com/products_category/marine/
https://alliedworldinsurance.com/products_category/personal-lines/
https://alliedworldinsurance.com/products_category/professional-liability-indemnity/
https://alliedworldinsurance.com/products/programs-usa/
https://alliedworldinsurance.com/products_category/property-energy/
https://alliedworldinsurance.com/products_category/small-medium-business/
https://alliedworldinsurance.com/products_category/workers-compensation/

https://alliedworldinsurance.com/general-claims/
"""

if __package__ in {None, ""}:
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.scrapers._generic_domain import GenericScraperConfig, run_cli_scraper

CONFIG = GenericScraperConfig(table_name="allied_world")


if __name__ == "__main__":
    run_cli_scraper(CONFIG, __doc__)
