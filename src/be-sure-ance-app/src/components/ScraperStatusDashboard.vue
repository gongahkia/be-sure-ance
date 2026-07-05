<template>
  <section class="scraper-status-panel hub-panel">
    <div class="section-top">
      <div>
        <p class="eyebrow">{{ t('ui.scraper.eyebrow') }}</p>
        <h2>{{ t('ui.scraper.panelTitle') }}</h2>
      </div>
      <p class="section-copy">{{ t('ui.scraper.panelCopy') }}</p>
    </div>

    <div class="status-summary" :aria-label="t('ui.scraper.summaryLabel')">
      <article v-for="item in summaryCounts" :key="item.key">
        <span>{{ item.label }}</span>
        <strong>{{ item.count }}</strong>
      </article>
    </div>

    <div class="status-table-wrap" tabindex="0" :aria-label="t('ui.scraper.tableLabel')">
      <table>
        <thead>
          <tr>
            <th>{{ t('ui.scraper.carrier') }}</th>
            <th>{{ t('ui.scraper.status') }}</th>
            <th>{{ t('ui.scraper.rows') }}</th>
            <th>{{ t('ui.scraper.lastSuccess') }}</th>
            <th>{{ t('ui.scraper.lastFailure') }}</th>
            <th>{{ t('ui.scraper.validation') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in normalizedRows" :key="row.carrier_key">
            <td>
              <strong>{{ row.display_name }}</strong>
              <span>{{ row.carrier_key }}</span>
            </td>
            <td>
              <span class="status-pill" :class="`status-${carrierState(row)}`">
                {{ carrierStateLabel(row) }}
              </span>
            </td>
            <td>{{ row.row_count ?? 0 }}</td>
            <td>{{ dateText(row.last_success_at) }}</td>
            <td>{{ dateText(row.last_failure_at) }}</td>
            <td>{{ validationText(row) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'

import { useI18n } from '../i18n'

const STALE_AFTER_DAYS = 8

const props = defineProps({
  healthRows: {
    type: Array,
    default: () => [],
  },
  providers: {
    type: Array,
    default: () => [],
  },
})

const { t } = useI18n()

const normalizedRows = computed(() => {
  const rowsByKey = new Map(props.healthRows.map((row) => [row.carrier_key, row]))
  const providerRows = props.providers.map((provider) =>
    normalizeRow(rowsByKey.get(provider.key), provider),
  )
  const providerKeys = new Set(props.providers.map((provider) => provider.key))
  const extraRows = props.healthRows
    .filter((row) => row?.carrier_key && !providerKeys.has(row.carrier_key))
    .map((row) => normalizeRow(row))
  return [...providerRows, ...extraRows].sort((left, right) =>
    left.display_name.localeCompare(right.display_name),
  )
})

const summaryCounts = computed(() => {
  const counts = { fresh: 0, stale: 0, failing: 0, unsupported: 0 }
  for (const row of normalizedRows.value) {
    counts[carrierState(row)] += 1
  }
  return [
    { key: 'errorRate', label: t('ui.scraper.errorRate'), count: errorRate(counts) },
    { key: 'fresh', label: t('ui.scraper.fresh'), count: counts.fresh },
    { key: 'stale', label: t('ui.scraper.stale'), count: counts.stale },
    { key: 'failing', label: t('ui.scraper.failing'), count: counts.failing },
    { key: 'unsupported', label: t('ui.scraper.unsupported'), count: counts.unsupported },
  ]
})

function normalizeRow(row, provider = {}) {
  return {
    carrier_key: row?.carrier_key || provider.key,
    display_name: row?.display_name || provider.name || provider.key,
    support_status: row?.support_status || 'supported',
    last_success_at: row?.last_success_at || '',
    last_failure_at: row?.last_failure_at || '',
    last_run_at: row?.last_run_at || '',
    row_count: row?.row_count ?? 0,
    validation_status: row?.validation_status || 'not_run',
    validation_checked_at: row?.validation_checked_at || '',
    validation_summary: row?.validation_summary || {},
  }
}

function errorRate(counts) {
  const supportedTotal = counts.fresh + counts.stale + counts.failing
  if (supportedTotal === 0) {
    return '0%'
  }
  return `${Math.round((counts.failing / supportedTotal) * 100)}%`
}

function carrierState(row) {
  if (row.support_status !== 'supported') {
    return 'unsupported'
  }
  if (
    row.last_failure_at &&
    (!row.last_success_at || new Date(row.last_failure_at) > new Date(row.last_success_at))
  ) {
    return 'failing'
  }
  if (['failed', 'error'].includes(row.validation_status)) {
    return 'failing'
  }
  if (!row.last_success_at || daysSince(row.last_success_at) > STALE_AFTER_DAYS) {
    return 'stale'
  }
  return 'fresh'
}

function carrierStateLabel(row) {
  const labels = {
    fresh: t('ui.scraper.fresh'),
    stale: t('ui.scraper.stale'),
    failing: t('ui.scraper.failing'),
    unsupported: t('ui.scraper.unsupported'),
  }
  return labels[carrierState(row)]
}

function validationText(row) {
  const summary = row.validation_summary || {}
  const status = row.validation_status || 'not_run'
  if (status === 'unsupported') {
    return t('ui.scraper.unsupportedScraper')
  }
  if (status === 'not_run') {
    return t('ui.scraper.notRun')
  }
  const parts = [
    status.replace('_', ' '),
    t('ui.scraper.targets', { count: summary.total_targets ?? 0 }),
    t('ui.scraper.failed', { count: summary.failed ?? 0 }),
    t('ui.scraper.errors', { count: summary.errors ?? 0 }),
  ]
  return parts.join(' · ')
}

function daysSince(value) {
  const timestamp = new Date(value).getTime()
  if (Number.isNaN(timestamp)) {
    return Number.POSITIVE_INFINITY
  }
  return (Date.now() - timestamp) / (1000 * 60 * 60 * 24)
}

function dateText(value) {
  return String(value || '').slice(0, 10) || t('ui.scraper.notRecorded')
}
</script>

<style scoped>
.scraper-status-panel {
  display: grid;
  gap: 1rem;
  padding: 18px;
}

.section-top {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
}

.section-top h2,
.section-copy {
  margin: 0;
}

.section-copy {
  max-width: 38rem;
  color: var(--hf-secondary);
}

.status-summary {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 0.75rem;
}

.status-summary article {
  padding: 0.9rem;
  border: 1px solid var(--hf-border);
  border-radius: var(--hf-radius-lg);
  background: var(--hf-surface-2);
}

.status-summary span {
  display: block;
  color: var(--hf-muted);
  font-weight: 700;
}

.status-summary strong {
  display: block;
  margin-top: 0.3rem;
  font-size: 1.5rem;
}

.status-table-wrap {
  overflow-x: auto;
}

.status-table-wrap:focus {
  outline: 2px solid rgba(255, 204, 77, 0.78);
  outline-offset: 0.2rem;
}

table {
  width: 100%;
  border-collapse: collapse;
  min-width: 820px;
}

th,
td {
  padding: 0.8rem;
  border-bottom: 1px solid var(--hf-border);
  text-align: left;
  vertical-align: top;
}

td span {
  display: block;
  margin-top: 0.15rem;
  color: var(--hf-muted);
  font-size: 0.84rem;
}

.status-pill {
  display: inline-block;
  margin: 0;
  padding: 0.3rem 0.5rem;
  border-radius: 999px;
  font-weight: 800;
}

.status-fresh {
  background: rgba(22, 101, 52, 0.36);
  color: #bbf7d0;
}

.status-stale {
  background: rgba(124, 45, 18, 0.36);
  color: #fde68a;
}

.status-failing {
  background: rgba(127, 29, 29, 0.36);
  color: #fecdd3;
}

.status-unsupported {
  background: var(--hf-surface-2);
  color: var(--hf-secondary);
}

@media (max-width: 780px) {
  .section-top,
  .status-summary {
    grid-template-columns: 1fr;
  }

  .section-top {
    display: grid;
  }
}
</style>
