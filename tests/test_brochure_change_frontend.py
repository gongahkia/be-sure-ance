import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_VUE = (ROOT / "src/be-sure-ance-app/src/App.vue").read_text()
PLAN_CARD = (ROOT / "src/be-sure-ance-app/src/components/PlanCard.vue").read_text()
CHANGE_LIST = (ROOT / "src/be-sure-ance-app/src/components/BrochureChangeList.vue").read_text()


class BrochureChangeFrontendTests(unittest.TestCase):
    def test_app_fetches_and_groups_brochure_change_alerts(self):
        for required in (
            "const brochureChangeAlerts = ref([])",
            "supabase.from('brochure_change_alerts').select('*')",
            "function groupBrochureChangesByPlan(rows)",
            "const brochureChangeMap = computed(() =>",
            "brochureChanges: brochureChangeMap.value[factKey] || []",
            ':brochure-changes="plan.brochureChanges"',
        ):
            with self.subTest(required=required):
                self.assertIn(required, APP_VUE)

    def test_plan_card_renders_brochure_change_component(self):
        for required in (
            "import BrochureChangeList from './BrochureChangeList.vue'",
            '<BrochureChangeList :changes="brochureChanges" />',
            "brochureChanges:",
        ):
            with self.subTest(required=required):
                self.assertIn(required, PLAN_CARD)

    def test_brochure_change_component_uses_safe_links_and_recent_limit(self):
        for required in (
            "Brochure changes",
            "Pending alert hook",
            ".slice(0, 3)",
            "safeExternalUrl(change.source_url)",
            "externalHostname(change.source_url)",
            'rel="noopener noreferrer"',
            'referrerpolicy="no-referrer"',
        ):
            with self.subTest(required=required):
                self.assertIn(required, CHANGE_LIST)

    def test_component_avoids_suitability_or_alarm_framing(self):
        for forbidden in ("avoid this insurer", "dangerous", "best plan", "worst plan"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, CHANGE_LIST.lower())


if __name__ == "__main__":
    unittest.main()
