<template>
  <div style="padding:16px">
    <h1>设置</h1>
    <section class="pane" style="max-width:420px">
      <h2>逾期宽限日</h2>
      <div class="muted">逾期 = 今天 ＞ 应还日 + 宽限日。改后看板顶栏、在借 / 逾期、借还记录立即一起重算。</div>
      <div style="margin-top:8px">
        <input v-model="graceDays" inputmode="numeric" placeholder="0 或正整数" style="width:120px" />
        <button @click="save" :disabled="saving">{{ saving ? '保存中…' : '保存' }}</button>
      </div>
      <div v-if="error" class="muted" style="color:#c0392b">{{ error }}</div>
      <div class="muted" style="margin-top:12px">邻里板：{{ boardName }}</div>
    </section>
  </div>
</template>
<script setup>
import { ref, inject, onMounted } from 'vue'
import { api } from '../api'
const reloadBoard = inject('reloadBoard')
const graceDays = ref('0')
const savedGrace = ref('0')
const boardName = ref('')
const error = ref('')
const saving = ref(false)

onMounted(async () => {
  const s = await api('/settings')
  boardName.value = s.board_name || ''
  savedGrace.value = /^\d+$/.test((s.grace_days ?? '').trim()) ? String(parseInt(s.grace_days, 10)) : '0'
  graceDays.value = savedGrace.value
})

async function save() {
  error.value = ''
  const raw = String(graceDays.value ?? '').trim()
  // zero or a positive integer only; on a bad value revert the field to the
  // last saved value and never call the API, so the bar stays unchanged.
  if (!/^\d+$/.test(raw)) {
    error.value = '宽限日需为 0 或正整数'
    graceDays.value = savedGrace.value
    return
  }
  saving.value = true
  try {
    await api('/settings/grace_days', { method: 'PUT', body: JSON.stringify({ grace_days: parseInt(raw, 10) }) })
    savedGrace.value = raw
    graceDays.value = raw
    await reloadBoard()
  } catch (e) {
    error.value = e.message || '保存失败'
    graceDays.value = savedGrace.value
  } finally {
    saving.value = false
  }
}
</script>
