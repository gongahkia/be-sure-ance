import unittest
from pathlib import Path

from src.scrapers.registry import EXPERIMENTAL_DECISION, EXPERIMENTAL_SCRAPERS, SUPPORTED_SCRAPERS
from src.validation.differ import discover_targets

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text()


class ScraperRegistryTests(unittest.TestCase):
    def test_supported_and_experimental_scrapers_are_disjoint(self):
        self.assertFalse(set(SUPPORTED_SCRAPERS) & set(EXPERIMENTAL_SCRAPERS))

    def test_each_experimental_scraper_has_defer_decision_documented(self):
        self.assertIn("defer", EXPERIMENTAL_DECISION)
        self.assertEqual(len(EXPERIMENTAL_SCRAPERS), 11)

    def test_readme_matrix_matches_registry_counts(self):
        self.assertEqual(README.count("Supported - scheduled"), len(SUPPORTED_SCRAPERS))
        self.assertEqual(README.count("Experimental - opt-in only"), len(EXPERIMENTAL_SCRAPERS))
        self.assertEqual(
            README.count("Defer until Phase 2 golden scraper coverage"),
            len(EXPERIMENTAL_SCRAPERS),
        )

    def test_validation_targets_default_to_supported_scrapers(self):
        target_insurers = {target.insurer for target in discover_targets(max_urls_per_insurer=1)}

        self.assertTrue(target_insurers)
        self.assertLessEqual(target_insurers, set(SUPPORTED_SCRAPERS))
        self.assertFalse(target_insurers & set(EXPERIMENTAL_SCRAPERS))


if __name__ == "__main__":
    unittest.main()
