import unittest

from src.scrapers import chubb, iii, panel_resources, uoi


class FakeStreamingResponse:
    def __init__(self, chunks):
        self.chunks = chunks

    def iter_content(self, chunk_size):
        return iter(self.chunks)


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


if __name__ == "__main__":
    unittest.main()
