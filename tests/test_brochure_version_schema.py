import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CREATE_SQL = (ROOT / "src/lib/create.sql").read_text()
MIGRATION_SQL = (ROOT / "src/lib/migrations/0006_brochure_version_history.sql").read_text()
RLS_SQL = (ROOT / "src/lib/migrations/0000_enforce_readonly_rls.sql").read_text()
DATA_MODEL = (ROOT / "docs/DATA_MODEL.md").read_text()
COMPLIANCE = (ROOT / "docs/COMPLIANCE.md").read_text()


class BrochureVersionSchemaTests(unittest.TestCase):
    def test_schema_adds_brochure_version_history(self):
        combined = CREATE_SQL + MIGRATION_SQL
        for required in (
            "CREATE TABLE IF NOT EXISTS brochure_version_history",
            "sha256 TEXT NOT NULL",
            "source_last_modified_at TEXT",
            "first_seen_at TIMESTAMPTZ NOT NULL",
            "last_seen_at TIMESTAMPTZ NOT NULL",
            "captured_at TIMESTAMPTZ NOT NULL",
            "extracted_text TEXT",
            "text_sha256 TEXT",
            "UNIQUE (insurer, plan_slug, source_url, sha256)",
        ):
            with self.subTest(required=required):
                self.assertIn(required, combined)

    def test_schema_adds_deduped_brochure_change_alerts(self):
        combined = CREATE_SQL + MIGRATION_SQL
        for required in (
            "CREATE TABLE IF NOT EXISTS brochure_change_alerts",
            "previous_sha256 TEXT NOT NULL",
            "current_sha256 TEXT NOT NULL",
            "previous_captured_at TIMESTAMPTZ",
            "current_captured_at TIMESTAMPTZ NOT NULL",
            "change_detected_at TIMESTAMPTZ NOT NULL",
            "alert_status TEXT NOT NULL CHECK (alert_status IN ('pending', 'sent', 'suppressed'))",
            "text_diff TEXT",
            "html_diff TEXT",
            "UNIQUE (insurer, plan_slug, source_url, previous_sha256, current_sha256)",
        ):
            with self.subTest(required=required):
                self.assertIn(required, combined)

    def test_public_access_is_read_only(self):
        combined = CREATE_SQL + MIGRATION_SQL + RLS_SQL
        for table in ("brochure_version_history", "brochure_change_alerts"):
            with self.subTest(table=table):
                self.assertIn(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY", combined)
                self.assertIn(f"GRANT SELECT ON TABLE {table} TO anon, authenticated", combined)
                self.assertIn(f"GRANT ALL ON TABLE {table} TO service_role", combined)
                self.assertIn(f"'{table}'", combined)

    def test_docs_cover_alert_hooks_and_no_pii(self):
        self.assertIn("email or Telegram dispatch hooks", DATA_MODEL)
        self.assertIn("No subscriber, client, or agent PII", DATA_MODEL)
        self.assertIn("Brochure change-alert rows", COMPLIANCE)


if __name__ == "__main__":
    unittest.main()
