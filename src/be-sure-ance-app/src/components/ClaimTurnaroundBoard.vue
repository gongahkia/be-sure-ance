<template>
  <section class="claim-board">
    <div class="section-top">
      <div>
        <p class="eyebrow">Claims</p>
        <h2>Claim turnaround evidence board</h2>
      </div>
      <p class="section-copy">LIA rows are industry-level evidence, not suitability rankings.</p>
    </div>

    <div v-if="sortedMetrics.length === 0" class="empty-state">No LIA claim metrics loaded.</div>

    <div v-else class="claim-table">
      <table>
        <thead>
          <tr>
            <th>Metric</th>
            <th>Scope</th>
            <th>Value</th>
            <th>Rank</th>
            <th>Source</th>
            <th>Limitations</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="metric in sortedMetrics" :key="metricKey(metric)">
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

import { externalHostname, safeExternalUrl } from '../utils/links'

const props = defineProps({
  metrics: {
    type: Array,
    default: () => [],
  },
})

const sortedMetrics = computed(() =>
  [...props.metrics].sort(
    (left, right) =>
      Number(right.source_year || 0) - Number(left.source_year || 0) ||
      String(left.metric_label || '').localeCompare(String(right.metric_label || '')),
  ),
)

function metricKey(metric) {
  return [metric.carrier_key, metric.metric_key, metric.source_year, metric.source_url].join(':')
}

function metricValue(metric) {
  const value = metric.metric_value?.value || {}
  if (value.days !== undefined) {
    return `${value.days} days`
  }
  if (value.months !== undefined) {
    return `${value.months} months`
  }
  if (value.amount_sgd_billion !== undefined) {
    return `S$${value.amount_sgd_billion}b`
  }
  return metric.metric_value?.status || 'Unknown'
}

function rankText(metric) {
  return metric.rank ? `#${metric.rank}` : 'Not ranked by LIA source'
}

function limitationText(metric) {
  return (metric.limitations || []).join(' ')
}
</script>

<style scoped>
.claim-board {
  display: grid;
  gap: 1rem;
  padding: 1.35rem;
  border-radius: 1.25rem;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(16, 39, 71, 0.1);
  box-shadow: 0 24px 60px rgba(16, 39, 71, 0.08);
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
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--muted-ink);
}

h2,
.section-copy {
  margin: 0;
}

.section-copy,
.empty-state {
  color: var(--muted-ink);
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
  border-bottom: 1px solid rgba(16, 39, 71, 0.08);
  text-align: left;
  vertical-align: top;
}

th {
  color: var(--muted-ink);
  font-size: 0.82rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
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
