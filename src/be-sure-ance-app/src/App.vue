<template>
  <div id="app" class="hub-app">
    <header class="hub-topbar">
      <a href="/" class="brand" @click="navigateTo('/', $event)">
        <img :src="appLogo" alt="" aria-hidden="true" />
        <span>Be-sure-ance</span>
      </a>

      <label class="global-search">
        <span class="sr-only">{{ t('ui.searchPlans') }}</span>
        <input
          v-model="searchQuery"
          class="hub-input"
          type="search"
          :placeholder="t('ui.searchPlaceholder')"
        />
      </label>

      <nav class="top-nav" aria-label="Workspace routes">
        <a
          href="/"
          :class="{ active: activeView === 'workspace' }"
          @click="navigateTo('/', $event)"
        >
          {{ t('ui.nav.models') }}
        </a>
        <a
          href="/compare"
          :class="{ active: activeView === 'compare' }"
          @click="navigateTo('/compare', $event)"
        >
          {{ t('ui.nav.compare') }}
        </a>
        <a
          href="/matrix/panel-hospitals"
          :class="{ active: activeView === 'panelMatrix' }"
          @click="navigateTo('/matrix/panel-hospitals', $event)"
        >
          {{ t('ui.nav.datasets') }}
        </a>
        <a
          href="/status"
          :class="{ active: activeView === 'scraperStatus' }"
          @click="navigateTo('/status', $event)"
        >
          {{ t('ui.nav.status') }}
        </a>
      </nav>

      <div class="header-controls">
        <button
          class="theme-toggle"
          type="button"
          :aria-label="t('theme.label')"
          :aria-pressed="theme === 'light'"
          @click="toggleTheme"
        >
          {{ theme === 'dark' ? t('theme.light') : t('theme.dark') }}
        </button>
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
    </header>

    <SelectedBriefBar
      v-if="selectedPlans.length > 0"
      :selected-plans="selectedPlans"
      @remove="togglePlanSelection"
    />

    <section v-if="loading" class="status-panel">{{ t('status.loading') }}</section>
    <section v-else-if="errorMessage" class="status-panel error">{{ errorMessage }}</section>

    <main v-else-if="activeView === 'panelMatrix'" class="page-shell">
      <section class="page-heading">
        <div>
          <p class="subtle-label">{{ t('ui.dataset') }}</p>
          <h1>{{ t('ui.panelMatrix.title') }}</h1>
          <p>{{ t('ui.panelMatrix.copy') }}</p>
        </div>
        <span class="hub-chip strong">
          {{ t('ui.panelMatrix.count', { count: totalPanelHospitalCount }) }}
        </span>
      </section>
      <PanelHospitalMatrix
        v-model:query="matrixSearchQuery"
        :plans="enrichedPlans"
        :providers="providers"
      />
    </main>

    <main v-else-if="activeView === 'scraperStatus'" class="page-shell">
      <section class="page-heading">
        <div>
          <p class="subtle-label">{{ t('ui.operations') }}</p>
          <h1>{{ t('ui.scraper.title') }}</h1>
          <p>{{ t('ui.scraper.copy') }}</p>
        </div>
        <span class="hub-chip strong">
          {{ t('ui.scraper.count', { count: providers.length }) }}
        </span>
      </section>
      <ScraperStatusDashboard :health-rows="scraperHealth" :providers="providers" />
    </main>

    <main v-else-if="activeView === 'compare'" class="page-shell">
      <CompareSplitView :plans="enrichedPlans" :initial-plans="selectedPlans" />
    </main>

    <main v-else-if="activeView === 'sharedComparison'" class="page-shell">
      <section class="repo-heading">
        <div>
          <p class="repo-owner">{{ t('ui.shared.owner') }}</p>
          <h1>{{ t('ui.shared.title') }}</h1>
          <p>{{ SHARE_DISCLAIMER }}</p>
        </div>
        <div class="repo-actions">
          <a href="/" class="hub-link-button" @click="navigateTo('/', $event)">
            {{ t('ui.shared.browse') }}
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

    <main v-else-if="activeView === 'planDetail'" class="page-shell">
      <section v-if="!detailPlan" class="status-panel">{{ t('empty.routePlan') }}</section>
      <template v-else>
        <section class="repo-heading">
          <div class="repo-heading-title">
            <ProviderLogo :provider="detailProvider" size="lg" />
            <div>
              <p class="repo-owner">{{ detailProvider.name }}</p>
              <h1>{{ detailPlan.plan_name }}</h1>
              <div class="chip-row">
                <span
                  v-for="tag in coverageTagsForPlan(detailPlan).map(localizedTagLabel)"
                  :key="tag"
                  class="hub-chip"
                >
                  {{ tag }}
                </span>
                <span class="hub-chip">
                  {{ t('ui.plan.facts', { count: factCount(detailPlan) }) }}
                </span>
                <span :class="['hub-chip', verificationChipClass(detailPlan)]">
                  {{ verificationText(detailPlan) }}
                </span>
                <span class="hub-chip">{{ brochureStatusText(detailPlan) }}</span>
              </div>
            </div>
          </div>
          <div class="repo-actions">
            <button
              class="hub-button primary"
              type="button"
              @click="togglePlanSelection(detailPlan.key)"
            >
              {{
                selectedPlanKeys.includes(detailPlan.key)
                  ? t('ui.detail.remove')
                  : t('ui.detail.add')
              }}
            </button>
            <a
              v-if="safeExternalUrl(detailPlan.plan_url)"
              class="hub-link-button"
              :href="safeExternalUrl(detailPlan.plan_url)"
              target="_blank"
              rel="noopener noreferrer"
              referrerpolicy="no-referrer"
            >
              {{ t('plan.productPage') }}
            </a>
          </div>
        </section>

        <nav class="repo-tabs" :aria-label="t('ui.detail.tabsLabel')">
          <button
            v-for="tab in detailTabs"
            :key="tab.key"
            type="button"
            :class="{ active: activeDetailTab === tab.key }"
            @click="activeDetailTab = tab.key"
          >
            {{ tab.label }}
          </button>
        </nav>

        <section class="repo-layout">
          <article class="repo-main hub-panel">
            <template v-if="activeDetailTab === 'card'">
              <h2>{{ t('ui.detail.planCard') }}</h2>
              <p class="lead">{{ detailLeadText }}</p>
              <FactProvenance :entries="profileProvenanceEntry(detailPlan)" compact />
              <div class="fact-sections">
                <section v-for="row in factRowsFor(detailPlan)" :key="row.key">
                  <h3>{{ row.label }}</h3>
                  <p>{{ row.value }}</p>
                  <FactProvenance
                    :entries="provenanceEntriesForFields(detailPlan.facts, row.fields)"
                  />
                </section>
              </div>
              <RegulatoryEventList :events="detailPlan.regulatoryEvents" />
            </template>

            <template v-else-if="activeDetailTab === 'facts'">
              <h2>{{ t('ui.detail.sourceFacts') }}</h2>
              <div class="fact-table">
                <div
                  v-for="fact in planFactsFor(detailPlan)"
                  :key="fact.field_name"
                  class="fact-row"
                >
                  <strong>{{ sourceFactLabel(fact.field_name) }}</strong>
                  <span>{{ summarizeFact(fact) }}</span>
                  <FactProvenance
                    :entries="provenanceEntriesForFields(detailPlan.facts, [fact.field_name])"
                    compact
                  />
                </div>
              </div>
            </template>

            <template v-else-if="activeDetailTab === 'files'">
              <h2>{{ t('ui.detail.files') }}</h2>
              <p class="lead">{{ brochureStatusText(detailPlan) }}</p>
              <BrochureChangeList :changes="detailPlan.brochureChanges" />
              <FactProvenance
                :entries="provenanceEntriesForFields(detailPlan.facts, ['brochure_metadata'])"
              />
            </template>

            <template v-else>
              <ComparisonTable :selected-plans="detailComparePlans" />
            </template>
          </article>

          <aside class="repo-sidebar">
            <section class="hub-panel sidebar-card">
              <h2>{{ t('ui.detail.metadata') }}</h2>
              <dl>
                <div>
                  <dt>{{ t('ui.detail.facts') }}</dt>
                  <dd>{{ factCount(detailPlan) }}</dd>
                </div>
                <div>
                  <dt>{{ t('ui.detail.sources') }}</dt>
                  <dd>{{ sourceCount(detailPlan) }}</dd>
                </div>
                <div>
                  <dt>{{ t('ui.detail.verified') }}</dt>
                  <dd>
                    {{ formatFactDate(latestVerifiedAt(detailPlan)) || t('ui.detail.missing') }}
                  </dd>
                </div>
                <div>
                  <dt>{{ t('ui.detail.carrier') }}</dt>
                  <dd>{{ detailPlan.carrierCanonical?.canonical_name || detailProvider.name }}</dd>
                </div>
              </dl>
            </section>

            <section class="hub-panel sidebar-card">
              <h2>{{ t('ui.detail.actions') }}</h2>
              <a
                v-if="safeExternalUrl(detailPlan.product_brochure_url)"
                class="hub-link-button"
                :href="safeExternalUrl(detailPlan.product_brochure_url)"
                target="_blank"
                rel="noopener noreferrer"
                referrerpolicy="no-referrer"
              >
                {{ t('plan.brochureLink') }}
              </a>
              <a
                v-if="safeExternalUrl(detailPlan.plan_url)"
                class="hub-link-button"
                :href="safeExternalUrl(detailPlan.plan_url)"
                target="_blank"
                rel="noopener noreferrer"
                referrerpolicy="no-referrer"
              >
                {{ t('ui.detail.carrierSource') }}
              </a>
            </section>

            <ClaimTurnaroundBoard :metrics="claimTurnaroundMetrics" compact />
          </aside>
        </section>
      </template>
    </main>

    <main v-else class="browse-shell">
      <ProviderRail
        :providers="providers"
        :active-provider-key="activeProviderKey"
        :provider-counts="providerCounts"
        :coverage-tags="allCoverageTags"
        :active-coverage-tags="activeCoverageTags"
        @select="activeProviderKey = $event"
        @toggle-coverage="toggleCoverageTag"
        @clear-filters="clearFilters"
      />

      <section class="browse-main">
        <section class="browse-toolbar">
          <div>
            <p class="subtle-label">{{ t('ui.browse.models') }}</p>
            <h1>
              {{ activeProviderLabel }}
              <span>{{ visiblePlans.length.toLocaleString() }}</span>
            </h1>
          </div>
          <div class="toolbar-controls">
            <input
              v-model="searchQuery"
              class="hub-input"
              type="search"
              :placeholder="t('ui.browse.filter')"
            />
            <label class="toggle-pill">
              <input v-model="verifiedOnly" type="checkbox" />
              {{ t('ui.browse.verifiedOnly') }}
            </label>
            <label class="toggle-pill">
              <input v-model="brochureOnly" type="checkbox" />
              {{ t('ui.browse.brochure') }}
            </label>
            <select v-model="sortMode" class="hub-select" :aria-label="t('ui.browse.sortLabel')">
              <option value="updated">{{ t('ui.browse.sort.updated') }}</option>
              <option value="name">{{ t('ui.browse.sort.name') }}</option>
              <option value="carrier">{{ t('ui.browse.sort.carrier') }}</option>
              <option value="facts">{{ t('ui.browse.sort.facts') }}</option>
            </select>
          </div>
        </section>

        <section v-if="visiblePlans.length > 0" class="repo-list">
          <PlanCard
            v-for="plan in visiblePlans"
            :key="plan.key"
            :plan="plan"
            :provider="providerFor(plan.providerKey)"
            :facts="plan.facts"
            :comparison-fact="plan.comparisonFact"
            :resources="plan.resources"
            :regulatory-events="plan.regulatoryEvents"
            :brochure-changes="plan.brochureChanges"
            :selected="selectedPlanKeys.includes(plan.key)"
            @toggle-select="togglePlanSelection"
          />
        </section>
        <section v-else class="empty-plan-state">{{ emptyPlanMessage }}</section>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import appLogo from './assets/logo.png'
