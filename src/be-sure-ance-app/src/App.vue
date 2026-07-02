<template>
  <div id="app" class="app-shell">
    <header class="hero">
      <div class="hero-copy">
        <div class="hero-topline">
          <p class="eyebrow">{{ t('hero.eyebrow') }}</p>
          <div class="language-toggle" :aria-label="t('language.label')">
            <button
              v-for="option in supportedLocales"
              :key="option.code"
              type="button"
              :class="{ active: locale === option.code }"
              :aria-pressed="locale === option.code"
              @click="setLocale(option.code)"
            >
              {{ option.label }}
            </button>
          </div>
        </div>
        <h1>{{ t('hero.title') }}</h1>
        <p class="hero-text">
          {{ t('hero.text') }}
        </p>
        <nav class="route-tabs" aria-label="Workspace views">
          <a
            href="/"
            :class="{ active: activeView === 'workspace' }"
            @click="navigateTo('/', $event)"
          >
            {{ t('route.workspace') }}
          </a>
          <a
            href="/matrix/panel-hospitals"
            :class="{ active: activeView === 'panelMatrix' }"
            @click="navigateTo('/matrix/panel-hospitals', $event)"
          >
            {{ t('route.panelHospitals') }}
          </a>
          <a
            href="/status"
            :class="{ active: activeView === 'scraperStatus' }"
            @click="navigateTo('/status', $event)"
          >
            {{ t('route.status') }}
          </a>
        </nav>
      </div>

      <div class="hero-stats">
        <article>
          <span>{{ t('stats.carriers') }}</span>
          <strong>{{ providers.length }}</strong>
        </article>
        <article>
          <span>{{ t('stats.plans') }}</span>
          <strong>{{ totalPlanCount }}</strong>
        </article>
        <article>
          <span>{{ t('stats.briefReady') }}</span>
          <strong>{{ planFactProfileCount }}</strong>
        </article>
        <article>
          <span>{{ t('stats.plansInBrief') }}</span>
          <strong>{{ selectedPlans.length }}</strong>
        </article>
      </div>
    </header>

    <section class="workflow-strip">
      <article>
        <p class="eyebrow dark">{{ t('workflow.meetingPrep.eyebrow') }}</p>
        <h2>{{ t('workflow.meetingPrep.title') }}</h2>
        <p>{{ t('workflow.meetingPrep.text') }}</p>
      </article>
      <article>
        <p class="eyebrow dark">{{ t('workflow.panelLookup.eyebrow') }}</p>
        <h2>{{ t('workflow.panelLookup.title') }}</h2>
        <p>{{ t('workflow.panelLookup.text') }}</p>
      </article>
      <article>
        <p class="eyebrow dark">{{ t('workflow.carrierResearch.eyebrow') }}</p>
        <h2>{{ t('workflow.carrierResearch.title') }}</h2>
        <p>{{ t('workflow.carrierResearch.text') }}</p>
      </article>
    </section>

    <section v-if="loading" class="status-panel">
      {{ t('status.loading') }}
    </section>

    <section v-else-if="errorMessage" class="status-panel error">
      {{ errorMessage }}
    </section>

    <main v-else-if="activeView === 'panelMatrix'" class="matrix-workspace">
      <PanelHospitalMatrix
        v-model:query="matrixSearchQuery"
        :plans="enrichedPlans"
        :providers="providers"
      />
    </main>

    <main v-else-if="activeView === 'scraperStatus'" class="status-workspace">
      <ScraperStatusDashboard :health-rows="scraperHealth" :providers="providers" />
    </main>

    <section v-else-if="activeView === 'sharedComparison'" class="shared-workspace">
      <main class="main-stage">
        <section class="toolbar">
          <div>
            <p class="eyebrow">{{ t('shared.eyebrow') }}</p>
            <h2>{{ t('shared.title') }}</h2>
            <p class="toolbar-copy">{{ SHARE_DISCLAIMER }}</p>
            <p v-if="sharedComparison" class="toolbar-copy">
              {{
                t('shared.created', {
                  date: dateText(sharedComparison.created_at),
                  views: shareViewText,
                })
              }}
            </p>
          </div>

          <div class="toolbar-actions">
            <a href="/" class="provider-link" @click="navigateTo('/', $event)">
              {{ t('shared.back') }}
            </a>
          </div>
        </section>

        <section v-if="sharedComparisonError" class="status-panel error">
          {{ sharedComparisonError }}
        </section>
        <section v-else-if="sharedComparison && sharedPlans.length === 0" class="status-panel">
          {{ t('shared.missingPlans') }}
        </section>
        <section v-else-if="!sharedComparison" class="status-panel">
          {{ t('shared.loading') }}
        </section>
        <ComparisonTable v-else :selected-plans="sharedPlans" />
      </main>
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
            <p class="eyebrow">{{ t('toolbar.activeProvider') }}</p>
            <h2>{{ activeProvider.name }}</h2>
            <p class="toolbar-copy">{{ activeProvider.focus }} {{ t('toolbar.copySuffix') }}</p>
          </div>

          <div class="toolbar-actions">
            <input
              v-model="searchQuery"
              class="search-input"
              type="search"
              :placeholder="t('toolbar.searchPlaceholder')"
            />
            <a
              v-if="safeExternalUrl(activeProvider.website)"
              :href="safeExternalUrl(activeProvider.website)"
              target="_blank"
              rel="noopener noreferrer"
              referrerpolicy="no-referrer"
              class="provider-link"
            >
              {{ t('toolbar.openCarrier') }}
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
            :regulatory-events="plan.regulatoryEvents"
            :brochure-changes="plan.brochureChanges"
            :selected="selectedPlanKeys.includes(plan.key)"
            @toggle-select="togglePlanSelection"
          />
        </section>

        <section v-else class="empty-panel">
          {{ emptyPlanMessage }}
        </section>

        <ClaimTurnaroundBoard :metrics="claimTurnaroundMetrics" />
        <BriefExportPanel :selected-plans="selectedPlans" />
        <ShareComparisonPanel :selected-plans="selectedPlans" />
        <ComparisonTable :selected-plans="selectedPlans" />
      </main>
    </section>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { createClient } from '@supabase/supabase-js'

