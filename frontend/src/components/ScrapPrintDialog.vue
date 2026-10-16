<template>
  <Teleport to="body">
    <div class="scrap-print-mask" @click.self="$emit('close')" @keydown.esc="$emit('close')">
      <section
        ref="dialog"
        class="scrap-print-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="scrap-print-title"
        tabindex="-1"
      >
        <header class="print-toolbar">
          <div>
            <h3 id="scrap-print-title">{{ record ? '打印报废申请单' : '打印空白报废单' }}</h3>
            <p>A5 竖版 · 可打印或另存为 PDF</p>
          </div>
          <div class="print-actions">
            <button class="btn-outline" @click="$emit('close')">关闭</button
            ><button class="btn-primary" :disabled="!ready" @click="print">打印 A5 报废单</button>
          </div>
        </header>
        <div class="print-content">
          <form class="print-options" @submit.prevent>
            <p class="print-hint">
              以下补充内容仅用于本次打印，不会修改系统记录。签字栏可打印后手写。
            </p>
            <label>单位名称<input v-model="extra.organization" maxlength="60" /></label>
            <label>规格型号<input v-model="extra.model" maxlength="60" /></label>
            <label>购置日期<input v-model="extra.purchaseDate" type="date" /></label>
            <label
              >原值（元）<input v-model="extra.originalValue" type="number" min="0" step="0.01"
            /></label>
            <label>保管 / 使用人<input v-model="extra.custodian" maxlength="40" /></label>
            <label>数量<input v-model="extra.quantity" type="number" min="1" step="1" /></label>
            <label v-if="!record"
              >报废原因<textarea v-model="extra.reason" maxlength="600" rows="3"></textarea>
            </label>
            <label>备注<textarea v-model="extra.notes" maxlength="200" rows="3"></textarea></label>
            <p class="print-hint">
              打印设置请选择 A5、纵向，并关闭页眉和页脚。长篇原因可能续页，请以打印预览为准。
            </p>
          </form>
          <div class="paper-preview">
            <iframe
              ref="frame"
              title="A5 报废申请单预览"
              :srcdoc="documentHtml"
              sandbox="allow-same-origin allow-modals"
              @load="ready = true"
            ></iframe>
          </div>
        </div>
        <p v-if="printError" role="alert" class="print-error">{{ printError }}</p>
      </section>
    </div>
  </Teleport>
</template>
<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { buildScrapPrintDocument } from '../scrapPrint'
const props = defineProps({ record: { type: Object, default: null } })
defineEmits(['close'])
const extra = reactive({
  organization: '',
  model: '',
  purchaseDate: '',
  originalValue: '',
  custodian: '',
  quantity: '',
  reason: '',
  notes: props.record?.notes || '',
})
const frame = ref(null),
  dialog = ref(null),
  ready = ref(false),
  printError = ref('')
const documentHtml = computed(() => buildScrapPrintDocument(props.record, extra))
watch(documentHtml, () => {
  ready.value = false
})
let previousFocus, previousOverflow
onMounted(async () => {
  previousFocus = document.activeElement
  previousOverflow = document.body.style.overflow
  document.body.style.overflow = 'hidden'
  await nextTick()
  dialog.value?.focus()
})
onBeforeUnmount(() => {
  document.body.style.overflow = previousOverflow
  previousFocus?.focus()
})
function print() {
  printError.value = ''
  try {
    frame.value.contentWindow.focus()
    frame.value.contentWindow.print()
  } catch {
    printError.value = '无法打开打印窗口，请使用浏览器打开本系统后重试。'
  }
}
</script>
<style scoped>
.scrap-print-mask {
  position: fixed;
  inset: 0;
  z-index: 1200;
  background: #122d4080;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}
.scrap-print-dialog {
  width: min(1080px, 100%);
  max-height: calc(100dvh - 40px);
  overflow: auto;
  background: #fff;
  border-radius: 12px;
}
.print-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 20px 24px;
  border-bottom: 1px solid var(--line);
}
.print-toolbar h3 {
  margin: 0 0 5px;
}
.print-toolbar p {
  margin: 0;
  color: var(--muted);
  font-size: 12px;
}
.print-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}
.print-content {
  display: grid;
  grid-template-columns: 260px minmax(0, 1fr);
}
.print-options {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.print-options label {
  display: flex;
  flex-direction: column;
  gap: 5px;
  font-size: 12px;
}
.print-options input,
.print-options textarea {
  width: 100%;
  min-height: 38px;
  padding: 8px 10px;
  color: var(--ink);
  border: 1px solid var(--line);
  border-radius: 6px;
  background: white;
}
.print-hint {
  color: var(--muted);
  font-size: 12px;
  line-height: 1.7;
  margin: 0;
}
.paper-preview {
  background: #edf1f5;
  overflow: auto;
}
.paper-preview iframe {
  display: block;
  width: 630px;
  height: 870px;
  max-width: none;
  border: 0;
}
.print-error {
  color: #b42318;
  padding: 0 20px 16px;
}
@media (max-width: 760px) {
  .scrap-print-mask {
    padding: 8px;
  }
  .scrap-print-dialog {
    max-height: calc(100dvh - 16px);
  }
  .print-toolbar {
    padding: 16px;
    align-items: flex-start;
    flex-direction: column;
  }
  .print-content {
    grid-template-columns: minmax(0, 1fr);
  }
  .print-options {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    padding: 16px;
  }
  .print-hint {
    grid-column: 1 / -1;
  }
  .paper-preview {
    height: 480px;
  }
  .print-actions {
    width: 100%;
  }
  .print-actions button {
    flex: 1;
  }
}
</style>
