<template>
  <section class="status-page" :aria-label="t('ui.scraper.tableLabel')">
    <header class="status-header">
      <p class="status-brand">Be-sure-ance status</p>
      <p>{{ t('ui.scraper.panelCopy') }}</p>
    </header>

    <section :class="['status-notice', `notice-${overallState}`]" aria-live="polite">
      <div>
        <strong>{{ overallTitle }}</strong>
        <span>{{ t('ui.scraper.updated', { date: dateTimeText(lastUpdatedAt) }) }}</span>
      </div>
      <p>{{ overallCopy }}</p>
    </section>

    <section class="carrier-statuses">
      <div class="section-heading">
        <h2>{{ t('ui.scraper.carrierMonitors') }}</h2>
        <span>{{ t('ui.scraper.monitorCount', { count: supportedRows.length }) }}</span>
      </div>

      <article v-for="row in supportedRows" :key="row.carrier_key" class="carrier-status-row">
        <div>
          <strong>{{ row.display_name }}</strong>
          <span>
            {{ t('ui.scraper.rowCount', { count: row.row_count ?? 0 }) }} ·
            {{ t('ui.scraper.lastSuccess') }}: {{ dateText(row.last_success_at) }}
          </span>
        </div>
        <div class="carrier-state">
          <span :class="['state-dot', `dot-${carrierState(row)}`]" aria-hidden="true"></span>
          <strong>{{ carrierStateLabel(row) }}</strong>
        </div>
      </article>
    </section>

    <section class="recent-observations">
      <h2>{{ t('ui.scraper.recentObservations') }}</h2>
      <template v-if="incidentRows.length > 0">
        <article v-for="row in incidentRows" :key="row.carrier_key">
          <p>{{ dateTimeText(row.last_failure_at || row.last_run_at) }}</p>
          <strong>{{ row.display_name }} · {{ carrierStateLabel(row) }}</strong>
          <span>{{ row.last_error || validationText(row) }}</span>
        </article>
      </template>
      <p v-else class="no-incidents">{{ t('ui.scraper.noIncidents') }}</p>
    </section>
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
  return props.providers
    .map((provider) => normalizeRow(rowsByKey.get(provider.key), provider))
    .sort((left, right) => left.display_name.localeCompare(right.display_name))
})

const supportedRows = computed(() =>
  normalizedRows.value.filter((row) => row.support_status === 'supported'),
)

const incidentRows = computed(() =>
  supportedRows.value.filter((row) => ['failing', 'stale'].includes(carrierState(row))),
)

const overallState = computed(() => {
  if (incidentRows.value.some((row) => carrierState(row) === 'failing')) {
    return 'failing'
  }
  if (incidentRows.value.length > 0) {
    return 'stale'
  }
  return 'fresh'
})

const overallTitle = computed(() => {
  const keyByState = {
    fresh: 'ui.scraper.allOperational',
    stale: 'ui.scraper.degraded',
    failing: 'ui.scraper.incident',
  }
  return t(keyByState[overallState.value])
})

const overallCopy = computed(() => {
  if (overallState.value === 'fresh') {
    return t('ui.scraper.allOperationalCopy')
  }
  return t('ui.scraper.incidentCopy', { count: incidentRows.value.length })
})

const lastUpdatedAt = computed(() =>
  supportedRows.value
    .flatMap((row) => [row.last_run_at, row.updated_at, row.last_success_at])
    .filter(Boolean)
    .sort()
    .at(-1),
)

function normalizeRow(row, provider = {}) {
  return {
    carrier_key: row?.carrier_key || provider.key,
    display_name: row?.display_name || provider.name || provider.key,
    support_status: row?.support_status || 'supported',
    last_success_at: row?.last_success_at || '',
    last_failure_at: row?.last_failure_at || '',
    last_run_at: row?.last_run_at || '',
    last_error: row?.last_error || '',
    row_count: row?.row_count ?? 0,
    validation_status: row?.validation_status || 'not_run',
    validation_checked_at: row?.validation_checked_at || '',
    validation_summary: row?.validation_summary || {},
    updated_at: row?.updated_at || '',
  }
}

