import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text()
DEPLOYMENT = (ROOT / "docs/DEPLOYMENT.md").read_text()
SUCCESSION = (ROOT / "docs/SUCCESSION.md").read_text()
LAUNCH_PREFLIGHT = (ROOT / "docs/LAUNCH_PREFLIGHT.md").read_text()
NETLIFY = (ROOT / "netlify.toml").read_text()


class DeploymentRunbookTests(unittest.TestCase):
    def test_readme_links_deployment_runbook_with_live_url_claim(self):
        self.assertIn("[Deployment runbook](./docs/DEPLOYMENT.md)", README)
        self.assertIn("Deployment decision: restored on Netlify", README)
        self.assertIn("https://besureance.netlify.app/", README)
        self.assertNotIn("Use the live website", README)

    def test_netlify_restore_decision_and_cloudflare_fallback_are_documented(self):
        for required in (
            "Restore Netlify first.",
            "Cloudflare Pages remains a fallback",
            "No DNS change or custom-domain change was performed",
            "README may claim `https://besureance.netlify.app/`",
            "Hosting provider: Netlify at `https://besureance.netlify.app/`",
        ):
            with self.subTest(required=required):
                self.assertIn(required, DEPLOYMENT + SUCCESSION)

    def test_frontend_env_allowlist_excludes_private_keys(self):
        for allowed in (
            "VITE_SITE_ORIGIN",
            "VITE_STATIC_DATA_PATH",
            "VITE_PDF_BRIEF_ENDPOINT",
            "optional `VITE_SENTRY_*`",
        ):
            with self.subTest(allowed=allowed):
                self.assertIn(allowed, DEPLOYMENT)

        for forbidden in (
            "TELEGRAM_BOT_TOKEN",
            "SENTRY_DSN",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertIn(forbidden, DEPLOYMENT)

    def test_netlify_config_supports_vite_spa_and_security_headers(self):
        for required in (
            'publish = "src/be-sure-ance-app/dist"',
            'functions = "netlify/functions"',
            'ignore = "bash ./scripts/netlify_ignore_data_refresh.sh"',
            'from = "/*"',
            'to = "/index.html"',
            "Content-Security-Policy",
            "Strict-Transport-Security",
        ):
            with self.subTest(required=required):
                self.assertIn(required, NETLIFY)

    def test_launch_prefight_depends_on_working_production_url(self):
        self.assertIn("deployment runbook has a working production URL", LAUNCH_PREFLIGHT)
        self.assertIn(
            "Update README with the live URL only after the production URL works.", DEPLOYMENT
        )

    def test_deployment_consumes_committed_static_data(self):
        self.assertIn("committed `src/be-sure-ance-app/public/data/app-data.json`", DEPLOYMENT)
        self.assertIn("Scheduled scraping runs in GitHub Actions", DEPLOYMENT)


if __name__ == "__main__":
    unittest.main()
