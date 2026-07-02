<template>
  <div id="app" class="app-shell">
    <header class="hero">
      <div class="hero-copy">
        <p class="eyebrow">For Insurance Agents</p>
        <h1>Prepare carrier comparisons and provider lookups before the client meeting.</h1>
        <p class="hero-text">
          Use the workspace to shortlist plans, open panel and specialist directories, and frame
          qualitative coverage signals instead of brochure-by-brochure guesswork.
        </p>
      </div>

      <div class="hero-stats">
        <article>
          <span>Carriers tracked</span>
          <strong>{{ providers.length }}</strong>
        </article>
        <article>
          <span>Plans loaded</span>
          <strong>{{ totalPlanCount }}</strong>
        </article>
        <article>
          <span>Brief-ready profiles</span>
          <strong>{{ planFactProfileCount }}</strong>
        </article>
        <article>
          <span>Plans in brief</span>
          <strong>{{ selectedPlans.length }}</strong>
        </article>
      </div>
    </header>

    <section class="workflow-strip">
      <article>
        <p class="eyebrow dark">Meeting Prep</p>
        <h2>Build a three-plan brief fast.</h2>
        <p>
          Keep shortlists tight, compare coverage signals side by side, and carry a cleaner story
          into the call.
        </p>
      </article>
      <article>
        <p class="eyebrow dark">Panel Lookup</p>
        <h2>Jump straight to provider directories.</h2>
        <p>
          Open hospital, panel, and specialist resources linked to the plan instead of hunting them
          down mid-conversation.
        </p>
      </article>
      <article>
        <p class="eyebrow dark">Carrier Research</p>
        <h2>Review one provider lane at a time.</h2>
        <p>
          Use the provider rail to move through carriers quickly, then add only the plans worth
          presenting.
        </p>
      </article>
    </section>

    <section v-if="loading" class="status-panel">
      Loading plan data and qualitative facts...
    </section>

    <section v-else-if="errorMessage" class="status-panel error">
      {{ errorMessage }}
    </section>

    <section v-else class="workspace">
      <ProviderRail
        :providers="providers"
        :active-provider-key="activeProviderKey"
        :provider-counts="providerCounts"
        @select="activeProviderKey = $event"
      />

      <main class="main-stage">
        <section class="toolbar">
          <div>
            <p class="eyebrow">Active Provider</p>
            <h2>{{ activeProvider.name }}</h2>
            <p class="toolbar-copy">
              {{ activeProvider.focus }} Use this lane for carrier research and shortlist building.
            </p>
          </div>

          <div class="toolbar-actions">
            <input
              v-model="searchQuery"
              class="search-input"
              type="search"
              placeholder="Search plans, benefits, notes, or provider resources"
            />
            <a
              v-if="safeExternalUrl(activeProvider.website)"
              :href="safeExternalUrl(activeProvider.website)"
              target="_blank"
              rel="noopener noreferrer"
              referrerpolicy="no-referrer"
              class="provider-link"
            >
              Open carrier site
            </a>
          </div>
        </section>

        <section v-if="visiblePlans.length > 0" class="plan-grid">
          <PlanCard
            v-for="plan in visiblePlans"
            :key="plan.key"
            :plan="plan"
            :provider="activeProvider"
            :facts="plan.facts"
            :comparison-fact="plan.comparisonFact"
            :resources="plan.resources"
            :selected="selectedPlanKeys.includes(plan.key)"
            @toggle-select="togglePlanSelection"
          />
        </section>

        <section v-else class="empty-panel">
          {{ emptyPlanMessage }}
        </section>

        <ComparisonTable :selected-plans="selectedPlans" />
      </main>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { createClient } from '@supabase/supabase-js'

import ComparisonTable from './components/ComparisonTable.vue'
import PlanCard from './components/PlanCard.vue'
import ProviderRail from './components/ProviderRail.vue'
import { buildPlanKey, providers } from './lib/providers'
import { safeExternalUrl } from './utils/links'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY
const supabase = supabaseUrl && supabaseAnonKey ? createClient(supabaseUrl, supabaseAnonKey) : null

const loading = ref(true)
const errorMessage = ref('')
const searchQuery = ref('')
const activeProviderKey = ref(providers[0].key)
const selectedPlanKeys = ref([])
const plansByProvider = ref({})
const comparisonFacts = ref([])
const planFacts = ref([])
const specialistResources = ref([])