import BrochureChangeList from './components/BrochureChangeList.vue'
import ClaimTurnaroundBoard from './components/ClaimTurnaroundBoard.vue'
import CompareSplitView from './components/CompareSplitView.vue'
import ComparisonTable from './components/ComparisonTable.vue'
import FactProvenance from './components/FactProvenance.vue'
import PanelHospitalMatrix from './components/PanelHospitalMatrix.vue'
import PlanCard from './components/PlanCard.vue'
import ProviderRail from './components/ProviderRail.vue'
import ProviderLogo from './components/ProviderLogo.vue'
import RegulatoryEventList from './components/RegulatoryEventList.vue'
import ScraperStatusDashboard from './components/ScraperStatusDashboard.vue'
import SelectedBriefBar from './components/SelectedBriefBar.vue'
import { useI18n } from './i18n'
import { buildPlanKey, providers } from './lib/providers'
import { loadAppData } from './lib/staticData'
import { translateContent } from './utils/contentTranslation'
import { safeExternalUrl } from './utils/links'
import {
  claimSlaText,
  coverageTagsForPlan,
  durationText,
  factItems,
  factStateText,
  factValue,
  formatFactDate,
  itemLabel,
  labelForTag,
  listText,
  profileProvenanceEntry,
  provenanceEntriesForFields,
  provenanceState,
  taxonomySuffix,
} from './utils/planFacts'

