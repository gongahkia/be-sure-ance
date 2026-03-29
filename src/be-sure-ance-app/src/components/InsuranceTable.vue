<template>
  <table v-if="plans.length > 0">
    <thead>
      <tr>
        <th>Name</th>
        <th>Description</th>
        <th>Benefits</th>
        <th>Overview</th>
        <th>Brochure</th>
        <th>Panel / Specialist</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="plan in plans" :key="plan.id">
        <td>
          <a
            v-if="safeExternalUrl(plan.plan_url)"
            :href="safeExternalUrl(plan.plan_url)"
            rel="noopener noreferrer"
            referrerpolicy="no-referrer"
            target="_blank"
          >
            {{ plan.plan_name }}
          </a>
          <span v-else>{{ plan.plan_name }}</span>
        </td>
        <td>{{ plan.plan_description }}</td>
        <td>
          <ul>
            <li v-for="benefit in plan.plan_benefits" :key="benefit">{{ benefit }}</li>
          </ul>
        </td>
        <td>{{ plan.plan_overview }}</td>
        <td>
          <a
            v-if="safeExternalUrl(plan.product_brochure_url)"
            :href="safeExternalUrl(plan.product_brochure_url)"
            rel="noopener noreferrer"
            referrerpolicy="no-referrer"
            target="_blank"
          >
            Brochure Link
          </a>
          <span v-else>Unavailable</span>
        </td>
        <td>
          <ul v-if="resourcesForPlan(plan).length > 0">
            <li v-for="resource in resourcesForPlan(plan)" :key="resource.id || resource.resource_url">
              <a
                v-if="safeExternalUrl(resource.resource_url)"
                :href="safeExternalUrl(resource.resource_url)"
                rel="noopener noreferrer"
                referrerpolicy="no-referrer"
                target="_blank"
              >
                {{ resource.resource_title || resource.resource_type }}
              </a>
              <span v-else>{{ resource.resource_title || resource.resource_type }}</span>
              <span v-if="resource.resource_description"> - {{ resource.resource_description }}</span>
            </li>
          </ul>
          <span v-else>No directory found.</span>
        </td>
      </tr>
    </tbody>
  </table>
  <div v-else>
    No results found.
  </div>
</template>

<script setup>
import { computed } from 'vue'

import { safeExternalUrl } from '../utils/links'

const props = defineProps({
  plans: Array,
  insurerKey: String,
  specialistResources: Array
})

const planResourceMap = computed(() => {
  const resources = Array.isArray(props.specialistResources) ? props.specialistResources : []
  return resources
    .filter((resource) => resource.insurer === props.insurerKey)
    .reduce((accumulator, resource) => {
      const key = resource.plan_name || ""
      if (!accumulator[key]) {
        accumulator[key] = []
      }
      accumulator[key].push(resource)
      return accumulator
    }, {})
})

function resourcesForPlan(plan) {
  return planResourceMap.value[plan.plan_name] || []
}
</script>
