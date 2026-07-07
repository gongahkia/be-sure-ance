import unittest
from pathlib import Path

from src.backend.helper import format_plan_rows
from src.scrapers import chubb, fwd, iii, panel_resources, prudential, raffles_health, uoi
from src.validation.plan_quality import validate_plan_rows

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"


class FakeStreamingResponse:
    def __init__(self, chunks):
        self.chunks = chunks

    def iter_content(self, chunk_size):
        return iter(self.chunks)


class FakeHTTPResponse:
    def __init__(self, text):
        self.text = text

    def raise_for_status(self):
        return None


class FakeSession:
    def __init__(self, html_by_url):
        self.html_by_url = html_by_url

    def get(self, url, timeout, headers):
        return FakeHTTPResponse(self.html_by_url[url])


class ScraperParserFixTests(unittest.TestCase):
    def test_chubb_product_parser_extracts_personal_plan(self):
        row = chubb.parse_product_html(
            """
            <html><head><meta name="description" content="Personal accident cover."></head>
            <body><h1>Personal Accident Insurance</h1>
            <p>Designed to cover you and your family.</p>
            <li>Accident-related injury protection</li></body></html>
            """,
            "https://www.chubb.com/sg-en/individuals-families/personal-accident-insurance.html",
        )

        self.assertEqual(row["plan_name"], "Personal Accident Insurance")
        self.assertEqual(row["plan_description"], "Personal accident cover.")
        self.assertIn("Accident-related injury protection", row["plan_benefits"])

    def test_chubb_dedupes_listing_and_direct_rows(self):
        rows = chubb.dedupe_rows(
            [
                {"plan_name": "Travel", "plan_url": "https://example.com/travel"},
                {"plan_name": "Travel", "plan_url": "https://example.com/travel"},
                {"plan_name": "Home", "plan_url": "https://example.com/home"},
            ]
        )

        self.assertEqual([row["plan_name"] for row in rows], ["Travel", "Home"])

    def test_iii_parser_falls_back_to_url_title(self):
        row = iii.parse_product_html(
            "<html><body><main><p>Simple travel coverage.</p><li>Trip delay</li></main></body></html>",
            "https://www.iii.com.sg/products/travel-insurance",
        )

        self.assertEqual(row["plan_name"], "Travel Insurance")
        self.assertEqual(row["plan_description"], "Simple travel coverage.")
        self.assertEqual(row["plan_benefits"], ["Trip delay"])

    def test_uoi_parser_treats_brochure_pdf_as_optional(self):
        row = uoi.parse_product_html(
            """
            <html><head><title>UniTravel Insurance</title></head><body>
            <h1>UniTravel Insurance</h1><p>Travel protection.</p><li>Medical expenses</li>
            <a href="/assets/unitravel-brochure.pdf">UniTravel Brochure</a>
            </body></html>
            """,
            "https://www.uoi.com.sg/personal/travel-insurance.page",
        )

        self.assertEqual(row["plan_name"], "UniTravel Insurance")
        self.assertEqual(
            row["product_brochure_url"],
            "https://www.uoi.com.sg/assets/unitravel-brochure.pdf",
        )

    def test_panel_pdf_reader_caps_streamed_bytes(self):
        with self.assertRaises(ValueError):
            panel_resources.read_limited_response_content(
                FakeStreamingResponse([b"a" * 4, b"b" * 4]),
                max_bytes=6,
            )

        self.assertEqual(
            panel_resources.read_limited_response_content(
                FakeStreamingResponse([b"a" * 4, b"b" * 2]),
                max_bytes=6,
            ),
            b"aaaabb",
        )

    def test_fwd_product_parser_scopes_out_navigation_chrome(self):
        html = (FIXTURES_DIR / "fwd_product.html").read_text()
        row = fwd.parse_product_html(
            html,
            "https://www.fwd.com.sg/home-insurance/",
        )

        self.assertEqual(row["plan_name"], "Home insurance")
        self.assertIn("comprehensive protection", row["plan_description"])
        self.assertNotIn("Life & health", row["plan_overview"])
        self.assertNotIn("Check your price", row["plan_overview"])
        self.assertEqual(
            row["product_brochure_url"],
            "https://www.fwd.com.sg/documents/home-insurance-policy-wording.pdf",
        )
        self.assertEqual(
            [],
            validate_plan_rows(format_plan_rows(fwd.TABLE_NAME, [row])),
        )

    def test_fwd_rejects_homepage_and_inactive_fire_pages_as_plan_rows(self):
        product_html = (FIXTURES_DIR / "fwd_product.html").read_text()
        reject_html = (FIXTURES_DIR / "fwd_reject.html").read_text()

        self.assertIsNone(
            fwd.parse_product_html(
                product_html,
                "https://www.fwd.com.sg/",
            )
        )
        self.assertIsNone(
            fwd.parse_product_html(
                reject_html,
                "https://www.fwd.com.sg/fire-insurance/",
            )
        )

    def test_fwd_scraper_has_exact_allowlisted_products(self):
        html = (FIXTURES_DIR / "fwd_product.html").read_text()
        session = FakeSession({url: html for url in fwd.PRODUCT_URLS})
        rows = fwd.scrape_fwd(session=session)

        self.assertEqual(
            [
                "Home insurance",
                "Maid insurance",
                "Car insurance",
                "Motorcycle insurance",
                "Travel insurance",
                "FWD Life PA insurance",
                "Direct Term Life insurance",
                "Critical Illness Plus insurance",
            ],
            [row["plan_name"] for row in rows],
        )
        self.assertNotIn("HDB Fire insurance", [row["plan_name"] for row in rows])
        self.assertEqual(
            [],
            validate_plan_rows(format_plan_rows(fwd.TABLE_NAME, rows)),
        )

    def test_raffles_product_parser_scopes_out_navigation_chrome(self):
        html = (FIXTURES_DIR / "raffles_health_product.html").read_text()
        row = raffles_health.parse_product_html(
            html,
            "https://www.raffleshealthinsurance.com/products/raffles-critical-illness-plan/",
        )

        self.assertEqual(row["plan_name"], "Raffles Critical Illness Plan")
        self.assertIn("37 critical illnesses", row["plan_description"])
        self.assertNotIn("Products For Individuals", row["plan_overview"])
        self.assertNotIn("Contact Us X Contact Us", row["plan_overview"])
        self.assertEqual(
            row["product_brochure_url"],
            "https://www.raffleshealthinsurance.com/wp-content/uploads/2026/06/Raffles-Critical-Illness-Plan-Brochure.pdf",
        )
        self.assertEqual(
            [],
            validate_plan_rows(format_plan_rows(raffles_health.TABLE_NAME, [row])),
        )

    def test_raffles_rejects_category_and_tpa_pages_as_plan_rows(self):
        html = (FIXTURES_DIR / "raffles_health_reject.html").read_text()

        self.assertIsNone(
            raffles_health.parse_product_html(
                html,
                "https://www.raffleshealthinsurance.com/products/business/singapore-regional-medical-cover/",
            )
        )
        self.assertIsNone(
            raffles_health.parse_product_html(
                html,
                "https://www.raffleshealthinsurance.com/products/business/third-party-administration/",
            )
        )

    def test_raffles_scraper_has_exact_allowlisted_products(self):
        html = (FIXTURES_DIR / "raffles_health_product.html").read_text()
        session = FakeSession({url: html for url in raffles_health.PRODUCT_URLS})
        rows = raffles_health.scrape_raffles_health(session=session)

        self.assertEqual(
            [
                "Raffles Shield",
                "Raffles Critical Illness Plan",
                "Raffles Elite Care",
                "Lifeline",
                "Worldwide Health Options",
                "Customised Group Insurance",
                "Raffles Corporate Care Enhanced III",
                "Foreign Workers Medical Insurance (FWMI) Enhanced II",
            ],
            [row["plan_name"] for row in rows],
        )
        self.assertNotIn("Third Party Administration", [row["plan_name"] for row in rows])
        self.assertEqual(
            [],
            validate_plan_rows(format_plan_rows(raffles_health.TABLE_NAME, rows)),
        )

    def test_prudential_product_parser_rejects_category_hero_copy(self):
        category_html = (FIXTURES_DIR / "prudential_category.html").read_text()

        self.assertIsNone(
            prudential.parse_product_html(
                category_html,
                "https://www.prudential.com.sg/products/health-insurance",
            )
        )

    def test_prudential_product_parser_extracts_detail_page(self):
        product_html = (FIXTURES_DIR / "prudential_product.html").read_text()
        row = prudential.parse_product_html(
            product_html,
            "https://www.prudential.com.sg/products/life-insurance/term-life-insurance/pruactive-term",
        )

        self.assertEqual(row["plan_name"], "PRU Active Term")
        self.assertIn("term life insurance plan", row["plan_description"])
        self.assertNotIn("Protect you and your family", row["plan_overview"])
        self.assertEqual(
            row["product_brochure_url"],
            "https://www.prudential.com.sg/-/media/project/prudential/pdf/ebrochures/pruactive-term/pruactive_term_ebrochure_english.pdf",
        )
        self.assertEqual(
            [],
            validate_plan_rows(format_plan_rows(prudential.TABLE_NAME, [row])),
        )

    def test_prudential_discovery_filters_to_product_details(self):
        category_url = "https://www.prudential.com.sg/products/health-insurance"
        product_url = (
            "https://www.prudential.com.sg/products/life-insurance/term-life-insurance/"
            "pruactive-term/"
        )
        session = FakeSession(
            {
                category_url: (FIXTURES_DIR / "prudential_category.html").read_text(),
                product_url: (FIXTURES_DIR / "prudential_product.html").read_text(),
            }
        )

        self.assertEqual(
            [product_url],
            prudential.discover_product_urls(session=session, discovery_urls=[category_url]),
        )
        rows = prudential.scrape_prudential(session=session, discovery_urls=[category_url])
        self.assertEqual(["PRU Active Term"], [row["plan_name"] for row in rows])


if __name__ == "__main__":
    unittest.main()
