"""
https://www.etiqa.com.sg/
https://www.etiqa.com.sg/personal/life-critical-illness-protection/
https://www.etiqa.com.sg/personal/premier-solutions/
https://www.etiqa.com.sg/personal/investments/
https://www.etiqa.com.sg/personal/savings-retirement/
https://www.etiqa.com.sg/personal/personal-accident/
https://www.etiqa.com.sg/personal/personal-cyber-insurance/
https://www.etiqa.com.sg/personal/maid-insurance/
https://www.etiqa.com.sg/personal/travel-insurance/
https://www.etiqa.com.sg/personal/home-insurance/
https://www.etiqa.com.sg/personal/fire-insurance/
https://www.etiqa.com.sg/personal/pet-insurance/
https://www.etiqa.com.sg/personal/motor-insurance/
https://www.etiqa.com.sg/business-insurance/accident-health/
https://www.etiqa.com.sg/business-insurance/commercial-vehicle/
https://www.etiqa.com.sg/business-insurance/casualty/
https://www.etiqa.com.sg/business-insurance/corporate-travel/
https://www.etiqa.com.sg/business-insurance/engineering/
https://www.etiqa.com.sg/business-insurance/marine/
https://www.etiqa.com.sg/business-insurance/business-owners-super-suite/
https://www.etiqa.com.sg/business-insurance/miscellaneous/
https://www.etiqa.com.sg/business-insurance/property/
https://www.etiqa.com.sg/claims-and-services/
"""

if __package__ in {None, ""}:
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.scrapers._static_pages import run_static_product_scraper

PRODUCT_URLS = [
    "https://www.etiqa.com.sg/personal/life-critical-illness-protection/",
    "https://www.etiqa.com.sg/personal/premier-solutions/",
    "https://www.etiqa.com.sg/personal/investments/",
    "https://www.etiqa.com.sg/personal/savings-retirement/",
    "https://www.etiqa.com.sg/personal/personal-accident/",
    "https://www.etiqa.com.sg/personal/personal-cyber-insurance/",
    "https://www.etiqa.com.sg/personal/maid-insurance/",
    "https://www.etiqa.com.sg/personal/travel-insurance/",
    "https://www.etiqa.com.sg/personal/home-insurance/",
    "https://www.etiqa.com.sg/personal/fire-insurance/",
    "https://www.etiqa.com.sg/personal/pet-insurance/",
    "https://www.etiqa.com.sg/personal/motor-insurance/",
    "https://www.etiqa.com.sg/business-insurance/accident-health/",
    "https://www.etiqa.com.sg/business-insurance/commercial-vehicle/",
    "https://www.etiqa.com.sg/business-insurance/corporate-travel/",
    "https://www.etiqa.com.sg/business-insurance/property/",
]


if __name__ == "__main__":
    run_static_product_scraper("etiqa", PRODUCT_URLS)
