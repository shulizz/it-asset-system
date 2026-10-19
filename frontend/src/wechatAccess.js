export function hasLegacyWeChatAccess(user) {
  return (
    user?.role === 'super_admin' ||
    ((user?.permissions || []).includes('wechat') && user.data_scope === 'all')
  )
}
export function hasWeChatRead(user) {
  return hasLegacyWeChatAccess(user) || (user?.permissions || []).includes('wechat_read')
}
export function hasWeChatEdit(user) {
  return (
    hasLegacyWeChatAccess(user) ||
    (hasWeChatRead(user) && (user?.permissions || []).includes('wechat_edit'))
  )
}
