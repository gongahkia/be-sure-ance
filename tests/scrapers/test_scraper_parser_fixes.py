import unittest
from pathlib import Path

from src.backend.helper import format_plan_rows
from src.scrapers import (
    allianz,
    china_life,
    chubb,
    etiqa,
    fwd,
    great_eastern,
    hl_assurance,
    hsbc,
    iii,
    income,
    manulife,
    panel_resources,
    prudential,
    raffles_health,
    singlife,
    sompo,
    sunlife,
    tokio_marine,
    uoi,
)
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
    def test_allianz_product_parser_scopes_out_navigation_chrome(self):
        html = (FIXTURES_DIR / "allianz_product.html").read_text()
        row = allianz.parse_product_html(
            html,
            "https://www.allianz.sg/individual-solutions/allianz-home-protect.html",
        )

        self.assertEqual(row["plan_name"], "Allianz Home Protect")
        self.assertIn("Home contents", row["plan_description"])
        self.assertNotIn("Contact Us", row["plan_overview"])
        self.assertIn("Covers your home contents", row["plan_benefits"])
        self.assertEqual(
            row["product_brochure_url"],
            "https://www.allianz.sg/content/dam/onemarketing/azsg/allianz-home-protect-policy-wording.pdf",
        )
        self.assertEqual(
            [],
            validate_plan_rows(format_plan_rows(allianz.TABLE_NAME, [row])),
        )

    def test_allianz_rejects_claims_and_unknown_pages_as_plan_rows(self):
        reject_html = (FIXTURES_DIR / "allianz_reject.html").read_text()

        self.assertIsNone(
            allianz.parse_product_html(
                reject_html,
                "https://www.allianz.sg/claims.html",
            )
        )
        self.assertIsNone(
            allianz.parse_product_html(
                reject_html,
                "https://www.allianz.sg/news.html",
            )
        )

    def test_allianz_catalog_outputs_exact_supported_rows(self):
        rows = allianz.scrape_allianz()
        names = [row["plan_name"] for row in rows]

        self.assertIn("Allianz Motor Protect", names)
        self.assertIn("Allianz Cyber360 Protect", names)
        self.assertIn("Commercial Motor Insurance", names)
        self.assertNotIn("Claims", names)
        self.assertEqual(18, len(rows))
        self.assertEqual(
            [],
            validate_plan_rows(format_plan_rows(allianz.TABLE_NAME, rows)),
        )

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
        self.assertEqual(
            [],
            validate_plan_rows(format_plan_rows(chubb.TABLE_NAME, [row])),
        )

    def test_chubb_rejects_listing_and_support_pages_as_plan_rows(self):
        html = """
        <html><body><h1>Contact Us</h1>
        <p>Explore Chubb claims centre and contact us pages.</p></body></html>
        """

        self.assertIsNone(
            chubb.parse_product_html(
                html,
                "https://www.chubb.com/sg-en/individuals-families.html",
            )
        )
        self.assertIsNone(
            chubb.parse_product_html(
                html,
                "https://www.chubb.com/sg-en/contact-us.html",
            )
        )

    def test_china_life_product_parser_extracts_summary_and_brochure(self):
        html = (FIXTURES_DIR / "china_life_product.html").read_text()
        row = china_life.parse_product_html(
            html,
            "https://www.chinalife.com.sg/products/china-life-critical-trio",
        )

        self.assertEqual(row["plan_name"], "China Life Critical Trio")
        self.assertIn("Cancer, Heart Attack and Stroke", row["plan_description"])
        self.assertIn("Critical Illness (CI) Benefit", row["plan_benefits"])
        self.assertEqual(
            row["product_brochure_url"],
            "https://www.chinalife.com.sg/sites/default/files/product/China%20Life%20Critical%20Trio%20Brochure_EN_0.pdf",
        )
        self.assertEqual(
            [],
            validate_plan_rows(format_plan_rows(china_life.TABLE_NAME, [row])),
        )

    def test_china_life_rejects_forms_and_category_pages_as_plan_rows(self):
        html = (FIXTURES_DIR / "china_life_reject.html").read_text()

        self.assertIsNone(
            china_life.parse_product_html(
                html,
                "https://www.chinalife.com.sg/forms",
            )
        )
        self.assertIsNone(
            china_life.parse_product_html(
                html,
                "https://www.chinalife.com.sg/products/protection",
            )
        )

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

    def test_iii_product_parser_stops_before_support_chrome(self):
        html = (FIXTURES_DIR / "iii_product.html").read_text()
        row = iii.parse_product_html(
            html,
            "https://www.iii.com.sg/products/travel-insurance",
        )

        self.assertEqual(row["plan_name"], "Travel Insurance")
        self.assertIn("reliable travel insurance", row["plan_description"])
        self.assertIn("Medical expenses", " ".join(row["plan_benefits"]))
        self.assertNotIn("Still Have Queries", row["plan_overview"])
        self.assertNotIn("pncuw@iii.com.sg", row["plan_overview"])
        self.assertEqual(
            row["product_brochure_url"],
            "https://www.iii.com.sg/sites/default/files/2024-08/travel.pdf",
        )
        self.assertEqual([], validate_plan_rows(format_plan_rows(iii.TABLE_NAME, [row])))

    def test_iii_rejects_homepage_as_plan_row(self):
        html = (FIXTURES_DIR / "iii_reject.html").read_text()

        self.assertIsNone(
            iii.parse_product_html(
                html,
                "https://www.iii.com.sg/",
            )
        )

    def test_hl_assurance_product_parser_uses_meta_and_brochure(self):
        html = (FIXTURES_DIR / "hl_assurance_product.html").read_text()
        row = hl_assurance.parse_product_html(
            html,
            "https://www.hlas.com.sg/personal-insurance/travel-insurance/",
        )

        self.assertEqual(row["plan_name"], "Travel Insurance")
        self.assertIn("no claims discount", row["plan_description"])
        self.assertIn("emergency evacuation cover", " ".join(row["plan_benefits"]))
        self.assertEqual(
            row["product_brochure_url"],
            "https://www.hlas.com.sg/wp-content/uploads/travel-insurance-policy-wording.pdf",
        )
        self.assertEqual(
            [],
            validate_plan_rows(format_plan_rows(hl_assurance.TABLE_NAME, [row])),
        )

    def test_hl_assurance_rejects_claim_pages_as_plan_rows(self):
        html = (FIXTURES_DIR / "hl_assurance_reject.html").read_text()

        self.assertIsNone(
            hl_assurance.parse_product_html(
                html,
                "https://www.hlas.com.sg/claim-forms/",
            )
        )

    def test_hsbc_product_parser_uses_meta_and_real_brochure_pdf(self):
        html = (FIXTURES_DIR / "hsbc_product.html").read_text()
        row = hsbc.parse_product_html(
            html,
            "https://www.insurance.hsbc.com.sg/life-and-critical-illness/products/life-treasure-iii/",
        )

        self.assertEqual(row["plan_name"], "HSBC Life – Life Treasure III")
        self.assertIn("multiplied coverage", row["plan_description"])
        self.assertIn("critical illness rider", " ".join(row["plan_benefits"]))
        self.assertNotIn("Help and support", row["plan_overview"])
        self.assertEqual(
            row["product_brochure_url"],
            "https://www.insurance.hsbc.com.sg/content/dam/hsbc/insn/documents/life/life-treasure-iii-product-brochure.pdf",
        )
        self.assertEqual(
            [],
            validate_plan_rows(format_plan_rows(hsbc.TABLE_NAME, [row])),
        )

    def test_hsbc_rejects_support_pages_and_legacy_report(self):
        html = (FIXTURES_DIR / "hsbc_reject.html").read_text()

        self.assertIsNone(
            hsbc.parse_product_html(
                html,
                "https://www.insurance.hsbc.com.sg/claims/",
            )
        )
        self.assertEqual(
            [],
            hsbc.scrape_product_url(
                "https://www.insurance.hsbc.com.sg/content/dam/hsbc/insn/documents/life-hnw-legacy-research-report.pdf"
            ),
        )

    def test_income_discovers_product_detail_links_from_listing(self):
        html = (FIXTURES_DIR / "income_listing.html").read_text()
        session = FakeSession(
            {
                "https://www.income.com.sg/health-insurance": html,
            }
        )

        self.assertEqual(
            income.discover_product_urls(
                session=session,
                listing_urls=["https://www.income.com.sg/health-insurance"],
            ),
            [
                "https://www.income.com.sg/travel-insurance",
                "https://www.income.com.sg/enhanced-prex-travel-insurance",
                "https://www.income.com.sg/drivo-car-insurance",
                "https://www.income.com.sg/edrivo-car-insurance",
                "https://www.income.com.sg/motorcycle-insurance",
                "https://www.income.com.sg/enhanced-home-insurance",
                "https://www.income.com.sg/domestic-helper-insurance",
                "https://www.income.com.sg/happy-tails-pet-insurance",
                "https://www.income.com.sg/overseas-study-protection-plan",
                "https://www.income.com.sg/home-ultimate-protect",
                "https://www.income.com.sg/health-insurance/enhanced-incomeshield",
            ],
        )

    def test_income_product_parser_filters_chrome_and_wrong_pdfs(self):
        html = (FIXTURES_DIR / "income_product.html").read_text()
        row = income.parse_product_html(
            html,
            "https://www.income.com.sg/drivo-car-insurance",
        )

        self.assertEqual(row["plan_name"], "Drivo Car Insurance")
        self.assertIn("affordable car insurance", row["plan_description"])
        self.assertIn("roadside assistance", row["plan_overview"])
        self.assertNotIn("Download My Income App", row["plan_overview"])
        self.assertEqual(
            row["product_brochure_url"],
            "https://assets.example/drivo-car-insurance-brochure.pdf",
        )
        self.assertEqual([], validate_plan_rows(format_plan_rows(income.TABLE_NAME, [row])))

    def test_income_rejects_claim_pages_as_plan_rows(self):
        html = (FIXTURES_DIR / "income_reject.html").read_text()

        self.assertIsNone(
            income.parse_product_html(
                html,
                "https://www.income.com.sg/claims/travel-claims",
            )
        )

    def test_manulife_listing_parser_extracts_plan_cards(self):
        html = (FIXTURES_DIR / "manulife_listing.html").read_text()
        rows = manulife.parse_listing_html(html, manulife.LIFE_URL)

        self.assertEqual(1, len(rows))
        self.assertEqual(rows[0]["plan_name"], "LifeReady Plus (II)")
        self.assertIn("Boost your coverage", rows[0]["plan_overview"])
        self.assertEqual(
            [],
            validate_plan_rows(format_plan_rows(manulife.TABLE_NAME, rows)),
        )

    def test_manulife_rejects_access_denied_pages(self):
        html = (FIXTURES_DIR / "manulife_reject.html").read_text()

        self.assertEqual([], manulife.parse_listing_html(html, manulife.LIFE_URL))
        self.assertEqual([], manulife.catalog_rows_for_url("https://www.manulife.com.sg/"))

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

    def test_etiqa_product_parser_uses_meta_and_scoped_benefits(self):
        html = (FIXTURES_DIR / "etiqa_product.html").read_text()
        row = etiqa.parse_product_html(
            html,
            "https://www.etiqa.com.sg/personal/travel-insurance/",
        )

        self.assertEqual(row["plan_name"], "Travel Insurance")
        self.assertIn("flight cancellations", row["plan_description"])
        self.assertIn("Trip cancellation benefit", " ".join(row["plan_benefits"]))
        self.assertEqual(
            row["product_brochure_url"],
            "https://www.etiqa.com.sg/wp-content/uploads/2024/02/travel-insurance-policy-wording.pdf",
        )
        self.assertEqual(
            [],
            validate_plan_rows(format_plan_rows(etiqa.TABLE_NAME, [row])),
        )

    def test_etiqa_rejects_home_and_claims_pages_as_plan_rows(self):
        html = (FIXTURES_DIR / "etiqa_reject.html").read_text()

        self.assertIsNone(etiqa.parse_product_html(html, "https://www.etiqa.com.sg/"))
        self.assertIsNone(
            etiqa.parse_product_html(
                html,
                "https://www.etiqa.com.sg/claims-and-services/",
            )
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

    def test_great_eastern_product_parser_scopes_out_navigation_chrome(self):
        html = (FIXTURES_DIR / "great_eastern_product.html").read_text()
        row = great_eastern.parse_product_html(
            html,
            "https://www.greateasternlife.com/sg/en/personal-insurance/our-products/car-insurance/great-ev-protect.html",
        )

        self.assertEqual(row["plan_name"], "GREAT EV Protect | Car Insurance")
        self.assertIn("electric vehicle insurance", row["plan_description"])
        self.assertNotIn("Life and health", row["plan_overview"])
        self.assertNotIn("How can we help", row["plan_overview"])
        self.assertEqual(
            row["product_brochure_url"],
            "https://www.greateasternlife.com/content/dam/great-ev-protect-brochure.pdf",
        )
        self.assertEqual(
            [],
            validate_plan_rows(format_plan_rows(great_eastern.TABLE_NAME, [row])),
        )

    def test_great_eastern_rejects_listing_and_campaign_pages_as_plan_rows(self):
        html = (FIXTURES_DIR / "great_eastern_reject.html").read_text()

        self.assertIsNone(
            great_eastern.parse_product_html(
                html,
                "https://www.greateasternlife.com/sg/en/personal-insurance/our-products/car-insurance.html",
            )
        )
        self.assertIsNone(
            great_eastern.parse_product_html(
                html,
                "https://www.greateasternlife.com/sg/en/campaigns/great-legacy-programme.html",
            )
        )

    def test_great_eastern_discovery_filters_to_product_details(self):
        category_url = (
            "https://www.greateasternlife.com/sg/en/personal-insurance/our-products/"
            "car-insurance.html"
        )
        product_url = (
            "https://www.greateasternlife.com/sg/en/personal-insurance/our-products/"
            "car-insurance/great-ev-protect.html"
        )
        session = FakeSession(
            {
                category_url: (FIXTURES_DIR / "great_eastern_reject.html").read_text(),
                product_url: (FIXTURES_DIR / "great_eastern_product.html").read_text(),
            }
        )

        self.assertEqual(
            [product_url],
            great_eastern.discover_product_urls(
                session=session,
                category_urls=[category_url],
                direct_product_urls=[],
            ),
        )
        rows = great_eastern.scrape_great_eastern(
            session=session,
            category_urls=[category_url],
            direct_product_urls=[],
        )
        self.assertEqual(["GREAT EV Protect | Car Insurance"], [row["plan_name"] for row in rows])

    def test_singlife_card_parser_sanitizes_category_banner_text(self):
        html = (FIXTURES_DIR / "singlife_category.html").read_text()
        rows = singlife.parse_source_html(
            html, "https://singlife.com/en/critical-illness-insurance"
        )

        self.assertEqual(
            ["Singlife Multipay Critical Illness II"], [row["plan_name"] for row in rows]
        )
        self.assertEqual("Critical Illness Insurance", rows[0]["plan_description"])
        self.assertNotIn("Speak to us", rows[0]["plan_description"])
        self.assertIn("multiple-payout plan", rows[0]["plan_overview"])
        self.assertEqual(
            rows[0]["product_brochure_url"],
            "https://singlife.com/content/dam/public/sg/documents/critical-illness-insurance/singlife-multipay-critical-illness-ii/brochure.pdf",
        )
        self.assertEqual([], validate_plan_rows(format_plan_rows(singlife.TABLE_NAME, rows)))

    def test_singlife_direct_product_parser_extracts_single_plan(self):
        html = (FIXTURES_DIR / "singlife_direct.html").read_text()
        rows = singlife.parse_source_html(html, "https://singlife.com/en/flexi-retirement-ii")

        self.assertEqual(
            ["Singlife Flexi Retirement II: Retirement Income & Savings Plan"],
            [row["plan_name"] for row in rows],
        )
        self.assertIn("flexible annuity plan", rows[0]["plan_description"])
        self.assertNotIn("Enjoy these special savings", rows[0]["plan_overview"])
        self.assertEqual(
            rows[0]["product_brochure_url"],
            "https://singlife.com/content/dam/public/sg/documents/retirement/singlife-flexi-retirement-ii/brochure.pdf",
        )
        self.assertEqual([], validate_plan_rows(format_plan_rows(singlife.TABLE_NAME, rows)))

    def test_singlife_rejects_non_plan_source_pages(self):
        html = (FIXTURES_DIR / "singlife_reject.html").read_text()

        self.assertEqual(
            [], singlife.parse_source_html(html, "https://singlife.com/en/grow-with-singlife")
        )

    def test_sunlife_product_parser_compacts_accordion_noise(self):
        html = (FIXTURES_DIR / "sunlife_product.html").read_text()
        row = sunlife.parse_product_html(
            html,
            "https://www.sunlife.com.sg/en/product-solutions/life-insurance/",
        )

        self.assertEqual(row["plan_name"], "SunBrilliance Whole Life")
        self.assertIn("lifetime protection", row["plan_description"])
        self.assertNotIn("Get more bright ideas", row["plan_overview"])
        self.assertLess(len(row["plan_overview"]), 500)
        self.assertEqual(
            row["product_brochure_url"],
            "https://www.sunlife.com.sg/content/dam/sbwholelife-productbrochure-en-feb2025.pdf",
        )
        self.assertEqual([], validate_plan_rows(format_plan_rows(sunlife.TABLE_NAME, [row])))

    def test_sunlife_rejects_homepage_as_plan_row(self):
        html = (FIXTURES_DIR / "sunlife_reject.html").read_text()

        self.assertIsNone(sunlife.parse_product_html(html, "https://www.sunlife.com.sg/en/"))

    def test_tokio_marine_product_parser_compacts_long_sections(self):
        html = (FIXTURES_DIR / "tokio_marine_product.html").read_text()
        row = tokio_marine.parse_product_html(
            html,
            "https://www.tokiomarine.com/sg/en/non-life/products/personal/accident/TM-365.html",
        )

        self.assertEqual(row["plan_name"], "TM365")
        self.assertEqual(row["plan_description"], "Comforting news for your family.")
        self.assertLessEqual(len(row["plan_overview"]), 900)
        self.assertIn("Accidental death", row["plan_overview"])
        self.assertEqual(
            row["product_brochure_url"],
            "https://www.tokiomarine.com/content/dam/tm365.pdf",
        )
        self.assertEqual([], validate_plan_rows(format_plan_rows(tokio_marine.TABLE_NAME, [row])))

    def test_tokio_marine_parser_rejects_empty_non_product_source(self):
        html = (FIXTURES_DIR / "tokio_marine_reject.html").read_text()

        self.assertIsNone(
            tokio_marine.parse_product_html(
                html,
                "https://www.tokiomarine.com/sg/en/life/claim/submit-a-claim.html",
            )
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

    def test_sompo_product_parser_scopes_to_product_body(self):
        html = (FIXTURES_DIR / "sompo_product.html").read_text()
        row = sompo.parse_product_html(
            html,
            "https://www.sompo.com.sg/products/travel",
        )

        self.assertEqual(row["plan_name"], "Travel Insurance")
        self.assertIn("trip cancellation", row["plan_description"])
        self.assertIn("Overseas Medical Expenses", row["plan_benefits"])
        self.assertNotIn("Submit A Claim", row["plan_overview"])
        self.assertEqual(
            row["product_brochure_url"],
            "https://www.sompo.com.sg/docs/default-source/products-downloads/products/travel/travel_brochure.pdf",
        )
        self.assertEqual([], validate_plan_rows(format_plan_rows(sompo.TABLE_NAME, [row])))

    def test_sompo_rejects_home_claims_and_404_pages(self):
        html = (FIXTURES_DIR / "sompo_reject.html").read_text()

        self.assertIsNone(sompo.parse_product_html(html, "https://www.sompo.com.sg/"))
        self.assertIsNone(
            sompo.parse_product_html(html, "https://www.sompo.com.sg/claims/claims-list")
        )
        self.assertIsNone(
            sompo.parse_product_html(
                html,
                "https://www.sompo.com.sg/commercial-insurance-products/sme",
            )
        )

    def test_sompo_scraper_filters_configured_404_source(self):
        html = (FIXTURES_DIR / "sompo_product.html").read_text()
        reject_html = (FIXTURES_DIR / "sompo_reject.html").read_text()
        source_url = "https://www.sompo.com.sg/products/travel"
        rejected_url = "https://www.sompo.com.sg/commercial-insurance-products/sme"
        session = FakeSession({source_url: html, rejected_url: reject_html})

        rows = sompo.scrape_sompo(session=session, product_urls=[source_url, rejected_url])

        self.assertEqual(["Travel Insurance"], [row["plan_name"] for row in rows])
        self.assertEqual([], validate_plan_rows(format_plan_rows(sompo.TABLE_NAME, rows)))


if __name__ == "__main__":
    unittest.main()
