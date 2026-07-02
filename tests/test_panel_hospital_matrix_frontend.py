import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_VUE = (ROOT / "src/be-sure-ance-app/src/App.vue").read_text()
MATRIX = (ROOT / "src/be-sure-ance-app/src/components/PanelHospitalMatrix.vue").read_text()


class PanelHospitalMatrixFrontendTests(unittest.TestCase):
    def test_app_exposes_panel_hospital_matrix_route(self):
        for required in (
            "import PanelHospitalMatrix from './components/PanelHospitalMatrix.vue'",
            'href="/matrix/panel-hospitals"',
            "path === '/matrix/panel-hospitals'",
            "window.history.pushState",
            "window.addEventListener('popstate', syncPathFromLocation)",
            "<PanelHospitalMatrix",
        ):
            with self.subTest(required=required):
                self.assertIn(required, APP_VUE)

    def test_matrix_renders_hospitals_by_provider_columns(self):
        for required in (
            "Hospital coverage by carrier",
            '<th class="hospital-column">Hospital</th>',
            'v-for="provider in visibleProviders"',
            "props.plans.filter((plan) => plan.providerKey === provider.key)",
            "factItems(plan.facts, 'panel_hospitals')",
            "cellFor(row, provider)",
        ):
            with self.subTest(required=required):
                self.assertIn(required, MATRIX)

    def test_matrix_supports_lookup_query_shape(self):
        for required in (
            "is Mt Elizabeth Novena on AIA's panel",
            "function providerMatchesQuery(provider, query)",
            "function hospitalQueryTokens(query, providerList)",
            "visibleRows",
            "visibleProviders",
        ):
            with self.subTest(required=required):
                self.assertIn(required, MATRIX)

    def test_matrix_distinguishes_required_cell_states(self):
        for required in (
            "status: 'no'",
            "status: 'unknown'",
            "status: freshMatches.length > 0 ? 'yes' : 'stale'",
            "status-pill status-yes",
            "status-pill status-no",
            "status-pill status-unknown",
            "status-pill status-stale",
        ):
            with self.subTest(required=required):
                self.assertIn(required, MATRIX)

    def test_matrix_preserves_source_links_safely(self):
        for required in (
            "safeExternalUrl(cellFor(row, provider).sourceUrl)",
            'target="_blank"',
            'rel="noopener noreferrer"',
            'referrerpolicy="no-referrer"',
            "last_verified_at",
            "STALE_AFTER_DAYS",
        ):
            with self.subTest(required=required):
                self.assertIn(required, MATRIX)

    def test_matrix_has_mobile_layout_guardrails(self):
        for required in (
            "overflow-x: auto",
            "min-width: 920px",
            "@media (max-width: 720px)",
            "flex-direction: column",
        ):
            with self.subTest(required=required):
                self.assertIn(required, MATRIX)


if __name__ == "__main__":
    unittest.main()
