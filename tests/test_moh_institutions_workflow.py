import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATIC_APP_DATA = (ROOT / "src/lib/static_app_data.py").read_text()


class MOHInstitutionWorkflowTests(unittest.TestCase):
    def test_weekly_scrape_ingests_moh_registry_before_brochure_parsing(self):
        ingest_index = STATIC_APP_DATA.index("src.scrapers.moh_institutions")
        parse_index = STATIC_APP_DATA.index("src.scrapers.brochure_facts")

        self.assertLess(ingest_index, parse_index)
        self.assertNotIn("SUPABASE", STATIC_APP_DATA)


if __name__ == "__main__":
    unittest.main()
