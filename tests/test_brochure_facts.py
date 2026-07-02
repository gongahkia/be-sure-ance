import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import src.backend.helper as helper
from src.scrapers.brochure_facts import (
    build_fact_rows,
    extract_pdf_text_from_bytes,
    main,
    parse_brochure_text,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_TEXT = (ROOT / "tests/fixtures/sample_brochure.txt").read_text()


def minimal_pdf_bytes(text: str) -> bytes:
    escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = f"BT /F1 12 Tf 72 720 Td ({escaped}) Tj ET"
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        f"<< /Length {len(stream.encode())} >>\nstream\n{stream}\nendstream".encode(),
    ]
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n".encode())
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")
    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode())
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode())
    pdf.extend(
        f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode()
    )
    return bytes(pdf)


class BrochureFactsTests(unittest.TestCase):
    def test_pypdf_extracts_text_from_fixture_pdf(self):
        text = extract_pdf_text_from_bytes(minimal_pdf_bytes(FIXTURE_TEXT))

        self.assertIn("Panel Hospitals", text)
        self.assertIn("Claims processed within 10 working days", text)

    def test_fixture_produces_expected_qualitative_plan_facts(self):
        parsed = parse_brochure_text(FIXTURE_TEXT)

        self.assertEqual(
            [item["name"] for item in parsed["panel_hospitals"]["items"]],
            ["Sample Hospital", "Example Medical Centre"],
        )
        self.assertEqual(parsed["waiting_periods"]["items"][0]["duration_days"], 90)
        self.assertEqual(parsed["waiting_periods"]["items"][0]["tags"], ["specified_condition"])
        self.assertEqual(parsed["claim_deadlines"]["items"][0]["deadline_days"], 30)
        self.assertEqual(parsed["claim_sla"]["value"]["duration_days"], 10)
        self.assertIn("Pre-existing conditions", parsed["exclusions"]["items"][0]["label"])
        self.assertEqual(parsed["exclusions"]["items"][0]["tags"], ["pre_existing_condition"])
        self.assertEqual(parsed["exclusions"]["items"][1]["tags"], ["self_inflicted_injury"])

    def test_taxonomy_marks_ambiguous_items_for_review(self):
        parsed = parse_brochure_text(
            "Exclusions: other policy exclusions. "
            "Waiting Period: 45 days waiting period for other benefits."
        )

        self.assertEqual(parsed["exclusions"]["items"][0]["taxonomy_status"], "needs_review")
        self.assertTrue(parsed["exclusions"]["items"][0]["review_required"])
        self.assertEqual(parsed["waiting_periods"]["items"][0]["taxonomy_status"], "needs_review")
        self.assertTrue(parsed["waiting_periods"]["items"][0]["review_required"])
        self.assertTrue(parsed["exclusions"]["review_required"])
        self.assertTrue(parsed["waiting_periods"]["review_required"])

    def test_built_fact_rows_include_provenance(self):
        rows = build_fact_rows(
            insurer="aia",
            plan_slug="sample-plan",
            source_url="https://example.com/sample.pdf",
            parsed_facts=parse_brochure_text(FIXTURE_TEXT),
            captured_at="2026-07-02T00:00:00Z",
        )

        self.assertEqual(
            {row["field_name"] for row in rows},
            {
                "panel_hospitals",
                "exclusions",
                "waiting_periods",
                "claim_deadlines",
                "claim_sla",
            },
        )
        for row in rows:
            with self.subTest(field=row["field_name"]):
                self.assertEqual(row["source_url"], "https://example.com/sample.pdf")
                self.assertEqual(row["source_type"], "brochure_pdf")
                self.assertEqual(row["scraped_at"], "2026-07-02T00:00:00Z")
                self.assertEqual(row["last_verified_at"], "2026-07-02T00:00:00Z")

    def test_parser_creates_no_dollar_projection_fields(self):
        rows = build_fact_rows(
            insurer="aia",
            plan_slug="sample-plan",
            source_url="https://example.com/sample.pdf",
            parsed_facts=parse_brochure_text(f"{FIXTURE_TEXT} Premium from S$500."),
            captured_at="2026-07-02T00:00:00Z",
        )

        serialized = str(rows).lower()
        self.assertNotIn("premium", serialized)
        self.assertNotIn("s$500", serialized)

    def test_dry_run_without_supabase_client_exits_cleanly(self):
        previous_client = helper.supabase
        helper.supabase = None
        output = io.StringIO()
        try:
            with patch.object(sys, "argv", ["brochure_facts.py", "--dry-run"]):
                with redirect_stdout(output):
                    main()
        finally:
            helper.supabase = previous_client

        self.assertIn('"plan_fact_count": 0', output.getvalue())


if __name__ == "__main__":
    unittest.main()
