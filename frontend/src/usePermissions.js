import { computed, onMounted } from 'vue'
import { currentUser, refreshCurrentUser } from './userState'

export function usePermissions() {
  const canWriteAssets = computed(() =>
    (currentUser.value.permissions || []).includes('assets_write'),
  )
  const canWriteAllDepartments = computed(
    () => currentUser.value.role === 'super_admin' || currentUser.value.data_scope === 'all',
  )
  function canUseDepartment(department) {
    return (
      canWriteAllDepartments.value ||
      (!!currentUser.value.department_id && department.id === currentUser.value.department_id)
    )
  }
  function canEditAsset(item) {
    if (!canWriteAssets.value) return false
    if (canWriteAllDepartments.value) return true
    const user = currentUser.value
    return (
      !!user.department_id &&
      (item.department_id
        ? item.department_id === user.department_id
        : item.department === user.department)
    )
  }
  function defaultAssetDepartment() {
    return canWriteAllDepartments.value ? '' : currentUser.value.department || ''
  }
  onMounted(async () => {
    try {
      await refreshCurrentUser()
    } catch {}
  })
  return {
    canWriteAssets,
    canEditAsset,
    canUseDepartment,
    canWriteAllDepartments,
    defaultAssetDepartment,
  }
}
