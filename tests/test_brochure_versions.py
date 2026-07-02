import hashlib
import unittest

from src.lib.brochure_versions import (
    build_change_alert,
    build_version_row,
    sha256_text,
    version_change_status,
)


class BrochureVersionTests(unittest.TestCase):
    def test_version_change_status_detects_new_same_and_changed_hashes(self):
        self.assertEqual(version_change_status(None, "abc"), "new")
        self.assertEqual(version_change_status({"sha256": "abc"}, "abc"), "unchanged")
        self.assertEqual(version_change_status({"sha256": "abc"}, "def"), "changed")

    def test_build_version_row_preserves_source_metadata_and_text_hash(self):
        row = build_version_row(
            insurer="aia",
            plan={"plan_slug": "sample-plan", "plan_name": "Sample Plan"},
            metadata={
                "url": "https://example.com/sample.pdf",
                "sha256": "content-hash",
                "storage_bucket": "plan-brochures",
                "storage_key": "brochures/aia/sample-plan/content-hash.pdf",
                "size_bytes": 99,
                "content_type": "application/pdf",
                "last_modified_at": "Wed, 01 Jul 2026 00:00:00 GMT",
            },
            captured_at="2026-07-02T00:00:00Z",
            extracted_text="Sample text",
        )

        self.assertEqual(row["insurer"], "aia")
        self.assertEqual(row["source_url"], "https://example.com/sample.pdf")
        self.assertEqual(row["captured_at"], "2026-07-02T00:00:00Z")
        self.assertEqual(row["first_seen_at"], "2026-07-02T00:00:00Z")
        self.assertEqual(row["last_seen_at"], "2026-07-02T00:00:00Z")
        self.assertEqual(row["text_sha256"], hashlib.sha256(b"Sample text").hexdigest())

    def test_build_change_alert_includes_source_timestamps_and_redlines(self):
        previous = {
            "insurer": "aia",
            "plan_slug": "sample-plan",
            "plan_name": "Sample Plan",
            "source_url": "https://example.com/sample.pdf",
            "sha256": "old-hash",
            "captured_at": "2026-07-01T00:00:00Z",
            "size_bytes": 100,
            "extracted_text": "Benefit limit: 100",
        }
        current = {
            "insurer": "aia",
            "plan_slug": "sample-plan",
            "plan_name": "Sample Plan",
            "source_url": "https://example.com/sample.pdf",
            "sha256": "new-hash",
            "captured_at": "2026-07-02T00:00:00Z",
            "size_bytes": 120,
            "extracted_text": "Benefit limit: 120",
        }

        alert = build_change_alert(previous, current, detected_at="2026-07-02T00:00:00Z")

        self.assertEqual(alert["source_url"], "https://example.com/sample.pdf")
        self.assertEqual(alert["previous_sha256"], "old-hash")
        self.assertEqual(alert["current_sha256"], "new-hash")
        self.assertEqual(alert["previous_captured_at"], "2026-07-01T00:00:00Z")
        self.assertEqual(alert["current_captured_at"], "2026-07-02T00:00:00Z")
        self.assertEqual(alert["change_detected_at"], "2026-07-02T00:00:00Z")
        self.assertEqual(alert["alert_status"], "pending")
        self.assertIn("-Benefit limit: 100", alert["text_diff"])
        self.assertIn("+Benefit limit: 120", alert["text_diff"])
        self.assertIn("<table", alert["html_diff"])
        self.assertIn("2 diff lines generated", alert["summary"])

    def test_sha256_text_is_stable(self):
        self.assertEqual(sha256_text("x"), hashlib.sha256(b"x").hexdigest())


if __name__ == "__main__":
    unittest.main()