async function fetchData() {
  if (!supabase) {
    errorMessage.value =
      'Supabase configuration is missing. Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY.'
    loading.value = false
    return
  }

  try {
    const [
      { data: planData, error: planError },
      { data: comparisonData, error: comparisonError },
      { data: factData, error: factError },
      { data: resourceData, error: resourceError },
    ] = await Promise.all([
      supabase.from('plans').select('*'),
      supabase.from('plan_comparison_facts').select('*'),
      supabase.from('plan_facts').select('*'),
      supabase.from('specialist_resources').select('*'),
    ])

    if (planError) {
      throw planError
    }
    if (comparisonError) {
      throw comparisonError
    }
    if (factError) {
      throw factError
    }
    if (resourceError) {
      throw resourceError
    }

    plansByProvider.value = groupPlansByProvider(planData || [])
    comparisonFacts.value = comparisonData || []
    planFacts.value = factData || []
    specialistResources.value = resourceData || []
  } catch (error) {
    errorMessage.value = error?.message || 'Unable to load qualitative plan data.'
  } finally {
    loading.value = false
  }
}

onMounted(fetchData)

function groupPlansByProvider(rows) {
  const groupedPlans = Object.fromEntries(providers.map((provider) => [provider.key, []]))

  for (const row of rows) {
    if (!row?.insurer || !groupedPlans[row.insurer]) {
      continue
    }
    groupedPlans[row.insurer].push(row)
  }

  return groupedPlans
}

const comparisonFactMap = computed(() =>
  Object.fromEntries(
    comparisonFacts.value.map((fact) => [buildPlanKey(fact.insurer, fact.plan_name), fact]),
  ),
)

const planFactMap = computed(() => groupPlanFactsByPlan(planFacts.value))

const planFactProfileCount = computed(() => Object.keys(planFactMap.value).length)

function groupPlanFactsByPlan(rows) {
  return rows.reduce((groupedFacts, fact) => {
    if (!fact?.insurer || !fact?.plan_slug || !fact?.field_name) {
      return groupedFacts
    }

    const key = buildPlanKey(fact.insurer, fact.plan_slug)
    if (!groupedFacts[key]) {
      groupedFacts[key] = {}
    }
    groupedFacts[key][fact.field_name] = fact
    return groupedFacts
  }, {})
}

const specialistResourceMap = computed(() =>
  specialistResources.value.reduce((accumulator, resource) => {
    const key = buildPlanKey(resource.insurer, resource.plan_name)
    if (!accumulator[key]) {
      accumulator[key] = []
    }
    accumulator[key].push(resource)
    return accumulator
  }, {}),
)

const enrichedPlans = computed(() =>
  providers.flatMap((provider) =>
    (plansByProvider.value[provider.key] || []).map((plan) => {
      const key = buildPlanKey(provider.key, plan.plan_name)
      const factKey = buildPlanKey(provider.key, plan.plan_slug || plan.plan_name)
      return {
        ...plan,
        key,
        providerKey: provider.key,
        providerName: provider.name,
        comparisonFact: comparisonFactMap.value[key] || null,
        facts: planFactMap.value[factKey] || {},
        resources: specialistResourceMap.value[key] || [],
      }
    }),
  ),
)

const activeProvider = computed(
  () => providers.find((provider) => provider.key === activeProviderKey.value) || providers[0],
)

const providerCounts = computed(() =>
  providers.reduce((accumulator, provider) => {
    accumulator[provider.key] = (plansByProvider.value[provider.key] || []).length
    return accumulator
  }, {}),
)

const totalPlanCount = computed(() =>
  Object.values(providerCounts.value).reduce((total, count) => total + count, 0),
)

const visiblePlans = computed(() =>
  enrichedPlans.value.filter((plan) => {
    if (plan.providerKey !== activeProviderKey.value) {
      return false
    }

    if (!searchQuery.value.trim()) {
      return true
    }

    const searchableText = [
      plan.plan_name,
      plan.plan_description,
      plan.plan_overview,
      (plan.plan_benefits || []).join(' '),
      plan.comparisonFact?.comparison_notes || '',
      (plan.comparisonFact?.coverage_tags || []).join(' '),
      stringifyFacts(plan.facts),
      (plan.resources || [])
        .map(
          (resource) => `${resource.resource_title || ''} ${resource.resource_description || ''}`,
        )
        .join(' '),
    ]
      .join(' ')
      .toLowerCase()

    return searchableText.includes(searchQuery.value.toLowerCase())
  }),
)

const emptyPlanMessage = computed(() => {
  const providerPlanCount = (plansByProvider.value[activeProviderKey.value] || []).length
  if (providerPlanCount === 0 && !searchQuery.value.trim()) {
    return 'No supported plans are loaded for this provider yet.'
  }
  return 'No plans match the current provider and search filters.'
})

const selectedPlans = computed(() =>
  selectedPlanKeys.value
    .map((key) => enrichedPlans.value.find((plan) => plan.key === key))
    .filter(Boolean),
)

