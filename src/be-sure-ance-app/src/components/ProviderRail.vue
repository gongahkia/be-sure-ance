<template>
  <aside class="provider-rail">
    <p class="rail-label">Providers</p>
    <button
      v-for="provider in providers"
      :key="provider.key"
      :class="['provider-chip', { active: provider.key === activeProviderKey }]"
      type="button"
      @click="$emit('select', provider.key)"
    >
      <span class="provider-name">{{ provider.name }}</span>
      <span class="provider-meta">{{ providerCounts[provider.key] || 0 }} plans</span>
    </button>
  </aside>
</template>

<script setup>
defineProps({
  providers: Array,
  activeProviderKey: String,
  providerCounts: Object
})

defineEmits(["select"])
</script>

<style scoped>
.provider-rail {
  display: grid;
  gap: 0.8rem;
}

.rail-label {
  margin: 0;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--muted-ink);
}

.provider-chip {
  display: grid;
  gap: 0.2rem;
  width: 100%;
  padding: 1rem 1.1rem;
  border: 1px solid rgba(16, 39, 71, 0.12);
  border-radius: 1rem;
  background: rgba(255, 255, 255, 0.8);
  text-align: left;
  cursor: pointer;
  transition: transform 0.2s ease, border-color 0.2s ease, background 0.2s ease;
}

.provider-chip:hover,
.provider-chip:focus-visible {
  transform: translateY(-1px);
  border-color: rgba(16, 39, 71, 0.35);
  outline: none;
}

.provider-chip.active {
  background: linear-gradient(135deg, rgba(16, 39, 71, 0.96), rgba(30, 90, 138, 0.92));
  border-color: transparent;
  color: #f8fbff;
}

.provider-name {
  font-weight: 700;
}

.provider-meta {
  font-size: 0.88rem;
  color: inherit;
  opacity: 0.78;
}
</style>
