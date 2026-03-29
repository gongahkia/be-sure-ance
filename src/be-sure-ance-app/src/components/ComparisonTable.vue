<template>
  <section class="comparison-panel">
    <div class="section-top">
      <div>
        <p class="eyebrow">Comparison</p>
        <h2>Side-by-side plan readout</h2>
      </div>
      <p class="section-copy">Coverage flags and cost-sharing fields come from the normalized comparison facts table.</p>
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

function currencyValue(value) {
  if (typeof value !== "number" || Number.isNaN(value) || value <= 0) {
    return "N/A"
  }
  return new Intl.NumberFormat("en-SG", {
    style: "currency",
    currency: "SGD",
    maximumFractionDigits: 0
  }).format(value)
}

function coverageValue(value) {
  if (value === true) {
    return "Covered"
  }
  if (value === false) {
    return "Not covered"
  }
  return "Unknown"
}

const rows = computed(() => [
  {
    key: "provider",
    label: "Provider",
    render: (plan) => plan.providerName
  },
  {
    key: "annual",
    label: "Annual premium",
    render: (plan) => currencyValue(plan.comparisonFact?.premium_facts?.annual_premium_min)
  },
  {
    key: "monthly",
    label: "Monthly premium",
    render: (plan) => currencyValue(plan.comparisonFact?.premium_facts?.monthly_premium_min)
  },
  {
    key: "deductible",
    label: "Deductible",
    render: (plan) => currencyValue(plan.comparisonFact?.cost_sharing?.deductible_amount)
  },
  {
    key: "coinsurance",
    label: "Co-insurance",
    render: (plan) => `${plan.comparisonFact?.cost_sharing?.coinsurance_percent || 0}%`
  },
  {
    key: "accident",
    label: "Accident",
    render: (plan) => coverageValue(plan.comparisonFact?.coverage_flags?.accident)
  },
  {
    key: "hospitalization",
    label: "Hospitalization",
    render: (plan) => coverageValue(plan.comparisonFact?.coverage_flags?.hospitalization)
  },
  {
    key: "life",
    label: "Life",
    render: (plan) => coverageValue(plan.comparisonFact?.coverage_flags?.life)
  },
  {
    key: "critical_illness",
    label: "Critical illness",
    render: (plan) => coverageValue(plan.comparisonFact?.coverage_flags?.critical_illness)
  },
  {
    key: "outpatient",
    label: "Outpatient",
    render: (plan) => coverageValue(plan.comparisonFact?.coverage_flags?.outpatient)
  },
  {
    key: "emergency",
    label: "Emergency",
    render: (plan) => coverageValue(plan.comparisonFact?.coverage_flags?.emergency)
  },
  {
    key: "specialist",
    label: "Provider directory",
    render: (plan) => coverageValue(plan.comparisonFact?.coverage_flags?.specialist_network)
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
