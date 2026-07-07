import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FACT_PROVENANCE = (ROOT / "src/be-sure-ance-app/src/components/FactProvenance.vue").read_text()
PLAN_CARD = (ROOT / "src/be-sure-ance-app/src/components/PlanCard.vue").read_text()
COMPARISON_TABLE = (ROOT / "src/be-sure-ance-app/src/components/ComparisonTable.vue").read_text()
PLAN_FACTS_UTIL = (ROOT / "src/be-sure-ance-app/src/utils/planFacts.js").read_text()
LINKS_UTIL = (ROOT / "src/be-sure-ance-app/src/utils/links.js").read_text()
I18N = (ROOT / "src/be-sure-ance-app/src/i18n.js").read_text()


class FrontendProvenanceTests(unittest.TestCase):
    def test_provenance_component_uses_safe_external_links(self):
        for required in (
            "safeExternalUrl(entry.sourceUrl)",
            "externalHostname(entry.sourceUrl)",
            'target="_blank"',
            'rel="noopener noreferrer"',
            'referrerpolicy="no-referrer"',
        ):
            with self.subTest(required=required):
                self.assertIn(required, FACT_PROVENANCE)

    def test_provenance_component_shows_source_type_and_dates(self):
        for required in (
            "sourceTypeText(entry.sourceType)",
            "formatFactDate(entry.scrapedAt)",
            "formatFactDate(entry.lastVerifiedAt)",
            "provenanceState(entry)",
            "t('provenance.sourceMissing')",
        ):
            with self.subTest(required=required):
                self.assertIn(required, FACT_PROVENANCE)
        self.assertIn("Source URL missing", I18N)

    def test_provenance_component_does_not_stretch_pills(self):
        for required in (
            ".provenance-list {",
            "align-items: flex-start",
            "display: inline-flex",
        ):
            with self.subTest(required=required):
                self.assertIn(required, FACT_PROVENANCE)

    def test_plan_card_marks_each_fact_group_with_provenance(self):
        for required in (
            ":entries=\"provenanceEntriesForFields(facts, ['panel_hospitals'])\"",
            "'waiting_periods'",
            "'claim_deadlines'",
            "'claim_sla'",
            ":entries=\"provenanceEntriesForFields(facts, ['exclusions'])\"",
            ":entries=\"provenanceEntriesForFields(facts, ['source_notes'])\"",
        ):
            with self.subTest(required=required):
                self.assertIn(required, PLAN_CARD)

    def test_comparison_table_adds_provenance_per_fact_row(self):
        for required in (
            '<FactProvenance :entries="row.provenance(plan)" compact />',
            "provenance: (plan) => provenanceEntriesForFields(plan.facts, ['coverage_tags'])",
            "provenance: (plan) => provenanceEntriesForFields(plan.facts, ['panel_hospitals'])",
            "provenance: (plan) => provenanceEntriesForFields(plan.facts, ['claim_sla'])",
            "provenance: (plan) => provenanceEntriesForFields(plan.facts, ['brochure_metadata'])",
        ):
            with self.subTest(required=required):
                self.assertIn(required, COMPARISON_TABLE)

    def test_plan_facts_helper_groups_and_flags_provenance(self):
        for required in (
            "function provenanceEntriesForFields(facts, fieldNames)",
            "fact.source_url || ''",
            "fact.source_type || ''",
            "fact.scraped_at || ''",
            "fact.last_verified_at || ''",
            "missing: true",
            "Source incomplete",
            "Verification missing",
            "Stale verification",
        ):
            with self.subTest(required=required):
                self.assertIn(required, PLAN_FACTS_UTIL)

    def test_link_helper_derives_host_only_after_url_safety_check(self):
        for required in (
            "export function externalHostname(value)",
            "const safeUrl = safeExternalUrl(value)",
            "return new URL(safeUrl).hostname.replace",
        ):
            with self.subTest(required=required):
                self.assertIn(required, LINKS_UTIL)


if __name__ == "__main__":
    unittest.main()
