export const hasFireAccess = (user) =>
  user.role === 'super_admin' ||
  (user.data_scope === 'all' && (user.permissions || []).includes('fire'))
