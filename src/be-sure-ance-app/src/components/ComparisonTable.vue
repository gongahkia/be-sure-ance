<template>
  <section class="comparison-panel">
    <div class="section-top">
      <div>
        <p class="eyebrow">Comparison</p>
        <h2>Client-ready comparison sheet</h2>
      </div>
      <p class="section-copy">Use this grid to frame what is covered, what is unknown, and where source links differ across shortlisted plans.</p>
    </div>

    <div v-if="selectedPlans.length === 0" class="empty-state">
      Select at least one plan to populate the comparison grid.
    </div>

    <div v-else class="comparison-grid">
      <table>
        <thead>
          <tr>
            <th>Metric</th>
            <th v-for="plan in selectedPlans" :key="plan.key">{{ plan.plan_name }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in rows" :key="row.key">
            <td>{{ row.label }}</td>
            <td v-for="plan in selectedPlans" :key="`${row.key}:${plan.key}`">{{ row.render(plan) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'

defineProps({
  selectedPlans: Array
})

function availabilityValue(value) {
  return value ? "Available" : "Missing"
}

function tagValue(tags, tag) {
  return (tags || []).includes(tag) ? "Tagged" : "Not tagged"
}

function nullableNumber(value, unit) {
  if (value === null || value === undefined) {
    return "Unknown"
  }
  return unit ? `${value} ${unit}` : String(value)
}

function listValue(value) {
  return value?.length ? value.join(", ") : "Unknown"
}

function sourceHost(value) {
  if (!value) {
    return "Missing"
  }
  try {
    return new URL(value).hostname.replace(/^www\./, "")
  } catch {
    return "Available"
  }
}

const rows = computed(() => [
  {
    key: "provider",
    label: "Provider",
    render: (plan) => plan.providerName
  },
  {
    key: "source",
    label: "Source host",
    render: (plan) => sourceHost(plan.comparisonFact?.source_url || plan.product_brochure_url || plan.plan_url)
  },
  {
    key: "accident",
    label: "Accident",
    render: (plan) => tagValue(plan.comparisonFact?.coverage_tags, "accident")
  },
  {
    key: "hospitalization",
    label: "Hospitalization",
    render: (plan) => tagValue(plan.comparisonFact?.coverage_tags, "hospitalization")
  },
  {
    key: "life",
    label: "Life",
    render: (plan) => tagValue(plan.comparisonFact?.coverage_tags, "life")
  },
  {
    key: "critical_illness",
    label: "Critical illness",
    render: (plan) => tagValue(plan.comparisonFact?.coverage_tags, "critical_illness")
  },
  {
    key: "outpatient",
    label: "Outpatient",
    render: (plan) => tagValue(plan.comparisonFact?.coverage_tags, "outpatient")
  },
  {
    key: "emergency",
    label: "Emergency",
    render: (plan) => tagValue(plan.comparisonFact?.coverage_tags, "emergency")
  },
  {
    key: "specialist",
    label: "Provider directory",
    render: (plan) => tagValue(plan.comparisonFact?.coverage_tags, "provider_directory")
  },
  {
    key: "brochure",
    label: "Brochure",
    render: (plan) => availabilityValue((plan.comparisonFact?.coverage_tags || []).includes("brochure_available") || plan.product_brochure_url)
  },
  {
    key: "panel_network_size",
    label: "Panel network size",
    render: (plan) => nullableNumber(plan.comparisonFact?.panel_network_size)
  },
  {
    key: "claim_sla_days",
    label: "Claim SLA",
    render: (plan) => nullableNumber(plan.comparisonFact?.claim_sla_days, "days")
  },
  {
    key: "waiting_period_days",
    label: "Waiting period",
    render: (plan) => nullableNumber(plan.comparisonFact?.waiting_period_days, "days")
  },
  {
    key: "exclusions",
    label: "Exclusions",
    render: (plan) => listValue(plan.comparisonFact?.exclusions)
  },
  {
    key: "notes",
    label: "Notes",
    render: (plan) => plan.comparisonFact?.comparison_notes || "No comparison note"
  }
])
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

@media (max-width: 720px) {
  .section-top {
    flex-direction: column;
    align-items: start;
  }
}
</style>
