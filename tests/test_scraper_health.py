import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.lib.scraper_health import (
    record_validation_report,
    sanitized_error,
    summarize_validation_results,
)
from src.validation.differ import ValidationTarget, run_validation

ROOT = Path(__file__).resolve().parents[1]
CREATE_SQL = (ROOT / "src/lib/create.sql").read_text()
MIGRATION_SQL = (ROOT / "src/lib/migrations/0009_scraper_health.sql").read_text()
RLS_SQL = (ROOT / "src/lib/migrations/0000_enforce_readonly_rls.sql").read_text()
RUN_ALL = (ROOT / "src/scrapers/run_all.py").read_text()
HELPER = (ROOT / "src/backend/helper.py").read_text()
DIFFER = (ROOT / "src/validation/differ.py").read_text()
WORKFLOW = (ROOT / ".github/workflows/validate-scraper-snapshots.yml").read_text()


class ScraperHealthTests(unittest.TestCase):
    def test_schema_persists_public_read_scraper_health(self):
        combined = CREATE_SQL + MIGRATION_SQL + RLS_SQL
        for required in (
            "CREATE TABLE IF NOT EXISTS public.scraper_health",
            "carrier_key TEXT NOT NULL",
            "support_status TEXT NOT NULL",
            "last_success_at TIMESTAMPTZ",
            "last_failure_at TIMESTAMPTZ",
            "row_count INT NOT NULL DEFAULT 0",
            "validation_status TEXT NOT NULL DEFAULT 'not_run'",
            "validation_summary JSONB NOT NULL DEFAULT '{}'::jsonb",
            "GRANT SELECT ON TABLE public.scraper_health TO anon, authenticated",
            "GRANT ALL ON TABLE public.scraper_health TO service_role",
            "'scraper_health'",
        ):
            with self.subTest(required=required):
                self.assertIn(required, combined)

    def test_scraper_and_validation_paths_record_health(self):
        for required in (
            "record_scraper_success(insurer, len(formatted_rows))",
            "record_scraper_failure(",
            "sync_scraper_registry_statuses(dry_run=args.dry_run)",
            "record_validation_report(report)",
            "SUPABASE_SECRET_KEY",
        ):
            with self.subTest(required=required):
                self.assertIn(required, HELPER + RUN_ALL + DIFFER + WORKFLOW)

    def test_validation_summary_aggregates_statuses_without_raw_secret_leak(self):
        summary = summarize_validation_results(
            [
                {"status": "passed"},
                {"status": "failed", "failures": ["Bearer live_token"]},
                {"status": "no_baseline"},
            ]
        )

        self.assertEqual(summary["status"], "failed")
        self.assertEqual(summary["total_targets"], 3)
        self.assertEqual(summary["failed"], 1)
        self.assertIn("[redacted]", summary["notes"][0])

    def test_sanitized_error_redacts_common_secret_shapes(self):
        text = sanitized_error("bad sb_secret_abc Bearer token eyJaaa.bbb.ccc")

        self.assertNotIn("sb_secret_abc", text)
        self.assertNotIn("Bearer token", text)
        self.assertNotIn("eyJaaa.bbb.ccc", text)
        self.assertEqual(text.count("[redacted]"), 3)

    def test_run_validation_writes_report_and_calls_health_recorder(self):
        target = ValidationTarget(
            insurer="aia",
            url="https://example.com",
            domain="example.com",
            source_file="aia.py",
        )
        with tempfile.TemporaryDirectory() as output_tmp:
            output_dir = Path(output_tmp)
            with (
                patch("src.validation.differ.discover_targets", return_value=[target]),
                patch(
                    "src.validation.differ.fetch_html", return_value="<html><body>x</body></html>"
                ),
                patch("src.validation.differ.record_validation_report") as record,
            ):
                exit_code = run_validation(
                    output_dir=output_dir,
                    baseline_dir=None,
                    max_urls_per_insurer=1,
                    request_timeout=5,
                    max_path_drift=0.1,
                    max_tag_drift=0.1,
                )

            report = json.loads((output_dir / "report.json").read_text())
            self.assertEqual(exit_code, 0)
            self.assertEqual(report["summary"]["no_baseline"], 1)
            record.assert_called_once()

    def test_record_validation_report_upserts_summarized_rows(self):
        report = {
            "generated_at": "2026-07-02T00:00:00+00:00",
            "results": [
                {"insurer": "aia", "status": "passed"},
                {"insurer": "aia", "status": "error", "errors": ["sb_secret_bad"]},
            ],
        }
        with (
            patch("src.lib.scraper_health.sync_scraper_registry_statuses") as sync,
            patch("src.lib.scraper_health.upsert_health_rows") as upsert,
        ):
            record_validation_report(report)

        sync.assert_called_once()
        row = upsert.call_args.args[0][0]
        self.assertEqual(row["carrier_key"], "aia")
        self.assertEqual(row["validation_status"], "error")
        self.assertIn("[redacted]", row["validation_summary"]["notes"][0])


if __name__ == "__main__":
    unittest.main()
