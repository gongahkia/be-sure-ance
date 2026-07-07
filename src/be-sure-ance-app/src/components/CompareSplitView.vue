<template>
  <section class="compare-split-view">
    <header class="compare-heading">
      <div>
        <p class="eyebrow">{{ t('comparison.eyebrow') }}</p>
        <h1>{{ t('compareSplit.title') }}</h1>
        <p>{{ t('compareSplit.copy') }}</p>
      </div>
      <div class="compare-actions">
        <button
          v-if="comparePlans.length === 2 && !editing"
          class="change-button"
          type="button"
          @click="editing = true"
        >
          {{ t('compareSplit.change') }}
        </button>
        <span class="hub-chip strong">
          {{ t('compareSplit.planCount', { count: plans.length.toLocaleString() }) }}
        </span>
      </div>
    </header>

    <div v-if="showPicker" class="split-picker-grid">
      <section class="compare-slot hub-panel">
        <div class="slot-header">
          <div>
            <p>{{ t('compareSplit.left') }}</p>
            <h2>{{ leftPlan?.plan_name || t('compareSplit.choose') }}</h2>
            <span>{{ leftPlan?.providerName || t('compareSplit.emptySlot') }}</span>
          </div>
          <button v-if="leftPlan" class="clear-button" type="button" @click="clearSlot('left')">
            {{ t('compareSplit.clear') }}
          </button>
        </div>

        <label class="picker-search">
          <span class="sr-only">{{ t('compareSplit.search') }}</span>
          <input
            v-model="leftQuery"
            class="hub-input"
            type="search"
            :placeholder="t('compareSplit.search')"
          />
        </label>

        <div class="tab-option-list" role="listbox" :aria-label="t('compareSplit.left')">
          <button
            v-for="plan in leftOptions"
            :key="planOptionKey(plan)"
            class="tab-option"
            :class="{ selected: leftKey === planOptionKey(plan) }"
            type="button"
            role="option"
            :aria-selected="leftKey === planOptionKey(plan)"
            @click="selectPlan('left', planOptionKey(plan))"
          >
            <ProviderLogo :provider="providerFor(plan.providerKey)" size="lg" />
            <span>
              <strong>{{ plan.plan_name }}</strong>
              <small>{{ plan.providerName }}</small>
            </span>
          </button>
          <p v-if="leftOptions.length === 0" class="picker-empty">{{ t('compareSplit.empty') }}</p>
        </div>
      </section>

      <section class="compare-slot hub-panel">
        <div class="slot-header">
          <div>
            <p>{{ t('compareSplit.right') }}</p>
            <h2>{{ rightPlan?.plan_name || t('compareSplit.choose') }}</h2>
            <span>{{ rightPlan?.providerName || t('compareSplit.emptySlot') }}</span>
          </div>
          <button v-if="rightPlan" class="clear-button" type="button" @click="clearSlot('right')">
            {{ t('compareSplit.clear') }}
          </button>
        </div>

        <label class="picker-search">
          <span class="sr-only">{{ t('compareSplit.search') }}</span>
          <input
            v-model="rightQuery"
            class="hub-input"
            type="search"
            :placeholder="t('compareSplit.search')"
          />
        </label>

        <div class="tab-option-list" role="listbox" :aria-label="t('compareSplit.right')">
          <button
            v-for="plan in rightOptions"
            :key="planOptionKey(plan)"
            class="tab-option"
            :class="{ selected: rightKey === planOptionKey(plan) }"
            type="button"
            role="option"
            :aria-selected="rightKey === planOptionKey(plan)"
            @click="selectPlan('right', planOptionKey(plan))"
          >
            <ProviderLogo :provider="providerFor(plan.providerKey)" size="lg" />
            <span>
              <strong>{{ plan.plan_name }}</strong>
              <small>{{ plan.providerName }}</small>
            </span>
          </button>
          <p v-if="rightOptions.length === 0" class="picker-empty">
            {{ t('compareSplit.empty') }}
          </p>
        </div>
      </section>
    </div>

    <section v-if="showPicker && comparePlans.length < 2" class="pending-panel hub-panel">
      {{ t('compareSplit.pending') }}
    </section>
    <ComparisonTable
      v-else-if="!showPicker && comparePlans.length === 2"
      :selected-plans="comparePlans"
    />
  </section>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

