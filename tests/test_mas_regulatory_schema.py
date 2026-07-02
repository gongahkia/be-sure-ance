import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CREATE_SQL = (ROOT / "src/lib/create.sql").read_text()
MIGRATION_SQL = (ROOT / "src/lib/migrations/0005_mas_regulatory_events.sql").read_text()
RLS_SQL = (ROOT / "src/lib/migrations/0000_enforce_readonly_rls.sql").read_text()
WORKFLOW = (ROOT / ".github/workflows/scrape-to-supabase.yml").read_text()
COMPLIANCE = (ROOT / "docs/COMPLIANCE.md").read_text()


class MasRegulatorySchemaTests(unittest.TestCase):
    def test_schema_adds_source_linked_mas_regulatory_events(self):
        combined = CREATE_SQL + MIGRATION_SQL
        for required in (
            "CREATE TABLE IF NOT EXISTS mas_regulatory_events",
            "event_date DATE NOT NULL",
            "source_url TEXT NOT NULL",
            "match_confidence NUMERIC NOT NULL",
            "match_status TEXT NOT NULL CHECK (match_status IN ('matched', 'needs_review'))",
            "UNIQUE (carrier_key, event_title, source_url)",
        ):
            with self.subTest(required=required):
                self.assertIn(required, combined)

    def test_public_access_is_read_only(self):
        combined = CREATE_SQL + MIGRATION_SQL + RLS_SQL
        for required in (
            "ALTER TABLE mas_regulatory_events ENABLE ROW LEVEL SECURITY",
            "GRANT SELECT ON TABLE mas_regulatory_events TO anon, authenticated",
            "GRANT ALL ON TABLE mas_regulatory_events TO service_role",
            "'mas_regulatory_events'",
        ):
            with self.subTest(required=required):
                self.assertIn(required, combined)

    def test_workflow_and_compliance_docs_cover_mas_regulatory_events(self):
        self.assertIn("python -m src.scrapers.mas_regulatory", WORKFLOW)
        self.assertIn("MAS regulatory-event rows are source-linked and dated", COMPLIANCE)
        self.assertIn("review-needed context", COMPLIANCE)


if __name__ == "__main__":
    unittest.main()
