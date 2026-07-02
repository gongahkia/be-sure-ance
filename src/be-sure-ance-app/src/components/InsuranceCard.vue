<template>
  <div class="card">
    <div class="card-header" @click="$emit('toggle')">
      <a
        v-if="safeExternalUrl(link)"
        :href="safeExternalUrl(link)"
        rel="noopener noreferrer"
        referrerpolicy="no-referrer"
        target="_blank"
      >
        {{ title }}
      </a>
      <span v-else>{{ title }}</span>
    </div>
    <Transition name="expand">
      <div class="card-content" v-show="expanded">
        <InsuranceTable
          :plans="plans"
          :insurer-key="insurerKey"
          :specialist-resources="specialistResources"
        />
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { safeExternalUrl } from '../utils/links'

import InsuranceTable from './InsuranceTable.vue'
defineProps({
  title: String,
  link: String,
  plans: Array,
  expanded: Boolean,
  insurerKey: String,
  specialistResources: Array,
})
defineEmits(['toggle'])
</script>
