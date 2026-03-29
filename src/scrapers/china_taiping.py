"""
https://www.sg.cntaiping.com/en/

https://www.sg.cntaiping.com/en/claims/life-insurance/claims-death-claim
https://www.sg.cntaiping.com/en/claims/general-insurance/claims-motor-insurance
https://www.sg.cntaiping.com/en/claims/business-insurance/claims-work-injury-compensation

https://www.sg.cntaiping.com/en/promotions.html

https://www.sg.cntaiping.com/en/personals/landing-protection/protection.html
https://www.sg.cntaiping.com/en/personals/landing-protection/personal-accident-and-health-insurance.html

https://www.sg.cntaiping.com/en/personals/landing-life-wealth/life.html
https://www.sg.cntaiping.com/en/personals/landing-life-wealth/wealth.html

https://www.sg.cntaiping.com/en/personals/landing-infinite-series/infinite-series.html

https://www.sg.cntaiping.com/en/business/landing-business/marine.html
https://www.sg.cntaiping.com/en/business/landing-business/financial-lines.html
https://www.sg.cntaiping.com/en/business/landing-business/business-packages.html

https://www.sg.cntaiping.com/en/business/landing-casualty-medical/casualty-commercial-insurance.html
https://www.sg.cntaiping.com/en/business/landing-casualty-medical/medical-health.html

https://www.sg.cntaiping.com/en/business/landing-insurance-engineering-bonds/property-insurance.html
https://www.sg.cntaiping.com/en/business/landing-insurance-engineering-bonds/engineering.html
https://www.sg.cntaiping.com/en/business/landing-insurance-engineering-bonds/bonds.html
"""

if __package__ in {None, ""}:
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.scrapers._generic_domain import GenericScraperConfig, run_cli_scraper

CONFIG = GenericScraperConfig(table_name="china_taiping")


if __name__ == "__main__":
    run_cli_scraper(CONFIG, __doc__)
