<template>
  <section v-if="changes.length > 0" class="brochure-changes">
    <h4>Brochure changes</h4>
    <ul>
      <li v-for="change in sortedChanges" :key="changeKey(change)">
        <div>
          <span class="status-badge">{{ statusText(change) }}</span>
          <strong>{{ dateText(change.change_detected_at) }}</strong>
        </div>
        <p>{{ change.summary || 'Brochure hash changed; review source document.' }}</p>
        <a
          v-if="safeExternalUrl(change.source_url)"
          :href="safeExternalUrl(change.source_url)"
          target="_blank"
          rel="noopener noreferrer"
          referrerpolicy="no-referrer"
        >
          {{ externalHostname(change.source_url) }} · {{ dateText(change.current_captured_at) }}
        </a>
      </li>
    </ul>
  </section>
</template>

<script setup>
import { computed } from 'vue'

import { externalHostname, safeExternalUrl } from '../utils/links'

const props = defineProps({
  changes: {
    type: Array,
    default: () => [],
  },
})

const sortedChanges = computed(() =>
  [...props.changes]
    .sort((left, right) =>
      String(right.change_detected_at || '').localeCompare(String(left.change_detected_at || '')),
    )
    .slice(0, 3),
)

function changeKey(change) {
  return [change.insurer, change.plan_slug, change.previous_sha256, change.current_sha256].join(':')
}

function statusText(change) {
  if (change.alert_status === 'sent') {
    return 'Alert sent'
  }
  if (change.alert_status === 'suppressed') {
    return 'Suppressed'
  }
  return 'Pending alert hook'
}

function dateText(value) {
  return String(value || '').slice(0, 10) || 'Unknown date'
}
</script>

<style scoped>
.brochure-changes {
  display: grid;
  gap: 0.6rem;
}

.brochure-changes h4,
.brochure-changes p,
.brochure-changes ul {
  margin: 0;
}

.brochure-changes ul {
  display: grid;
  gap: 0.65rem;
  padding-left: 0;
  list-style: none;
}

.brochure-changes li {
  display: grid;
  gap: 0.35rem;
  padding: 0.75rem;
  border: 1px solid rgba(16, 39, 71, 0.08);
  border-radius: 0.75rem;
}

.brochure-changes div {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
  align-items: center;
}

.brochure-changes p {
  color: var(--muted-ink);
}

.status-badge {
  padding: 0.28rem 0.5rem;
  border-radius: 999px;
  background: rgba(219, 234, 194, 0.9);
  color: #355118;
  font-size: 0.78rem;
  font-weight: 700;
}
</style>
