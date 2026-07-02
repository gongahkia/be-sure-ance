import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_VUE = (ROOT / "src/be-sure-ance-app/src/App.vue").read_text()
BRIEF_EXPORT = (ROOT / "src/be-sure-ance-app/src/components/BriefExportPanel.vue").read_text()


class BriefExportFrontendTests(unittest.TestCase):
    def test_app_renders_brief_export_panel_for_selected_plans(self):
        for required in (
            "import BriefExportPanel from './components/BriefExportPanel.vue'",
            '<BriefExportPanel :selected-plans="selectedPlans" />',
        ):
            with self.subTest(required=required):
                self.assertIn(required, APP_VUE)

    def test_export_panel_has_session_branding_fields(self):
        for required in (
            "Agent name",
            "MAS rep no.",
            "const agentName = ref('')",
            "const masRepNumber = ref('')",
            'autocomplete="off"',
            "brandingPayload()",
        ):
            with self.subTest(required=required):
                self.assertIn(required, BRIEF_EXPORT)

    def test_export_panel_posts_branding_and_selected_plans_only(self):
        for required in (
            "VITE_PDF_BRIEF_ENDPOINT",
            "fetch(pdfBriefEndpoint.value",
            "plans: props.selectedPlans.map(publicPlanPayload)",
            "canonical_carrier_name: plan.carrierCanonical?.canonical_name",
            "carrier_mismatch_flags: plan.carrierCanonical?.mismatch_flags || []",
            "branding: brandingPayload()",
            "agent_name: agentName.value.trim()",
            "mas_rep_number: masRepNumber.value.trim()",
        ):
            with self.subTest(required=required):
                self.assertIn(required, BRIEF_EXPORT)

    def test_export_panel_does_not_persist_client_or_agent_data(self):
        for forbidden in ("localStorage", "sessionStorage", "supabase", ".insert(", ".upsert("):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, BRIEF_EXPORT)


if __name__ == "__main__":
    unittest.main()
