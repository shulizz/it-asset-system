// A display role called "管理员" does not confer the reserved administrator identity.
export function hasMedicalAccess(user) {
  return user?.role === 'super_admin' || (!!user?.department_id && user?.medical_access === true)
}
