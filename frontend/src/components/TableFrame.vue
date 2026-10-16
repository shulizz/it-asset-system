<template>
  <section class="data-frame panel">
    <header class="table-heading">
      <div>
        <h3>{{ title }}</h3>
        <span class="record-count">{{ count }} 条记录</span>
      </div>
      <div class="frame-actions">
        <slot name="actions" /><span class="scroll-hint">左右滑动查看表格</span>
      </div>
    </header>
    <div class="table-scroll" tabindex="0" role="region" :aria-label="title"><slot /></div>
    <EmptyState v-if="count === 0" :title="emptyTitle" :description="emptyDescription" />
  </section>
</template>
<script setup>
import EmptyState from './EmptyState.vue'
defineProps({
  title: { type: String, default: '数据列表' },
  count: { type: Number, default: 0 },
  emptyTitle: { type: String, default: '暂无记录' },
  emptyDescription: {
    type: String,
    default: '数据录入后会在这里展示；如已设置筛选，可调整条件再试。',
  },
})
</script>
<style scoped>
.frame-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}
.data-frame.panel {
  padding: 0;
  min-width: 0;
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 10px;
  background: var(--surface);
}
.table-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--line);
}
.table-heading > div {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}
.table-heading h3 {
  font-size: 14px;
  font-weight: 600;
  white-space: nowrap;
}
.record-count {
  font-size: 11px;
  background: #f1f5f9;
  color: #63798d;
  border-radius: 5px;
  padding: 2px 7px;
  white-space: nowrap;
}
.table-scroll {
  overflow-x: auto;
  overscroll-behavior-x: contain;
  scrollbar-width: thin;
  min-width: 0;
}
.scroll-hint {
  display: none;
  font-size: 11px;
  color: var(--muted);
  white-space: nowrap;
}
@media (max-width: 760px) {
  .table-heading {
    padding: 14px 16px;
  }
  .scroll-hint {
    display: block;
  }
  .record-count {
    font-size: 10px;
  }
}
@media (max-width: 480px) {
  .table-heading {
    flex-wrap: wrap;
    gap: 8px;
  }
  .frame-actions {
    margin-left: auto;
  }
}
</style>
