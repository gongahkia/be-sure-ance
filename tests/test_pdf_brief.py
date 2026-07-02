import io
import unittest
from datetime import datetime, timezone

from pypdf import PdfReader

from src.backend.pdf_brief import (
    MAX_PLANS_PER_BRIEF,
    NO_ADVICE_DISCLAIMER,
    branding_footer_text,
    build_pdf_brief,
    build_pdf_brief_with_branding,
    validate_plan_selection,
)
from src.backend.pdf_brief_api import BriefRequest, create_client_brief


def sample_plan(name="AIA Health Shield", insurer="aia"):
    return {
        "insurer": insurer,
        "providerName": insurer.upper(),
        "plan_name": name,
        "facts": {
            "coverage_tags": {
                "field_value": {
                    "status": "known",
                    "items": ["hospitalization", "emergency"],
                    "raw_text": "Hospitalization and emergency",
                    "notes": [],
                },
                "source_url": "https://example.com/product",
                "source_type": "product_page",
                "scraped_at": "2026-07-02T00:00:00Z",
                "last_verified_at": "2026-07-02T00:00:00Z",
            },
            "panel_hospitals": {
                "field_value": {
                    "status": "known",
                    "items": [
                        {
                            "name": "Singapore Gen Hospital",
                            "normalized_name": "Singapore General Hospital",
                        }
                    ],
                    "raw_text": "Singapore Gen Hospital",
                    "notes": [],
                },
                "source_url": "https://example.com/brochure.pdf",
                "source_type": "brochure_pdf",
                "scraped_at": "2026-07-02T00:00:00Z",
                "last_verified_at": "2026-07-02T00:00:00Z",
            },
            "claim_sla": {
                "field_value": {
                    "status": "known",
                    "value": {"duration_days": 10, "basis": "published target"},
                    "raw_text": "Claims are processed within 10 working days",
                    "notes": [],
                },
                "source_url": "https://example.com/claims",
                "source_type": "product_page",
                "scraped_at": "2026-07-02T00:00:00Z",
                "last_verified_at": "2026-07-02T00:00:00Z",
            },
        },
    }


def extract_pdf_text(pdf_bytes):
    reader = PdfReader(io.BytesIO(pdf_bytes))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


class PdfBriefTests(unittest.TestCase):
    def test_pdf_brief_contains_qualitative_facts_sources_and_disclaimer(self):
        pdf = build_pdf_brief(
            [sample_plan()],
            generated_at=datetime(2026, 7, 2, tzinfo=timezone.utc),
        )
        text = extract_pdf_text(pdf)

        self.assertTrue(pdf.startswith(b"%PDF"))
        self.assertIn("Be-sure-ance Client Brief", text)
        self.assertIn("Generated at 2026-07-02T00:00:00+00:00", text)
        self.assertIn("AIA Health Shield", text)
        self.assertIn("Singapore General Hospital", text)
        self.assertIn("10 days (published target)", text)
        self.assertIn("https://example.com/brochure.pdf", text)
        self.assertIn(NO_ADVICE_DISCLAIMER[:60], text)

    def test_pdf_brief_rejects_more_than_three_plans(self):
        plans = [sample_plan(f"Plan {index}") for index in range(MAX_PLANS_PER_BRIEF + 1)]

        with self.assertRaises(ValueError):
            validate_plan_selection(plans)

    def test_pdf_brief_accepts_three_plans(self):
        plans = [sample_plan(f"Plan {index}") for index in range(MAX_PLANS_PER_BRIEF)]
        text = extract_pdf_text(build_pdf_brief(plans))

        for index in range(MAX_PLANS_PER_BRIEF):
            with self.subTest(index=index):
                self.assertIn(f"Plan {index}", text)

    def test_pdf_footer_includes_supplied_agent_branding(self):
        text = extract_pdf_text(
            build_pdf_brief_with_branding(
                [sample_plan()],
                branding={"agent_name": "Jamie Tan", "mas_rep_number": "A123456"},
            )
        )

        self.assertIn("Prepared by Jamie Tan | MAS rep no. A123456", text)

    def test_pdf_footer_falls_back_without_branding(self):
        self.assertEqual(
            branding_footer_text({}),
            "Prepared by unbranded adviser | MAS rep no. not provided",
        )

    def test_pdf_brief_rejects_empty_selection(self):
        with self.assertRaises(ValueError):
            validate_plan_selection([])

    def test_pdf_brief_omits_inferred_cost_and_ranking_language(self):
        text = extract_pdf_text(build_pdf_brief([sample_plan()]))

        for forbidden in ("Premium from", "S$", "Best plan", "Recommended plan"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, text)

    def test_fastapi_endpoint_returns_pdf_without_storage_headers(self):
        response = create_client_brief(
            BriefRequest(
                plans=[sample_plan()],
                branding={"agent_name": "Jamie Tan", "mas_rep_number": "A123456"},
            )
        )

        self.assertEqual(response.media_type, "application/pdf")
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        self.assertIn("attachment", response.headers["Content-Disposition"])
        self.assertTrue(response.body.startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()
