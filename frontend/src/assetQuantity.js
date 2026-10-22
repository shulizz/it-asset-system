// Missing quantities belong to legacy single-device records.
export const assetQuantity = (item) => item.quantity ?? 1
export const totalQuantity = (items) => items.reduce((sum, item) => sum + assetQuantity(item), 0)
