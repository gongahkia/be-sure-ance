<template>
  <section class="comparison-panel">
    <div class="section-top">
      <div>
        <p class="eyebrow">Comparison</p>
        <h2>Client-ready comparison sheet</h2>
      </div>
      <p class="section-copy">
        Use this grid to frame what is covered, what is unknown, and where source links differ
        across shortlisted plans.
      </p>
    </div>

    <div v-if="selectedPlans.length === 0" class="empty-state">
      Select at least one plan to populate the comparison grid.
    </div>

    <div v-else class="comparison-grid">
      <table>
        <thead>
          <tr>
            <th>Field</th>
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
} from '../utils/planFacts'

defineProps({
  selectedPlans: Array,
})

const rows = computed(() => [
  {
    key: 'coverage_tags',
    label: 'Coverage',
    render: coverageValue,
    provenance: (plan) => provenanceEntriesForFields(plan.facts, ['coverage_tags']),
  },
  {
    key: 'panel_hospitals',
    label: 'Network',
    render: (plan) => qualitativeListValue(plan, 'panel_hospitals'),
    provenance: (plan) => provenanceEntriesForFields(plan.facts, ['panel_hospitals']),
  },
  {
    key: 'waiting_periods',
    label: 'Waiting periods',
    render: (plan) => durationListValue(plan, 'waiting_periods', 'duration_days'),
    provenance: (plan) => provenanceEntriesForFields(plan.facts, ['waiting_periods']),
  },
  {
    key: 'claim_deadlines',
    label: 'Claim deadlines',
    render: (plan) => durationListValue(plan, 'claim_deadlines', 'deadline_days'),
    provenance: (plan) => provenanceEntriesForFields(plan.facts, ['claim_deadlines']),
  },
  {
    key: 'claim_sla',
    label: 'Claim SLA',
    render: (plan) => claimSlaText(plan.facts) || factStateText(plan.facts, 'claim_sla'),
    provenance: (plan) => provenanceEntriesForFields(plan.facts, ['claim_sla']),
  },
  {
    key: 'exclusions',
    label: 'Exclusions',
    render: (plan) => qualitativeListValue(plan, 'exclusions'),
    provenance: (plan) => provenanceEntriesForFields(plan.facts, ['exclusions']),
  },
  {
    key: 'brochure_metadata',
    label: 'Brochure',
    render: brochureValue,
    provenance: (plan) => provenanceEntriesForFields(plan.facts, ['brochure_metadata']),
  },
  {
    key: 'source_notes',
    label: 'Source notes',
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
    return 'Captured'
  }
  if (
    plan.product_brochure_url ||
    (plan.comparisonFact?.coverage_tags || []).includes('brochure_available')
  ) {
    return 'Available'
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
