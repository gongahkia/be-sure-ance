<template>
  <section class="brief-export" :class="{ compact }">
    <div v-if="!compact" class="panel-heading">
      <p>{{ t('ui.pdf.eyebrow') }}</p>
      <h2>{{ t('ui.pdf.title') }}</h2>
    </div>

    <details v-if="compact" class="compact-export">
      <summary class="hub-button primary">{{ t('ui.pdf.download') }}</summary>
      <div class="brief-fields popover-fields">
        <label>
          <span>{{ t('ui.pdf.agent') }}</span>
          <input v-model="agentName" type="text" autocomplete="off" />
        </label>
        <label>
          <span>{{ t('ui.pdf.rep') }}</span>
          <input v-model="masRepNumber" type="text" autocomplete="off" />
        </label>
        <button
          type="button"
          :disabled="selectedPlans.length === 0 || exporting"
          @click="downloadPdf"
        >
          {{ exporting ? t('ui.pdf.preparing') : t('ui.pdf.export') }}
        </button>
      </div>
    </details>

    <div v-else class="brief-fields">
      <label>
        <span>{{ t('ui.pdf.agent') }}</span>
        <input v-model="agentName" type="text" autocomplete="off" />
      </label>
      <label>
        <span>{{ t('ui.pdf.rep') }}</span>
        <input v-model="masRepNumber" type="text" autocomplete="off" />
      </label>
      <button
        type="button"
        :disabled="selectedPlans.length === 0 || exporting"
        @click="downloadPdf"
      >
        {{ exporting ? t('ui.pdf.preparingPdf') : t('ui.pdf.download') }}
      </button>
    </div>

    <p v-if="statusMessage" class="export-status">{{ statusMessage }}</p>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'

import { useI18n } from '../i18n'

const props = defineProps({
  selectedPlans: {
    type: Array,
    default: () => [],
  },
  compact: Boolean,
})

const { t } = useI18n()
const agentName = ref('')
const masRepNumber = ref('')
const exporting = ref(false)
const statusMessage = ref('')
const pdfBriefEndpoint = computed(
  () => import.meta.env.VITE_PDF_BRIEF_ENDPOINT || '/briefs/client.pdf',
)

async function downloadPdf() {
  if (props.selectedPlans.length === 0) {
    statusMessage.value = t('ui.pdf.selectOne')
    return
  }

  exporting.value = true
  statusMessage.value = ''
  try {
    const response = await fetch(pdfBriefEndpoint.value, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        plans: props.selectedPlans.map(publicPlanPayload),
        branding: brandingPayload(),
      }),
    })
    if (!response.ok) {
      throw new Error(`PDF export failed with ${response.status}`)
    }
    const blob = await response.blob()
    triggerDownload(blob)
    statusMessage.value = t('ui.pdf.ready')
  } catch (error) {
    statusMessage.value = error?.message || t('ui.pdf.failed')
  } finally {
    exporting.value = false
  }
}

function publicPlanPayload(plan) {
  return {
    insurer: plan.insurer,
    providerName: plan.providerName,
    canonical_carrier_name: plan.carrierCanonical?.canonical_name,
    carrier_mismatch_flags: plan.carrierCanonical?.mismatch_flags || [],
    plan_name: plan.plan_name,
    plan_slug: plan.plan_slug,
    facts: plan.facts,
  }
}

function brandingPayload() {
  return {
    agent_name: agentName.value.trim(),
    mas_rep_number: masRepNumber.value.trim(),
  }
}

function triggerDownload(blob) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'be-sure-ance-client-brief.pdf'
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}
</script>

<style scoped>
.brief-export {
  display: grid;
  gap: 14px;
  padding: 18px;
  border: 1px solid var(--hf-border);
  border-radius: var(--hf-radius-lg);
  background: var(--hf-surface);
}

.brief-export.compact {
  display: block;
  padding: 0;
  border: 0;
  background: transparent;
}

.panel-heading p,
.panel-heading h2,
.export-status {
  margin: 0;
}

.panel-heading p {
  color: var(--hf-muted);
  font-size: 14px;
}

.brief-fields {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr)) auto;
  gap: 10px;
  align-items: end;
}

.compact-export {
  position: relative;
}

.compact-export summary {
  list-style: none;
}

.compact-export summary::-webkit-details-marker {
  display: none;
}

.popover-fields {
  position: absolute;
  right: 0;
  top: calc(100% + 8px);
  z-index: 30;
  width: min(520px, calc(100vw - 28px));
  padding: 14px;
  border: 1px solid var(--hf-border);
  border-radius: var(--hf-radius-lg);
  background: var(--hf-surface);
  box-shadow: 0 18px 48px rgba(0, 0, 0, 0.36);
}

label {
  display: grid;
  gap: 5px;
}

label span,
.export-status {
  color: var(--hf-muted);
  font-size: 14px;
}

input {
  min-width: 0;
  min-height: 40px;
  padding: 9px 12px;
  border: 1px solid var(--hf-border);
  border-radius: var(--hf-radius-md);
  background: var(--hf-neutral);
  color: var(--hf-primary);
}

button {
  min-height: 40px;
  padding: 8px 14px;
  border: 1px solid var(--hf-border);
  border-radius: var(--hf-radius-full);
  background: var(--hf-primary);
  color: #111827;
  font-weight: 700;
}

button:disabled {
  opacity: 0.5;
}

@media (max-width: 720px) {
  .brief-fields {
    grid-template-columns: 1fr;
  }

  .popover-fields {
    left: 0;
    right: auto;
  }
}
</style>
