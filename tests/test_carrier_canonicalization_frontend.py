import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_VUE = (ROOT / "src/be-sure-ance-app/src/App.vue").read_text()
PLAN_CARD = (ROOT / "src/be-sure-ance-app/src/components/PlanCard.vue").read_text()
BRIEF_EXPORT = (ROOT / "src/be-sure-ance-app/src/components/BriefExportPanel.vue").read_text()
PDF_BRIEF = (ROOT / "src/backend/pdf_brief.py").read_text()
DATA_MODEL = (ROOT / "docs/DATA_MODEL.md").read_text()
README = (ROOT / "README.md").read_text()


class CarrierCanonicalizationFrontendTests(unittest.TestCase):
    def test_app_fetches_and_enriches_canonical_carrier_rows(self):
        for required in (
            "const carrierCanonicalNames = ref([])",
            "carrierCanonicalNames.value = data.carrier_canonical_names",
            "const carrierCanonicalMap = computed(() =>",
            "carrierCanonical: carrierCanonicalMap.value[provider.key] || null",
        ):
            with self.subTest(required=required):
                self.assertIn(required, APP_VUE)

    def test_plan_card_surfaces_canonical_name_and_flags(self):
        for required in (
            "t('plan.canonicalCarrier')",
            "canonicalCarrierText",
            "canonicalFlagsText",
            "mismatch_flags",
        ):
            with self.subTest(required=required):
                self.assertIn(required, PLAN_CARD)

    def test_pdf_export_payload_includes_canonical_carrier_context(self):
        for required in (
            "canonical_carrier_name: plan.carrierCanonical?.canonical_name",
            "carrier_mismatch_flags: plan.carrierCanonical?.mismatch_flags || []",
            'plan.get("canonical_carrier_name")',
        ):
            with self.subTest(required=required):
                self.assertIn(required, BRIEF_EXPORT + PDF_BRIEF)

    def test_docs_mention_civic_sources_and_limitations(self):
        for required in (
            "MAS Financial Institutions Directory",
            "LIA Singapore member companies",
            "mismatch_flags",
            "Civic carrier canonicalization",
        ):
            with self.subTest(required=required):
                self.assertIn(required, DATA_MODEL + README)


if __name__ == "__main__":
    unittest.main()
