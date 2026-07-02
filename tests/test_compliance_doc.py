import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPLIANCE = (ROOT / "docs/COMPLIANCE.md").read_text()
README = (ROOT / "README.md").read_text()


class ComplianceDocTests(unittest.TestCase):
    def test_readme_links_compliance_doc(self):
        self.assertIn("[compliance posture](./docs/COMPLIANCE.md)", README)

    def test_pdpa_no_pii_stance_is_documented(self):
        for required in (
            "V1 collects no PII",
            "No user accounts or authentication",
            "No client names",
            "No client data capture",
            "PDPA review",
        ):
            with self.subTest(required=required):
                self.assertIn(required, COMPLIANCE)

    def test_mas_faa_no_advice_boundary_is_documented(self):
        for required in (
            "MAS FAA Stance",
            "[Inference]",
            "No advice, recommendation, suitability, or ranking engine",
            "No quote, premium, deductible, coinsurance, or projected-cost UI",
            "No purchase, lead-generation, application, payment, or referral flow",
            "compareFIRST and carrier sites",
        ):
            with self.subTest(required=required):
                self.assertIn(required, COMPLIANCE)

    def test_scraping_ethics_and_takedown_are_documented(self):
        for required in (
            "Respect robots.txt",
            "User-Agent",
            "robots.txt enforcement is not complete yet",
            "be-sure-ance-bot/1.0 (mailto:gabrielzmong@gmail.com)",
            "Takedown SLA",
            "within 7 calendar days",
            "gabrielzmong@gmail.com",
        ):
            with self.subTest(required=required):
                self.assertIn(required, COMPLIANCE)

    def test_legal_review_launch_gate_is_documented(self):
        for required in (
            "not legal advice",
            "Singapore fintech/compliance lawyer",
            "Do not publicly relaunch until",
        ):
            with self.subTest(required=required):
                self.assertIn(required, COMPLIANCE)


if __name__ == "__main__":
    unittest.main()