import BriefExportPanel from './components/BriefExportPanel.vue'
import ClaimTurnaroundBoard from './components/ClaimTurnaroundBoard.vue'
import ComparisonTable from './components/ComparisonTable.vue'
import PanelHospitalMatrix from './components/PanelHospitalMatrix.vue'
import PlanCard from './components/PlanCard.vue'
import ProviderRail from './components/ProviderRail.vue'
import ScraperStatusDashboard from './components/ScraperStatusDashboard.vue'
import ShareComparisonPanel from './components/ShareComparisonPanel.vue'
import { buildPlanKey, providers } from './lib/providers'
import { useI18n } from './i18n'
import { safeExternalUrl } from './utils/links'

const { locale, supportedLocales, setLocale, t } = useI18n()
const SHARE_DISCLAIMER = computed(() => t('disclaimer.share'))
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY
const supabase = supabaseUrl && supabaseAnonKey ? createClient(supabaseUrl, supabaseAnonKey) : null
const shareEndpoint = computed(() => import.meta.env.VITE_SHARE_ENDPOINT || '/shares')
const trackedShareViews = new Set()

const loading = ref(true)
const errorMessage = ref('')
const sharedComparison = ref(null)
const sharedComparisonError = ref('')
const searchQuery = ref('')
const matrixSearchQuery = ref('')
const currentPath = ref(window.location.pathname)
const activeProviderKey = ref(providerKeyFromPath(window.location.pathname) || providers[0].key)
const selectedPlanKeys = ref([])
const plansByProvider = ref({})
const comparisonFacts = ref([])
const planFacts = ref([])
const specialistResources = ref([])
const claimTurnaroundMetrics = ref([])
const masRegulatoryEvents = ref([])
const brochureChangeAlerts = ref([])
const carrierCanonicalNames = ref([])
const scraperHealth = ref([])

