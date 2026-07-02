import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text()
DATA_MODEL = (ROOT / "docs/DATA_MODEL.md").read_text()
SUCCESSION = (ROOT / "docs/SUCCESSION.md").read_text()
BLOG_DRAFT = (ROOT / "docs/blog/why-we-ripped-out-regex-derived-premiums.md").read_text()
CASE_STUDY = (ROOT / "docs/case-studies/README.md").read_text()
TALKS = (ROOT / "docs/talks/README.md").read_text()


class StorytellingArtifactsTests(unittest.TestCase):
    def test_readme_links_portfolio_artifacts(self):
        for required in (
            "[Succession runbook](./docs/SUCCESSION.md)",
            "[Pivot blog draft](./docs/blog/why-we-ripped-out-regex-derived-premiums.md)",
            "[Case study template](./docs/case-studies/)",
            "[Talk proposal](./docs/talks/)",
        ):
            with self.subTest(required=required):
                self.assertIn(required, README)

    def test_blog_draft_explains_pivot_and_limits(self):
        for required in (
            "Status: draft, unpublished.",
            "regex-derived premium",
            "False precision",
            "compareFIRST remains the reference point",
            "No public relaunch should happen before Phase 5",
        ):
            with self.subTest(required=required):
                self.assertIn(required, BLOG_DRAFT)

    def test_succession_doc_lists_locations_without_secret_values(self):
        for required in (
            "Credential Inventory Locations",
            "Do not store actual secrets in this document.",
            "GitHub Actions: repository or organisation secrets.",
            "Incident Shutdown",
            "Handover Checklist",
        ):
            with self.subTest(required=required):
                self.assertIn(required, SUCCESSION)

    def test_case_study_and_talk_placeholders_are_honest(self):
        for required in (
            "Do not invent testimonials.",
            "No-PII confirmation",
            "Scraping 28 SG insurer sites without lying to anyone",
            "Slides not created yet.",
        ):
            with self.subTest(required=required):
                self.assertIn(required, CASE_STUDY + TALKS)

    def test_data_model_includes_scraper_health_limitations(self):
        for required in (
            "`scraper_health` powers the public `/status` page.",
            "raw error text belongs in private logs or Sentry",
            "`row_count` only proves a scraper wrote rows",
            "does not prove the source content is semantically correct",
        ):
            with self.subTest(required=required):
                self.assertIn(required, DATA_MODEL)

    def test_docs_do_not_contain_committed_secret_values(self):
        combined = "\n".join((README, SUCCESSION, BLOG_DRAFT, CASE_STUDY, TALKS, DATA_MODEL))
        forbidden_patterns = (
            r"sb_secret_[A-Za-z0-9_-]+",
            r"SUPABASE_SERVICE_ROLE_KEY=\\S+",
            r"TELEGRAM_BOT_TOKEN=\\S+",
            r"SENTRY_DSN=https://",
        )
        for pattern in forbidden_patterns:
            with self.subTest(pattern=pattern):
                self.assertIsNone(re.search(pattern, combined))


if __name__ == "__main__":
    unittest.main()
