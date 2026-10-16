import { computed, onMounted } from 'vue'
import { currentUser, refreshCurrentUser } from './userState'

export function usePermissions() {
  const canWriteAssets = computed(() =>
    (currentUser.value.permissions || []).includes('assets_write'),
  )
  onMounted(async () => {
    try {
      await refreshCurrentUser()
    } catch {}
  })
  return { canWriteAssets }
}
