<template>
  <section class="matrix-page">
    <div class="matrix-top">
      <div>
        <p class="eyebrow">{{ t('ui.matrix.eyebrow') }}</p>
        <h2>{{ t('ui.matrix.title') }}</h2>
      </div>
      <input
        v-model="searchModel"
        class="matrix-search"
        type="search"
        :placeholder="t('ui.matrix.placeholder')"
      />
    </div>

    <div v-if="hospitalRows.length === 0" class="empty-state">
      {{ t('ui.matrix.empty') }}
    </div>

    <div v-else-if="visibleRows.length === 0" class="empty-state">
      {{ t('ui.matrix.noMatch') }}
    </div>

    <div v-else class="matrix-scroll">
      <table>
        <thead>
          <tr>
            <th class="hospital-column">{{ t('ui.matrix.hospital') }}</th>
            <th v-for="provider in visibleProviders" :key="provider.key">
              {{ provider.name }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in visibleRows" :key="row.key">
            <th class="hospital-column" scope="row">
              <span>{{ row.name }}</span>
              <small v-if="row.reviewRequired">{{ t('ui.matrix.review') }}</small>
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
                    {{ t('ui.matrix.source') }}
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

import { useI18n } from '../i18n'
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
const { t } = useI18n()

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
      label: freshMatches.length > 0 ? t('ui.matrix.yes') : t('ui.matrix.stale'),
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
      label: t('ui.matrix.no'),
      matches: [],
      planNames: '',
      sourceUrl: '',
      note: t('ui.matrix.notListed'),
    }
  }
  return {
    status: 'unknown',
    label: t('ui.matrix.unknown'),
    matches: [],
    planNames: '',
    sourceUrl: '',
    note: t('ui.matrix.noFacts'),
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
  border-top: 1px solid var(--hf-border);
  border-bottom: 1px solid var(--hf-border);
}

.matrix-top {
  display: flex;
  gap: 1rem;
  align-items: end;
  justify-content: space-between;
  padding: 18px 0;
  border-bottom: 1px solid var(--hf-border);
}

.eyebrow,
h2 {
  margin: 0;
}

.eyebrow {
  margin-bottom: 0.35rem;
  color: var(--hf-muted);
  font-size: 0.78rem;
  font-weight: 700;
}

.matrix-search {
  width: min(440px, 100%);
  padding: 0.85rem 1rem;
  border: 1px solid var(--hf-border);
  border-radius: 0;
  background: transparent;
  color: var(--hf-primary);
}

.empty-state {
  padding: 18px 0;
  color: var(--hf-secondary);
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
  border-right: 1px solid var(--hf-border);
  border-bottom: 1px solid var(--hf-border);
  text-align: left;
  vertical-align: top;
}

th {
  padding: 0.75rem;
}

td {
  padding: 0;
}

th:last-child,
td:last-child {
  border-right: 0;
}

thead th {
  color: var(--hf-muted);
  font-size: 0.76rem;
}

.hospital-column {
  position: sticky;
  left: 0;
  z-index: 1;
  width: 220px;
  background: var(--hf-neutral);
}

.hospital-column span,
.hospital-column small {
  display: block;
}

.hospital-column small {
  margin-top: 0.25rem;
  color: var(--hf-muted);
}

.matrix-cell {
  display: grid;
  min-width: 140px;
  min-height: 100%;
  gap: 0.25rem;
  padding: 0.75rem;
  border-left: 3px solid var(--hf-border);
}

.cell-yes {
  color: var(--hf-primary);
  border-left-color: var(--hf-primary);
}

.cell-no {
  color: var(--hf-secondary);
  border-left-color: var(--hf-secondary);
}

.cell-unknown {
  color: var(--hf-secondary);
  border-left-color: var(--hf-tertiary);
}

.cell-stale {
  color: var(--hf-muted);
  border-left-color: var(--hf-muted);
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
  .matrix-top {
    align-items: stretch;
    flex-direction: column;
  }

  .matrix-search {
    width: 100%;
  }
}
</style>
