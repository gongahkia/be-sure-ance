<template>
  <article class="plan-card">
    <div class="plan-card-top">
      <div>
        <p class="eyebrow">{{ provider.name }}</p>
        <h3>{{ plan.plan_name }}</h3>
      </div>
      <button class="select-button" type="button" @click="$emit('toggle-select', plan.key)">
        {{ selected ? 'Remove from brief' : 'Add to brief' }}
      </button>
    </div>

    <p class="summary">
      {{
        plan.plan_description || comparisonFact?.comparison_notes || 'No plan summary available.'
      }}
    </p>
    <p v-if="canonicalCarrierText" class="canonical-line">
      Canonical carrier: {{ canonicalCarrierText }}
      <span v-if="canonicalFlagsText">({{ canonicalFlagsText }})</span>
    </p>
    <FactProvenance :entries="profileProvenance" compact />

    <div class="fact-row">
      <div v-for="fact in factHighlights" :key="fact.label" class="fact">
        <span class="fact-label">{{ fact.label }}</span>
        <strong>{{ fact.value }}</strong>
      </div>
    </div>
    <FactProvenance :entries="highlightProvenance" compact />

    <div class="tag-row">
      <span v-for="badge in coverageBadges" :key="badge" class="coverage-badge">
        {{ badge }}
      </span>
      <span v-if="resources.length > 0" class="resource-badge"
        >{{ resources.length }} provider links</span
      >
    </div>

    <details class="detail-panel">
      <summary>Agent detail</summary>
      <p class="detail-copy">
        {{
          plan.plan_overview ||
          comparisonFact?.comparison_notes ||
          'No additional overview available.'
        }}
      </p>

      <div class="link-row">
        <a
          v-if="safeExternalUrl(plan.plan_url)"
          :href="safeExternalUrl(plan.plan_url)"
          target="_blank"
          rel="noopener noreferrer"
          referrerpolicy="no-referrer"
        >
          Product page
        </a>
        <a
          v-if="safeExternalUrl(plan.product_brochure_url)"
          :href="safeExternalUrl(plan.product_brochure_url)"
          target="_blank"
          rel="noopener noreferrer"
          referrerpolicy="no-referrer"
        >
          Brochure
        </a>
        <a v-if="planPagePath" :href="planPagePath">Plan page</a>
      </div>

      <div class="qualitative-sections">
        <section>
          <h4>Coverage</h4>
          <p>{{ coverageSummary }}</p>
          <FactProvenance :entries="coverageProvenance" />
        </section>

        <section>
          <h4>Network</h4>
          <p>{{ networkSummary }}</p>
          <ul v-if="panelHospitals.length > 0">
            <li v-for="hospital in panelHospitals.slice(0, 4)" :key="itemLabel(hospital)">
              {{ itemLabel(hospital) }}
            </li>
          </ul>
          <FactProvenance :entries="networkProvenance" />
        </section>

        <section>
          <h4>Process</h4>
          <p>Waiting periods: {{ waitingPeriodSummary }}</p>
          <p v-if="waitingPeriodTags.length > 0">Tags: {{ waitingPeriodTags.join(', ') }}</p>
          <p>Claim deadlines: {{ claimDeadlineSummary }}</p>
          <p>Claim SLA: {{ claimSlaSummary }}</p>
          <FactProvenance :entries="processProvenance" />
        </section>

        <section>
          <h4>Exclusions</h4>
          <p>{{ exclusionSummary }}</p>
          <p v-if="exclusionTags.length > 0">Tags: {{ exclusionTags.join(', ') }}</p>
          <FactProvenance :entries="exclusionProvenance" />
        </section>

        <section>
          <h4>Brochure</h4>
          <p>{{ brochureSummary }}</p>
          <FactProvenance :entries="brochureProvenance" />
        </section>

        <BrochureChangeList :changes="brochureChanges" />

        <section v-if="sourceNotes.length > 0">
          <h4>Source notes</h4>
          <p>{{ listText(sourceNotes) }}</p>
          <FactProvenance :entries="sourceNotesProvenance" />
        </section>

        <RegulatoryEventList :events="regulatoryEvents" />
      </div>

      <ul v-if="resources.length > 0" class="resource-list">
        <li v-for="resource in resources" :key="resource.id || resource.resource_url">
          <a
            v-if="safeExternalUrl(resource.resource_url)"
            :href="safeExternalUrl(resource.resource_url)"
            target="_blank"
            rel="noopener noreferrer"
            referrerpolicy="no-referrer"
          >
            {{ resource.resource_title || resource.resource_type }}
          </a>
          <span v-if="resource.resource_description"> - {{ resource.resource_description }}</span>
        </li>
      </ul>
      <FactProvenance v-if="resources.length > 0" :entries="resourceProvenance" compact />
    </details>
  </article>
