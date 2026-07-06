<template>
  <aside class="filter-rail">
    <section>
      <div class="section-head">
        <h2>{{ t('ui.rail.carriers') }}</h2>
        <button type="button" @click="$emit('clear-filters')">{{ t('ui.rail.clear') }}</button>
      </div>
      <button
        type="button"
        :class="['filter-chip', { active: activeProviderKey === 'all' }]"
        @click="$emit('select', 'all')"
      >
        <span>{{ t('ui.rail.allCarriers') }}</span>
        <strong>{{ totalCount }}</strong>
      </button>
      <button
        v-for="provider in providers"
        :key="provider.key"
        type="button"
        :class="['filter-chip', { active: provider.key === activeProviderKey }]"
        @click="$emit('select', provider.key)"
      >
        <ProviderLogo :provider="provider" size="sm" />
        <span>{{ provider.name }}</span>
        <strong>{{ providerCounts[provider.key] || 0 }}</strong>
      </button>
    </section>

    <section>
      <h2>{{ t('ui.rail.tags') }}</h2>
      <div class="chip-grid">
        <button
          v-for="tag in coverageTags"
          :key="tag"
          type="button"
          :class="['tag-chip', { active: activeCoverageTags.includes(tag) }]"
          @click="$emit('toggle-coverage', tag)"
        >
          {{ tagLabel(tag) }}
        </button>
      </div>
    </section>
  </aside>
</template>

<script setup>
import { computed } from 'vue'

import ProviderLogo from './ProviderLogo.vue'
import { useI18n } from '../i18n'
import { translateContent } from '../utils/contentTranslation'
import { labelForTag } from '../utils/planFacts'

const props = defineProps({
  providers: {
    type: Array,
    default: () => [],
  },
  activeProviderKey: String,
  providerCounts: {
    type: Object,
    default: () => ({}),
  },
  coverageTags: {
    type: Array,
    default: () => [],
  },
  activeCoverageTags: {
    type: Array,
    default: () => [],
  },
})

defineEmits(['select', 'toggle-coverage', 'clear-filters'])

const { locale, t } = useI18n()
const totalCount = computed(() =>
  Object.values(props.providerCounts).reduce((total, count) => total + Number(count || 0), 0),
)

function tagLabel(tag) {
  const translated = t(`tag.${tag}`)
  return translated.startsWith('[missing:')
    ? translateContent(labelForTag(tag), locale.value)
    : translated
}
</script>

<style scoped>
.filter-rail {
  position: sticky;
  top: 100px;
  display: grid;
  min-width: 0;
  align-content: start;
  gap: 26px;
  max-height: calc(100vh - 120px);
  overflow: auto;
  padding-right: 6px;
}

section {
  display: grid;
  gap: 10px;
}

.section-head {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  align-items: center;
}

h2 {
  margin: 0;
  color: var(--hf-muted);
  font-size: 16px;
  line-height: 22px;
  font-weight: 600;
}

.section-head button {
  border: 0;
  background: transparent;
  color: var(--hf-secondary);
  text-decoration: underline;
  text-underline-offset: 3px;
}

.filter-chip {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  width: 100%;
  min-height: 38px;
  gap: 12px;
  align-items: center;
  border: 1px solid var(--hf-border);
  border-radius: var(--hf-radius-full);
  background: var(--hf-surface);
  color: var(--hf-secondary);
  padding: 7px 12px;
  text-align: left;
}

.filter-chip.active,
.tag-chip.active {
  border-color: var(--hf-active-border);
  color: var(--hf-primary);
}

.filter-chip span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.filter-chip:first-of-type {
  grid-template-columns: minmax(0, 1fr) auto;
}

.filter-chip strong {
  color: var(--hf-muted);
}

.chip-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag-chip {
  min-height: 34px;
  border: 1px solid var(--hf-border);
  border-radius: var(--hf-radius-full);
  background: var(--hf-surface-2);
  color: var(--hf-secondary);
  padding: 5px 10px;
}

@media (max-width: 1280px) {
  .filter-rail {
    position: static;
    max-height: none;
    overflow: visible;
    padding-right: 0;
  }
}

@media (max-width: 720px) {
  .filter-rail {
    gap: 20px;
  }
}
</style>
