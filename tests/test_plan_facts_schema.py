import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_SQL = (ROOT / "src/lib/create.sql").read_text()
MIGRATION_SQL = (ROOT / "src/lib/migrations/0002_plan_facts.sql").read_text()
DATA_MODEL = (ROOT / "docs/DATA_MODEL.md").read_text()


class PlanFactsSchemaTests(unittest.TestCase):
    def test_fresh_schema_creates_source_traceable_plan_facts(self):
        for required in (
            "CREATE TABLE IF NOT EXISTS plan_facts",
            "insurer TEXT NOT NULL",
            "plan_slug TEXT NOT NULL",
            "field_name TEXT NOT NULL",
            "field_value JSONB NOT NULL",
            "source_url TEXT NOT NULL",
            "source_type TEXT NOT NULL CHECK",
            "scraped_at TIMESTAMPTZ NOT NULL DEFAULT now()",
            "last_verified_at TIMESTAMPTZ NOT NULL DEFAULT now()",
        ):
            with self.subTest(required=required):
                self.assertIn(required, SCHEMA_SQL)

    def test_migration_supports_required_source_types(self):
        for source_type in ("brochure_pdf", "product_page", "manual_entry"):
            with self.subTest(source_type=source_type):
                self.assertIn(source_type, MIGRATION_SQL)

    def test_plan_facts_have_deterministic_unique_upsert_key(self):
        for required in (
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_plan_facts_unique_fact",
            "ON public.plan_facts (insurer, plan_slug, field_name)",
            "ON CONFLICT (insurer, plan_slug, field_name) DO UPDATE SET",
        ):
            with self.subTest(required=required):
                self.assertIn(required, MIGRATION_SQL)

    def test_plan_facts_are_public_read_service_role_write(self):
        for required in (
            "ALTER TABLE public.plan_facts ENABLE ROW LEVEL SECURITY",
            'CREATE POLICY "public read access"',
            "ON public.plan_facts FOR SELECT",
            "TO anon, authenticated",
            "REVOKE ALL ON TABLE public.plan_facts FROM anon, authenticated",
            "GRANT SELECT ON TABLE public.plan_facts TO anon, authenticated",
            "GRANT ALL ON TABLE public.plan_facts TO service_role",
        ):
            with self.subTest(required=required):
                self.assertIn(required, MIGRATION_SQL)

    def test_data_model_documents_relation_and_source_contract(self):
        for required in (
            "`plans` is the plan catalog",
            "`plan_comparison_facts` is an interim UI summary table",
            "`plan_facts` is the canonical source-traceable fact table",
            "`brochure_pdf`",
            "`product_page`",
            "`manual_entry`",
            "ON CONFLICT (insurer, plan_slug, field_name) DO UPDATE SET",
        ):
            with self.subTest(required=required):
                self.assertIn(required, DATA_MODEL)


if __name__ == "__main__":
    unittest.main()
