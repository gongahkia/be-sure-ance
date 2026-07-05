<template>
  <span class="provider-logo" :class="[`size-${size}`, { failed: logoFailed }]">
    <img
      v-if="logoSrc && !logoFailed"
      :src="logoSrc"
      alt=""
      loading="lazy"
      decoding="async"
      referrerpolicy="no-referrer"
      @error="logoFailed = true"
    />
    <span v-else>{{ initials }}</span>
  </span>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  provider: {
    type: Object,
    default: () => ({}),
  },
  size: {
    type: String,
    default: 'md',
  },
})

const logoFailed = ref(false)

watch(
  () => props.provider?.key,
  () => {
    logoFailed.value = false
  },
)

const logoSrc = computed(() => {
  if (props.provider?.logoUrl) {
    return props.provider.logoUrl
  }
  if (!props.provider?.website) {
    return ''
  }
  try {
    const hostname = new URL(props.provider.website).hostname.replace(/^www\./, '')
    return `https://www.google.com/s2/favicons?sz=128&domain=${encodeURIComponent(hostname)}`
  } catch {
    return ''
  }
})

const initials = computed(() =>
  String(props.provider?.name || props.provider?.key || 'B')
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part.slice(0, 1))
    .join('')
    .toUpperCase(),
)
</script>

<style scoped>
.provider-logo {
  display: inline-grid;
  flex: 0 0 auto;
  place-items: center;
  overflow: hidden;
  border: 1px solid var(--hf-border);
  border-radius: var(--hf-radius-md);
  background: #ffffff;
  color: #111827;
  font-weight: 800;
}

.provider-logo img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: contain;
  padding: 4px;
}

.provider-logo.failed {
  background: var(--hf-surface-2);
  color: var(--hf-accent);
}

.provider-logo.size-sm {
  width: 24px;
  height: 24px;
  font-size: 11px;
}

.provider-logo.size-md {
  width: 34px;
  height: 34px;
  font-size: 13px;
}

.provider-logo.size-lg {
  width: 48px;
  height: 48px;
  font-size: 16px;
}
</style>
