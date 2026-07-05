<template>
  <section v-if="events.length > 0" class="regulatory-events">
    <h4>{{ t('ui.regulatory.title') }}</h4>
    <ul>
      <li v-for="event in sortedEvents" :key="eventKey(event)">
        <div>
          <span class="status-badge">{{ statusText(event) }}</span>
          <strong>{{ event.event_title }}</strong>
        </div>
        <p>{{ eventSummary(event) }}</p>
        <a
          v-if="safeExternalUrl(event.source_url)"
          :href="safeExternalUrl(event.source_url)"
          target="_blank"
          rel="noopener noreferrer"
          referrerpolicy="no-referrer"
        >
          {{ externalHostname(event.source_url) }} · {{ event.event_date }}
        </a>
      </li>
    </ul>
  </section>
</template>

<script setup>
import { computed } from 'vue'

import { useI18n } from '../i18n'
import { externalHostname, safeExternalUrl } from '../utils/links'

const props = defineProps({
  events: {
    type: Array,
    default: () => [],
  },
})

const { t } = useI18n()

const sortedEvents = computed(() =>
  [...props.events]
    .sort((left, right) =>
      String(right.event_date || '').localeCompare(String(left.event_date || '')),
    )
    .slice(0, 3),
)

function eventKey(event) {
  return [event.carrier_key, event.event_title, event.source_url].join(':')
}

function statusText(event) {
  return event.match_status === 'matched'
    ? t('ui.regulatory.sourceMatch')
    : t('ui.regulatory.needsReview')
}

function eventSummary(event) {
  return event.match_status === 'matched'
    ? event.summary
    : t('ui.regulatory.possibleMatch', { alias: event.matched_alias })
}
</script>

<style scoped>
.regulatory-events {
  display: grid;
  gap: 0.6rem;
  padding-top: 10px;
  border-top: 1px solid var(--hf-border);
}

.regulatory-events h4,
.regulatory-events p,
.regulatory-events ul {
  margin: 0;
}

.regulatory-events ul {
  display: grid;
  gap: 0.65rem;
  padding-left: 0;
  list-style: none;
}

.regulatory-events li {
  display: grid;
  gap: 0.35rem;
  padding: 0.75rem;
  border: 1px solid var(--hf-border);
  border-radius: var(--hf-radius-md);
  background: var(--hf-surface-2);
}

.regulatory-events div {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
  align-items: center;
}

.regulatory-events p {
  color: var(--hf-secondary);
}

.status-badge {
  padding: 0.28rem 0.5rem;
  border-radius: 999px;
  border: 1px solid var(--hf-border);
  background: var(--hf-neutral);
  color: var(--hf-secondary);
  font-size: 0.78rem;
  font-weight: 700;
}
</style>
