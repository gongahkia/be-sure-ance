<template>
  <section class="scraper-status-panel">
    <div class="section-top">
      <div>
        <p class="eyebrow">Scraper Health</p>
        <h2>Carrier freshness and validation</h2>
      </div>
      <p class="section-copy">
        Public operational metadata: row counts, last run timestamps, and structural validation
        summaries.
      </p>
    </div>

    <div class="status-summary" aria-label="Scraper health summary">
      <article v-for="item in summaryCounts" :key="item.key">
        <span>{{ item.label }}</span>
        <strong>{{ item.count }}</strong>
      </article>
    </div>

    <div class="status-table-wrap" tabindex="0" aria-label="Carrier scraper health table">
      <table>
        <thead>
          <tr>
            <th>Carrier</th>
            <th>Status</th>
            <th>Rows</th>
            <th>Last success</th>
            <th>Last failure</th>
            <th>Validation</th>
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
    { key: 'errorRate', label: 'Error rate', count: errorRate(counts) },
    { key: 'fresh', label: 'Fresh', count: counts.fresh },
    { key: 'stale', label: 'Stale', count: counts.stale },
    { key: 'failing', label: 'Failing', count: counts.failing },
    { key: 'unsupported', label: 'Unsupported', count: counts.unsupported },
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
    fresh: 'Fresh',
    stale: 'Stale',
    failing: 'Failing',
    unsupported: 'Unsupported',
  }
  return labels[carrierState(row)]
}

function validationText(row) {
  const summary = row.validation_summary || {}
  const status = row.validation_status || 'not_run'
  if (status === 'unsupported') {
    return 'Unsupported scraper'
  }
  if (status === 'not_run') {
    return 'Not run'
  }
  const parts = [
    status.replace('_', ' '),
    `${summary.total_targets ?? 0} targets`,
    `${summary.failed ?? 0} failed`,
    `${summary.errors ?? 0} errors`,
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
  return String(value || '').slice(0, 10) || 'Not recorded'
}
</script>

<style scoped>
.scraper-status-panel {
  display: grid;
  gap: 1rem;
  padding: 1.25rem;
  border-radius: 1.25rem;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(16, 39, 71, 0.08);
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
  color: var(--muted-ink);
}

.status-summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.75rem;
}

.status-summary article {
  padding: 0.9rem;
  border-radius: 0.9rem;
  background: #f4f7fb;
}

.status-summary span {
  display: block;
  color: var(--muted-ink);
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
  outline: 3px solid #2f73c7;
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
  border-bottom: 1px solid rgba(16, 39, 71, 0.08);
  text-align: left;
  vertical-align: top;
}

td span {
  display: block;
  margin-top: 0.15rem;
  color: var(--muted-ink);
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
  background: #e3f8ed;
  color: #166237;
}

.status-stale {
  background: #fff4d6;
  color: #76540f;
}

.status-failing {
  background: #ffe4e8;
  color: #8a1f32;
}

.status-unsupported {
  background: #edf1f6;
  color: #4f6275;
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
