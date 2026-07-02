import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CREATE_SQL = (ROOT / "src/lib/create.sql").read_text()
MIGRATION_SQL = (ROOT / "src/lib/migrations/0004_claim_turnaround_metrics.sql").read_text()
RLS_SQL = (ROOT / "src/lib/migrations/0000_enforce_readonly_rls.sql").read_text()
STATIC_APP_DATA = (ROOT / "src/lib/static_app_data.py").read_text()
DATA_MODEL = (ROOT / "docs/DATA_MODEL.md").read_text()


class ClaimTurnaroundSchemaTests(unittest.TestCase):
    def test_schema_adds_source_traceable_claim_turnaround_table(self):
        combined = CREATE_SQL + MIGRATION_SQL
        for required in (
            "CREATE TABLE IF NOT EXISTS claim_turnaround_metrics",
            "metric_value JSONB NOT NULL",
            "rank INT",
            "source_year INT NOT NULL",
            "source_url TEXT NOT NULL",
            "limitations TEXT[] NOT NULL DEFAULT '{}'",
            "UNIQUE (carrier_key, metric_key, source_year, source_url)",
        ):
            with self.subTest(required=required):
                self.assertIn(required, combined)

    def test_public_access_is_read_only(self):
        combined = CREATE_SQL + MIGRATION_SQL + RLS_SQL
        for required in (
            "ALTER TABLE claim_turnaround_metrics ENABLE ROW LEVEL SECURITY",
            'CREATE POLICY "public read access"',
            "GRANT SELECT ON TABLE claim_turnaround_metrics TO anon, authenticated",
            "GRANT ALL ON TABLE claim_turnaround_metrics TO service_role",
            "'claim_turnaround_metrics'",
        ):
            with self.subTest(required=required):
                self.assertIn(required, combined)

    def test_workflow_runs_lia_claim_metric_ingest(self):
        self.assertIn("src.scrapers.lia_claim_turnaround", STATIC_APP_DATA)

    def test_data_model_documents_lia_limits(self):
        for required in (
            "`claim_turnaround_metrics`",
            "source_year",
            "rank` is nullable",
            "does not publish carrier-level turnaround rankings",
        ):
            with self.subTest(required=required):
                self.assertIn(required, DATA_MODEL)


if __name__ == "__main__":
    unittest.main()
