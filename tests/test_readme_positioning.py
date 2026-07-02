import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text()


class ReadmePositioningTests(unittest.TestCase):
    def test_first_paragraph_states_comparefirst_complement(self):
        intro = README.split("## Usage", 1)[0]
        for required in (
            "IFA pre-meeting research tool",
            "compareFIRST",
            "regulated quantitative life-insurance comparison",
            "qualitative facts",
        ):
            with self.subTest(required=required):
                self.assertIn(required, intro)

    def test_readme_denies_advice_quotes_recommendations_and_cost_projections(self):
        required_sentence = (
            "The app does not provide financial advice, insurance advice, quotes, "
            "recommendations, suitability rankings, premium estimates, or cost projections."
        )
        self.assertIn(required_sentence, README)

    def test_readme_does_not_claim_live_deployment_before_phase_5(self):
        self.assertIn("No production deployment is claimed during Phases 1-4.", README)
        self.assertNotIn("Use the live website", README)
        self.assertNotIn("be-sure-ance.netlify.app", README)

    def test_readme_documents_current_data_model(self):
        for required in (
            "plans",
            "plan_facts",
            "source_url",
            "source_type",
            "last_verified_at",
            "Supabase Storage",
        ):
            with self.subTest(required=required):
                self.assertIn(required, README)


if __name__ == "__main__":
    unittest.main()