function carrierState(row) {
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
  }
  return labels[carrierState(row)]
}

function validationText(row) {
  const summary = row.validation_summary || {}
  const status = row.validation_status || 'not_run'
  if (status === 'not_run') {
    return t('ui.scraper.notRun')
  }
  return [
    status.replace('_', ' '),
    t('ui.scraper.targets', { count: summary.total_targets ?? 0 }),
    t('ui.scraper.failed', { count: summary.failed ?? 0 }),
  ].join(' · ')
}

function daysSince(value) {
  const timestamp = new Date(value).getTime()
  if (Number.isNaN(timestamp)) {
    return Number.POSITIVE_INFINITY
  }
  return (Date.now() - timestamp) / 86400000
}

function dateText(value) {
  return String(value || '').slice(0, 10) || t('ui.scraper.notRecorded')
}

function dateTimeText(value) {
  if (!value) {
    return t('ui.scraper.notRecorded')
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return dateText(value)
  }
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date)
}
</script>

<style scoped>
.status-page {
  width: min(880px, 100%);
  margin: 0 auto;
  color: var(--hf-primary);
}

.status-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 24px;
  padding: 8px 0 22px;
  border-bottom: 1px solid var(--hf-border);
}

.status-header p {
  margin: 0;
  color: var(--hf-muted);
  font-size: 14px;
}

.status-header .status-brand {
  color: var(--hf-primary);
  font-weight: 800;
}

.status-notice {
  display: grid;
  gap: 8px;
  margin: 28px 0 34px;
  padding: 14px 16px;
  border: 1px solid var(--hf-border);
  border-left-width: 4px;
}

.status-notice div,
.carrier-state,
.section-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.status-notice strong,
.carrier-state strong {
  font-size: 14px;
}

.status-notice span,
.status-notice p,
.carrier-status-row span,
.recent-observations span,
.section-heading span {
  color: var(--hf-muted);
  font-size: 13px;
}

.status-notice p {
  margin: 0;
}

.notice-fresh {
  border-left-color: var(--hf-primary);
}

.notice-stale {
  border-left-color: var(--hf-warn);
}

.notice-failing {
  border-left-color: var(--hf-error);
}

.section-heading {
  padding-bottom: 10px;
  border-bottom: 1px solid var(--hf-border);
}

.section-heading h2,
.recent-observations h2 {
  margin: 0;
  font-size: 16px;
}

.carrier-status-row {
  display: flex;
  min-height: 62px;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  border-bottom: 1px solid var(--hf-border);
}

.carrier-status-row > div:first-child {
  display: grid;
  gap: 4px;
}

.carrier-status-row > div:first-child strong {
  font-size: 14px;
}

.carrier-state {
  min-width: 112px;
  justify-content: flex-end;
}

.state-dot {
  width: 8px;
  height: 8px;
  background: var(--hf-tertiary);
}

.dot-fresh {
  background: var(--hf-primary);
}

.dot-stale {
  background: var(--hf-warn);
}

.dot-failing {
  background: var(--hf-error);
}

.recent-observations {
  margin-top: 42px;
}

.recent-observations h2 {
  padding-bottom: 10px;
  border-bottom: 1px solid var(--hf-border);
}

.recent-observations article,
.no-incidents {
  display: grid;
  gap: 5px;
  padding: 16px 0;
  border-bottom: 1px solid var(--hf-border);
}

.recent-observations article p,
.no-incidents {
  margin: 0;
  color: var(--hf-muted);
  font-size: 13px;
}

.recent-observations article strong {
  font-size: 14px;
}

@media (max-width: 720px) {
  .status-header,
  .carrier-status-row {
    align-items: flex-start;
    flex-direction: column;
  }

  .carrier-status-row {
    gap: 10px;
    padding: 14px 0;
  }

  .carrier-state {
    justify-content: flex-start;
  }
}
</style>
