import unittest
from pathlib import Path

from src.scrapers.aia import build_plan_row, parse_listing_html, parse_product_html
from src.scrapers.comparison_facts import build_fact_row

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/fixtures"


class AiaGoldenTests(unittest.TestCase):
    def test_listing_fixture_extracts_plan_names_and_urls(self):
        plans = parse_listing_html((FIXTURES / "aia_listing.html").read_text())

        self.assertEqual(
            plans,
            [
                {
                    "plan_name": "Golden Accident Plan",
                    "plan_url": "https://www.aia.com.sg/en/our-products/accident-protection/golden-accident-plan",
                    "plan_description": "Personal accident and emergency support for active clients.",
                },
                {
                    "plan_name": "Golden Health Plan",
                    "plan_url": "https://www.aia.com.sg/en/our-products/health/golden-health-plan",
                    "plan_description": "Hospital and medical support with brochure-backed benefits.",
                },
            ],
        )

    def test_product_fixture_extracts_brochure_and_benefits(self):
        product = parse_product_html((FIXTURES / "aia_product.html").read_text())

        self.assertEqual(
            product["product_brochure_url"],
            "https://www.aia.com.sg/content/dam/sg/golden-accident-plan.pdf",
        )
        self.assertEqual(
            product["plan_benefits"],
            ["Emergency outpatient support", "Hospital cash benefit"],
        )
        self.assertIn("personal accident events", product["plan_overview"])

    def test_golden_plan_row_feeds_qualitative_fact_tags(self):
        filter_data = parse_listing_html((FIXTURES / "aia_listing.html").read_text())[0]
        product_data = parse_product_html((FIXTURES / "aia_product.html").read_text())
        row = build_plan_row(filter_data, product_data)
        fact_row = build_fact_row("aia", row, specialist_resource_count=1)

        self.assertEqual(row["plan_name"], "Golden Accident Plan")
        self.assertEqual(
            row["product_brochure_url"],
            "https://www.aia.com.sg/content/dam/sg/golden-accident-plan.pdf",
        )
        self.assertIn("Emergency outpatient support", row["plan_benefits"])
        self.assertEqual(fact_row["plan_slug"], "golden-accident-plan")
        self.assertIn("accident", fact_row["coverage_tags"])
        self.assertIn("emergency", fact_row["coverage_tags"])
        self.assertIn("hospitalization", fact_row["coverage_tags"])
        self.assertIn("provider_directory", fact_row["coverage_tags"])
        self.assertIn("brochure_available", fact_row["coverage_tags"])


if __name__ == "__main__":
    unittest.main()
