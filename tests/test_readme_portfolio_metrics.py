import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text()


class ReadmePortfolioMetricsTests(unittest.TestCase):
    def test_first_screen_frames_public_good_and_comparefirst_boundary(self):
        opening = README.split("## Usage", 1)[0]

        for required in (
            "public-good IFA pre-meeting research tool",
            "complements compareFIRST",
            "does not replace compareFIRST",
            "source-traceable qualitative metadata",
        ):
            with self.subTest(required=required):
                self.assertIn(required, opening)

    def test_metrics_stat_block_marks_unavailable_usage_metrics(self):
        for required in (
            "Supported scheduled carriers | 10",
            "30-day lookups | Unavailable",
            "Brochure alerts fired | Unavailable",
            "Plausible/Umami/privacy-safe analytics",
        ):
            with self.subTest(required=required):
                self.assertIn(required, README)

    def test_cost_transparency_uses_free_tier_language(self):
        for required in (
            "Cost posture: `$0/mo` target",
            "Supabase free tier",
            "Netlify or Cloudflare Pages free tier",
            "GitHub Actions free tier",
        ):
            with self.subTest(required=required):
                self.assertIn(required, README)


if __name__ == "__main__":
    unittest.main()
