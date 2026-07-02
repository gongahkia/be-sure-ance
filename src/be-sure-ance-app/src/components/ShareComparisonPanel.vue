<template>
  <section class="share-panel">
    <div>
      <p class="eyebrow">Share Link</p>
      <h2>Save comparison set</h2>
    </div>

    <div class="share-actions">
      <button type="button" :disabled="selectedPlans.length === 0 || sharing" @click="createShare">
        {{ sharing ? 'Saving link' : 'Create share link' }}
      </button>
      <a
        v-if="safeExternalUrl(shareUrl)"
        :href="safeExternalUrl(shareUrl)"
        target="_blank"
        rel="noopener noreferrer"
        referrerpolicy="no-referrer"
      >
        Open share link
      </a>
    </div>

    <p v-if="statusMessage" class="share-status">{{ statusMessage }}</p>
  </section>
</template>

<script setup>
import { ref } from 'vue'

import { safeExternalUrl } from '../utils/links'

const props = defineProps({
  selectedPlans: {
    type: Array,
    default: () => [],
  },
})

const sharing = ref(false)
const statusMessage = ref('')
const shareUrl = ref('')

function createShare() {
  if (props.selectedPlans.length === 0) {
    statusMessage.value = 'Select at least one plan.'
    return
  }

  sharing.value = true
  statusMessage.value = ''
  shareUrl.value = ''
  try {
    const refs = props.selectedPlans.map(sharePlanPayload).filter(Boolean)
    shareUrl.value = absoluteShareUrl(`/share?plans=${encodeURIComponent(refs.join(','))}`)
    statusMessage.value = 'Share link ready.'
  } catch (error) {
    statusMessage.value = error?.message || 'Share link failed.'
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
  gap: 1rem;
  padding: 1.35rem;
  border-radius: 1.25rem;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(16, 39, 71, 0.1);
  box-shadow: 0 24px 60px rgba(16, 39, 71, 0.08);
}

.eyebrow,
h2 {
  margin: 0;
}

.eyebrow {
  margin-bottom: 0.35rem;
  color: var(--muted-ink);
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.share-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  align-items: center;
}

button {
  min-height: 42px;
  padding: 0.75rem 1rem;
  border: 0;
  border-radius: 0.7rem;
  background: var(--ink);
  color: #ffffff;
  font-weight: 700;
}

button:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.share-actions a {
  font-weight: 700;
}

.share-status {
  margin: 0;
  color: var(--muted-ink);
  font-size: 0.84rem;
}
</style>
