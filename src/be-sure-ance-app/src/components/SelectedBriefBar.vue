<template>
  <section class="selected-brief">
    <div class="brief-summary">
      <span class="hub-chip strong">{{
        t('ui.selected.count', { count: selectedPlans.length, max: maxPlans })
      }}</span>
      <div class="selected-list">
        <button
          v-for="plan in selectedPlans"
          :key="plan.key"
          type="button"
          class="selected-plan"
          @click="$emit('remove', plan.key)"
        >
          <span>{{ plan.plan_name }}</span>
          <strong>{{ t('ui.selected.remove') }}</strong>
        </button>
      </div>
    </div>
    <div class="brief-actions">
      <BriefExportPanel :selected-plans="selectedPlans" compact />
      <ShareComparisonPanel :selected-plans="selectedPlans" compact />
    </div>
  </section>
</template>

<script setup>
import BriefExportPanel from './BriefExportPanel.vue'
import ShareComparisonPanel from './ShareComparisonPanel.vue'
import { useI18n } from '../i18n'

defineProps({
  selectedPlans: {
    type: Array,
    default: () => [],
  },
})

defineEmits(['remove'])

const { t } = useI18n()
const maxPlans = 10
</script>

<style scoped>
.selected-brief {
  position: sticky;
  top: 72px;
  z-index: 12;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 14px;
  align-items: center;
  padding: 10px 24px;
  border-bottom: 1px solid var(--hf-border);
  background: var(--hf-briefbar);
  backdrop-filter: blur(16px);
}

.brief-summary,
.selected-list,
.brief-actions {
  display: flex;
  min-width: 0;
  gap: 10px;
  align-items: center;
}

.selected-list {
  overflow-x: auto;
}

.selected-plan {
  display: inline-flex;
  max-width: 240px;
  min-height: 34px;
  align-items: center;
  gap: 8px;
  padding: 5px 10px;
  border: 1px solid var(--hf-border);
  border-radius: var(--hf-radius-full);
  background: var(--hf-neutral);
  color: var(--hf-secondary);
  white-space: nowrap;
}

.selected-plan span {
  overflow: hidden;
  text-overflow: ellipsis;
}

.selected-plan strong {
  color: var(--hf-primary);
  font-size: 12px;
}

@media (max-width: 920px) {
  .selected-brief {
    position: static;
    grid-template-columns: 1fr;
  }

  .brief-actions {
    flex-wrap: wrap;
  }
}
</style>