async function fetchData() {
  if (!supabase) {
    errorMessage.value = t('status.supabaseMissing')
    loading.value = false
    return
  }

  try {
    const [
      { data: planData, error: planError },
      { data: comparisonData, error: comparisonError },
      { data: factData, error: factError },
      { data: resourceData, error: resourceError },
      { data: claimData, error: claimError },
      { data: regulatoryData, error: regulatoryError },
      { data: brochureChangeData, error: brochureChangeError },
      { data: carrierCanonicalData, error: carrierCanonicalError },
      { data: scraperHealthData, error: scraperHealthError },
    ] = await Promise.all([
      supabase.from('plans').select('*'),
      supabase.from('plan_comparison_facts').select('*'),
      supabase.from('plan_facts').select('*'),
      supabase.from('specialist_resources').select('*'),
      supabase.from('claim_turnaround_metrics').select('*'),
      supabase.from('mas_regulatory_events').select('*'),
      supabase.from('brochure_change_alerts').select('*'),
      supabase.from('carrier_canonical_names').select('*'),
      supabase
        .from('scraper_health')
        .select(
          'carrier_key,display_name,support_status,last_success_at,last_failure_at,last_run_at,row_count,validation_status,validation_checked_at,validation_summary,updated_at',
        ),
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
    if (claimError) {
      throw claimError
    }
    if (regulatoryError) {
      throw regulatoryError
    }
    if (brochureChangeError) {
      throw brochureChangeError
    }
    if (carrierCanonicalError) {
      throw carrierCanonicalError
    }
    if (scraperHealthError) {
      throw scraperHealthError
    }

    plansByProvider.value = groupPlansByProvider(planData || [])
    comparisonFacts.value = comparisonData || []
    planFacts.value = factData || []
    specialistResources.value = resourceData || []
    claimTurnaroundMetrics.value = claimData || []
    masRegulatoryEvents.value = regulatoryData || []
    brochureChangeAlerts.value = brochureChangeData || []
    carrierCanonicalNames.value = carrierCanonicalData || []
    scraperHealth.value = scraperHealthData || []
    await loadShareFromRoute()
  } catch (error) {
    errorMessage.value = error?.message || t('status.loadError')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchData()
  window.addEventListener('popstate', syncPathFromLocation)
})

onBeforeUnmount(() => {
  window.removeEventListener('popstate', syncPathFromLocation)
})

const currentShareId = computed(() => parseShareRoute(currentPath.value))
const activeView = computed(() => {
  if (currentPath.value === '/matrix/panel-hospitals') {
    return 'panelMatrix'
  }
  if (currentPath.value === '/status') {
    return 'scraperStatus'
  }
  if (currentShareId.value) {
    return 'sharedComparison'
  }
  return 'workspace'
})
const routePlanTarget = computed(() => parsePlanRoute(currentPath.value))

watch(currentShareId, () => {
  if (!loading.value) {
    loadShareFromRoute()
  }
})

function syncPathFromLocation() {
  setCurrentPath(window.location.pathname)
}

function navigateTo(path, event) {
  if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) {
    return
  }
  event.preventDefault()
  if (window.location.pathname !== path) {
    window.history.pushState({}, '', path)
  }
  setCurrentPath(path)
}

function setCurrentPath(path) {
  currentPath.value = path
  const providerKey = providerKeyFromPath(path)
  if (providerKey) {
    activeProviderKey.value = providerKey
  }
}

function providerKeyFromPath(path) {
  const routeTarget = parsePlanRoute(path)
  if (routeTarget && providers.some((provider) => provider.key === routeTarget.providerKey)) {
    return routeTarget.providerKey
  }
  return ''
}

function parsePlanRoute(path) {
  const match = path.match(/^\/plan\/([^/]+)\/([^/]+)\/?$/)
  if (!match) {
    return null
  }
  return {
    providerKey: decodePathPart(match[1]),
    planSlug: decodePathPart(match[2]),
  }
}

function parseShareRoute(path) {
  const match = path.match(
    /^\/share\/([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})\/?$/,
  )
  return match ? match[1].toLowerCase() : ''
}

function decodePathPart(value) {
  try {
    return decodeURIComponent(value)
  } catch {
    return value
  }
}

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

const regulatoryEventMap = computed(() =>
  masRegulatoryEvents.value.reduce((accumulator, event) => {
    if (!event?.carrier_key) {
      return accumulator
    }
    if (!accumulator[event.carrier_key]) {
      accumulator[event.carrier_key] = []
    }
    accumulator[event.carrier_key].push(event)
    return accumulator
  }, {}),
)

const brochureChangeMap = computed(() => groupBrochureChangesByPlan(brochureChangeAlerts.value))
const carrierCanonicalMap = computed(() =>
  Object.fromEntries(carrierCanonicalNames.value.map((carrier) => [carrier.carrier_key, carrier])),
)

function groupBrochureChangesByPlan(rows) {
  return rows.reduce((groupedChanges, change) => {
    if (!change?.insurer || !change?.plan_slug) {
      return groupedChanges
    }
    const key = buildPlanKey(change.insurer, change.plan_slug)
    if (!groupedChanges[key]) {
      groupedChanges[key] = []
    }
    groupedChanges[key].push(change)
    return groupedChanges
  }, {})
}

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
        regulatoryEvents: regulatoryEventMap.value[provider.key] || [],
        brochureChanges: brochureChangeMap.value[factKey] || [],
        carrierCanonical: carrierCanonicalMap.value[provider.key] || null,
      }
    }),
  ),
)

