<template>
  <article class="plan-card">
    <div class="plan-card-top">
      <div>
        <p class="eyebrow">{{ provider.name }}</p>
        <h3>{{ plan.plan_name }}</h3>
      </div>
      <button class="select-button" type="button" @click="$emit('toggle-select', plan.key)">
        {{ selected ? "Remove from brief" : "Add to brief" }}
      </button>
    </div>

    <p class="summary">{{ plan.plan_description || comparisonFact?.comparison_notes || "No plan summary available." }}</p>

    <div class="fact-row">
      <div v-for="fact in factHighlights" :key="fact.label" class="fact">
        <span class="fact-label">{{ fact.label }}</span>
        <strong>{{ fact.value }}</strong>
      </div>
    </div>

    <div class="tag-row">
      <span
        v-for="badge in coverageBadges"
        :key="badge"
        class="coverage-badge"
      >
        {{ badge }}
      </span>
      <span v-if="resources.length > 0" class="resource-badge">{{ resources.length }} provider links</span>
    </div>

    <details class="detail-panel">
      <summary>Agent detail</summary>
      <p class="detail-copy">{{ plan.plan_overview || comparisonFact?.comparison_notes || "No additional overview available." }}</p>

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
    </details>
  </article>
</template>

<script setup>
import { computed } from 'vue'

import { safeExternalUrl } from '../utils/links'

const props = defineProps({
  plan: Object,
  provider: Object,
  comparisonFact: Object,
  resources: Array,
  selected: Boolean
})

defineEmits(["toggle-select"])

const coverageBadges = computed(() => {
  const tags = props.comparisonFact?.coverage_tags || []
  return tags.map(labelForTag)
})

const factHighlights = computed(() => [
  {
    label: "Coverage signals",
    value: coverageBadges.value.length ? coverageBadges.value.length : "None"
  },
  {
    label: "Provider links",
    value: props.resources?.length || 0
  },
  {
    label: "Brochure",
    value: (props.comparisonFact?.coverage_tags || []).includes("brochure_available") ||
      props.plan?.product_brochure_url ? "Available" : "Missing"
  }
])

function labelForTag(tag) {
  return String(tag)
    .split("_")
    .filter(Boolean)
    .map((part) => `${part.charAt(0).toUpperCase()}${part.slice(1)}`)
    .join(" ")
}
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
.detail-copy {
  margin: 0;
  color: var(--muted-ink);
}

.fact-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
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
