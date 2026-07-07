import unittest

from scripts.validate_static_app_data import validation_errors
from src.backend.demo_data import demo_tables
from src.lib.static_app_data import build_app_data_payload
from src.validation.plan_quality import semantic_quality_report, validate_plan_rows


class StaticAppDataValidationTests(unittest.TestCase):
    def test_valid_live_sized_payload_passes(self):
        tables = {
            "plans": [
                {
                    "insurer": f"carrier_{index % 3}",
                    "plan_slug": f"plan-{index}",
                    "plan_name": f"Shield Plan {index}",
                    "plan_url": f"https://example.com/products/shield-plan-{index}",
                    "plan_description": "Medical insurance",
                    "plan_overview": "Hospital and surgical coverage.",
                }
                for index in range(10)
            ],
            "plan_facts": [
                {"insurer": "carrier_0", "plan_slug": "plan-0", "field_name": "coverage"}
            ],
            "plan_comparison_facts": [{"insurer": "carrier_0", "plan_slug": "plan-0"}],
        }
        payload = build_app_data_payload(tables, generated_at_value="2026-07-06T00:00:00+00:00")

        self.assertEqual([], validation_errors(payload))

    def test_seeded_demo_payload_fails_production_validation(self):
        payload = build_app_data_payload(
            demo_tables(), generated_at_value="2026-07-06T00:00:00+00:00"
        )

        self.assertIn("payload contains seeded demo markers", validation_errors(payload))

    def test_sparse_payload_fails_minimum_counts(self):
        payload = build_app_data_payload(
            {"plans": [{"insurer": "aia", "plan_slug": "one"}]},
            generated_at_value="2026-07-06T00:00:00+00:00",
        )
        errors = validation_errors(payload)

        self.assertTrue(any("expected at least 10 plans" in error for error in errors))
        self.assertTrue(any("expected at least 3 carriers" in error for error in errors))

    def test_polluted_raffles_like_row_fails_semantic_validation(self):
        payload = build_app_data_payload(
            {
                "plans": [
                    {
                        "insurer": "raffles_health",
                        "plan_slug": "third-party-administration",
                        "plan_name": "Raffles Health Insurance/Third Party Administration",
                        "plan_url": "https://www.raffleshealthinsurance.com/resource-centre/downloads/",
                        "plan_description": (
                            "Home Products For Individuals and Families Singapore Coverage "
                            "Raffles Shield Raffles Critical Illness Plan Regional Coverage "
                            "Forms and Downloads Resource Centre About Us Blog Webinar "
                            "Social Media Facebook Instagram Linkedin Contact Us X Contact Us"
                        ),
                        "plan_overview": " ".join(["navigation"] * 400),
                    }
                ],
                "plan_facts": [
                    {"insurer": "raffles_health", "plan_slug": "third-party-administration"}
                ],
                "plan_comparison_facts": [
                    {"insurer": "raffles_health", "plan_slug": "third-party-administration"}
                ],
            },
            generated_at_value="2026-07-06T00:00:00+00:00",
        )

        errors = validation_errors(payload, min_plans=1, min_carriers=1)

        self.assertTrue(any("page chrome" in error for error in errors))
        self.assertTrue(any("non-product content" in error for error in errors))
        self.assertTrue(any("plan_overview length" in error for error in errors))

    def test_prudential_category_hero_name_fails_semantic_validation(self):
        payload = build_app_data_payload(
            {
                "plans": [
                    {
                        "insurer": "prudential",
                        "plan_slug": "best-health-insurance-plans",
                        "plan_name": "Best Health Insurance Plans in Singapore for Everyone",
                        "plan_url": "https://www.prudential.com.sg/products/health-insurance",
                    }
                ],
                "plan_facts": [
                    {"insurer": "prudential", "plan_slug": "best-health-insurance-plans"}
                ],
                "plan_comparison_facts": [
                    {"insurer": "prudential", "plan_slug": "best-health-insurance-plans"}
                ],
            },
            generated_at_value="2026-07-06T00:00:00+00:00",
        )

        errors = validation_errors(payload, min_plans=1, min_carriers=1)

        self.assertTrue(any("category or hero copy" in error for error in errors))

    def test_claim_or_contact_url_fails_semantic_validation(self):
        payload = build_app_data_payload(
            {
                "plans": [
                    {
                        "insurer": "income",
                        "plan_slug": "personal-claim",
                        "plan_name": "Personal Claim Request",
                        "plan_url": "https://www.income.com.sg/claims/personal-claim",
                    }
                ],
                "plan_facts": [{"insurer": "income", "plan_slug": "personal-claim"}],
                "plan_comparison_facts": [{"insurer": "income", "plan_slug": "personal-claim"}],
            },
            generated_at_value="2026-07-06T00:00:00+00:00",
        )

        errors = validation_errors(payload, min_plans=1, min_carriers=1)

        self.assertTrue(any("non-product content" in error for error in errors))

    def test_missing_plan_url_fails_semantic_validation(self):
        payload = build_app_data_payload(
            {
                "plans": [
                    {
                        "insurer": "income",
                        "plan_slug": "enhanced-incomeshield",
                        "plan_name": "Enhanced IncomeShield",
                    }
                ],
                "plan_facts": [{"insurer": "income", "plan_slug": "enhanced-incomeshield"}],
                "plan_comparison_facts": [
                    {"insurer": "income", "plan_slug": "enhanced-incomeshield"}
                ],
            },
            generated_at_value="2026-07-06T00:00:00+00:00",
        )

        errors = validation_errors(payload, min_plans=1, min_carriers=1)

        self.assertTrue(any("missing plan_url" in error for error in errors))

    def test_duplicate_plan_identity_fails_semantic_validation(self):
        payload = build_app_data_payload(
            {
                "plans": [
                    {
                        "insurer": "singlife",
                        "plan_slug": "shield",
                        "plan_name": "Singlife Shield",
                        "plan_url": "https://singlife.com/products/singlife-shield",
                    },
                    {
                        "insurer": "singlife",
                        "plan_slug": "shield",
                        "plan_name": "Singlife Shield Duplicate",
                        "plan_url": "https://singlife.com/products/singlife-shield",
                    },
                ],
                "plan_facts": [{"insurer": "singlife", "plan_slug": "shield"}],
                "plan_comparison_facts": [{"insurer": "singlife", "plan_slug": "shield"}],
            },
            generated_at_value="2026-07-06T00:00:00+00:00",
        )

        errors = validation_errors(payload, min_plans=1, min_carriers=1)

        self.assertTrue(any("duplicate (insurer, plan_slug)" in error for error in errors))

    def test_semantic_report_is_scraper_health_shaped(self):
        report = semantic_quality_report(
            [
                {
                    "insurer": "carrier_a",
                    "plan_slug": "clean",
                    "plan_name": "Clean Shield",
                    "plan_url": "https://example.com/products/clean-shield",
                },
                {
                    "insurer": "carrier_b",
                    "plan_slug": "bad",
                    "plan_name": "Best Health Insurance Plans in Singapore",
                    "plan_url": "https://example.com/products/bad",
                },
            ]
        )

        self.assertEqual("failed", report["status"])
        self.assertEqual(2, report["total_targets"])
        self.assertEqual(1, report["failed"])
        self.assertIn("notes", report)

    def test_overlong_exception_requires_source_evidence(self):
        row = {
            "insurer": "carrier",
            "plan_slug": "long-overview",
            "plan_name": "Long Overview Shield",
            "plan_url": "https://example.com/products/long-overview",
            "plan_overview": " ".join(["covered"] * 400),
        }
        unsupported_exception = [
            {
                "insurer": "carrier",
                "plan_slug": "long-overview",
                "field": "plan_overview",
                "code": "overlong_text",
            }
        ]
        supported_exception = [
            {
                **unsupported_exception[0],
                "source_url": "https://example.com/products/long-overview",
            }
        ]

        self.assertTrue(validate_plan_rows([row], exceptions=unsupported_exception))
        self.assertEqual([], validate_plan_rows([row], exceptions=supported_exception))


if __name__ == "__main__":
    unittest.main()
