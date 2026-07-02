import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_SQL = (ROOT / "src/lib/create.sql").read_text()
MIGRATION_SQL = (ROOT / "src/lib/migrations/0003_moh_institutions.sql").read_text()


class MOHInstitutionSchemaTests(unittest.TestCase):
    def test_moh_institutions_schema_exists_in_create_and_migration(self):
        for sql in (SCHEMA_SQL, MIGRATION_SQL):
            with self.subTest(sql=sql[:24]):
                self.assertIn("CREATE TABLE IF NOT EXISTS", sql)
                self.assertIn("moh_institutions", sql)
                self.assertIn("canonical_id TEXT NOT NULL", sql)
                self.assertIn("aliases TEXT[] NOT NULL DEFAULT '{}'", sql)
                self.assertIn("source_dataset_id TEXT NOT NULL", sql)
                self.assertIn("source_record_id TEXT NOT NULL", sql)

    def test_moh_institutions_are_read_only_public(self):
        self.assertIn(
            "ALTER TABLE public.moh_institutions ENABLE ROW LEVEL SECURITY", MIGRATION_SQL
        )
        self.assertIn("ON public.moh_institutions FOR SELECT", MIGRATION_SQL)
        self.assertIn(
            "REVOKE ALL ON TABLE public.moh_institutions FROM anon, authenticated",
            MIGRATION_SQL,
        )
        self.assertIn(
            "GRANT SELECT ON TABLE public.moh_institutions TO anon, authenticated",
            MIGRATION_SQL,
        )
        self.assertIn("GRANT ALL ON TABLE public.moh_institutions TO service_role", MIGRATION_SQL)


if __name__ == "__main__":
    unittest.main()
