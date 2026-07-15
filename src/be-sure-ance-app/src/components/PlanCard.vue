<template>
  <article class="repo-row">
    <ProviderLogo :provider="provider" size="md" />
    <div class="repo-body">
      <div class="repo-title-line">
        <div>
          <a v-if="planPagePath" class="repo-title" :href="planPagePath">
            <span>{{ provider.name }}</span>
            <strong>/{{ plan.plan_name }}</strong>
          </a>
          <span v-else class="repo-title">
            <span>{{ provider.name }}</span>
            <strong>/{{ plan.plan_name }}</strong>
          </span>
          <p class="repo-summary">
            {{ planSummary }}
          </p>
        </div>
        <button class="hub-button" type="button" @click="$emit('toggle-select', plan.key)">
          {{ selected ? t('ui.plan.selected') : t('ui.plan.add') }}
        </button>
      </div>

      <div v-if="coverageBadges.length > 0" class="chip-row">
        <span v-for="badge in coverageBadges" :key="badge" class="hub-chip">{{ badge }}</span>
      </div>

      <details class="row-details">
        <summary>{{ t('ui.plan.modelPreview') }}</summary>
        <div class="detail-grid">
          <section>
            <h3>{{ t('field.panel_hospitals') }}</h3>
            <p>{{ networkSummary }}</p>
            <FactProvenance
              :entries="provenanceEntriesForFields(facts, ['panel_hospitals'])"
              compact
            />
          </section>
          <section>
            <h3>{{ t('plan.process') }}</h3>
            <p>{{ processSummary }}</p>
            <FactProvenance
              :entries="
                provenanceEntriesForFields(facts, [
                  'waiting_periods',
                  'claim_deadlines',
                  'claim_sla',
                ])
              "
              compact
            />
          </section>
          <section>
            <h3>{{ t('field.exclusions') }}</h3>
            <p>{{ exclusionSummary }}</p>
            <FactProvenance :entries="provenanceEntriesForFields(facts, ['exclusions'])" compact />
          </section>
          <section>
            <h3>{{ t('field.source_notes') }}</h3>
            <p>{{ sourceNotesSummary }}</p>
            <FactProvenance
              :entries="provenanceEntriesForFields(facts, ['source_notes'])"
              compact
            />
          </section>
          <section v-if="resources.length > 0">
            <h3>{{ t('ui.plan.providerResources') }}</h3>
            <ul>
              <li
                v-for="resource in resources.slice(0, 4)"
                :key="resource.id || resource.resource_url"
              >
                <a
                  v-if="safeExternalUrl(resource.resource_url)"
                  :href="safeExternalUrl(resource.resource_url)"
                  target="_blank"
                  rel="noopener noreferrer"
                  referrerpolicy="no-referrer"
                >
                  {{ resourceLabel(resource) }}
                </a>
                <span v-else>{{ resourceLabel(resource) }}</span>
              </li>
            </ul>
          </section>
          <BrochureChangeList :changes="brochureChanges" />
          <RegulatoryEventList :events="regulatoryEvents" />
        </div>
      </details>
    </div>
  </article>
</template>

<script setup>
import { computed } from 'vue'

import BrochureChangeList from './BrochureChangeList.vue'
import FactProvenance from './FactProvenance.vue'
import ProviderLogo from './ProviderLogo.vue'
import RegulatoryEventList from './RegulatoryEventList.vue'
import { useI18n } from '../i18n'
import { translateContent } from '../utils/contentTranslation'
import { safeExternalUrl } from '../utils/links'
import {
  claimSlaText,
  coverageTagsForPlan,
  durationText,
  factItems,
  factStateText,
  itemLabel,
  labelForTag,
  listText,
  provenanceEntriesForFields,
  taxonomySuffix,
} from '../utils/planFacts'

