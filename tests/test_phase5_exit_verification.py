import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text()
PHASE5 = (ROOT / "docs/PHASE5_EXIT_VERIFICATION.md").read_text()


class Phase5ExitVerificationTests(unittest.TestCase):
    def test_readme_links_phase5_exit_record(self):
        self.assertIn("[Phase 5 exit verification](./docs/PHASE5_EXIT_VERIFICATION.md)", README)

    def test_phase5_exit_is_explicitly_blocked(self):
        for required in (
            "Phase 5 exit is blocked.",
            "Do not publicly launch yet.",
            "Production deployment is restored",
            "Phase 5 P0 blockers remain",
            "launch exit criteria are not met",
        ):
            with self.subTest(required=required):
                self.assertIn(required, PHASE5)

    def test_live_url_and_indexing_failures_are_recorded(self):
        for required in (
            "https://be-sure-ance.netlify.app",
            "https://besureance.netlify.app",
            "returned HTTP 404",
            "returned HTTP 200",
            "on 2026-07-07",
            "scripts/staging_preflight.py",
            "overall_status=passed",
            "overall_status=failed",
            "scripts/search_indexing_preflight.py",
            "subjectOf",
            "Live JS bundle check",
            "SERVICE_ROLE",
        ):
            with self.subTest(required=required):
                self.assertIn(required, PHASE5)

    def test_open_issue_blockers_are_recorded(self):
        for required in (
            "#73",
            "sitemap submission is not complete",
            "compliance",
            "metrics",
            "IFA trial",
            "Closed Phase 5 prep",
            "#74",
            "outreach drafts are complete and issue-closed",
            "no outreach should be posted",
        ):
            with self.subTest(required=required):
                self.assertIn(required, PHASE5)

    def test_acceptance_requirements_to_pass_are_recorded(self):
        for required in (
            "Submit sitemap in Google Search Console and Bing Webmaster Tools",
            "compliance lawyer outcome",
            "usage metrics",
            "at least one IFA",
            "first post-launch operations review issue",
        ):
            with self.subTest(required=required):
                self.assertIn(required, PHASE5)


if __name__ == "__main__":
    unittest.main()
