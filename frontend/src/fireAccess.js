// Fire equipment is reserved for the super administrator until grants are introduced.
export const hasFireAccess = (user) => user.role === 'super_admin'