</template>

<script setup>
import { computed } from 'vue'

import BrochureChangeList from './BrochureChangeList.vue'
import FactProvenance from './FactProvenance.vue'
import RegulatoryEventList from './RegulatoryEventList.vue'
import { safeExternalUrl } from '../utils/links'
import {
  claimSlaText,
  coverageTagsForPlan,
  durationText,
  factItems,
  factStateText,
  factValue,
  itemLabel,
  labelForTag,
  listText,
  profileProvenanceEntry,
  provenanceEntriesForFields,
  taxonomySuffix,
  taxonomyTagLabels,
} from '../utils/planFacts'

const props = defineProps({
  plan: Object,
  provider: Object,
  facts: Object,
  comparisonFact: Object,
  resources: Array,
  regulatoryEvents: {
    type: Array,
    default: () => [],
  },
  brochureChanges: {
    type: Array,
    default: () => [],
  },
  selected: Boolean,
})

defineEmits(['toggle-select'])

const planWithFacts = computed(() => ({
  ...props.plan,
  facts: props.facts,
  comparisonFact: props.comparisonFact,
}))

const coverageBadges = computed(() => coverageTagsForPlan(planWithFacts.value).map(labelForTag))
const carrierCanonical = computed(() => props.plan?.carrierCanonical || null)
const canonicalCarrierText = computed(() => carrierCanonical.value?.canonical_name || '')
const canonicalFlagsText = computed(() =>
  (carrierCanonical.value?.mismatch_flags || []).map(labelForTag).join(', '),
)

const panelHospitals = computed(() => factItems(props.facts, 'panel_hospitals'))
const waitingPeriods = computed(() => factItems(props.facts, 'waiting_periods'))
const claimDeadlines = computed(() => factItems(props.facts, 'claim_deadlines'))
const exclusions = computed(() => factItems(props.facts, 'exclusions'))
const waitingPeriodTags = computed(() => taxonomyTagLabels(waitingPeriods.value))
const exclusionTags = computed(() => taxonomyTagLabels(exclusions.value))
const sourceNotes = computed(() => factItems(props.facts, 'source_notes'))
const brochureMetadata = computed(() => factValue(props.facts, 'brochure_metadata'))
const planPagePath = computed(() =>
  props.plan?.providerKey && props.plan?.plan_slug
    ? `/plan/${encodeURIComponent(props.plan.providerKey)}/${encodeURIComponent(props.plan.plan_slug)}`
    : '',
)
const profileProvenance = computed(() => profileProvenanceEntry(props.plan))
const highlightProvenance = computed(() =>
  provenanceEntriesForFields(props.facts, [
    'coverage_tags',
    'panel_hospitals',
    'waiting_periods',
    'claim_deadlines',
    'claim_sla',
    'exclusions',
    'brochure_metadata',
  ]),
)
const coverageProvenance = computed(() =>
  provenanceEntriesForFields(props.facts, ['coverage_tags']),
)
const networkProvenance = computed(() =>
  provenanceEntriesForFields(props.facts, ['panel_hospitals']),
)
const processProvenance = computed(() =>
  provenanceEntriesForFields(props.facts, ['waiting_periods', 'claim_deadlines', 'claim_sla']),
)
const exclusionProvenance = computed(() => provenanceEntriesForFields(props.facts, ['exclusions']))
const brochureProvenance = computed(() =>
  provenanceEntriesForFields(props.facts, ['brochure_metadata']),
)
const sourceNotesProvenance = computed(() =>
  provenanceEntriesForFields(props.facts, ['source_notes']),
)
const resourceProvenance = computed(() =>
  (props.resources || []).map((resource, index) => ({
    key: `resource:${resource.id || resource.resource_url || index}`,
    fields: [resource.resource_title || resource.resource_type || 'Provider resource'],
    sourceUrl: resource.source_url || resource.resource_url || '',
    sourceType: 'product_page',
    scrapedAt: '',
    lastVerifiedAt: '',
  })),
)
const claimSlaSummary = computed(
  () => claimSlaText(props.facts) || factStateText(props.facts, 'claim_sla'),
)

const coverageSummary = computed(() =>
  coverageBadges.value.length > 0
    ? coverageBadges.value.join(', ')
    : factStateText(props.facts, 'coverage_tags', 'Unknown'),
)

const networkSummary = computed(() =>
  panelHospitals.value.length > 0
    ? `${panelHospitals.value.length} listed`
    : factStateText(props.facts, 'panel_hospitals', 'Unknown'),
)

