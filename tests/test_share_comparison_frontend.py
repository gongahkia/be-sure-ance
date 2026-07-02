import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_VUE = (ROOT / "src/be-sure-ance-app/src/App.vue").read_text()
SHARE_PANEL = (ROOT / "src/be-sure-ance-app/src/components/ShareComparisonPanel.vue").read_text()


class ShareComparisonFrontendTests(unittest.TestCase):
    def test_app_exposes_share_route_and_loads_share_record(self):
        for required in (
            "parseShareRoute(path)",
            "activeView === 'sharedComparison'",
            ".from('comparison_shares')",
            ".select('*')",
            "const sharedPlans = computed(() =>",
            'ComparisonTable v-else :selected-plans="sharedPlans"',
            "SHARE_DISCLAIMER",
            "trackShareView(shareId)",
        ):
            with self.subTest(required=required):
                self.assertIn(required, APP_VUE)

    def test_share_panel_posts_plan_refs_only(self):
        for required in (
            "VITE_SHARE_ENDPOINT",
            "fetch(shareEndpoint.value",
            "plans: props.selectedPlans.map(sharePlanPayload)",
            "insurer: plan.insurer || plan.providerKey",
            "plan_slug: plan.plan_slug",
            "Open share link",
        ):
            with self.subTest(required=required):
                self.assertIn(required, SHARE_PANEL)

    def test_share_panel_does_not_store_or_send_pii(self):
        for forbidden in (
            "localStorage",
            "sessionStorage",
            "agent_name",
            "mas_rep_number",
            "client",
            "facts:",
            "plan_name",
            "supabase",
            ".insert(",
            ".upsert(",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, SHARE_PANEL)

    def test_share_route_preserves_no_advice_and_provenance(self):
        for required in (
            "This shared comparison is for pre-meeting research only",
            "Verify every fact against the carrier source",
            "ComparisonTable v-else",
        ):
            with self.subTest(required=required):
                self.assertIn(required, APP_VUE)


if __name__ == "__main__":
    unittest.main()