function togglePlanSelection(planKey) {
  if (selectedPlanKeys.value.includes(planKey)) {
    selectedPlanKeys.value = selectedPlanKeys.value.filter((item) => item !== planKey)
    return
  }

  if (selectedPlanKeys.value.length >= 3) {
    selectedPlanKeys.value = [...selectedPlanKeys.value.slice(1), planKey]
    return
  }

  selectedPlanKeys.value = [...selectedPlanKeys.value, planKey]
}

function stringifyFacts(facts) {
  return Object.values(facts || {})
    .map((fact) => JSON.stringify(fact.field_value || ''))
    .join(' ')
}
</script>

<style>
:root {
  --ink: #102747;
  --muted-ink: #567086;
  --paper: #f4f7fb;
  --panel: rgba(255, 255, 255, 0.88);
}

body {
  margin: 0;
  background:
    radial-gradient(circle at top left, rgba(194, 225, 255, 0.9), transparent 36%),
    linear-gradient(180deg, #eef4fb 0%, #f8fafc 100%);
  color: var(--ink);
  font-family: 'IBM Plex Sans', 'Segoe UI', sans-serif;
}

a {
  color: inherit;
}
</style>

<style scoped>
.app-shell {
  min-height: 100vh;
  padding: 2rem;
}

.hero {
  display: grid;
  gap: 1.5rem;
  padding: 2rem;
  border-radius: 1.75rem;
  background: linear-gradient(120deg, rgba(16, 39, 71, 0.98), rgba(24, 76, 120, 0.94)), var(--ink);
  color: #f6fbff;
  box-shadow: 0 34px 80px rgba(16, 39, 71, 0.18);
}

.hero-copy {
  max-width: 52rem;
}

.eyebrow {
  margin: 0 0 0.4rem;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.7);
}

h1 {
  margin: 0;
  max-width: 48rem;
  font-size: clamp(2rem, 4vw, 3.8rem);
  line-height: 1.02;
}

.hero-text {
  margin: 1rem 0 0;
  max-width: 42rem;
  color: rgba(246, 251, 255, 0.78);
  font-size: 1.05rem;
}

.hero-stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 1rem;
}

.hero-stats article {
  padding: 1rem;
  border-radius: 1rem;
  background: rgba(255, 255, 255, 0.08);
}

.hero-stats span {
  display: block;
  font-size: 0.84rem;
  color: rgba(255, 255, 255, 0.66);
}

.hero-stats strong {
  display: block;
  margin-top: 0.35rem;
  font-size: 1.7rem;
}

.workflow-strip {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1rem;
  margin-top: 1.5rem;
}

.workflow-strip article {
  padding: 1.25rem;
  border-radius: 1.25rem;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(16, 39, 71, 0.08);
  box-shadow: 0 24px 60px rgba(16, 39, 71, 0.05);
}

.workflow-strip h2,
.workflow-strip p:last-child {
  margin: 0;
}

.workflow-strip h2 {
  margin-bottom: 0.5rem;
  font-size: 1.15rem;
}

.eyebrow.dark {
  color: var(--muted-ink);
}

.status-panel,
.empty-panel {
  margin-top: 1.5rem;
  padding: 1.2rem 1.4rem;
  border-radius: 1rem;
  background: var(--panel);
  border: 1px solid rgba(16, 39, 71, 0.08);
  color: var(--muted-ink);
}

.status-panel.error {
  color: #7a1d21;
  border-color: rgba(160, 38, 46, 0.2);
  background: rgba(255, 243, 244, 0.92);
}

.workspace {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  gap: 1.5rem;
  margin-top: 1.5rem;
}

.main-stage {
  display: grid;
  gap: 1.5rem;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: end;
  padding: 1.35rem;
  border-radius: 1.25rem;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(16, 39, 71, 0.08);
}

.toolbar h2,
.toolbar-copy {
  margin: 0;
}

.toolbar-copy {
  margin-top: 0.4rem;
  color: var(--muted-ink);
}

.toolbar-actions {
  display: grid;
  gap: 0.75rem;
  justify-items: end;
}

.search-input {
  width: min(420px, 100%);
  padding: 0.9rem 1rem;
  border-radius: 999px;
  border: 1px solid rgba(16, 39, 71, 0.14);
  background: #ffffff;
}

.provider-link {
  font-weight: 700;
  text-decoration: none;
}

.plan-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1rem;
}

@media (max-width: 1080px) {
  .workspace {
    grid-template-columns: 1fr;
  }

  .hero-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .workflow-strip {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .app-shell {
    padding: 1rem;
  }

  .hero,
  .toolbar {
    padding: 1.25rem;
  }

  .hero-stats {
    grid-template-columns: 1fr;
  }

  .toolbar {
    flex-direction: column;
    align-items: start;
  }

  .toolbar-actions {
    width: 100%;
    justify-items: stretch;
  }

  .search-input {
    width: 100%;
  }
}
</style>
