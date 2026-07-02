import unittest

from src.lib.benefit_taxonomy import (
    TAXONOMY_VERSION,
    normalize_exclusion_item,
    normalize_waiting_period_item,
)


class BenefitTaxonomyTests(unittest.TestCase):
    def test_exclusion_taxonomy_maps_known_clauses_to_stable_tags(self):
        cases = {
            "Pre-existing conditions": ["pre_existing_condition"],
            "self-inflicted injury": ["self_inflicted_injury"],
            "war or terrorism": ["war_or_terrorism"],
            "cosmetic treatment": ["cosmetic_treatment"],
        }

        for text, tags in cases.items():
            with self.subTest(text=text):
                item = normalize_exclusion_item(text)
                self.assertEqual(item["tags"], tags)
                self.assertEqual(item["taxonomy_status"], "tagged")
                self.assertFalse(item["review_required"])

    def test_waiting_period_taxonomy_maps_known_conditions_to_stable_tags(self):
        item = normalize_waiting_period_item(
            condition="specified conditions",
            duration_days=90,
            raw_text="90 days waiting period for specified conditions",
        )

        self.assertEqual(TAXONOMY_VERSION, 1)
        self.assertEqual(item["tags"], ["specified_condition"])
        self.assertEqual(item["duration_days"], 90)
        self.assertEqual(item["taxonomy_status"], "tagged")

    def test_unknown_taxonomy_match_keeps_raw_item_for_manual_review(self):
        item = normalize_exclusion_item("other policy exclusions")

        self.assertEqual(item["tags"], [])
        self.assertEqual(item["taxonomy_status"], "needs_review")
        self.assertTrue(item["review_required"])
        self.assertEqual(item["review_reason"], "no_taxonomy_match")


if __name__ == "__main__":
    unittest.main()
