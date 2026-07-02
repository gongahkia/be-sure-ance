import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
I18N = (ROOT / "src/be-sure-ance-app/src/i18n.js").read_text()
APP_VUE = (ROOT / "src/be-sure-ance-app/src/App.vue").read_text()
COMPARISON_TABLE = (ROOT / "src/be-sure-ance-app/src/components/ComparisonTable.vue").read_text()
FACT_PROVENANCE = (ROOT / "src/be-sure-ance-app/src/components/FactProvenance.vue").read_text()
PLAN_CARD = (ROOT / "src/be-sure-ance-app/src/components/PlanCard.vue").read_text()


class FrontendI18nTests(unittest.TestCase):
    def test_lightweight_i18n_supports_en_and_zh_sg_with_fallback(self):
        for required in (
            "export const messages",
            "en:",
            "'zh-SG':",
            "export function useI18n()",
            "[missing:${key}]",
            "supportedLocales",
        ):
            with self.subTest(required=required):
                self.assertIn(required, I18N)

    def test_language_toggle_preserves_route_state(self):
        for required in (
            'v-for="option in supportedLocales"',
            "setLocale(option.code)",
            "activeView === 'panelMatrix'",
            "window.history.pushState",
        ):
            with self.subTest(required=required):
                self.assertIn(required, APP_VUE)

    def test_core_surfaces_use_i18n_keys(self):
        for required in (
            "t('hero.title')",
            "t('disclaimer.share')",
            "t('comparison.field')",
            "t('provenance.scraped'",
            "t('plan.coverage')",
        ):
            with self.subTest(required=required):
                self.assertIn(required, APP_VUE + COMPARISON_TABLE + FACT_PROVENANCE + PLAN_CARD)

    def test_zh_disclaimer_preserves_compliance_meaning(self):
        for required in (
            "此共享比较仅供会前研究使用",
            "不是财务建议、保险建议、法律建议",
            "推荐、排名、报价或保单交易",
            "compareFIRST",
            "合规流程",
        ):
            with self.subTest(required=required):
                self.assertIn(required, I18N)


if __name__ == "__main__":
    unittest.main()
