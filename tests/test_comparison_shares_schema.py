import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CREATE_SQL = (ROOT / "src/lib/create.sql").read_text()
MIGRATION_SQL = (ROOT / "src/lib/migrations/0007_comparison_shares.sql").read_text()
RLS_SQL = (ROOT / "src/lib/migrations/0000_enforce_readonly_rls.sql").read_text()
DATA_MODEL = (ROOT / "docs/DATA_MODEL.md").read_text()
COMPLIANCE = (ROOT / "docs/COMPLIANCE.md").read_text()


class ComparisonSharesSchemaTests(unittest.TestCase):
    def test_schema_adds_uuid_comparison_shares(self):
        combined = CREATE_SQL + MIGRATION_SQL
        for required in (
            "CREATE EXTENSION IF NOT EXISTS pgcrypto",
            "CREATE TABLE IF NOT EXISTS comparison_shares",
            "id UUID PRIMARY KEY DEFAULT gen_random_uuid()",
            "selected_plans JSONB NOT NULL",
            "view_count INT NOT NULL DEFAULT 0 CHECK (view_count >= 0)",
            "last_viewed_at TIMESTAMPTZ",
            "jsonb_array_length(selected_plans) BETWEEN 1 AND 3",
        ):
            with self.subTest(required=required):
                self.assertIn(required, combined)

    def test_public_access_is_read_only(self):
        combined = CREATE_SQL + MIGRATION_SQL + RLS_SQL
        for required in (
            "ALTER TABLE comparison_shares ENABLE ROW LEVEL SECURITY",
            "GRANT SELECT ON TABLE comparison_shares TO anon, authenticated",
            "GRANT ALL ON TABLE comparison_shares TO service_role",
            "'comparison_shares'",
        ):
            with self.subTest(required=required):
                self.assertIn(required, combined)

    def test_docs_state_no_pii_share_refs_only(self):
        for required in (
            "`comparison_shares` stores UUID-addressed saved comparison sets",
            "only `insurer` and `plan_slug`",
            "non-identifying aggregate counter",
            "no client, agent, visitor, account, cookie, IP address, or user-agent data",
        ):
            with self.subTest(required=required):
                self.assertIn(required, DATA_MODEL + COMPLIANCE)


if __name__ == "__main__":
    unittest.main()
