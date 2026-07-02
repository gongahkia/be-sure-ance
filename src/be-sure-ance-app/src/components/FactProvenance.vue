<template>
  <div class="provenance-list" :class="{ compact }">
    <p
      v-for="entry in entries"
      :key="entry.key"
      class="provenance-entry"
      :class="{ warning: provenanceState(entry) !== 'Verified' }"
    >
      <span class="provenance-fields">{{ entry.fields.join(', ') }}</span>
      <span>{{ sourceTypeText(entry.sourceType) }}</span>
      <a
        v-if="safeExternalUrl(entry.sourceUrl)"
        :href="safeExternalUrl(entry.sourceUrl)"
        target="_blank"
        rel="noopener noreferrer"
        referrerpolicy="no-referrer"
      >
        {{ externalHostname(entry.sourceUrl) || t('provenance.source') }}
      </a>
      <span v-else>{{ t('provenance.sourceMissing') }}</span>
      <span>{{
        t('provenance.scraped', {
          date: formatFactDate(entry.scrapedAt) || t('provenance.missing'),
        })
      }}</span>
      <span>{{
        t('provenance.verified', {
          date: formatFactDate(entry.lastVerifiedAt) || t('provenance.missing'),
        })
      }}</span>
      <strong v-if="provenanceState(entry) !== 'Verified'">
        {{ provenanceStateText(entry) }}
      </strong>
    </p>
  </div>
</template>

<script setup>
import { externalHostname, safeExternalUrl } from '../utils/links'
import { useI18n } from '../i18n'
import { formatFactDate, provenanceState } from '../utils/planFacts'

defineProps({
  entries: {
    type: Array,
    default: () => [],
  },
  compact: Boolean,
})

const { t } = useI18n()

function sourceTypeText(sourceType) {
  return t(`sourceType.${sourceType || 'source'}`)
}

function provenanceStateText(entry) {
  const keyByState = {
    Verified: 'provenance.state.verified',
    'Source incomplete': 'provenance.state.sourceIncomplete',
    'Verification missing': 'provenance.state.verificationMissing',
    'Stale verification': 'provenance.state.staleVerification',
  }
  return t(keyByState[provenanceState(entry)] || 'provenance.state.sourceIncomplete')
}
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
