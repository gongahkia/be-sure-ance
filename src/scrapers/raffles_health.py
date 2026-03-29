"""
https://www.raffleshealthinsurance.com/

https://www.raffleshealthinsurance.com/products/personal/singapore-medical-cover/
https://www.raffleshealthinsurance.com/products/personal/regional-medical-cover/
https://www.raffleshealthinsurance.com/lifeline/
https://www.raffleshealthinsurance.com/worldwide-health-options/

https://www.raffleshealthinsurance.com/products/business/singapore-regional-medical-cover/
https://www.raffleshealthinsurance.com/products/business/third-party-administration/

https://www.raffleshealthinsurance.com/claims/file-a-claim/personal-insurance-claim/
https://www.raffleshealthinsurance.com/claims/file-a-claim/corporate-insurance-claim/
"""

if __package__ in {None, ""}:
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.scrapers._generic_domain import GenericScraperConfig, run_cli_scraper

CONFIG = GenericScraperConfig(table_name="raffles_health")


if __name__ == "__main__":
    run_cli_scraper(CONFIG, __doc__)
