<template>
  <div class="provenance-list" :class="{ compact }">
    <p
      v-for="entry in entries"
      :key="entry.key"
      class="provenance-entry"
      :class="{ warning: provenanceState(entry) !== 'Verified' }"
    >
      <span class="provenance-fields">{{ fieldText(entry) }}</span>
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

function fieldText(entry) {
  const fieldKeys = entry.fieldKeys || []
  if (fieldKeys.length === 0) {
    return entry.fields.join(', ')
  }
  return fieldKeys.map(fieldLabelText).join(', ')
}

function fieldLabelText(fieldKey) {
  const translated = t(`field.${fieldKey}`)
  return translated.startsWith('[missing:') ? fieldKey : translated
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
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.provenance-entry {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 4px 8px;
  align-items: center;
  margin: 0;
  padding: 4px 8px;
  border: 1px solid var(--hf-border);
  border-radius: var(--hf-radius-full);
  background: var(--hf-surface-2);
  color: var(--hf-muted);
  font-size: 12px;
  line-height: 16px;
}

.provenance-entry span,
.provenance-entry a,
.provenance-entry strong {
  overflow-wrap: anywhere;
}

.provenance-entry.warning strong {
  color: #fde68a;
}

.provenance-fields {
  font-weight: 700;
  color: var(--hf-secondary);
}

.compact {
  margin-top: 6px;
}

.compact .provenance-entry {
  gap: 4px 6px;
  font-size: 12px;
}
</style>
