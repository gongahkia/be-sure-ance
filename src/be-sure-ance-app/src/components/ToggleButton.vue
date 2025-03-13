<template>
    <div class="toggle-button" @click="$emit('toggle')">
    {{ isDark ? '🌞' : '🌚' }}
    </div>
</template>

<script setup>
defineProps({ isDark: Boolean })
defineEmits(['toggle'])
</script>