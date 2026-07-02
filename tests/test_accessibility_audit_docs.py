import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text()
ACCESSIBILITY_DOC = (ROOT / "docs/ACCESSIBILITY.md").read_text()
APP_VUE = (ROOT / "src/be-sure-ance-app/src/App.vue").read_text()
STATUS_DASHBOARD = (
    ROOT / "src/be-sure-ance-app/src/components/ScraperStatusDashboard.vue"
).read_text()
ARTIFACT_DIR = ROOT / "output/playwright/accessibility"


class AccessibilityAuditDocsTests(unittest.TestCase):
    def test_readme_links_accessibility_evidence(self):
        for required in (
            "WCAG 2.1 AA audit",
            "0 Axe violations / Lighthouse 100",
            "[docs/ACCESSIBILITY.md](./docs/ACCESSIBILITY.md)",
        ):
            with self.subTest(required=required):
                self.assertIn(required, README)

    def test_accessibility_doc_records_scope_scores_and_exceptions(self):
        for required in (
            "Target standard: WCAG 2.1 AA.",
            "`/matrix/panel-hospitals` | 0 | 100",
            "`/status` | 0 | 100",
            "Manual screen-reader testing is still required",
            "No automated WCAG 2.1 A/AA violations remain",
        ):
            with self.subTest(required=required):
                self.assertIn(required, ACCESSIBILITY_DOC)

    def test_landmark_and_scroll_region_fixes_are_present(self):
        for required in (
            "<main v-else-if=\"activeView === 'panelMatrix'\"",
            "<main v-else-if=\"activeView === 'scraperStatus'\"",
            'tabindex="0"',
            'aria-label="Carrier scraper health table"',
            ".status-table-wrap:focus",
        ):
            with self.subTest(required=required):
                self.assertIn(required, APP_VUE + STATUS_DASHBOARD)

    def test_lighthouse_artifacts_record_100_accessibility(self):
        for name in (
            "lighthouse-workspace.json",
            "lighthouse-matrix.json",
            "lighthouse-status.json",
            "lighthouse-share.json",
        ):
            with self.subTest(name=name):
                payload = json.loads((ARTIFACT_DIR / name).read_text())
                self.assertEqual(payload["categories"]["accessibility"]["score"], 1)

    def test_axe_after_artifact_records_zero_violations(self):
        payload = json.loads((ARTIFACT_DIR / "axe-results-after.json").read_text())
        self.assertEqual(sum(len(result["violations"]) for result in payload), 0)


if __name__ == "__main__":
    unittest.main()
