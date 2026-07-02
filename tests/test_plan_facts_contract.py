import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads((ROOT / "src/lib/plan_facts_contract.json").read_text())
DATA_MODEL = (ROOT / "docs/DATA_MODEL.md").read_text()


class PlanFactsContractTests(unittest.TestCase):
    def test_contract_lists_all_v1_fields(self):
        field_names = {field["field_name"] for field in CONTRACT["fields"]}

        self.assertEqual(
            field_names,
            {
                "coverage_tags",
                "panel_hospitals",
                "exclusions",
                "waiting_periods",
                "claim_deadlines",
                "claim_sla",
                "brochure_metadata",
                "source_notes",
            },
        )

    def test_each_field_has_shape_and_example_json(self):
        status_values = set(CONTRACT["status_values"])
        value_shapes = set(CONTRACT["value_shapes"])

        for field in CONTRACT["fields"]:
            with self.subTest(field=field["field_name"]):
                self.assertIn(field["value_shape"], value_shapes)
                self.assertIn("description", field)
                self.assertIn("example_json", field)
                self.assertIn(field["example_json"]["status"], status_values)
                self.assertTrue(
                    {"value", "items"} & set(field["example_json"]),
                    "example_json must include value or items",
                )

    def test_unknown_states_are_explicit(self):
        self.assertEqual(
            set(CONTRACT["unknown_representation"]),
            {"unknown", "not_found", "not_applicable"},
        )
        for status, example in CONTRACT["unknown_representation"].items():
            with self.subTest(status=status):
                self.assertEqual(example["status"], status)
                self.assertIsNone(example["value"])

    def test_contract_preserves_qualitative_no_advice_stance(self):
        never_infer = " ".join(CONTRACT["never_infer"])

        for forbidden in (
            "premium",
            "deductibles",
            "coinsurance",
            "medical advice",
            "financial advice",
            "plan recommendations",
            "panel membership without a source",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertIn(forbidden, never_infer)

    def test_data_model_documents_contract_fields(self):
        for field in CONTRACT["fields"]:
            with self.subTest(field=field["field_name"]):
                self.assertIn(f'`{field["field_name"]}`', DATA_MODEL)
                self.assertIn(json.dumps(field["example_json"], separators=(",", ":")), DATA_MODEL)


if __name__ == "__main__":
    unittest.main()
