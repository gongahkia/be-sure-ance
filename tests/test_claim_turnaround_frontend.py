import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_VUE = (ROOT / "src/be-sure-ance-app/src/App.vue").read_text()
CLAIM_BOARD = (ROOT / "src/be-sure-ance-app/src/components/ClaimTurnaroundBoard.vue").read_text()


class ClaimTurnaroundFrontendTests(unittest.TestCase):
    def test_app_fetches_claim_turnaround_metrics(self):
        for required in (
            "supabase.from('claim_turnaround_metrics').select('*')",
            "const claimTurnaroundMetrics = ref([])",
            '<ClaimTurnaroundBoard :metrics="claimTurnaroundMetrics" />',
        ):
            with self.subTest(required=required):
                self.assertIn(required, APP_VUE)

    def test_claim_board_renders_source_year_and_limitations(self):
        for required in (
            "Claim turnaround evidence board",
            "Not ranked by LIA source",
            "LIA rows are industry-level evidence, not suitability rankings.",
            "externalHostname(metric.source_url)",
            'referrerpolicy="no-referrer"',
            "metric.source_year",
            "metric.limitations",
        ):
            with self.subTest(required=required):
                self.assertIn(required, CLAIM_BOARD)

    def test_claim_board_does_not_claim_suitability_or_certainty(self):
        for forbidden in ("best insurer", "guaranteed", "recommended carrier"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, CLAIM_BOARD.lower())


if __name__ == "__main__":
    unittest.main()