const sharedPlans = computed(() => {
  const allPlans = enrichedPlans.value
  return (sharedComparison.value?.selected_plans || [])
    .map((planRef) =>
      allPlans.find(
        (plan) => plan.providerKey === planRef.insurer && plan.plan_slug === planRef.plan_slug,
      ),
    )
    .filter(Boolean)
})

const shareViewText = computed(() => {
  const count = Number(sharedComparison.value?.view_count || 0)
  return `${count} ${count === 1 ? 'view' : 'views'}`
})

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
    const routeTarget = routePlanTarget.value
    if (routeTarget) {
      return plan.providerKey === routeTarget.providerKey && plan.plan_slug === routeTarget.planSlug
    }

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
  if (routePlanTarget.value) {
    return t('empty.routePlan')
  }
  const providerPlanCount = (plansByProvider.value[activeProviderKey.value] || []).length
  if (providerPlanCount === 0 && !searchQuery.value.trim()) {
    return t('empty.provider')
  }
  return t('empty.search')
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

async function loadShareFromRoute() {
  const shareId = currentShareId.value
  sharedComparison.value = null
  sharedComparisonError.value = ''
  if (!shareId) {
    return
  }
  if (!supabase) {
    sharedComparisonError.value = t('status.supabaseMissing')
    return
  }

  try {
    const { data, error } = await supabase
      .from('comparison_shares')
      .select('*')
      .eq('id', shareId)
      .limit(1)
    if (currentShareId.value !== shareId) {
      return
    }
    if (error) {
      throw error
    }
    const row = (data || [])[0]
    if (!row) {
      sharedComparisonError.value = t('shared.notFound')
      return
    }
    sharedComparison.value = {
      ...row,
      disclaimer: SHARE_DISCLAIMER.value,
    }
    trackShareView(shareId)
  } catch (error) {
    sharedComparisonError.value = error?.message || t('shared.loadError')
  }
}

async function trackShareView(shareId) {
  if (trackedShareViews.has(shareId)) {
    return
  }
  trackedShareViews.add(shareId)
  try {
    const response = await fetch(`${shareEndpoint.value}/${encodeURIComponent(shareId)}/view`, {
      method: 'POST',
    })
    if (!response.ok) {
      return
    }
    const payload = await response.json()
    if (sharedComparison.value?.id === shareId && payload.view_count !== undefined) {
      sharedComparison.value = {
        ...sharedComparison.value,
        view_count: payload.view_count,
      }
    }
  } catch {
    return
  }
}

function dateText(value) {
  return String(value || '').slice(0, 10) || 'Unknown date'
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

.hero-topline {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: start;
}

.language-toggle {
  display: flex;
  gap: 0.35rem;
}

.language-toggle button {
  min-height: 34px;
  padding: 0.35rem 0.55rem;
  border: 1px solid rgba(255, 255, 255, 0.28);
  border-radius: 0.55rem;
  background: transparent;
  color: #f6fbff;
  font-weight: 700;
}

.language-toggle button.active {
  background: #f6fbff;
  color: var(--ink);
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

.route-tabs {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
  margin-top: 1.25rem;
}

.route-tabs a {
  padding: 0.55rem 0.8rem;
  border: 1px solid rgba(255, 255, 255, 0.28);
  border-radius: 999px;
  color: #f6fbff;
  font-weight: 700;
  text-decoration: none;
}

.route-tabs a.active {
  background: #f6fbff;
  color: var(--ink);
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

.matrix-workspace {
  margin-top: 1.5rem;
}

.shared-workspace {
  margin-top: 1.5rem;
}

.status-workspace {
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
