<template>
  <section v-if="changes.length > 0" class="brochure-changes">
    <h4>{{ t('ui.brochureChanges.title') }}</h4>
    <ul>
      <li v-for="change in sortedChanges" :key="changeKey(change)">
        <div>
          <span class="status-badge">{{ statusText(change) }}</span>
          <strong>{{ dateText(change.change_detected_at) }}</strong>
        </div>
        <p>{{ change.summary || t('ui.brochureChanges.defaultSummary') }}</p>
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
import { useI18n } from '../i18n'

const props = defineProps({
  changes: {
    type: Array,
    default: () => [],
  },
})

const { t } = useI18n()

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
    return t('ui.brochureChanges.alertSent')
  }
  if (change.alert_status === 'suppressed') {
    return t('ui.brochureChanges.suppressed')
  }
  return t('ui.brochureChanges.pending')
}

function dateText(value) {
  return String(value || '').slice(0, 10) || t('ui.brochureChanges.unknownDate')
}
</script>

<style scoped>
.brochure-changes {
  display: grid;
  gap: 0.6rem;
  padding-top: 10px;
  border-top: 1px solid var(--hf-border);
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
  border: 1px solid var(--hf-border);
  border-radius: var(--hf-radius-md);
  background: var(--hf-surface-2);
}

.brochure-changes div {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
  align-items: center;
}

.brochure-changes p {
  color: var(--hf-secondary);
}

.status-badge {
  padding: 0.28rem 0.5rem;
  border-radius: 999px;
  border: 1px solid rgba(250, 204, 21, 0.34);
  background: rgba(124, 45, 18, 0.36);
  color: #fde68a;
  font-size: 0.78rem;
  font-weight: 700;
}
</style>
