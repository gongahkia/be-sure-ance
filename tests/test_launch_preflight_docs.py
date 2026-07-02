import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text()
COMPLIANCE = (ROOT / "docs/COMPLIANCE.md").read_text()
RUNBOOK = (ROOT / "docs/LAUNCH_PREFLIGHT.md").read_text()
WORKFLOW = (ROOT / ".github/workflows/staging-preflight.yml").read_text()
NETLIFY = (ROOT / "netlify.toml").read_text()


class LaunchPreflightDocsTests(unittest.TestCase):
    def test_readme_and_compliance_link_launch_preflight(self):
        self.assertIn("[Launch pre-flight runbook](./docs/LAUNCH_PREFLIGHT.md)", README)
        self.assertIn("[launch pre-flight runbook](./LAUNCH_PREFLIGHT.md)", COMPLIANCE)

    def test_runbook_documents_smoke_load_security_and_compliance_status(self):
        for required in (
            "Compliance lawyer sign-off status: blocked - not obtained as of 2026-07-02.",
            "/matrix/panel-hospitals",
            "/status",
            "/share/11111111-2222-4333-8444-555555555555",
            "--load-requests 24",
            "Performance >= 90",
            "Accessibility >= 90",
            "execute_sql",
            "anon",
            "authenticated",
            "No public launch is approved",
        ):
            with self.subTest(required=required):
                self.assertIn(required, RUNBOOK)

    def test_workflow_runs_staging_preflight_and_lighthouse_gate(self):
        for required in (
            "name: staging-preflight",
            "STAGING_ORIGIN",
            "python scripts/staging_preflight.py",
            "--load-concurrency 3",
            "npx --yes lighthouse",
            "--only-categories=performance,accessibility,best-practices,seo",
            "python scripts/lighthouse_score_gate.py",
            "--minimum 0.9",
            "actions/upload-artifact@v4",
        ):
            with self.subTest(required=required):
                self.assertIn(required, WORKFLOW)

    def test_netlify_security_headers_support_security_gate(self):
        for required in (
            "Content-Security-Policy",
            "frame-ancestors 'none'",
            "X-Content-Type-Options",
            "nosniff",
            "Referrer-Policy",
            "Permissions-Policy",
            "Strict-Transport-Security",
        ):
            with self.subTest(required=required):
                self.assertIn(required, NETLIFY)


if __name__ == "__main__":
    unittest.main()
