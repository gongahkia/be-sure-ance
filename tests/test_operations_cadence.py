import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text()
OPERATIONS = (ROOT / "docs/OPERATIONS.md").read_text()
SUCCESSION = (ROOT / "docs/SUCCESSION.md").read_text()
COMPLIANCE = (ROOT / "docs/COMPLIANCE.md").read_text()
WEEKLY_TEMPLATE = (ROOT / ".github/ISSUE_TEMPLATE/weekly_health_review.yml").read_text()
MONTHLY_TEMPLATE = (ROOT / ".github/ISSUE_TEMPLATE/monthly_brochure_dataset_review.yml").read_text()
QUARTERLY_TEMPLATE = (ROOT / ".github/ISSUE_TEMPLATE/quarterly_advisor_review.yml").read_text()


class OperationsCadenceTests(unittest.TestCase):
    def test_readme_and_docs_link_operations_cadence(self):
        self.assertIn("[Post-launch operations](./docs/OPERATIONS.md)", README)
        self.assertIn("[Post-launch operations cadence](./OPERATIONS.md)", SUCCESSION)
        self.assertIn("[Post-launch operations cadence](./OPERATIONS.md)", COMPLIANCE)

    def test_weekly_health_review_is_documented_from_dashboards_and_artifacts(self):
        for required in (
            "Weekly Scraper Health Review",
            "/status",
            "refresh-static-data",
            "validate-scraper-snapshots",
            "publish-open-dataset",
            "Sentry",
            "First health review can be performed from existing dashboards/artifacts",
        ):
            with self.subTest(required=required):
                self.assertIn(required, OPERATIONS)

    def test_monthly_brochure_and_dataset_review_is_documented(self):
        for required in (
            "Monthly Brochure Alert And Dataset Review",
            "brochure_change_alerts",
            "pending",
            "suppressed",
            "open dataset CSV summary",
            "row count",
            "source URL coverage",
            "Do not dispatch public brochure alerts",
        ):
            with self.subTest(required=required):
                self.assertIn(required, OPERATIONS)

    def test_quarterly_advisor_review_requirements_are_explicit(self):
        for required in (
            "Quarterly Licensed-Advisor Review",
            "Singapore-licensed financial adviser",
            "at least 3 scheduled carriers",
            "at least 2 plans per sampled carrier",
            "Does any copy read like advice",
            "Keep private legal, compliance, or adviser notes outside the repository",
        ):
            with self.subTest(required=required):
                self.assertIn(required, OPERATIONS)

    def test_takedown_owner_and_sla_are_documented(self):
        for required in (
            "Owner: Gabriel Ong Zhe Mian.",
            "gabrielzmong@gmail.com",
            "within 2 business days",
            "within 7 calendar days",
            "docs/TAKEDOWN_RUNBOOK.md",
        ):
            with self.subTest(required=required):
                self.assertIn(required, OPERATIONS)

    def test_issue_templates_exist_for_recurring_reviews(self):
        combined = WEEKLY_TEMPLATE + MONTHLY_TEMPLATE + QUARTERLY_TEMPLATE
        for required in (
            "Weekly scraper health review",
            "Monthly brochure and dataset review",
            "Quarterly licensed-advisor review",
            "docs/OPERATIONS.md",
            "validations:",
            "required: true",
        ):
            with self.subTest(required=required):
                self.assertIn(required, combined)


if __name__ == "__main__":
    unittest.main()
