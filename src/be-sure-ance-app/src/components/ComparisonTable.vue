<template>
  <section class="comparison-panel hub-panel">
    <div class="section-top">
      <div>
        <p class="eyebrow">{{ t('comparison.eyebrow') }}</p>
        <h2>{{ t('comparison.title') }}</h2>
      </div>
      <p class="section-copy">{{ t('comparison.copy') }}</p>
    </div>

    <div v-if="selectedPlans.length === 0" class="empty-state">
      {{ t('comparison.empty') }}
    </div>

    <div v-else class="comparison-grid" tabindex="0" aria-label="Selected plan comparison table">
      <table>
        <thead>
          <tr>
            <th>{{ t('comparison.field') }}</th>
            <th v-for="plan in selectedPlans" :key="plan.key">{{ plan.plan_name }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in rows" :key="row.key">
            <td>{{ row.label }}</td>
            <td v-for="plan in selectedPlans" :key="`${row.key}:${plan.key}`">
              <span class="cell-value">{{ row.render(plan) }}</span>
              <FactProvenance :entries="row.provenance(plan)" compact />
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'

import FactProvenance from './FactProvenance.vue'
import { useI18n } from '../i18n'
import { translateContent } from '../utils/contentTranslation'
import {
  claimSlaText,
  coverageTagsForPlan,
  durationText,
  factItems,
  factStateText,
  factValue,
  labelForTag,
  listText,
  provenanceEntriesForFields,
  taxonomySuffix,
} from '../utils/planFacts'

defineProps({
  selectedPlans: Array,
})

const { locale, t } = useI18n()
const rows = computed(() => [
  {
    key: 'coverage_tags',
    label: t('field.coverage_tags'),
    render: coverageValue,
    provenance: (plan) => provenanceEntriesForFields(plan.facts, ['coverage_tags']),
  },
  {
    key: 'panel_hospitals',
    label: t('field.panel_hospitals'),
    render: (plan) => qualitativeListValue(plan, 'panel_hospitals'),
    provenance: (plan) => provenanceEntriesForFields(plan.facts, ['panel_hospitals']),
  },
  {
    key: 'waiting_periods',
    label: t('field.waiting_periods'),
    render: (plan) => durationListValue(plan, 'waiting_periods', 'duration_days'),
    provenance: (plan) => provenanceEntriesForFields(plan.facts, ['waiting_periods']),
  },
  {
    key: 'claim_deadlines',
    label: t('field.claim_deadlines'),
    render: (plan) => durationListValue(plan, 'claim_deadlines', 'deadline_days'),
    provenance: (plan) => provenanceEntriesForFields(plan.facts, ['claim_deadlines']),
  },
  {
    key: 'claim_sla',
    label: t('field.claim_sla'),
    render: (plan) => localize(claimSlaText(plan.facts) || factStateText(plan.facts, 'claim_sla')),
    provenance: (plan) => provenanceEntriesForFields(plan.facts, ['claim_sla']),
  },
  {
    key: 'exclusions',
    label: t('field.exclusions'),
    render: exclusionValue,
    provenance: (plan) => provenanceEntriesForFields(plan.facts, ['exclusions']),
  },
  {
    key: 'brochure_metadata',
    label: t('field.brochure_metadata'),
    render: brochureValue,
    provenance: (plan) => provenanceEntriesForFields(plan.facts, ['brochure_metadata']),
  },
  {
    key: 'source_notes',
    label: t('field.source_notes'),
    render: (plan) => qualitativeListValue(plan, 'source_notes'),
    provenance: (plan) => provenanceEntriesForFields(plan.facts, ['source_notes']),
  },
])

function coverageValue(plan) {
  const tags = coverageTagsForPlan(plan).map(tagLabel)
  return tags.length > 0 ? tags.join(', ') : localize(factStateText(plan.facts, 'coverage_tags'))
}

function tagLabel(tag) {
  const translated = t(`tag.${tag}`)
  return translated.startsWith('[missing:') ? localize(labelForTag(tag)) : translated
}

function qualitativeListValue(plan, fieldName) {
  const items = factItems(plan.facts, fieldName)
  return localize(items.length > 0 ? listText(items) : factStateText(plan.facts, fieldName))
}

function exclusionValue(plan) {
  const items = factItems(plan.facts, 'exclusions')
  return localize(
    items.length > 0
      ? items.map((item) => `${listText([item])}${taxonomySuffix(item)}`).join(', ')
      : factStateText(plan.facts, 'exclusions'),
  )
}

function durationListValue(plan, fieldName, durationFieldName) {
  const items = factItems(plan.facts, fieldName)
  return localize(
    items.length > 0
      ? items
          .map((item) => durationText(item, durationFieldName))
          .filter(Boolean)
          .join(', ')
      : factStateText(plan.facts, fieldName),
  )
}

function brochureValue(plan) {
  const metadata = factValue(plan.facts, 'brochure_metadata')
  if (metadata?.sha256 || metadata?.url) {
    return t('common.captured')
  }
  if (
    plan.product_brochure_url ||
    (plan.comparisonFact?.coverage_tags || []).includes('brochure_available')
  ) {
    return t('common.available')
  }
  return localize(factStateText(plan.facts, 'brochure_metadata'))
}

function localize(value) {
  return translateContent(value, locale.value)
}
</script>

<style scoped>
.comparison-panel {
  display: grid;
  gap: 1rem;
  padding: 18px;
}

.section-top {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: end;
}

.eyebrow {
  margin: 0 0 0.35rem;
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--hf-muted);
}

h2,
.section-copy {
  margin: 0;
}

.section-copy,
.empty-state {
  color: var(--hf-secondary);
}

.comparison-grid {
  overflow-x: auto;
}

.comparison-grid:focus {
  outline: 2px solid rgba(255, 204, 77, 0.78);
  outline-offset: 2px;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th,
td {
  padding: 12px;
  border-bottom: 1px solid var(--hf-border);
  text-align: left;
  vertical-align: top;
}

th {
  font-size: 0.82rem;
  color: var(--hf-muted);
}

tbody tr:hover {
  background: var(--hf-hover);
}

.cell-value {
  display: block;
  color: var(--hf-primary);
}

@media (max-width: 720px) {
  .section-top {
    flex-direction: column;
    align-items: start;
  }
}
</style>
