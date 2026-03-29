<template>
  <section class="calculator-panel">
    <div class="section-top">
      <div>
        <p class="eyebrow">Scenario Calculator</p>
        <h2>Assumption-driven annual cost estimate</h2>
      </div>
      <select v-model="selectedScenario" class="scenario-select">
        <option v-for="scenario in scenarioOptions" :key="scenario.value" :value="scenario.value">
          {{ scenario.label }}
        </option>
      </select>
    </div>

    <div v-if="selectedPlans.length === 0" class="empty-state">
      Select plans to estimate annual cost for a stored scenario.
    </div>

    <div v-else class="calculator-grid">
      <article v-for="plan in calculatedPlans" :key="plan.key" class="calculator-card">
        <h3>{{ plan.plan_name }}</h3>
        <p class="provider-name">{{ plan.providerName }}</p>
        <dl>
          <div>
            <dt>Scenario amount</dt>
            <dd>{{ currencyValue(plan.scenarioAmount) }}</dd>
          </div>
          <div>
            <dt>Annual premium</dt>
            <dd>{{ currencyValue(plan.annualPremium) }}</dd>
          </div>
          <div>
            <dt>Deductible</dt>
            <dd>{{ currencyValue(plan.deductible) }}</dd>
          </div>
          <div>
            <dt>Co-insurance</dt>
            <dd>{{ plan.coinsurance }}%</dd>
          </div>
          <div>
            <dt>Estimated out-of-pocket</dt>
            <dd>{{ currencyValue(plan.outOfPocket) }}</dd>
          </div>
          <div>
            <dt>Total annual cost</dt>
            <dd>{{ currencyValue(plan.totalAnnualCost) }}</dd>
          </div>
        </dl>
        <p class="calculator-note">{{ plan.note }}</p>
      </article>
    </div>
  </section>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  selectedPlans: Array
})

const scenarioCatalog = {
  hospitalization: {
    label: "Hospitalization",
    coverageKey: "hospitalization"
  },
  outpatient: {
    label: "Outpatient",
    coverageKey: "outpatient"
  },
  accident: {
    label: "Accident",
    coverageKey: "accident"
  },
  critical_illness: {
    label: "Critical illness",
    coverageKey: "critical_illness"
  }
}

const selectedScenario = ref("hospitalization")

const scenarioOptions = computed(() =>
  Object.entries(scenarioCatalog).map(([value, item]) => ({
    value,
    label: item.label
  }))
)

watch(
  () => props.selectedPlans,
  () => {
    if (!scenarioCatalog[selectedScenario.value]) {
      selectedScenario.value = "hospitalization"
    }
  },
  { deep: true }
)

const calculatedPlans = computed(() =>
  (props.selectedPlans || []).map((plan) => {
    const scenarioAmount =
      plan.comparisonFact?.scenario_assumptions?.claim_amounts?.[selectedScenario.value] || 0
    const annualPremium = plan.comparisonFact?.premium_facts?.annual_premium_min || 0
    const deductible = plan.comparisonFact?.cost_sharing?.deductible_amount || 0
    const coinsurance = plan.comparisonFact?.cost_sharing?.coinsurance_percent || 0
    const covered = Boolean(plan.comparisonFact?.coverage_flags?.[scenarioCatalog[selectedScenario.value].coverageKey])
    const outOfPocket = covered
      ? deductible + scenarioAmount * (coinsurance / 100)
      : scenarioAmount

    return {
      ...plan,
      scenarioAmount,
      annualPremium,
      deductible,
      coinsurance,
      outOfPocket,
      totalAnnualCost: annualPremium + outOfPocket,
      note: covered
        ? plan.comparisonFact?.scenario_assumptions?.calculation_method
        : "Scenario marked as not covered, so the calculator assigns the full claim amount."
    }
  })
)

function currencyValue(value) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "N/A"
  }
  return new Intl.NumberFormat("en-SG", {
    style: "currency",
    currency: "SGD",
    maximumFractionDigits: 0
  }).format(value)
}
</script>

<style scoped>
.calculator-panel {
  display: grid;
  gap: 1rem;
  padding: 1.35rem;
  border-radius: 1.25rem;
  background: rgba(14, 31, 53, 0.96);
  color: #eef5ff;
  box-shadow: 0 24px 60px rgba(16, 39, 71, 0.16);
}

.section-top {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: center;
}

.eyebrow {
  margin: 0 0 0.35rem;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: rgba(238, 245, 255, 0.7);
}

h2,
.empty-state {
  margin: 0;
}

.scenario-select {
  border: 1px solid rgba(238, 245, 255, 0.24);
  border-radius: 999px;
  padding: 0.7rem 1rem;
  background: rgba(255, 255, 255, 0.08);
  color: inherit;
}

.calculator-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1rem;
}

.calculator-card {
  padding: 1rem;
  border-radius: 1rem;
  background: rgba(255, 255, 255, 0.06);
}

.provider-name,
.calculator-note {
  color: rgba(238, 245, 255, 0.75);
}

dl {
  display: grid;
  gap: 0.75rem;
}

dt {
  font-size: 0.8rem;
  color: rgba(238, 245, 255, 0.65);
}

dd {
  margin: 0.2rem 0 0;
  font-weight: 700;
}

@media (max-width: 720px) {
  .section-top {
    flex-direction: column;
    align-items: start;
  }
}
</style>
