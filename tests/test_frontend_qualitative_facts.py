import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_VUE = (ROOT / "src/be-sure-ance-app/src/App.vue").read_text()
PLAN_CARD = (ROOT / "src/be-sure-ance-app/src/components/PlanCard.vue").read_text()
COMPARISON_TABLE = (ROOT / "src/be-sure-ance-app/src/components/ComparisonTable.vue").read_text()
PLAN_FACTS_UTIL = (ROOT / "src/be-sure-ance-app/src/utils/planFacts.js").read_text()


class FrontendQualitativeFactsTests(unittest.TestCase):
    def test_app_loads_source_traceable_plan_facts(self):
        for required in (
            "const planFacts = ref([])",
            "supabase.from('plan_facts').select('*')",
            "function groupPlanFactsByPlan(rows)",
            "fact?.plan_slug",
            "groupedFacts[key][fact.field_name] = fact",
            "facts: planFactMap.value[factKey] || {}",
        ):
            with self.subTest(required=required):
                self.assertIn(required, APP_VUE)

    def test_plan_card_groups_contract_fields(self):
        for required in (
            "t('plan.coverage')",
            "t('plan.network')",
            "t('plan.process')",
            "t('plan.exclusions')",
            "coverage_tags",
            "panel_hospitals",
            "waiting_periods",
            "claim_deadlines",
            "claim_sla",
            "brochure_metadata",
            "source_notes",
            "waitingPeriodTags",
            "exclusionTags",
        ):
            with self.subTest(required=required):
                self.assertIn(required, PLAN_CARD)

    def test_comparison_table_uses_qualitative_fact_rows(self):
        for required in (
            "t('comparison.field')",
            "coverage_tags",
            "panel_hospitals",
            "waiting_periods",
            "claim_deadlines",
            "claim_sla",
            "exclusions",
            "brochure_metadata",
            "source_notes",
            "taxonomySuffix(item)",
        ):
            with self.subTest(required=required):
                self.assertIn(required, COMPARISON_TABLE)

    def test_frontend_exposes_taxonomy_tags_without_suitability_language(self):
        for required in (
            "export function taxonomyTagLabels(items)",
            "export function taxonomySuffix(item)",
            "Needs review",
        ):
            with self.subTest(required=required):
                self.assertIn(required, PLAN_FACTS_UTIL)

        frontend_text = "\n".join([PLAN_CARD, COMPARISON_TABLE]).lower()
        for forbidden in ("better tag", "worse tag", "suitable tag"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, frontend_text)

    def test_old_calculator_terms_are_not_rendered_by_frontend_components(self):
        frontend_text = "\n".join([PLAN_CARD, COMPARISON_TABLE]).lower()
        for forbidden in (
            "premium",
            "deductible",
            "coinsurance",
            "co-insurance",
            "estimated cost",
            "out-of-pocket",
            "scenario",
            "panel_network_size",
            "claim_sla_days",
            "waiting_period_days",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, frontend_text)

    def test_plan_facts_helper_preserves_unknown_states(self):
        for required in (
            "status === 'not_found'",
            "status === 'not_applicable'",
            "status === 'unknown'",
            "return 'Unknown'",
        ):
            with self.subTest(required=required):
                self.assertIn(required, PLAN_FACTS_UTIL)


if __name__ == "__main__":
    unittest.main()