const { locale, supportedLocales, setLocale, t } = useI18n()
const SHARE_DISCLAIMER = computed(() => t('disclaimer.share'))
const SELECTED_PLANS_STORAGE_KEY = 'be-sure-ance:selected-plan-keys'
const THEME_STORAGE_KEY = 'be-sure-ance-theme'
const ALL_PROVIDERS_KEY = 'all'

const loading = ref(true)
const errorMessage = ref('')
const sharedComparison = ref(null)
const sharedComparisonError = ref('')
const searchQuery = ref('')
const matrixSearchQuery = ref('')
const currentPath = ref(locationPath())
const activeProviderKey = ref(providerKeyFromPath(window.location.pathname) || ALL_PROVIDERS_KEY)
const selectedPlanKeys = ref(loadStoredSelectedPlanKeys())
const plansByProvider = ref({})
const comparisonFacts = ref([])
const planFacts = ref([])
const specialistResources = ref([])
const claimTurnaroundMetrics = ref([])
const masRegulatoryEvents = ref([])
const brochureChangeAlerts = ref([])
const carrierCanonicalNames = ref([])
const scraperHealth = ref([])
const activeCoverageTags = ref([])
const verifiedOnly = ref(false)
const brochureOnly = ref(false)
const sortMode = ref('updated')
const activeDetailTab = ref('card')
const theme = ref(initialTheme())

