import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_VUE = (ROOT / "src/be-sure-ance-app/src/App.vue").read_text()
CLAIM_BOARD = (ROOT / "src/be-sure-ance-app/src/components/ClaimTurnaroundBoard.vue").read_text()
I18N = (ROOT / "src/be-sure-ance-app/src/i18n.js").read_text()


class ClaimTurnaroundFrontendTests(unittest.TestCase):
    def test_app_fetches_claim_turnaround_metrics(self):
        for required in (
            "claimTurnaroundMetrics.value = data.claim_turnaround_metrics",
            "const claimTurnaroundMetrics = ref([])",
            '<ClaimTurnaroundBoard :metrics="claimTurnaroundMetrics" compact />',
        ):
            with self.subTest(required=required):
                self.assertIn(required, APP_VUE)

    def test_claim_board_renders_source_year_and_limitations(self):
        for required in (
            "t('ui.claims.title')",
            "t('ui.claims.notRanked')",
            "t('ui.claims.copy')",
            "externalHostname(metric.source_url)",
            'referrerpolicy="no-referrer"',
            "metric.source_year",
            "metric.limitations",
        ):
            with self.subTest(required=required):
                self.assertIn(required, CLAIM_BOARD)
        for required in (
            "Claim turnaround evidence board",
            "Not ranked by LIA source",
            "LIA rows are industry-level evidence, not suitability rankings.",
        ):
            with self.subTest(required=required):
                self.assertIn(required, I18N)

    def test_claim_board_does_not_claim_suitability_or_certainty(self):
        for forbidden in ("best insurer", "guaranteed", "recommended carrier"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, CLAIM_BOARD.lower())


if __name__ == "__main__":
    unittest.main()
