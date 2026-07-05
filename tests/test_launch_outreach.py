import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text()
OUTREACH = (ROOT / "docs/OUTREACH.md").read_text()


class LaunchOutreachTests(unittest.TestCase):
    def test_readme_links_launch_outreach_drafts(self):
        self.assertIn("[Launch outreach drafts](./docs/OUTREACH.md)", README)

    def test_all_requested_drafts_exist(self):
        for required in (
            "Seedly Draft",
            "SG IFA Telegram/WhatsApp Draft",
            "Reddit Open Dataset Draft",
            "Show HN Draft",
            "MAS/OGP/GovTech Note Draft",
        ):
            with self.subTest(required=required):
                self.assertIn(required, OUTREACH)

    def test_drafts_include_no_advice_and_limitations(self):
        for required in (
            "not financial advice",
            "insurance advice",
            "no premium estimates or cost projections",
            "16 scheduled carriers",
            "not a complete carrier database",
            "not a substitute for compareFIRST",
            "source data can be stale or incomplete",
            "missing or unsupported facts instead of guessing",
        ):
            with self.subTest(required=required):
                self.assertIn(required, OUTREACH)

    def test_unsupported_claims_and_live_launch_are_blocked(self):
        for required in (
            "Do not claim all Singapore carriers are supported.",
            "Do not claim production analytics",
            "Do not post yet",
            "returns HTTP 404",
            "Compliance sign-off is not obtained.",
            "Google/Bing sitemap submission is not done.",
        ):
            with self.subTest(required=required):
                self.assertIn(required, OUTREACH)

    def test_feedback_channels_are_monitored(self):
        for required in (
            "GitHub Issues",
            "gabrielzmong@gmail.com",
            "docs/TAKEDOWN_RUNBOOK.md",
            "at least 7 calendar days",
        ):
            with self.subTest(required=required):
                self.assertIn(required, OUTREACH)

    def test_community_guidelines_sources_are_recorded(self):
        for required in (
            "seedlysg.zendesk.com",
            "reddit.com/r/reddit.com/wiki/selfpromotion",
            "news.ycombinator.com/showhn.html",
        ):
            with self.subTest(required=required):
                self.assertIn(required, OUTREACH)


if __name__ == "__main__":
    unittest.main()
