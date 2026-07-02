import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_SQL = (ROOT / "src/lib/create.sql").read_text()
MIGRATION_SQL = (ROOT / "src/lib/migrations/0001_unify_plans.sql").read_text()


class PlansMigrationTests(unittest.TestCase):
    def test_fresh_schema_creates_unified_plans_table(self):
        for required in (
            "CREATE TABLE IF NOT EXISTS plans",
            "insurer TEXT NOT NULL",
            "plan_name TEXT NOT NULL",
            "plan_slug TEXT NOT NULL",
            "plan_benefits TEXT[] NOT NULL DEFAULT '{}'",
            "plan_description TEXT",
            "plan_overview TEXT",
            "plan_url TEXT",
            "product_brochure_url TEXT",
            "scraped_at TIMESTAMPTZ NOT NULL DEFAULT now()",
            "UNIQUE (insurer, plan_slug)",
            "ON plans (insurer, plan_slug)",
        ):
            with self.subTest(required=required):
                self.assertIn(required, SCHEMA_SQL)

    def test_migration_preserves_insurer_identity(self):
        for required in (
            "INSERT INTO public.plans",
            "%L::TEXT AS insurer",
            "FROM public.%I",
            "ON CONFLICT (insurer, plan_slug) DO UPDATE SET",
        ):
            with self.subTest(required=required):
                self.assertIn(required, MIGRATION_SQL)

    def test_migration_generates_stable_deduped_slugs(self):
        for required in (
            "regexp_replace(plan_name, '[^a-zA-Z0-9]+', '-', 'g')",
            "row_number() OVER",
            "PARTITION BY insurer, base_slug",
            "ELSE base_slug || '-' || duplicate_index",
        ):
            with self.subTest(required=required):
                self.assertIn(required, MIGRATION_SQL)

    def test_old_tables_are_left_for_migration_window(self):
        self.assertIn("left in place for one migration window", MIGRATION_SQL)
        self.assertNotIn("DROP TABLE", MIGRATION_SQL.upper())


if __name__ == "__main__":
    unittest.main()
