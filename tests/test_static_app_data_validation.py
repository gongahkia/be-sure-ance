import unittest

from scripts.validate_static_app_data import validation_errors
from src.backend.demo_data import demo_tables
from src.lib.static_app_data import build_app_data_payload


class StaticAppDataValidationTests(unittest.TestCase):
    def test_valid_live_sized_payload_passes(self):
        tables = {
            "plans": [
                {"insurer": f"carrier_{index % 3}", "plan_slug": f"plan-{index}"}
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


if __name__ == "__main__":
    unittest.main()
