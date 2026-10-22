<template>
  <svg
    class="app-icon"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.65"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
    focusable="false"
  >
    <path v-for="(path, index) in paths[name] || paths.asset" :key="index" :d="path" />
  </svg>
</template>
<script setup>
defineProps({ name: { type: String, default: 'asset' } })
const paths = {
  asset: ['M3 7 12 3l9 4-9 4-9-4Z', 'M3 7v10l9 4 9-4V7', 'M12 11v10'],
  dashboard: ['M3 3h7v7H3z', 'M14 3h7v4h-7z', 'M14 11h7v10h-7z', 'M3 14h7v7H3z'],
  it: ['M3 4h18v12H3z', 'M8 21h8', 'M12 16v5'],
  phone: [
    'M8 2h8a2 2 0 0 1 2 2v16a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2Z',
    'M10 5h4',
    'M11 19h2',
  ],
  fire: ['M12 3c2 4 6 5 6 10a6 6 0 0 1-12 0c0-3 2-5 3-6v5c2-2 3-5 3-9Z'],
  medical: ['M4 4h16v16H4z', 'M12 8v8', 'M8 12h8'],
  number: ['M5 5h14v14H5z', 'M9 2v6', 'M15 2v6', 'M9 12h6', 'M9 16h3'],
  wechat: [
    'M21 11a8 8 0 0 1-8 8H8l-5 3 1-6a8 8 0 1 1 17-5Z',
    'M8 10h.01',
    'M13 10h.01',
    'M17 10h.01',
  ],
  transfer: ['M3 7h17', 'm16 3 4 4-4 4', 'M21 17H4', 'm8 13-4 4 4 4'],
  scrap: ['M4 6h16', 'M9 6V3h6v3', 'M6 6l1 15h10l1-15', 'M10 10v7', 'M14 10v7'],
  reports: ['M4 3v18h17', 'M8 16v-4', 'M13 16V8', 'M18 16V5'],
  apply: ['M5 3h10l4 4v14H5z', 'M14 3v5h5', 'M9 13h6', 'M9 17h4'],
  idle: ['M12 3a9 9 0 1 1-9 9 9 9 0 0 1 9-9Z', 'M9 8v8', 'M15 8v8'],
  approval: ['M9 3h6v4H9z', 'M9 5H5v16h14V5h-4', 'm8 14 3 3 5-6'],
  departments: ['M4 21V4h11v17', 'M15 10h5v11', 'M8 8h3', 'M8 12h3', 'M8 16h3', 'M2 21h20'],
  users: [
    'M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2',
    'M9 3a4 4 0 1 1 0 8 4 4 0 0 1 0-8Z',
    'M17 4a4 4 0 0 1 0 7',
    'M22 21v-2a4 4 0 0 0-3-4',
  ],
  logs: ['M5 3h14v18H5z', 'M9 7h6', 'M9 12h6', 'M9 17h4'],
  check: ['m5 12 4 4L19 6'],
  clock: ['M12 3a9 9 0 1 1 0 18 9 9 0 0 1 0-18Z', 'M12 7v5l3 2'],
  calendar: ['M4 5h16v16H4z', 'M8 3v4', 'M16 3v4', 'M4 10h16', 'M8 14h2', 'M14 14h2'],
  arrow: ['M5 12h14', 'm14 7 5 5-5 5'],
  logout: ['M9 3H4v18h5', 'M8 12h13', 'm17 8 4 4-4 4'],
  menu: ['M4 6h16', 'M4 12h16', 'M4 18h16'],
  shield: ['m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6l8-3Z', 'm8 12 3 3 5-6'],
}
</script>
<style scoped>
.app-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  vertical-align: middle;
}
</style>
