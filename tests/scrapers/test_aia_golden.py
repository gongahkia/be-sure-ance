import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.backend.helper import format_plan_rows
from src.scrapers.aia import (
    AIA_DIRECT_PRODUCT_URLS,
    build_plan_row,
    cache_candidates,
    cached_payload,
    page_content_or_fallback,
    parse_listing_html,
    parse_product_html,
    parse_product_text,
    scrape_aia,
)
from src.scrapers.comparison_facts import build_fact_row
from src.validation.plan_quality import validate_plan_rows

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

    def test_cached_official_html_payload_is_loaded_by_url(self):
        url = "https://www.aia.com.sg/en/our-products/health/medical-insurance/aia-healthshield-gold-max"
        with tempfile.TemporaryDirectory() as tmp:
            cache_path = cache_candidates(url, tmp)[0]
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text((FIXTURES / "aia_product.html").read_text())

            payload, kind = cached_payload(url, tmp)

        self.assertEqual(kind, "html")
        self.assertIn("Hospital cash benefit", payload)

    def test_cached_pdf_text_can_build_plan_row(self):
        product = parse_product_text(
            """
            AIA Sample Protect

            Covers hospital and medical expenses after an accident.
            Accident benefit with health protection.
            """,
            "https://www.aia.com.sg/content/dam/sg/sample-protect.pdf",
        )
        row = build_plan_row(
            {
                "plan_name": "",
                "plan_url": "https://www.aia.com.sg/en/our-products/sample-protect",
            },
            product,
        )

        self.assertEqual(row["plan_name"], "AIA Sample Protect")
        self.assertEqual(
            row["product_brochure_url"],
            "https://www.aia.com.sg/content/dam/sg/sample-protect.pdf",
        )
        self.assertIn("Accident benefit with health protection.", row["plan_benefits"])

    def test_live_failures_fall_back_to_cache(self):
        async def run():
            with (
                patch("src.scrapers.aia.goto_with_retry", side_effect=RuntimeError("live down")),
                patch("src.scrapers.aia.fetch_html", side_effect=RuntimeError("requests down")),
                patch(
                    "src.scrapers.aia.cached_payload",
                    return_value=("<html><title>AIA Cached Plan</title></html>", "html"),
                ),
            ):
                return await page_content_or_fallback(object(), "https://www.aia.com.sg/x")

        payload, kind = asyncio.run(run())

        self.assertEqual(kind, "html")
        self.assertIn("AIA Cached Plan", payload)

    def test_direct_product_urls_use_current_official_paths(self):
        urls = "\n".join(AIA_DIRECT_PRODUCT_URLS)

        self.assertIn("/term-insurance/direct-aia-term-cover", urls)
        self.assertIn("/term-insurance/aia-secure-flexi-term", urls)
        self.assertIn("/accident-protection/aia-prime-assured", urls)
        self.assertIn("/corporate-medical-insurance/aia-foreign-worker-protector-plus", urls)
        self.assertNotIn("/term-life-insurance/", urls)

    def test_category_pages_are_rejected_as_plan_rows(self):
        row = parse_product_html(
            (FIXTURES / "aia_reject_category.html").read_text(),
            "https://www.aia.com.sg/en/our-products/life-insurance",
        )

        self.assertIsNone(row)

    def test_audited_catalog_outputs_sanitized_supported_rows(self):
        rows = scrape_aia()
        names = [row["plan_name"] for row in rows]

        self.assertIn("AIA HealthShield Gold Max", names)
        self.assertIn("AIA Platinum International Health", names)
        self.assertIn("AIA Around the World Plus (II)", names)
        self.assertIn("AIA Platinum Wealth Venture 2.0", names)
        self.assertNotIn("Life Insurance", names)
        self.assertGreaterEqual(len(rows), 40)
        self.assertEqual([], validate_plan_rows(format_plan_rows("aia", rows)))


if __name__ == "__main__":
    unittest.main()
