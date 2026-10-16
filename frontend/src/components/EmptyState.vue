<template>
  <div class="empty-state">
    <span class="empty-symbol"><AppIcon :name="icon" /></span>
    <p>{{ title }}</p>
    <span v-if="description" class="empty-description">{{ description }}</span>
  </div>
</template>
<script setup>
import AppIcon from './AppIcon.vue'
defineProps({
  title: { type: String, default: '暂无记录' },
  description: { type: String, default: '' },
  icon: { type: String, default: 'asset' },
})
</script>
<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 34px 16px;
  text-align: center;
  gap: 7px;
  color: var(--muted);
}
.empty-symbol {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  border: 1px solid var(--line);
  background: #f6f9fc;
  border-radius: 12px;
  margin-bottom: 6px;
  color: #8499ac;
}
.empty-symbol .app-icon {
  width: 24px;
  height: 24px;
}
.empty-state p {
  font-size: 13px;
  font-weight: 500;
  color: #536a80;
}
.empty-description {
  font-size: 12px;
  line-height: 1.7;
  max-width: 280px;
}
</style>
