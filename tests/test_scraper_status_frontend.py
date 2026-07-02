import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_VUE = (ROOT / "src/be-sure-ance-app/src/App.vue").read_text()
STATUS_DASHBOARD = (
    ROOT / "src/be-sure-ance-app/src/components/ScraperStatusDashboard.vue"
).read_text()
I18N = (ROOT / "src/be-sure-ance-app/src/i18n.js").read_text()
README = (ROOT / "README.md").read_text()
REDIRECTS = (ROOT / "src/be-sure-ance-app/public/_redirects").read_text()
SSG_SCRIPT = (ROOT / "src/be-sure-ance-app/scripts/generate-static-pages.mjs").read_text()
DEMO_DATA = (ROOT / "src/backend/demo_data.py").read_text()


class ScraperStatusFrontendTests(unittest.TestCase):
    def test_app_exposes_status_route_and_queries_health_table(self):
        for required in (
            'href="/status"',
            "activeView === 'scraperStatus'",
            "currentPath.value === '/status'",
            ".from('scraper_health')",
            "carrier_key,display_name,support_status,last_success_at,last_failure_at,last_run_at,row_count,validation_status,validation_checked_at,validation_summary,updated_at",
            '<ScraperStatusDashboard :health-rows="scraperHealth" :providers="providers" />',
        ):
            with self.subTest(required=required):
                self.assertIn(required, APP_VUE)

    def test_dashboard_surfaces_expected_public_states(self):
        for required in (
            "Fresh",
            "Stale",
            "Failing",
            "Unsupported",
            "validation_summary",
            "row_count",
            "last_success_at",
            "last_failure_at",
            "Raw failure",
        ):
            with self.subTest(required=required):
                if required == "Raw failure":
                    self.assertNotIn(required, STATUS_DASHBOARD)
                else:
                    self.assertIn(required, STATUS_DASHBOARD)

    def test_status_route_is_linked_and_static_hosted(self):
        for required in (
            "'/status'",
            "/status /index.html 200",
            "public scraper health dashboard is available at `/status`",
            "'route.status': 'Scraper status'",
            "'route.status': '爬取状态'",
        ):
            with self.subTest(required=required):
                self.assertIn(required, SSG_SCRIPT + REDIRECTS + README + I18N)

    def test_demo_data_includes_status_rows(self):
        for required in (
            '"scraper_health"',
            '"validation_status": "passed"',
            '"validation_status": "no_baseline"',
            '"validation_status": "unsupported"',
        ):
            with self.subTest(required=required):
                self.assertIn(required, DEMO_DATA)


if __name__ == "__main__":
    unittest.main()