import ComparisonTable from './ComparisonTable.vue'
import ProviderLogo from './ProviderLogo.vue'
import { useI18n } from '../i18n'
import { providers } from '../lib/providers'
import { translateContent } from '../utils/contentTranslation'
import { coverageTagsForPlan, labelForTag } from '../utils/planFacts'

const props = defineProps({
  plans: {
    type: Array,
    default: () => [],
  },
  initialPlans: {
    type: Array,
    default: () => [],
  },
})

const STORAGE_KEY = 'be-sure-ance:compare-plan-keys'

const { locale, t } = useI18n()
const leftKey = ref('')
const rightKey = ref('')
const leftQuery = ref('')
const rightQuery = ref('')
const initialized = ref(false)
const editing = ref(false)

const planMap = computed(() =>
  Object.fromEntries(props.plans.map((plan) => [planOptionKey(plan), plan])),
)
const sortedPlans = computed(() =>
  [...props.plans].sort((left, right) => {
    const carrierSort = String(left.providerName).localeCompare(String(right.providerName))
    if (carrierSort !== 0) {
      return carrierSort
    }
    return String(left.plan_name).localeCompare(String(right.plan_name))
  }),
)
const leftPlan = computed(() => planMap.value[leftKey.value] || null)
const rightPlan = computed(() => planMap.value[rightKey.value] || null)
const leftOptions = computed(() => filteredOptions(leftQuery.value, rightKey.value))
const rightOptions = computed(() => filteredOptions(rightQuery.value, leftKey.value))
const comparePlans = computed(() => [leftPlan.value, rightPlan.value].filter(Boolean))
const showPicker = computed(() => editing.value || comparePlans.value.length < 2)

watch(
  () => [props.plans, props.initialPlans],
  () => initializeSelection(),
  { immediate: true },
)

watch([leftKey, rightKey], () => {
  storeKeys([leftKey.value, rightKey.value].filter(Boolean))
  if (leftKey.value && rightKey.value) {
    editing.value = false
  }
})

function initializeSelection() {
  if (initialized.value || props.plans.length === 0) {
    reconcileKeys()
    return
  }
  const availableKeys = new Set(props.plans.map(planOptionKey))
  const seedKeys = uniqueKeys([
    ...loadStoredKeys(),
    ...props.initialPlans.map(planOptionKey),
  ])
    .filter((key) => availableKeys.has(key))
    .slice(0, 2)
  leftKey.value = seedKeys[0] || ''
  rightKey.value = seedKeys.find((key) => key !== leftKey.value) || ''
  initialized.value = true
}

function reconcileKeys() {
  if (props.plans.length === 0) {
    return
  }
  const availableKeys = new Set(props.plans.map(planOptionKey))
  if (leftKey.value && !availableKeys.has(leftKey.value)) {
    leftKey.value = ''
  }
  if (rightKey.value && !availableKeys.has(rightKey.value)) {
    rightKey.value = ''
  }
}

function filteredOptions(query, blockedKey) {
  const needle = query.trim().toLowerCase()
  return sortedPlans.value
    .filter((plan) => planOptionKey(plan) !== blockedKey)
    .filter((plan) => !needle || searchablePlanText(plan).includes(needle))
    .slice(0, 80)
}

function searchablePlanText(plan) {
  const parts = [
    plan.providerName,
    plan.plan_name,
    plan.plan_description,
    plan.plan_overview,
    (plan.plan_benefits || []).join(' '),
    coverageTagsForPlan(plan).map(labelForTag).join(' '),
  ].filter(Boolean)
  if (locale.value === 'zh-SG') {
    parts.push(...parts.map((part) => translateContent(part, locale.value)))
  }
  return parts.join(' ').toLowerCase()
}

function selectPlan(slot, key) {
  if (slot === 'left') {
    leftKey.value = key
    if (rightKey.value === key) {
      rightKey.value = ''
    }
    return
  }
  rightKey.value = key
  if (leftKey.value === key) {
    leftKey.value = ''
  }
}

