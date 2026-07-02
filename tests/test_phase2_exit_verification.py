import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PHASE2 = (ROOT / "docs/PHASE2_EXIT_VERIFICATION.md").read_text()


class Phase2ExitVerificationTests(unittest.TestCase):
    def test_phase2_exit_evidence_mentions_required_artifacts(self):
        for required in (
            "plan_facts",
            "FactProvenance.vue",
            "docs/COMPLIANCE.md",
            "tests/scrapers/test_aia_golden.py",
            "Run unit and offline golden tests",
            "passed 93 tests",
        ):
            with self.subTest(required=required):
                self.assertIn(required, PHASE2)

    def test_validation_differ_caveat_is_explicit(self):
        for required in (
            "Validation Differ",
            '"errors": 1',
            '"no_baseline": 9',
            "AIA timeout",
            "not green",
            "Do not treat this as Phase 5 release evidence",
        ):
            with self.subTest(required=required):
                self.assertIn(required, PHASE2)

    def test_phase2_exit_keeps_deployment_blocked_until_phase5(self):
        self.assertIn("Public deployment remains blocked until Phase 5.", PHASE2)
        self.assertIn("Remote CI is not verified", PHASE2)


if __name__ == "__main__":
    unittest.main()
