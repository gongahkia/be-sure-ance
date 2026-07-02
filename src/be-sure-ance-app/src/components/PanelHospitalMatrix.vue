<template>
  <section class="matrix-page">
    <div class="matrix-top">
      <div>
        <p class="eyebrow">Panel Matrix</p>
        <h2>Hospital coverage by carrier</h2>
      </div>
      <input
        v-model="searchModel"
        class="matrix-search"
        type="search"
        placeholder="is Mt Elizabeth Novena on AIA's panel"
      />
    </div>

    <div class="legend-row" aria-label="Matrix status legend">
      <span class="status-pill status-yes">Yes</span>
      <span class="status-pill status-no">No</span>
      <span class="status-pill status-unknown">Unknown</span>
      <span class="status-pill status-stale">Stale</span>
    </div>

    <div v-if="hospitalRows.length === 0" class="empty-state">
      No panel hospital facts are loaded yet.
    </div>

    <div v-else-if="visibleRows.length === 0" class="empty-state">
      No hospitals match the current lookup.
    </div>

    <div v-else class="matrix-scroll">
      <table>
        <thead>
          <tr>
            <th class="hospital-column">Hospital</th>
            <th v-for="provider in visibleProviders" :key="provider.key">
              {{ provider.name }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in visibleRows" :key="row.key">
            <th class="hospital-column" scope="row">
              <span>{{ row.name }}</span>
              <small v-if="row.reviewRequired">Review</small>
            </th>
            <td v-for="provider in visibleProviders" :key="`${row.key}:${provider.key}`">
              <div :class="['matrix-cell', `cell-${cellFor(row, provider).status}`]">
                <strong>{{ cellFor(row, provider).label }}</strong>
                <template v-if="cellFor(row, provider).matches.length > 0">
                  <span>{{ cellFor(row, provider).planNames }}</span>
                  <a
                    v-if="safeExternalUrl(cellFor(row, provider).sourceUrl)"
                    :href="safeExternalUrl(cellFor(row, provider).sourceUrl)"
                    target="_blank"
                    rel="noopener noreferrer"
                    referrerpolicy="no-referrer"
                  >
                    Source
                  </a>
                </template>
                <span v-else>{{ cellFor(row, provider).note }}</span>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'

import { safeExternalUrl } from '../utils/links'
import { factItems, itemLabel } from '../utils/planFacts'

const STALE_AFTER_DAYS = 30

const props = defineProps({
  plans: {
    type: Array,
    default: () => [],
  },
  providers: {
    type: Array,
    default: () => [],
  },
  query: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['update:query'])

const searchModel = computed({
  get: () => props.query,
  set: (value) => emit('update:query', value),
})

const providerPlanMap = computed(() =>
  props.providers.reduce((accumulator, provider) => {
    accumulator[provider.key] = props.plans.filter((plan) => plan.providerKey === provider.key)
    return accumulator
  }, {}),
)

const hospitalRows = computed(() => {
  const rows = new Map()

  for (const plan of props.plans) {
    const panelFact = plan.facts?.panel_hospitals
    for (const item of factItems(plan.facts, 'panel_hospitals')) {
      const key = hospitalKey(item)
      if (!key) {
        continue
      }
      if (!rows.has(key)) {
        rows.set(key, {
          key,
          name: hospitalName(item),
          searchText: hospitalSearchText(item),
          reviewRequired: Boolean(item.review_required),
          entries: [],
        })
      }
      const row = rows.get(key)
      row.reviewRequired = row.reviewRequired || Boolean(item.review_required)
      row.entries.push({
        providerKey: plan.providerKey,
        plan,
        item,
        fact: panelFact,
      })
    }
  }

  return Array.from(rows.values()).sort((left, right) => left.name.localeCompare(right.name))
})

const providerMatches = computed(() => {
  const query = props.query.toLowerCase()
  if (!query.trim()) {
    return []
  }
  return props.providers.filter((provider) => providerMatchesQuery(provider, query))
})

const visibleProviders = computed(() =>
  providerMatches.value.length > 0 ? providerMatches.value : props.providers,
)

const visibleRows = computed(() => {
  const tokens = hospitalQueryTokens(props.query, props.providers)
  if (tokens.length === 0) {
    return hospitalRows.value
  }
  return hospitalRows.value.filter((row) => tokens.every((token) => row.searchText.includes(token)))
})

function cellFor(row, provider) {
  const matches = row.entries.filter((entry) => entry.providerKey === provider.key)
  if (matches.length > 0) {
    const freshMatches = matches.filter((entry) => !isStale(entry.fact))
    const displayMatches = freshMatches.length > 0 ? freshMatches : matches
    return {
      status: freshMatches.length > 0 ? 'yes' : 'stale',
      label: freshMatches.length > 0 ? 'Yes' : 'Stale',
      matches: displayMatches,
      planNames: displayMatches.map((entry) => entry.plan.plan_name).join(', '),
      sourceUrl: displayMatches[0]?.fact?.source_url || displayMatches[0]?.plan?.plan_url || '',
      note: '',
    }
  }

  const providerPlans = providerPlanMap.value[provider.key] || []
  const hasPanelFacts = providerPlans.some(
    (plan) => plan.facts?.panel_hospitals && factItems(plan.facts, 'panel_hospitals').length > 0,
  )
  if (hasPanelFacts) {
    return {
      status: 'no',
      label: 'No',
      matches: [],
      planNames: '',
      sourceUrl: '',
      note: 'Not listed in loaded panel facts',
    }
  }
  return {
    status: 'unknown',
    label: 'Unknown',
    matches: [],
    planNames: '',
    sourceUrl: '',
    note: 'No panel facts loaded',
  }
}

function hospitalKey(item) {
  return item?.canonical_id || slugify(item?.normalized_name || item?.name || itemLabel(item))
}

function hospitalName(item) {
  if (item?.match_status === 'matched' && item?.normalized_name) {
    return item.normalized_name
  }
  return item?.name || item?.normalized_name || itemLabel(item)
}

function hospitalSearchText(item) {
  return [
    item?.name,
    item?.normalized_name,
    item?.matched_alias,
    item?.suggested_normalized_name,
    itemLabel(item),
  ]
    .filter(Boolean)
    .join(' ')
    .toLowerCase()
}

function providerMatchesQuery(provider, query) {
  const providerTerms = [
    provider.key,
    provider.key.replace(/_/g, ' '),
    provider.name,
    provider.name.split(' ')[0],
  ].map((term) => term.toLowerCase())
  return providerTerms.some((term) => term && query.includes(term))
}

function hospitalQueryTokens(query, providerList) {
  let normalized = query.toLowerCase()
  for (const provider of providerList) {
    const terms = [provider.key, provider.key.replace(/_/g, ' '), provider.name]
    for (const term of terms) {
      normalized = normalized.replaceAll(term.toLowerCase(), ' ')
    }
  }
  return normalized
    .replace(/[^a-z0-9]+/g, ' ')
    .split(' ')
    .filter(
      (token) =>
        token.length > 1 &&
        !['is', 'on', 'the', 'panel', 'carrier', 'provider', 'plan', 'plans'].includes(token),
    )
}

function isStale(fact) {
  if (!fact?.last_verified_at) {
    return true
  }
  const verifiedAt = new Date(fact.last_verified_at)
  if (Number.isNaN(verifiedAt.getTime())) {
    return true
  }
  return (Date.now() - verifiedAt.getTime()) / 86400000 > STALE_AFTER_DAYS
}

function slugify(value) {
  return String(value || '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '')
}
</script>

<style scoped>
.matrix-page {
  display: grid;
  gap: 1rem;
  padding: 1.35rem;
  border-radius: 1.25rem;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(16, 39, 71, 0.1);
  box-shadow: 0 24px 60px rgba(16, 39, 71, 0.08);
}

.matrix-top {
  display: flex;
  gap: 1rem;
  justify-content: space-between;
  align-items: end;
}

.eyebrow,
h2 {
  margin: 0;
}

.eyebrow {
  margin-bottom: 0.35rem;
  color: var(--muted-ink);
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.matrix-search {
  width: min(440px, 100%);
  padding: 0.85rem 1rem;
  border: 1px solid rgba(16, 39, 71, 0.14);
  border-radius: 999px;
  background: #ffffff;
}

.legend-row {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.status-pill {
  padding: 0.28rem 0.55rem;
  border-radius: 999px;
  font-size: 0.78rem;
  font-weight: 700;
}

.status-yes,
.cell-yes {
  color: #14532d;
  background: #dcfce7;
}

.status-no,
.cell-no {
  color: #7f1d1d;
  background: #fee2e2;
}

.status-unknown,
.cell-unknown {
  color: #334155;
  background: #e2e8f0;
}

.status-stale,
.cell-stale {
  color: #7c2d12;
  background: #ffedd5;
}

.empty-state {
  color: var(--muted-ink);
}

.matrix-scroll {
  overflow-x: auto;
}

table {
  width: 100%;
  min-width: 920px;
  border-collapse: collapse;
}

th,
td {
  padding: 0.75rem;
  border-bottom: 1px solid rgba(16, 39, 71, 0.08);
  text-align: left;
  vertical-align: top;
}

thead th {
  color: var(--muted-ink);
  font-size: 0.76rem;
  text-transform: uppercase;
}

.hospital-column {
  position: sticky;
  left: 0;
  z-index: 1;
  width: 220px;
  background: rgba(255, 255, 255, 0.98);
}

.hospital-column span,
.hospital-column small {
  display: block;
}

.hospital-column small {
  margin-top: 0.25rem;
  color: #7c2d12;
}

.matrix-cell {
  display: grid;
  gap: 0.25rem;
  min-width: 140px;
  min-height: 76px;
  padding: 0.6rem;
  border-radius: 0.65rem;
}

.matrix-cell span {
  color: inherit;
  font-size: 0.82rem;
}

.matrix-cell a {
  font-size: 0.82rem;
  font-weight: 700;
}

@media (max-width: 720px) {
  .matrix-page {
    padding: 1rem;
  }

  .matrix-top {
    align-items: stretch;
    flex-direction: column;
  }

  .matrix-search {
    width: 100%;
  }
}
</style>
