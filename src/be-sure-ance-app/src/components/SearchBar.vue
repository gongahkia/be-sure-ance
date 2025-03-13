<template>
    <input type="text" class="search-bar" placeholder="Search plans..."
    :value="modelValue" @input="$emit('update:modelValue', $event.target.value)" />
</template>

<script setup>
defineProps(['modelValue'])
defineEmits(['update:modelValue'])
</script>