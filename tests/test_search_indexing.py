import json
import tempfile
import unittest
from pathlib import Path

from scripts.search_indexing_preflight import run_preflight

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text()
RUNBOOK = (ROOT / "docs/SEARCH_INDEXING.md").read_text()
WORKFLOW = (ROOT / ".github/workflows/search-indexing-preflight.yml").read_text()


class SearchIndexingTests(unittest.TestCase):
    def test_runbook_records_submission_blocker_and_official_paths(self):
        for required in (
            "Current submission status as of 2026-07-07: pre-submission fix pending.",
            "https://besureance.netlify.app",
            "returns HTTP 200",
            "missing JSON-LD `subjectOf` source links",
            "Google Search Console",
            "Bing Webmaster Tools",
            "owner permissions",
            "Sitemap:",
            "Status Log",
            "Pending - not submitted",
        ):
            with self.subTest(required=required):
                self.assertIn(required, RUNBOOK)

    def test_readme_links_search_indexing_runbook(self):
        self.assertIn("[Search indexing runbook](./docs/SEARCH_INDEXING.md)", README)
        self.assertIn("Google submission, and Bing submission status", README)

    def test_workflow_runs_preflight_against_live_origin(self):
        for required in (
            "name: search-indexing-preflight",
            "LIVE_ORIGIN",
            "python3 scripts/search_indexing_preflight.py",
            "output/search-indexing/preflight.json",
            "actions/upload-artifact@v4",
        ):
            with self.subTest(required=required):
                self.assertIn(required, WORKFLOW)

    def test_preflight_validates_sitemap_robots_canonical_and_json_ld(self):
        origin = "https://example.com"
        with tempfile.TemporaryDirectory() as tmp:
            dist = Path(tmp)
            plan_dir = dist / "plan" / "aia" / "healthshield-gold-max-demo"
            plan_dir.mkdir(parents=True)
            (dist / "sitemap.xml").write_text(
                "\n".join(
                    (
                        '<?xml version="1.0" encoding="UTF-8"?>',
                        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
                        f"<url><loc>{origin}/</loc></url>",
                        f"<url><loc>{origin}/plan/aia/healthshield-gold-max-demo</loc></url>",
                        "</urlset>",
                    )
                )
            )
            (dist / "robots.txt").write_text(f"Sitemap: {origin}/sitemap.xml\n")
            json_ld = {
                "@context": "https://schema.org",
                "@type": "FinancialProduct",
                "url": f"{origin}/plan/aia/healthshield-gold-max-demo",
                "subjectOf": [{"@type": "CreativeWork", "url": "https://example.com/source"}],
            }
            (plan_dir / "index.html").write_text(
                "\n".join(
                    (
                        "<html><head>",
                        '<meta name="description" content="Demo plan" />',
                        f'<link rel="canonical" href="{origin}/plan/aia/healthshield-gold-max-demo" />',
                        f'<script type="application/ld+json">{json.dumps(json_ld)}</script>',
                        "</head><body></body></html>",
                    )
                )
            )

            report = run_preflight(origin, dist_dir=dist)

        self.assertEqual(report["overall_status"], "passed")
        self.assertEqual(report["sitemap"]["url_count"], 2)
        self.assertEqual(report["robots"]["status"], "passed")
        self.assertEqual(report["representative_plan_pages"][0]["status"], "passed")


if __name__ == "__main__":
    unittest.main()