const props = defineProps({
  plan: Object,
  provider: Object,
  facts: Object,
  comparisonFact: Object,
  resources: {
    type: Array,
    default: () => [],
  },
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

const { locale, t } = useI18n()
const planWithFacts = computed(() => ({
  ...props.plan,
  facts: props.facts,
  comparisonFact: props.comparisonFact,
}))

const coverageBadges = computed(() => coverageTagsForPlan(planWithFacts.value).map(tagLabel))
const panelHospitals = computed(() => factItems(props.facts, 'panel_hospitals'))
const waitingPeriods = computed(() => factItems(props.facts, 'waiting_periods'))
const claimDeadlines = computed(() => factItems(props.facts, 'claim_deadlines'))
const exclusions = computed(() => factItems(props.facts, 'exclusions'))
const sourceNotes = computed(() => factItems(props.facts, 'source_notes'))
const planSummary = computed(() =>
  localize(
    props.plan?.plan_description ||
      props.comparisonFact?.comparison_notes ||
      props.plan?.plan_overview ||
      t('ui.plan.noSummary'),
  ),
)
const planPagePath = computed(() =>
  props.plan?.providerKey && props.plan?.plan_slug
    ? `/plan/${encodeURIComponent(props.plan.providerKey)}/${encodeURIComponent(props.plan.plan_slug)}`
    : '',
)

function tagLabel(tag) {
  const translated = t(`tag.${tag}`)
  return translated.startsWith('[missing:') ? localize(labelForTag(tag)) : translated
}

const networkSummary = computed(() =>
  localize(
    panelHospitals.value.length > 0
      ? panelHospitals.value.map(itemLabel).join(', ')
      : factStateText(props.facts, 'panel_hospitals', t('ui.matrix.unknown')),
  ),
)

const processSummary = computed(() =>
  localize(
    [
      waitingPeriods.value.length
        ? waitingPeriods.value.map((item) => durationText(item)).join(', ')
        : factStateText(props.facts, 'waiting_periods', t('ui.matrix.unknown')),
      claimDeadlines.value.length
        ? claimDeadlines.value.map((item) => durationText(item, 'deadline_days')).join(', ')
        : factStateText(props.facts, 'claim_deadlines', t('ui.matrix.unknown')),
      claimSlaText(props.facts) || factStateText(props.facts, 'claim_sla', t('ui.matrix.unknown')),
    ].join(' / '),
  ),
)

const exclusionSummary = computed(() =>
  localize(
    exclusions.value.length > 0
      ? exclusions.value.map((item) => `${listText([item])}${taxonomySuffix(item)}`).join(', ')
      : factStateText(props.facts, 'exclusions'),
  ),
)

const sourceNotesSummary = computed(() =>
  localize(listText(sourceNotes.value, factStateText(props.facts, 'source_notes'))),
)

function resourceLabel(resource) {
  return localize(resource.resource_title || resource.resource_type)
}

function localize(value) {
  return translateContent(value, locale.value)
}
</script>

<style scoped>
.repo-row {
  display: grid;
  grid-template-columns: 34px minmax(0, 1fr);
  gap: 14px;
  padding: 16px;
  border: 1px solid var(--hf-border);
  border-radius: var(--hf-radius-lg);
  background: var(--hf-surface);
}

.repo-row:hover {
  border-color: var(--hf-tertiary);
}

.repo-body {
  display: grid;
  min-width: 0;
  gap: 10px;
}

.repo-title-line {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 16px;
  align-items: flex-start;
}

.repo-title {
  display: inline-flex;
  max-width: 100%;
  gap: 2px;
  color: var(--hf-primary);
  font-size: 20px;
  line-height: 26px;
  text-decoration: none;
  flex-wrap: wrap;
  overflow-wrap: anywhere;
}

.repo-title span {
  color: var(--hf-muted);
}

.repo-title strong {
  overflow-wrap: anywhere;
}

.repo-summary {
  margin: 4px 0 0;
  color: var(--hf-secondary);
  line-height: 22px;
}

.chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.row-details {
  border-top: 1px solid var(--hf-border);
  padding-top: 10px;
}

.row-details summary {
  color: var(--hf-secondary);
  cursor: pointer;
  font-weight: 700;
}

.detail-grid {
  display: grid;
  gap: 14px;
  margin-top: 14px;
}

.detail-grid section {
  display: grid;
  gap: 6px;
}

.detail-grid h3,
.detail-grid p,
.detail-grid ul {
  margin: 0;
}

.detail-grid h3 {
  font-size: 16px;
}

.detail-grid p,
.detail-grid li {
  color: var(--hf-secondary);
}

.detail-grid ul {
  padding-left: 18px;
}

@media (max-width: 760px) {
  .repo-row {
    grid-template-columns: 34px minmax(0, 1fr);
  }

  .repo-title-line {
    grid-template-columns: 1fr;
  }

  .repo-title-line .hub-button {
    width: max-content;
  }
}
</style>
