<template>
  <section class="comparison-panel">
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

    <div v-else class="comparison-grid">
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

const { t } = useI18n()
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
    render: (plan) => claimSlaText(plan.facts) || factStateText(plan.facts, 'claim_sla'),
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
  const tags = coverageTagsForPlan(plan).map(labelForTag)
  return tags.length > 0 ? tags.join(', ') : factStateText(plan.facts, 'coverage_tags')
}

function qualitativeListValue(plan, fieldName) {
  const items = factItems(plan.facts, fieldName)
  return items.length > 0 ? listText(items) : factStateText(plan.facts, fieldName)
}

function exclusionValue(plan) {
  const items = factItems(plan.facts, 'exclusions')
  return items.length > 0
    ? items.map((item) => `${listText([item])}${taxonomySuffix(item)}`).join(', ')
    : factStateText(plan.facts, 'exclusions')
}

function durationListValue(plan, fieldName, durationFieldName) {
  const items = factItems(plan.facts, fieldName)
  return items.length > 0
    ? items
        .map((item) => durationText(item, durationFieldName))
        .filter(Boolean)
        .join(', ')
    : factStateText(plan.facts, fieldName)
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
  return factStateText(plan.facts, 'brochure_metadata')
}
</script>

<style scoped>
.comparison-panel {
  display: grid;
  gap: 1rem;
  padding: 1.35rem;
  border-radius: 1.25rem;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(16, 39, 71, 0.1);
  box-shadow: 0 24px 60px rgba(16, 39, 71, 0.08);
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
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--muted-ink);
}

h2,
.section-copy {
  margin: 0;
}

.section-copy,
.empty-state {
  color: var(--muted-ink);
}

.comparison-grid {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th,
td {
  padding: 0.85rem;
  border-bottom: 1px solid rgba(16, 39, 71, 0.08);
  text-align: left;
  vertical-align: top;
}

th {
  font-size: 0.82rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--muted-ink);
}

.cell-value {
  display: block;
}

@media (max-width: 720px) {
  .section-top {
    flex-direction: column;
    align-items: start;
  }
}
</style>
