<template>
  <section class="brief-export">
    <div>
      <p class="eyebrow">PDF Brief</p>
      <h2>Export selected plans</h2>
    </div>

    <div class="brief-fields">
      <label>
        <span>Agent name</span>
        <input v-model="agentName" type="text" autocomplete="off" />
      </label>
      <label>
        <span>MAS rep no.</span>
        <input v-model="masRepNumber" type="text" autocomplete="off" />
      </label>
      <button
        type="button"
        :disabled="selectedPlans.length === 0 || exporting"
        @click="downloadPdf"
      >
        {{ exporting ? 'Preparing PDF' : 'Download PDF' }}
      </button>
    </div>

    <p v-if="statusMessage" class="export-status">{{ statusMessage }}</p>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  selectedPlans: {
    type: Array,
    default: () => [],
  },
})

const agentName = ref('')
const masRepNumber = ref('')
const exporting = ref(false)
const statusMessage = ref('')
const pdfBriefEndpoint = computed(
  () => import.meta.env.VITE_PDF_BRIEF_ENDPOINT || '/briefs/client.pdf',
)

async function downloadPdf() {
  if (props.selectedPlans.length === 0) {
    statusMessage.value = 'Select at least one plan.'
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
    statusMessage.value = 'PDF ready.'
  } catch (error) {
    statusMessage.value = error?.message || 'PDF export failed.'
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

.brief-fields {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr)) auto;
  gap: 0.75rem;
  align-items: end;
}

label {
  display: grid;
  gap: 0.3rem;
}

label span,
.export-status {
  color: var(--muted-ink);
  font-size: 0.84rem;
}

input {
  min-width: 0;
  padding: 0.75rem 0.8rem;
  border: 1px solid rgba(16, 39, 71, 0.14);
  border-radius: 0.7rem;
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

.export-status {
  margin: 0;
}

@media (max-width: 720px) {
  .brief-fields {
    grid-template-columns: 1fr;
  }
}
</style>
