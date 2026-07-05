<template>
  <section class="share-panel" :class="{ compact }">
    <div v-if="!compact" class="panel-heading">
      <p>{{ t('ui.share.eyebrow') }}</p>
      <h2>{{ t('ui.share.title') }}</h2>
    </div>

    <div class="share-actions">
      <button type="button" :disabled="selectedPlans.length === 0 || sharing" @click="createShare">
        {{ sharing ? t('ui.share.saving') : compact ? t('ui.share.share') : t('ui.share.create') }}
      </button>
      <a
        v-if="safeExternalUrl(shareUrl)"
        class="hub-link-button"
        :href="safeExternalUrl(shareUrl)"
        target="_blank"
        rel="noopener noreferrer"
        referrerpolicy="no-referrer"
      >
        {{ t('ui.share.open') }}
      </a>
    </div>

    <p v-if="statusMessage && !compact" class="share-status">{{ statusMessage }}</p>
  </section>
</template>

<script setup>
import { ref } from 'vue'

import { useI18n } from '../i18n'
import { safeExternalUrl } from '../utils/links'

const props = defineProps({
  selectedPlans: {
    type: Array,
    default: () => [],
  },
  compact: Boolean,
})

const sharing = ref(false)
const statusMessage = ref('')
const shareUrl = ref('')
const { t } = useI18n()

function createShare() {
  if (props.selectedPlans.length === 0) {
    statusMessage.value = t('ui.pdf.selectOne')
    return
  }

  sharing.value = true
  statusMessage.value = ''
  shareUrl.value = ''
  try {
    const refs = props.selectedPlans.map(sharePlanPayload).filter(Boolean)
    shareUrl.value = absoluteShareUrl(`/share?plans=${encodeURIComponent(refs.join(','))}`)
    statusMessage.value = t('ui.share.ready')
  } catch (error) {
    statusMessage.value = error?.message || t('ui.share.failed')
  } finally {
    sharing.value = false
  }
}

function sharePlanPayload(plan) {
  const insurer = plan.insurer || plan.providerKey
  const planSlug = plan.plan_slug
  return safePlanRef(insurer) && safePlanRef(planSlug) ? `${insurer}:${planSlug}` : ''
}

function absoluteShareUrl(path) {
  return new URL(path, window.location.origin).toString()
}

function safePlanRef(value) {
  return /^[a-z0-9][a-z0-9_-]{0,119}$/.test(String(value || ''))
}
</script>

<style scoped>
.share-panel {
  display: grid;
  gap: 14px;
  padding: 18px;
  border: 1px solid var(--hf-border);
  border-radius: var(--hf-radius-lg);
  background: var(--hf-surface);
}

.share-panel.compact {
  display: block;
  padding: 0;
  border: 0;
  background: transparent;
}

.panel-heading p,
.panel-heading h2,
.share-status {
  margin: 0;
}

.panel-heading p,
.share-status {
  color: var(--hf-muted);
  font-size: 14px;
}

.share-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

button {
  min-height: 40px;
  padding: 8px 14px;
  border: 1px solid var(--hf-border);
  border-radius: var(--hf-radius-full);
  background: transparent;
  color: var(--hf-primary);
  font-weight: 700;
}

button:hover {
  border-color: var(--hf-tertiary);
}

button:disabled {
  opacity: 0.5;
}
</style>
