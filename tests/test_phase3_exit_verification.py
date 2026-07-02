import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PHASE3 = (ROOT / "docs/PHASE3_EXIT_VERIFICATION.md").read_text()


class Phase3ExitVerificationTests(unittest.TestCase):
    def test_starter_combo_is_verified(self):
        for required in (
            "Panel matrix",
            "PDF brief",
            "Per-plan static pages",
            "/matrix/panel-hospitals",
            "scripts/generate-static-pages.mjs",
        ):
            with self.subTest(required=required):
                self.assertIn(required, PHASE3)

    def test_expansion_moats_and_defer_decision_are_recorded(self):
        for required in (
            "Claim turnaround evidence board",
            "Exclusion and waiting-period taxonomy",
            "MAS regulatory event feed",
            "Brochure version history",
            "Saved comparison sets",
            "Telegram lookup bot beta",
            "Chrome MV3 sidebar extension",
            "docs/adr/0006-defer-chrome-extension-sidebar.md",
        ):
            with self.subTest(required=required):
                self.assertIn(required, PHASE3)

    def test_local_gates_and_scraper_dry_runs_are_recorded(self):
        for required in (
            "45 tests passed",
            "moh_institution_count: 5305",
            "claim_turnaround_metric_count: 12",
            "mas_regulatory_event_count: 0",
            "black --check src tests",
            "ruff check src tests",
            "python -m unittest discover -s tests",
            "pre-commit run --all-files",
            "git diff --check",
        ):
            with self.subTest(required=required):
                self.assertIn(required, PHASE3)

    def test_no_pii_no_advice_and_limitations_are_recorded(self):
        for required in (
            "Share links encode selected `insurer` and `plan_slug` references in the URL.",
            "Telegram bot lookup does not persist chat IDs",
            "Claim metrics are source evidence, not suitability rankings.",
            "Public deployment is still blocked until Phase 5.",
            "Remote CI is not verified until commits are pushed.",
            "static_pages:",
            "MAS live source was unavailable",
        ):
            with self.subTest(required=required):
                self.assertIn(required, PHASE3)


if __name__ == "__main__":
    unittest.main()