applyTheme(theme.value)

const detailTabs = computed(() => [
  { key: 'card', label: t('ui.detail.card') },
  { key: 'facts', label: t('ui.detail.facts') },
  { key: 'files', label: t('ui.detail.files') },
  { key: 'compare', label: t('ui.detail.compare') },
])

async function fetchData() {
  try {
    const data = await loadAppData()
    plansByProvider.value = groupPlansByProvider(data.plans)
    comparisonFacts.value = data.plan_comparison_facts
    planFacts.value = data.plan_facts
    specialistResources.value = data.specialist_resources
    claimTurnaroundMetrics.value = data.claim_turnaround_metrics
    masRegulatoryEvents.value = data.mas_regulatory_events
    brochureChangeAlerts.value = data.brochure_change_alerts
    carrierCanonicalNames.value = data.carrier_canonical_names
    scraperHealth.value = data.scraper_health
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

const currentShareRefs = computed(() => parseShareRoute(currentPath.value))
const routePlanTarget = computed(() => parsePlanRoute(currentPath.value))
const activeView = computed(() => {
  const path = pathWithoutQuery(currentPath.value)
  if (path === '/matrix/panel-hospitals') {
    return 'panelMatrix'
  }
  if (path === '/compare') {
    return 'compare'
  }
  if (path === '/status') {
    return 'scraperStatus'
  }
  if (currentShareRefs.value.length > 0) {
    return 'sharedComparison'
  }
  if (routePlanTarget.value) {
    return 'planDetail'
  }
  return 'workspace'
})

watch(currentPath, () => {
  activeDetailTab.value = 'card'
  if (!loading.value) {
    loadShareFromRoute()
  }
})

watch(
  selectedPlanKeys,
  (keys) => {
    storeSelectedPlanKeys(keys)
  },
  { deep: true },
)

function syncPathFromLocation() {
  setCurrentPath(locationPath())
}

function navigateTo(path, event) {
  if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) {
    return
  }
  event.preventDefault()
  if (window.location.pathname + window.location.search !== path) {
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
  const routeTarget = parsePlanRoute(pathWithoutQuery(path))
  if (routeTarget && providers.some((provider) => provider.key === routeTarget.providerKey)) {
    return routeTarget.providerKey
  }
  return ''
}

function parsePlanRoute(path) {
  const match = pathWithoutQuery(path).match(/^\/plan\/([^/]+)\/([^/]+)\/?$/)
  if (!match) {
    return null
  }
  return {
    providerKey: decodePathPart(match[1]),
    planSlug: decodePathPart(match[2]),
  }
}

function parseShareRoute(path) {
  if (pathWithoutQuery(path) !== '/share') {
    return []
  }
  const params = new URLSearchParams(queryPart(path))
  return parseSharePlanRefs(params.get('plans') || '')
}

function decodePathPart(value) {
  try {
    return decodeURIComponent(value)
  } catch {
    return value
  }
}

function locationPath() {
  return `${window.location.pathname}${window.location.search}`
}

function pathWithoutQuery(path) {
  return String(path || '').split('?')[0]
}

function queryPart(path) {
  const index = String(path || '').indexOf('?')
  return index === -1 ? '' : String(path).slice(index + 1)
}

function parseSharePlanRefs(value) {
  return String(value || '')
    .split(',')
    .map((item) => item.trim().toLowerCase())
    .map((item) => {
      const [insurer, planSlug] = item.split(':')
      if (!safePlanRef(insurer) || !safePlanRef(planSlug)) {
        return null
      }
      return { insurer, plan_slug: planSlug }
    })
    .filter(Boolean)
    .slice(0, 3)
}

function safePlanRef(value) {
  return /^[a-z0-9][a-z0-9_-]{0,119}$/.test(String(value || ''))
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

const visiblePlans = computed(() => sortPlans(filteredPlans()))

function filteredPlans() {
  const query = searchQuery.value.trim().toLowerCase()
  return enrichedPlans.value.filter((plan) => {
    if (
      activeProviderKey.value !== ALL_PROVIDERS_KEY &&
      plan.providerKey !== activeProviderKey.value
    ) {
      return false
    }
    if (brochureOnly.value && !hasBrochure(plan)) {
      return false
    }
    if (verifiedOnly.value && planVerificationState(plan) !== 'verified') {
      return false
    }
    if (activeCoverageTags.value.length > 0) {
      const tags = coverageTagsForPlan(plan)
      if (!activeCoverageTags.value.every((tag) => tags.includes(tag))) {
        return false
      }
    }
    if (!query) {
      return true
    }
    return searchableText(plan).includes(query)
  })
}

function sortPlans(plans) {
  return [...plans].sort((left, right) => {
    if (sortMode.value === 'name') {
      return String(left.plan_name).localeCompare(String(right.plan_name))
    }
    if (sortMode.value === 'carrier') {
      return String(left.providerName).localeCompare(String(right.providerName))
    }
    if (sortMode.value === 'facts') {
      return factCount(right) - factCount(left)
    }
    return String(latestTimestamp(right)).localeCompare(String(latestTimestamp(left)))
  })
}

function searchableText(plan) {
  const parts = [
    plan.providerName,
    plan.plan_name,
    plan.plan_description,
    plan.plan_overview,
    (plan.plan_benefits || []).join(' '),
    plan.comparisonFact?.comparison_notes || '',
    coverageTagsForPlan(plan).join(' '),
    stringifyFacts(plan.facts),
    (plan.resources || [])
      .map((resource) => `${resource.resource_title || ''} ${resource.resource_description || ''}`)
      .join(' '),
  ]
  if (locale.value === 'zh-SG') {
    parts.push(...parts.map((part) => translateContent(part, locale.value)))
  }
  return parts.join(' ').toLowerCase()
}

const detailPlan = computed(() => {
  const routeTarget = routePlanTarget.value
  if (!routeTarget) {
    return null
  }
  return (
    enrichedPlans.value.find(
      (plan) =>
        plan.providerKey === routeTarget.providerKey && plan.plan_slug === routeTarget.planSlug,
    ) || null
  )
})

const detailProvider = computed(() =>
  detailPlan.value ? providerFor(detailPlan.value.providerKey) : providers[0],
)

const detailLeadText = computed(() => {
  if (!detailPlan.value) {
    return ''
  }
  return localize(
    detailPlan.value.plan_overview ||
      detailPlan.value.plan_description ||
      detailPlan.value.comparisonFact?.comparison_notes ||
      t('ui.detail.noOverview'),
  )
})

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

const providerCounts = computed(() =>
  providers.reduce((accumulator, provider) => {
    accumulator[provider.key] = (plansByProvider.value[provider.key] || []).length
    return accumulator
  }, {}),
)

const activeProviderLabel = computed(() => {
  if (activeProviderKey.value === ALL_PROVIDERS_KEY) {
    return t('ui.browse.plans')
  }
  return providerFor(activeProviderKey.value).name
})

const allCoverageTags = computed(() =>
  Array.from(new Set(enrichedPlans.value.flatMap((plan) => coverageTagsForPlan(plan)))).sort(),
)

const selectedPlans = computed(() =>
  selectedPlanKeys.value
    .map((key) => enrichedPlans.value.find((plan) => plan.key === key))
    .filter(Boolean),
)

const detailComparePlans = computed(() => {
  if (!detailPlan.value) {
    return []
  }
  const keyed = new Map([[detailPlan.value.key, detailPlan.value]])
  for (const plan of selectedPlans.value) {
    keyed.set(plan.key, plan)
  }
  return Array.from(keyed.values()).slice(0, 3)
})

const totalPanelHospitalCount = computed(() =>
  enrichedPlans.value.reduce(
    (total, plan) => total + factItems(plan.facts, 'panel_hospitals').length,
    0,
  ),
)

const emptyPlanMessage = computed(() => {
  const providerPlanCount =
    activeProviderKey.value === ALL_PROVIDERS_KEY
      ? enrichedPlans.value.length
      : providerCounts.value[activeProviderKey.value] || 0
  if (providerPlanCount === 0 && !searchQuery.value.trim()) {
    return t('empty.provider')
  }
  return t('empty.search')
})

function providerFor(providerKey) {
  return providers.find((provider) => provider.key === providerKey) || providers[0]
}

function togglePlanSelection(planKey) {
  const key = typeof planKey === 'string' ? planKey : planKey?.key
  if (!key) {
    return
  }
  if (selectedPlanKeys.value.includes(key)) {
    selectedPlanKeys.value = selectedPlanKeys.value.filter((item) => item !== key)
    return
  }
  if (selectedPlanKeys.value.length >= 3) {
    selectedPlanKeys.value = [...selectedPlanKeys.value.slice(1), key]
    return
  }
  selectedPlanKeys.value = [...selectedPlanKeys.value, key]
}

function toggleCoverageTag(tag) {
  if (activeCoverageTags.value.includes(tag)) {
    activeCoverageTags.value = activeCoverageTags.value.filter((item) => item !== tag)
    return
  }
  activeCoverageTags.value = [...activeCoverageTags.value, tag]
}

function clearFilters() {
  activeProviderKey.value = ALL_PROVIDERS_KEY
  activeCoverageTags.value = []
  verifiedOnly.value = false
  brochureOnly.value = false
  searchQuery.value = ''
}

function stringifyFacts(facts) {
  return Object.values(facts || {})
    .map((fact) => JSON.stringify(fact.field_value || ''))
    .join(' ')
}

async function loadShareFromRoute() {
  const shareRefs = currentShareRefs.value
  sharedComparison.value = null
  sharedComparisonError.value = ''
  if (shareRefs.length === 0) {
    return
  }
  sharedComparison.value = {
    id: 'url',
    selected_plans: shareRefs,
    created_at: '',
    view_count: 0,
    disclaimer: SHARE_DISCLAIMER.value,
  }
}

function loadStoredSelectedPlanKeys() {
  try {
    const stored = JSON.parse(window.localStorage.getItem(SELECTED_PLANS_STORAGE_KEY) || '[]')
    if (Array.isArray(stored)) {
      return stored.filter((item) => typeof item === 'string').slice(0, 3)
    }
  } catch {
    return []
  }
  return []
}

function storeSelectedPlanKeys(keys) {
  try {
    window.localStorage.setItem(SELECTED_PLANS_STORAGE_KEY, JSON.stringify(keys.slice(0, 3)))
  } catch {
    return
  }
}

function initialTheme() {
  if (typeof window === 'undefined') {
    return 'dark'
  }
  const storedTheme = window.localStorage.getItem(THEME_STORAGE_KEY)
  if (storedTheme === 'light' || storedTheme === 'dark') {
    return storedTheme
  }
  return window.matchMedia?.('(prefers-color-scheme: light)').matches ? 'light' : 'dark'
}

function toggleTheme() {
  setTheme(theme.value === 'dark' ? 'light' : 'dark')
}

function setTheme(nextTheme) {
  if (!['dark', 'light'].includes(nextTheme)) {
    return
  }
  theme.value = nextTheme
  applyTheme(nextTheme)
  try {
    window.localStorage.setItem(THEME_STORAGE_KEY, nextTheme)
  } catch {
    return
  }
}

function applyTheme(nextTheme) {
  if (typeof document !== 'undefined') {
    document.documentElement.dataset.theme = nextTheme
  }
}

function factRowsFor(plan) {
  const waitingPeriods = factItems(plan.facts, 'waiting_periods')
  const claimDeadlines = factItems(plan.facts, 'claim_deadlines')
  const exclusions = factItems(plan.facts, 'exclusions')
  return [
    {
      key: 'coverage',
      label: t('field.coverage_tags'),
      value:
        coverageTagsForPlan(plan).map(localizedTagLabel).join(', ') ||
        localize(factStateText(plan.facts, 'coverage_tags')),
      fields: ['coverage_tags'],
    },
    {
      key: 'network',
      label: t('field.panel_hospitals'),
      value: localize(
        factItems(plan.facts, 'panel_hospitals').map(itemLabel).join(', ') ||
          factStateText(plan.facts, 'panel_hospitals'),
      ),
      fields: ['panel_hospitals'],
    },
    {
      key: 'process',
      label: t('plan.process'),
      value: [
        waitingPeriods.length
          ? localize(waitingPeriods.map((item) => durationText(item)).join(', '))
          : localize(factStateText(plan.facts, 'waiting_periods')),
        claimDeadlines.length
          ? localize(claimDeadlines.map((item) => durationText(item, 'deadline_days')).join(', '))
          : localize(factStateText(plan.facts, 'claim_deadlines')),
        localize(claimSlaText(plan.facts) || factStateText(plan.facts, 'claim_sla')),
      ].join(' / '),
      fields: ['waiting_periods', 'claim_deadlines', 'claim_sla'],
    },
    {
      key: 'exclusions',
      label: t('field.exclusions'),
      value: localize(
        exclusions.map((item) => `${listText([item])}${taxonomySuffix(item)}`).join(', ') ||
          factStateText(plan.facts, 'exclusions'),
      ),
      fields: ['exclusions'],
    },
    {
      key: 'source_notes',
      label: t('field.source_notes'),
      value: localize(listText(factItems(plan.facts, 'source_notes'), t('empty.search'))),
      fields: ['source_notes'],
    },
  ]
}

function planFactsFor(plan) {
  return Object.values(plan.facts || {}).sort((left, right) =>
    String(left.field_name).localeCompare(String(right.field_name)),
  )
}

function summarizeFact(fact) {
  const fieldValue = fact?.field_value || {}
  if (fieldValue.status && fieldValue.status !== 'known') {
    return localize(labelForTag(fieldValue.status))
  }
  if (fact?.field_name === 'claim_sla') {
    return localize(claimSlaText({ claim_sla: fact }) || t('ui.state.known'))
  }
  if (fact?.field_name === 'brochure_metadata') {
    const value = fieldValue.value || {}
    return value.sha256
      ? t('ui.brochure.captured', { hash: String(value.sha256).slice(0, 12) })
      : t('ui.state.known')
  }
  if (Array.isArray(fieldValue.items)) {
    return localize(
      fieldValue.items.map(itemLabel).filter(Boolean).join(', ') || t('ui.state.known'),
    )
  }
  if (fieldValue.value && typeof fieldValue.value === 'object') {
    return localize(
      Object.entries(fieldValue.value)
        .slice(0, 3)
        .map(([key, value]) => `${labelForTag(key)}: ${value}`)
        .join(', '),
    )
  }
  return localize(String(fieldValue.value || t('ui.state.known')))
}

function factCount(plan) {
  return Object.keys(plan?.facts || {}).length
}

function sourceCount(plan) {
  return new Set(
    Object.values(plan?.facts || {})
      .map((fact) => fact.source_url)
      .filter(Boolean),
  ).size
}

function latestVerifiedAt(plan) {
  return Object.values(plan?.facts || {})
    .map((fact) => fact.last_verified_at || fact.scraped_at || '')
    .filter(Boolean)
    .sort()
    .at(-1)
}

function latestTimestamp(plan) {
  return latestVerifiedAt(plan) || plan?.scraped_at || ''
}

function planVerificationState(plan) {
  const entries = Object.values(plan?.facts || {}).map((fact) => ({
    sourceUrl: fact.source_url || '',
    scrapedAt: fact.scraped_at || '',
    lastVerifiedAt: fact.last_verified_at || '',
  }))
  if (entries.length === 0) {
    return 'missing'
  }
  return entries.some((entry) => provenanceState(entry) === 'Verified') ? 'verified' : 'stale'
}

function verificationText(plan) {
  const state = planVerificationState(plan)
  if (state === 'verified') {
    return t('ui.state.verified')
  }
  if (state === 'stale') {
    return t('ui.state.staleVerification')
  }
  return t('ui.state.sourceIncomplete')
}

function verificationChipClass(plan) {
  const state = planVerificationState(plan)
  if (state === 'verified') {
    return 'good'
  }
  if (state === 'stale') {
    return 'warn'
  }
  return 'bad'
}

function hasBrochure(plan) {
  return Boolean(factValue(plan?.facts, 'brochure_metadata')?.url || plan?.product_brochure_url)
}

function brochureStatusText(plan) {
  const metadata = factValue(plan?.facts, 'brochure_metadata')
  if (metadata?.sha256) {
    return t('ui.brochure.captured', { hash: String(metadata.sha256).slice(0, 12) })
  }
  if (plan?.product_brochure_url) {
    return t('ui.brochure.linked')
  }
  return localize(factStateText(plan?.facts, 'brochure_metadata', t('ui.plan.noBrochure')))
}

function localizedTagLabel(tag) {
  const translated = t(`tag.${tag}`)
  return translated.startsWith('[missing:') ? localize(labelForTag(tag)) : translated
}

function sourceFactLabel(fieldName) {
  const translated = t(`field.${fieldName}`)
  return translated.startsWith('[missing:') ? localize(labelForTag(fieldName)) : translated
}

function localize(value) {
  return translateContent(value, locale.value)
}
</script>

<style scoped>
.hub-app {
  min-height: 100vh;
  background: var(--hf-neutral);
  color: var(--hf-primary);
}

.hub-topbar {
  position: sticky;
  top: 0;
  z-index: 20;
  display: grid;
  grid-template-columns: auto minmax(220px, 460px) minmax(0, 1fr) auto;
  gap: 16px;
  align-items: center;
  min-height: 72px;
  padding: 12px 24px;
  border-bottom: 1px solid var(--hf-border);
  background: var(--hf-topbar);
  backdrop-filter: blur(16px);
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: var(--hf-primary);
  font-size: 20px;
  font-weight: 800;
  text-decoration: none;
}

.brand img {
  width: 36px;
  height: 36px;
  flex: 0 0 auto;
  object-fit: contain;
}

.global-search .hub-input {
  width: 100%;
}

.top-nav {
  display: flex;
  gap: 18px;
  align-items: center;
}

.top-nav a {
  color: var(--hf-secondary);
  font-weight: 600;
  text-decoration: none;
}

.top-nav a.active,
.top-nav a:hover {
  color: var(--hf-primary);
}

.header-controls {
  display: inline-flex;
  gap: 8px;
  align-items: center;
  justify-content: flex-end;
}

.language-toggle {
  display: inline-flex;
  gap: 6px;
}

.language-toggle button,
.theme-toggle {
  min-height: 32px;
  border: 1px solid var(--hf-border);
  border-radius: var(--hf-radius-full);
  background: transparent;
  color: var(--hf-secondary);
  padding: 4px 10px;
  font-weight: 700;
}

.language-toggle button.active {
  background: var(--hf-primary);
  color: var(--hf-primary-contrast);
}

.browse-shell {
  display: grid;
  grid-template-columns: minmax(240px, 300px) minmax(0, 1fr);
  gap: 28px;
  width: min(var(--hf-page-max), 100%);
  margin: 0 auto;
  padding: 28px 24px 48px;
}

.browse-main,
.page-shell {
  display: grid;
  min-width: 0;
  align-content: start;
  gap: 20px;
}

.page-shell {
  width: min(1500px, 100%);
  margin: 0 auto;
  padding: 28px 24px 48px;
}

.browse-toolbar,
.page-heading,
.repo-heading {
  display: flex;
  min-width: 0;
  gap: 16px;
  align-items: flex-end;
  justify-content: space-between;
}

.repo-heading-title {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 14px;
  min-width: 0;
  align-items: start;
}

.subtle-label,
.repo-owner {
  margin: 0 0 4px;
  color: var(--hf-muted);
  font-size: 14px;
}

h1,
h2,
h3,
p {
  letter-spacing: 0;
}

h1,
h2,
h3 {
  margin: 0;
}

h1 {
  font-size: 32px;
  line-height: 38px;
}

h1 span {
  margin-left: 10px;
  color: var(--hf-tertiary);
  font-weight: 600;
}

.page-heading p,
.repo-heading p,
.lead {
  margin: 8px 0 0;
  color: var(--hf-secondary);
  font-size: 16px;
  line-height: 24px;
}

.toolbar-controls,
.repo-actions,
.chip-row {
  display: flex;
  min-width: 0;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  justify-content: flex-end;
}

.toolbar-controls .hub-input {
  width: min(320px, 100%);
}

.toggle-pill {
  display: inline-flex;
  min-height: 40px;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border: 1px solid var(--hf-border);
  border-radius: var(--hf-radius-full);
  color: var(--hf-secondary);
  background: var(--hf-surface);
}

.repo-list {
  display: grid;
  gap: 12px;
}

.repo-tabs {
  display: flex;
  gap: 22px;
  min-height: 52px;
  align-items: end;
  border-bottom: 1px solid var(--hf-border);
}

.repo-tabs button {
  min-height: 52px;
  border: 0;
  border-bottom: 2px solid transparent;
  background: transparent;
  color: var(--hf-secondary);
  font-weight: 700;
}

.repo-tabs button.active {
  border-bottom-color: var(--hf-primary);
  color: var(--hf-primary);
}

.repo-layout {
  display: grid;
  align-items: start;
  grid-template-columns: minmax(0, 1fr) 360px;
  gap: 24px;
}

.repo-main {
  display: grid;
  align-content: start;
  align-self: start;
  gap: 18px;
  padding: 24px;
}

.fact-sections {
  display: grid;
  gap: 16px;
}

.fact-sections section,
.fact-row {
  border-top: 1px solid var(--hf-border);
  padding-top: 14px;
}

.fact-sections h3,
.fact-row strong {
  font-size: 18px;
  line-height: 24px;
}

.fact-sections p,
.fact-row span {
  color: var(--hf-secondary);
}

.fact-table {
  display: grid;
  gap: 14px;
}

.fact-row {
  display: grid;
  gap: 6px;
}

.repo-sidebar {
  display: grid;
  min-width: 0;
  align-content: start;
  gap: 16px;
}

.sidebar-card {
  display: grid;
  gap: 14px;
  padding: 18px;
}

.sidebar-card dl {
  display: grid;
  gap: 12px;
  margin: 0;
}

.sidebar-card dl div {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  border-top: 1px solid var(--hf-border);
  padding-top: 10px;
}

.sidebar-card dt {
  color: var(--hf-muted);
}

.sidebar-card dd {
  margin: 0;
  text-align: right;
}

.status-panel,
.empty-panel {
  margin: 24px;
  padding: 16px;
  border: 1px solid var(--hf-border);
  border-radius: var(--hf-radius-lg);
  background: var(--hf-surface);
  color: var(--hf-secondary);
}

.empty-plan-state {
  padding: 20px 0;
  border-top: 1px solid var(--hf-border);
  border-bottom: 1px solid var(--hf-border);
  color: var(--hf-secondary);
}

.status-panel.error {
  border-color: rgba(229, 72, 77, 0.42);
  color: #fecdd3;
}

@media (max-width: 1280px) {
  .browse-shell,
  .repo-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 980px) {
  .hub-topbar {
    grid-template-columns: minmax(0, 1fr) auto;
    align-items: stretch;
    gap: 10px;
  }

  .global-search,
  .top-nav {
    grid-column: 1 / -1;
  }

  .top-nav,
  .toolbar-controls,
  .repo-actions {
    justify-content: flex-start;
  }
}

@media (max-width: 720px) {
  .hub-topbar,
  .browse-shell,
  .page-shell {
    padding-inline: 14px;
  }

  .hub-topbar {
    position: static;
    min-height: 0;
    padding-block: 12px;
  }

  .brand {
    font-size: 18px;
  }

  .top-nav {
    overflow-x: auto;
    padding-bottom: 2px;
  }

  .browse-toolbar,
  .page-heading,
  .repo-heading {
    display: grid;
    align-items: start;
  }

  .browse-main {
    order: 1;
  }

  .filter-rail {
    order: 2;
  }

  .repo-heading-title {
    grid-template-columns: 1fr;
  }

  h1 {
    font-size: 28px;
    line-height: 34px;
  }

  .toolbar-controls,
  .toolbar-controls .hub-input,
  .hub-select {
    width: 100%;
  }

  .repo-main {
    padding: 16px;
  }
}
</style>
