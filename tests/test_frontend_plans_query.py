import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_VUE = (ROOT / "src/be-sure-ance-app/src/App.vue").read_text()
I18N = (ROOT / "src/be-sure-ance-app/src/i18n.js").read_text()


class FrontendPlansQueryTests(unittest.TestCase):
    def test_app_loads_plan_rows_from_single_plans_query(self):
        self.assertEqual(APP_VUE.count("supabase.from('plans').select('*')"), 1)
        self.assertNotIn("supabase.from(provider.key)", APP_VUE)
        self.assertNotIn("providers.map(async (provider)", APP_VUE)

    def test_app_groups_plan_rows_by_insurer(self):
        for required in (
            "function groupPlansByProvider(rows)",
            "Object.fromEntries(providers.map((provider) => [provider.key, []]))",
            "row?.insurer",
            "groupedPlans[row.insurer].push(row)",
        ):
            with self.subTest(required=required):
                self.assertIn(required, APP_VUE)

    def test_shortlist_limit_remains_three_plans(self):
        self.assertIn("selectedPlanKeys.value.length >= 3", APP_VUE)
        self.assertIn("selectedPlanKeys.value.slice(1)", APP_VUE)

    def test_empty_provider_state_is_distinct_from_search_miss(self):
        self.assertIn("t('empty.provider')", APP_VUE)
        self.assertIn("t('empty.search')", APP_VUE)
        self.assertIn("No supported plans are loaded for this provider yet.", I18N)
        self.assertIn("No plans match the current provider and search filters.", I18N)


if __name__ == "__main__":
    unittest.main()
