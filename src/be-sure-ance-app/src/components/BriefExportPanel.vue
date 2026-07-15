<template>
  <section class="brief-export" :class="{ compact }">
    <template v-if="compact">
      <details class="compact-export">
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
          <button type="button" :disabled="exporting" @click="downloadPdf">
            {{ exporting ? t('ui.pdf.preparing') : t('ui.pdf.export') }}
          </button>
        </div>
      </details>
    </template>

    <template v-else>
      <div class="panel-heading">
        <p>{{ t('ui.pdf.eyebrow') }}</p>
        <h2>{{ t('ui.pdf.preview') }}</h2>
      </div>

      <iframe
        v-if="previewUrl"
        class="pdf-preview"
        :src="previewUrl"
        :title="t('ui.pdf.preview')"
      ></iframe>
      <div v-else class="pdf-preview loading-preview">{{ t('ui.pdf.preparingPdf') }}</div>
      <p v-if="statusMessage" class="export-status">{{ statusMessage }}</p>

      <details class="download-options">
        <summary class="hub-button primary">{{ t('ui.pdf.download') }}</summary>
        <label class="appendix-option">
          <input v-model="includePlanDetails" type="checkbox" />
          {{ t('ui.pdf.includeAppendices') }}
        </label>
        <div class="brief-fields">
          <label>
            <span>{{ t('ui.pdf.agent') }}</span>
            <input v-model="agentName" type="text" autocomplete="off" />
          </label>
          <label>
            <span>{{ t('ui.pdf.rep') }}</span>
            <input v-model="masRepNumber" type="text" autocomplete="off" />
          </label>
          <button type="button" :disabled="exporting" @click="downloadPdf">
            {{ exporting ? t('ui.pdf.preparingPdf') : t('ui.pdf.download') }}
          </button>
        </div>
      </details>
    </template>
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'

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
const previewUrl = ref('')
const includePlanDetails = ref(true)
let previewTimer
const pdfBriefEndpoint = computed(
  () => import.meta.env.VITE_PDF_BRIEF_ENDPOINT || '/briefs/client.pdf',
)

watch(
  [() => props.selectedPlans, agentName, masRepNumber, includePlanDetails],
  () => {
    if (props.compact) return
    window.clearTimeout(previewTimer)
    previewTimer = window.setTimeout(refreshPreview, 250)
  },
  { deep: true, immediate: true },
)

async function downloadPdf() {
  const blob = await requestPdf()
  if (!blob) return
  triggerDownload(blob)
  statusMessage.value = t('ui.pdf.ready')
}

async function refreshPreview() {
  const blob = await requestPdf({ silent: true })
  if (!blob) return
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  previewUrl.value = URL.createObjectURL(blob)
  statusMessage.value = ''
}

async function requestPdf({ silent = false } = {}) {
  if (props.selectedPlans.length === 0) {
    if (!silent) statusMessage.value = t('ui.pdf.selectOne')
    return null
  }

  exporting.value = true
  if (!silent) statusMessage.value = ''
  try {
    const response = await fetch(pdfBriefEndpoint.value, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        plans: props.selectedPlans.map(publicPlanPayload),
        branding: brandingPayload(),
        options: { include_plan_details: includePlanDetails.value },
      }),
    })
    if (!response.ok) throw new Error(`PDF export failed with ${response.status}`)
    return await response.blob()
  } catch (error) {
    statusMessage.value = error?.message || t('ui.pdf.failed')
    return null
  } finally {
    exporting.value = false
  }
}

function publicPlanPayload(plan) {
  return {
    insurer: plan.insurer,
    providerName: plan.providerName,
    provider_logo_url: providerLogoUrl(plan.providerWebsite),
    canonical_carrier_name: plan.carrierCanonical?.canonical_name,
    carrier_mismatch_flags: plan.carrierCanonical?.mismatch_flags || [],
    plan_name: plan.plan_name,
    plan_slug: plan.plan_slug,
    plan_description: plan.plan_description,
    plan_overview: plan.plan_overview,
    plan_benefits: plan.plan_benefits,
    plan_url: plan.plan_url,
    product_brochure_url: plan.product_brochure_url,
    facts: plan.facts,
  }
}

function providerLogoUrl(website) {
  try {
    const domain = new URL(website).hostname.replace(/^www\./, '')
    return `https://www.google.com/s2/favicons?sz=128&domain=${encodeURIComponent(domain)}`
  } catch {
    return ''
  }
}

function brandingPayload() {
  return {
    agent_name: agentName.value.trim(),
    mas_rep_number: masRepNumber.value.trim(),
  }
}

onBeforeUnmount(() => {
  window.clearTimeout(previewTimer)
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
})

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
  min-width: 0;
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

.panel-heading p,
label span,
.export-status {
  color: var(--hf-muted);
  font-size: 14px;
}

.compact-export,
.download-options {
  position: relative;
}

.compact-export summary,
.download-options summary {
  list-style: none;
}

.compact-export summary::-webkit-details-marker,
.download-options summary::-webkit-details-marker {
  display: none;
}

.download-options {
  border-top: 1px solid var(--hf-border);
  padding-top: 14px;
}

.download-options[open] {
  display: grid;
  gap: 14px;
}

.brief-fields {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr)) auto;
  gap: 10px;
  align-items: end;
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

input {
  min-width: 0;
  min-height: 40px;
  padding: 9px 12px;
  border: 1px solid var(--hf-border);
  border-radius: var(--hf-radius-md);
  background: var(--hf-neutral);
  color: var(--hf-primary);
}

.appendix-option {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--hf-secondary);
  font-size: 14px;
}

.appendix-option input {
  min-width: auto;
  min-height: auto;
}

button {
  min-height: 40px;
  padding: 8px 14px;
  border: 1px solid var(--hf-border);
  border-radius: var(--hf-radius-full);
  background: var(--hf-primary);
  color: var(--hf-primary-contrast);
  font-weight: 700;
}

button:disabled {
  opacity: 0.5;
}

.pdf-preview {
  width: 100%;
  min-height: 720px;
  border: 1px solid var(--hf-border);
  border-radius: var(--hf-radius-md);
  background: #ffffff;
}

.loading-preview {
  display: grid;
  min-height: 720px;
  place-items: center;
  color: var(--hf-muted);
}

@media (max-width: 720px) {
  .brief-fields {
    grid-template-columns: 1fr;
  }

  .popover-fields {
    left: 0;
    right: auto;
  }

  .pdf-preview,
  .loading-preview {
    min-height: 560px;
  }
}
</style>
