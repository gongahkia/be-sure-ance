import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = (ROOT / ".github/workflows/scrape-to-supabase.yml").read_text()


class MOHInstitutionWorkflowTests(unittest.TestCase):
    def test_weekly_scrape_ingests_moh_registry_before_brochure_parsing(self):
        ingest_index = WORKFLOW.index("python -m src.scrapers.moh_institutions")
        parse_index = WORKFLOW.index("python -m src.scrapers.brochure_facts")

        self.assertLess(ingest_index, parse_index)
        self.assertIn("Ingest MOH institution registry", WORKFLOW)
        self.assertIn("SUPABASE_SERVICE_ROLE_KEY", WORKFLOW)


if __name__ == "__main__":
    unittest.main()