function clearSlot(slot) {
  if (slot === 'left') {
    leftKey.value = ''
    return
  }
  rightKey.value = ''
}

function providerFor(providerKey) {
  return providers.find((provider) => provider.key === providerKey) || providers[0]
}

function planOptionKey(plan) {
  return `${plan.providerKey || plan.insurer}::${plan.plan_slug || plan.plan_name}`
}

function uniqueKeys(keys) {
  return Array.from(new Set(keys.filter(Boolean)))
}

function loadStoredKeys() {
  try {
    const stored = JSON.parse(window.localStorage.getItem(STORAGE_KEY) || '[]')
    return Array.isArray(stored) ? stored.filter((key) => typeof key === 'string') : []
  } catch {
    return []
  }
}

function storeKeys(keys) {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(keys.slice(0, 2)))
  } catch {
    return
  }
}
</script>

<style scoped>
.compare-split-view {
  display: grid;
  gap: 20px;
}

.compare-heading,
.slot-header {
  display: flex;
  min-width: 0;
  gap: 16px;
  justify-content: space-between;
}

.compare-heading {
  align-items: flex-end;
}

.compare-actions {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  justify-content: flex-end;
}

.compare-heading h1,
.compare-heading p,
.slot-header h2,
.slot-header p,
.slot-header span,
.picker-empty {
  margin: 0;
}

.compare-heading h1 {
  font-size: 32px;
  line-height: 38px;
}

.compare-heading p:not(.eyebrow),
.slot-header span,
.picker-empty {
  color: var(--hf-secondary);
}

.eyebrow {
  margin: 0 0 4px;
  color: var(--hf-muted);
  font-size: 14px;
  font-weight: 700;
}

.split-picker-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.compare-slot {
  display: grid;
  min-width: 0;
  gap: 14px;
  padding: 18px;
}

.slot-header {
  align-items: start;
}

.slot-header div {
  display: grid;
  min-width: 0;
  gap: 4px;
}

.slot-header p {
  color: var(--hf-muted);
  font-size: 14px;
  font-weight: 700;
}

.slot-header h2 {
  overflow-wrap: anywhere;
  font-size: 22px;
  line-height: 28px;
}

.change-button,
.clear-button {
  border: 1px solid var(--hf-border);
  border-radius: var(--hf-radius-full);
  background: transparent;
  color: var(--hf-secondary);
  padding: 5px 10px;
  font-size: 13px;
  font-weight: 700;
}

.change-button:hover,
.clear-button:hover {
  border-color: var(--hf-tertiary);
  color: var(--hf-primary);
}

.picker-search .hub-input {
  width: 100%;
}

.tab-option-list {
  display: grid;
  max-height: min(52vh, 560px);
  overflow: auto;
  gap: 6px;
  padding-right: 4px;
}

.tab-option {
  display: grid;
  grid-template-columns: 48px minmax(0, 1fr);
  gap: 12px;
  align-items: center;
  width: 100%;
  border: 1px solid transparent;
  border-radius: var(--hf-radius-md);
  background: transparent;
  color: var(--hf-primary);
  padding: 10px;
  text-align: left;
}

.tab-option:hover,
.tab-option.selected {
  border-color: var(--hf-border);
  background: var(--hf-hover);
}

.tab-option.selected {
  border-color: var(--hf-active-border);
}

.tab-option span {
  display: grid;
  min-width: 0;
  gap: 2px;
}

.tab-option strong,
.tab-option small {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tab-option strong {
  font-size: 17px;
  line-height: 22px;
}

.tab-option small {
  color: var(--hf-secondary);
  font-size: 14px;
}

.picker-empty,
.pending-panel {
  padding: 16px;
}

.pending-panel {
  color: var(--hf-secondary);
}

@media (max-width: 900px) {
  .split-picker-grid,
  .compare-heading {
    grid-template-columns: 1fr;
  }

  .compare-heading {
    display: grid;
    align-items: start;
  }
}

@media (max-width: 640px) {
  .compare-heading h1 {
    font-size: 28px;
    line-height: 34px;
  }

  .slot-header {
    display: grid;
  }
}
</style>
