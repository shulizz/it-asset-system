<template>
  <header class="page-heading">
    <div class="page-heading-copy">
      <h2>{{ title }}</h2>
      <p>{{ description }}</p>
    </div>
    <div v-if="$slots.default" class="page-actions"><slot /></div>
  </header>
</template>
<script setup>
defineProps({ title: String, description: String })
</script>
<style scoped>
.page-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  margin-bottom: 22px;
}
.page-heading-copy {
  min-width: 0;
}
.page-heading h2 {
  font-size: 22px;
  font-weight: 650;
  letter-spacing: -0.3px;
  color: var(--ink);
}
.page-heading p {
  color: var(--muted);
  font-size: 12px;
  margin-top: 6px;
  line-height: 1.7;
}
.page-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
}
@media (max-width: 760px) {
  .page-heading {
    align-items: flex-start;
    flex-direction: column;
    gap: 14px;
    margin-bottom: 18px;
  }
  .page-actions {
    justify-content: flex-start;
    width: 100%;
  }
  .page-heading h2 {
    font-size: 21px;
  }
}
</style>
