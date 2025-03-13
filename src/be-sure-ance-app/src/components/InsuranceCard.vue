<template>
    <div class="card">
        <div class="card-header" @click="$emit('toggle')">
            <a :href="link">{{ title }}</a></div>
            <Transition name="expand">
                <div class="card-content" v-show="expanded">
                    <InsuranceTable :plans="plans"/>
                </div>
            </Transition>
    </div>
</template>

<script setup>
import InsuranceTable from './InsuranceTable.vue'
defineProps({
title: String,
link: String,
plans: Array,
expanded: Boolean
})
defineEmits(['toggle'])
</script>