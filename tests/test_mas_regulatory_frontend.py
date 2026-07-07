import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_VUE = (ROOT / "src/be-sure-ance-app/src/App.vue").read_text()
PLAN_CARD = (ROOT / "src/be-sure-ance-app/src/components/PlanCard.vue").read_text()
REGULATORY_LIST = (ROOT / "src/be-sure-ance-app/src/components/RegulatoryEventList.vue").read_text()
I18N = (ROOT / "src/be-sure-ance-app/src/i18n.js").read_text()


class MasRegulatoryFrontendTests(unittest.TestCase):
    def test_app_fetches_and_groups_mas_regulatory_events(self):
        for required in (
            "masRegulatoryEvents.value = data.mas_regulatory_events",
            "const masRegulatoryEvents = ref([])",
            "const regulatoryEventMap = computed(() =>",
            "regulatoryEvents: regulatoryEventMap.value[provider.key] || []",
        ):
            with self.subTest(required=required):
                self.assertIn(required, APP_VUE)

    def test_plan_card_renders_regulatory_context_component(self):
        for required in (
            "import RegulatoryEventList from './RegulatoryEventList.vue'",
            '<RegulatoryEventList :events="regulatoryEvents" />',
            "regulatoryEvents:",
        ):
            with self.subTest(required=required):
                self.assertIn(required, PLAN_CARD)

    def test_regulatory_component_uses_safe_links_and_review_caveat(self):
        for required in (
            "t('ui.regulatory.title')",
            "t('ui.regulatory.needsReview')",
            "t('ui.regulatory.possibleMatch'",
            "safeExternalUrl(event.source_url)",
            "externalHostname(event.source_url)",
            'rel="noopener noreferrer"',
            'referrerpolicy="no-referrer"',
        ):
            with self.subTest(required=required):
                self.assertIn(required, REGULATORY_LIST)
        for required in ("MAS regulatory context", "Needs review", "Verify against MAS source."):
            with self.subTest(required=required):
                self.assertIn(required, I18N)

    def test_regulatory_component_avoids_sensational_framing(self):
        for forbidden in ("scandal", "dangerous carrier", "avoid this insurer", "blacklist"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, REGULATORY_LIST.lower())


if __name__ == "__main__":
    unittest.main()
