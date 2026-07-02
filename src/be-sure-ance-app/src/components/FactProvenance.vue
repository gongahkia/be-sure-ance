<template>
  <div class="provenance-list" :class="{ compact }">
    <p
      v-for="entry in entries"
      :key="entry.key"
      class="provenance-entry"
      :class="{ warning: provenanceState(entry) !== 'Verified' }"
    >
      <span class="provenance-fields">{{ entry.fields.join(', ') }}</span>
      <span>{{ sourceTypeLabel(entry.sourceType) }}</span>
      <a
        v-if="safeExternalUrl(entry.sourceUrl)"
        :href="safeExternalUrl(entry.sourceUrl)"
        target="_blank"
        rel="noopener noreferrer"
        referrerpolicy="no-referrer"
      >
        {{ externalHostname(entry.sourceUrl) || 'source' }}
      </a>
      <span v-else>Source URL missing</span>
      <span>Scraped {{ formatFactDate(entry.scrapedAt) || 'missing' }}</span>
      <span>Verified {{ formatFactDate(entry.lastVerifiedAt) || 'missing' }}</span>
      <strong v-if="provenanceState(entry) !== 'Verified'">
        {{ provenanceState(entry) }}
      </strong>
    </p>
  </div>
</template>

<script setup>
import { externalHostname, safeExternalUrl } from '../utils/links'
import { formatFactDate, provenanceState, sourceTypeLabel } from '../utils/planFacts'

defineProps({
  entries: {
    type: Array,
    default: () => [],
  },
  compact: Boolean,
})
</script>

<style scoped>
.provenance-list {
  display: grid;
  gap: 0.35rem;
  margin-top: 0.55rem;
}

.provenance-entry {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem 0.55rem;
  margin: 0;
  color: var(--muted-ink);
  font-size: 0.78rem;
  line-height: 1.35;
}

.provenance-entry span,
.provenance-entry a,
.provenance-entry strong {
  overflow-wrap: anywhere;
}

.provenance-entry.warning strong {
  color: #7a1d21;
}

.provenance-fields {
  font-weight: 700;
  color: var(--ink);
}

.compact {
  margin-top: 0.35rem;
}

.compact .provenance-entry {
  display: grid;
  gap: 0.15rem;
  font-size: 0.74rem;
}
</style>
