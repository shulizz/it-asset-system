import { ref, computed, onMounted } from 'vue'
import api from './api'

export function usePermissions() {
  const permissions = ref([])
  const canWriteAssets = computed(() => permissions.value.includes('assets_write'))
  onMounted(async () => {
    try { permissions.value = (await api.get('/auth/me')).data.permissions || [] }
    catch { permissions.value = [] }
  })
  return { canWriteAssets }
}
