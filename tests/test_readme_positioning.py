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

    def test_readme_claims_verified_netlify_deployment_without_public_launch(self):
        self.assertIn("Production app: https://besureance.netlify.app/.", README)
        self.assertIn("Before any public launch", README)
        self.assertNotIn("Use the live website", README)

    def test_readme_documents_current_data_model(self):
        for required in (
            "plans",
            "plan_facts",
            "source_url",
            "source_type",
            "last_verified_at",
            "Static data",
        ):
            with self.subTest(required=required):
                self.assertIn(required, README)


if __name__ == "__main__":
    unittest.main()
