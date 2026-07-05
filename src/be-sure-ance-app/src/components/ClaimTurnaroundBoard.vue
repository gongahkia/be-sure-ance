<template>
  <section class="claim-board hub-panel" :class="{ compact }">
    <div class="section-top">
      <div>
        <p class="eyebrow">{{ t('ui.claims.eyebrow') }}</p>
        <h2>{{ t('ui.claims.title') }}</h2>
      </div>
      <p class="section-copy">{{ t('ui.claims.copy') }}</p>
    </div>

    <div v-if="displayMetrics.length === 0" class="empty-state">{{ t('ui.claims.empty') }}</div>

    <div v-else class="claim-table">
      <table>
        <thead>
          <tr>
            <th>{{ t('ui.claims.metric') }}</th>
            <th>{{ t('ui.claims.scope') }}</th>
            <th>{{ t('ui.claims.value') }}</th>
            <th>{{ t('ui.claims.rank') }}</th>
            <th>{{ t('ui.claims.source') }}</th>
            <th>{{ t('ui.claims.limitations') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="metric in displayMetrics" :key="metricKey(metric)">
            <td>{{ metric.metric_label }}</td>
            <td>{{ metric.carrier_name }}</td>
            <td>{{ metricValue(metric) }}</td>
            <td>{{ rankText(metric) }}</td>
            <td>
              <a
                v-if="safeExternalUrl(metric.source_url)"
                :href="safeExternalUrl(metric.source_url)"
                target="_blank"
                rel="noopener noreferrer"
                referrerpolicy="no-referrer"
              >
                {{ externalHostname(metric.source_url) }} · {{ metric.source_year }}
              </a>
              <span v-else>{{ metric.source_year }}</span>
            </td>
            <td>{{ limitationText(metric) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'

import { useI18n } from '../i18n'
import { externalHostname, safeExternalUrl } from '../utils/links'

const props = defineProps({
  metrics: {
    type: Array,
    default: () => [],
  },
  compact: Boolean,
})

const { t } = useI18n()

const sortedMetrics = computed(() =>
  [...props.metrics].sort(
    (left, right) =>
      Number(right.source_year || 0) - Number(left.source_year || 0) ||
      String(left.metric_label || '').localeCompare(String(right.metric_label || '')),
  ),
)

const displayMetrics = computed(() =>
  props.compact ? sortedMetrics.value.slice(0, 4) : sortedMetrics.value,
)

function metricKey(metric) {
  return [metric.carrier_key, metric.metric_key, metric.source_year, metric.source_url].join(':')
}

function metricValue(metric) {
  const value = metric.metric_value?.value || {}
  if (value.days !== undefined) {
    return t('ui.claims.days', { count: value.days })
  }
  if (value.months !== undefined) {
    return t('ui.claims.months', { count: value.months })
  }
  if (value.amount_sgd_billion !== undefined) {
    return `S$${value.amount_sgd_billion}b`
  }
  return metric.metric_value?.status || t('ui.matrix.unknown')
}

function rankText(metric) {
  return metric.rank ? `#${metric.rank}` : t('ui.claims.notRanked')
}

function limitationText(metric) {
  return (metric.limitations || []).join(' ')
}
</script>

<style scoped>
.claim-board {
  display: grid;
  gap: 1rem;
  padding: 18px;
}

.claim-board.compact {
  padding: 18px;
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
  color: var(--hf-muted);
}

h2,
.section-copy {
  margin: 0;
}

.section-copy,
.empty-state {
  color: var(--hf-secondary);
}

.claim-table {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th,
td {
  padding: 0.85rem;
  border-bottom: 1px solid var(--hf-border);
  text-align: left;
  vertical-align: top;
}

th {
  color: var(--hf-muted);
  font-size: 0.82rem;
}

td {
  min-width: 9rem;
}

@media (max-width: 720px) {
  .section-top {
    flex-direction: column;
    align-items: start;
  }
}
</style>
