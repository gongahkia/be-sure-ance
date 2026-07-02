import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATION_SQL = (ROOT / "src/lib/migrations/0008_carrier_canonical_names.sql").read_text()
CREATE_SQL = (ROOT / "src/lib/create.sql").read_text()
STATIC_APP_DATA = (ROOT / "src/lib/static_app_data.py").read_text()


class CarrierCanonicalizationSchemaTests(unittest.TestCase):
    def test_schema_exists_in_create_and_migration(self):
        for sql in (MIGRATION_SQL, CREATE_SQL):
            with self.subTest(sql=sql[:20]):
                self.assertIn("carrier_canonical_names", sql)
                self.assertIn("carrier_key TEXT NOT NULL", sql)
                self.assertIn("canonical_name TEXT NOT NULL", sql)
                self.assertIn("mas_match_status TEXT NOT NULL", sql)
                self.assertIn("lia_match_status TEXT NOT NULL", sql)
                self.assertIn("mismatch_flags TEXT[] NOT NULL DEFAULT '{}'", sql)

    def test_schema_is_public_read_service_role_write(self):
        for required in (
            "ALTER TABLE public.carrier_canonical_names ENABLE ROW LEVEL SECURITY",
            "ON public.carrier_canonical_names FOR SELECT",
            "REVOKE ALL ON TABLE public.carrier_canonical_names FROM anon, authenticated",
            "GRANT SELECT ON TABLE public.carrier_canonical_names TO anon, authenticated",
            "GRANT ALL ON TABLE public.carrier_canonical_names TO service_role",
        ):
            with self.subTest(required=required):
                self.assertIn(required, MIGRATION_SQL)

    def test_workflow_refreshes_carrier_canonicalization(self):
        self.assertIn("src.scrapers.carrier_canonicalization", STATIC_APP_DATA)


if __name__ == "__main__":
    unittest.main()