const waitingPeriodSummary = computed(() =>
  waitingPeriods.value.length > 0
    ? waitingPeriods.value.map((item) => durationText(item)).join(', ')
    : factStateText(props.facts, 'waiting_periods', 'Unknown'),
)

const claimDeadlineSummary = computed(() =>
  claimDeadlines.value.length > 0
    ? claimDeadlines.value.map((item) => durationText(item, 'deadline_days')).join(', ')
    : factStateText(props.facts, 'claim_deadlines', 'Unknown'),
)

const exclusionSummary = computed(() =>
  exclusions.value.length > 0
    ? exclusions.value.map((item) => `${listText([item])}${taxonomySuffix(item)}`).join(', ')
    : factStateText(props.facts, 'exclusions'),
)

const brochureSummary = computed(() => {
  if (brochureMetadata.value?.sha256 || brochureMetadata.value?.url) {
    return 'Captured'
  }
  if (props.plan?.product_brochure_url) {
    return 'Available'
  }
  return factStateText(props.facts, 'brochure_metadata')
})

const processFactCount = computed(
  () =>
    waitingPeriods.value.length + claimDeadlines.value.length + (claimSlaText(props.facts) ? 1 : 0),
)

const factHighlights = computed(() => [
  {
    label: 'Coverage signals',
    value: coverageBadges.value.length
      ? coverageBadges.value.length
      : factStateText(props.facts, 'coverage_tags', 'Unknown'),
  },
  {
    label: 'Network facts',
    value: networkSummary.value,
  },
  {
    label: 'Process facts',
    value: processFactCount.value ? `${processFactCount.value} listed` : 'Unknown',
  },
  {
    label: 'Exclusions',
    value: exclusions.value.length ? `${exclusions.value.length} noted` : exclusionSummary.value,
  },
  {
    label: 'Brochure',
    value: brochureSummary.value,
  },
])
</script>

<style scoped>
.plan-card {
  display: grid;
  gap: 1rem;
  padding: 1.35rem;
  border: 1px solid rgba(16, 39, 71, 0.1);
  border-radius: 1.25rem;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 24px 60px rgba(16, 39, 71, 0.08);
}

.plan-card-top {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: start;
}

.eyebrow {
  margin: 0 0 0.35rem;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--muted-ink);
}

h3 {
  margin: 0;
  font-size: 1.15rem;
  line-height: 1.25;
}

.summary,
.detail-copy,
.canonical-line {
  margin: 0;
  color: var(--muted-ink);
}

.canonical-line {
  font-size: 0.84rem;
}

.fact-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(8rem, 1fr));
  gap: 0.8rem;
}

.fact {
  padding: 0.85rem;
  border-radius: 1rem;
  background: rgba(16, 39, 71, 0.04);
}

.fact-label {
  display: block;
  margin-bottom: 0.25rem;
  font-size: 0.78rem;
  color: var(--muted-ink);
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
}

.coverage-badge,
.resource-badge {
  padding: 0.45rem 0.7rem;
  border-radius: 999px;
  font-size: 0.82rem;
  background: rgba(194, 225, 255, 0.72);
  color: #133d5e;
}

.resource-badge {
  background: rgba(219, 234, 194, 0.9);
  color: #355118;
}

.detail-panel {
  padding-top: 0.2rem;
}

.detail-panel summary {
  cursor: pointer;
  font-weight: 700;
}

.link-row {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-top: 0.85rem;
}

.qualitative-sections {
  display: grid;
  gap: 0.8rem;
  margin-top: 1rem;
}

.qualitative-sections section {
  padding-top: 0.8rem;
  border-top: 1px solid rgba(16, 39, 71, 0.08);
}

.qualitative-sections h4,
.qualitative-sections p,
.qualitative-sections ul {
  margin: 0;
}

.qualitative-sections h4 {
  margin-bottom: 0.35rem;
  font-size: 0.86rem;
}

.qualitative-sections p,
.qualitative-sections li {
  color: var(--muted-ink);
}

.qualitative-sections ul {
  padding-left: 1rem;
  margin-top: 0.45rem;
}

.resource-list {
  margin: 1rem 0 0;
  padding-left: 1rem;
  color: var(--muted-ink);
}

.select-button {
  border: none;
  border-radius: 999px;
  padding: 0.75rem 1rem;
  background: #102747;
  color: #f8fbff;
  cursor: pointer;
  font-weight: 700;
}

@media (max-width: 720px) {
  .fact-row {
    grid-template-columns: 1fr;
  }
}
</style>
