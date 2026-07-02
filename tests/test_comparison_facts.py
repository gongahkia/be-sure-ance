import unittest

from src.scrapers.comparison_facts import build_fact_row


class ComparisonFactTests(unittest.TestCase):
    def test_build_fact_row_uses_qualitative_fields_only(self):
        row = build_fact_row(
            "aia",
            {
                "plan_name": "Sample Plan",
                "plan_description": "Personal accident and emergency support from S$500.",
                "plan_overview": "20% launch copy should not create quantitative fields.",
                "plan_benefits": ["Hospital support"],
                "plan_url": "https://example.com/plan",
                "product_brochure_url": "https://example.com/brochure.pdf",
            },
            specialist_resource_count=1,
        )

        self.assertEqual(row["plan_slug"], "sample-plan")
        self.assertEqual(row["panel_network_size"], None)
        self.assertEqual(row["claim_sla_days"], None)
        self.assertEqual(row["exclusions"], [])
        self.assertEqual(row["waiting_period_days"], None)
        self.assertEqual(row["brochure_hash"], None)
        self.assertEqual(row["brochure_last_changed_at"], None)
        self.assertEqual(row["source_url"], "https://example.com/brochure.pdf")
        self.assertIn("accident", row["coverage_tags"])
        self.assertIn("emergency", row["coverage_tags"])
        self.assertIn("hospitalization", row["coverage_tags"])
        self.assertIn("provider_directory", row["coverage_tags"])
        self.assertIn("brochure_available", row["coverage_tags"])

        for forbidden in ("premium_facts", "cost_sharing", "scenario_assumptions"):
            self.assertNotIn(forbidden, row)


if __name__ == "__main__":
    unittest.main()
