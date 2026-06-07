import { defineStore } from 'pinia'
import { ref } from 'vue'

const MAX_RECORDS = 100
const HISTORY_KEY = 'app_history_records'

export const useHistoryStore = defineStore('history', () => {
  const items = ref([])

  async function loadHistory() {
    try {
      const raw = uni.getStorageSync(HISTORY_KEY) || '[]'
      items.value = JSON.parse(raw)
    } catch (e) {
      items.value = []
    }
  }

  function addEntry(entry) {
    items.value.unshift({
      type: entry.type || 'unknown',
      title: entry.title || '',
      detail: entry.detail || '',
      recipeId: entry.recipeId || '',
      createdAt: entry.createdAt || new Date().toISOString()
    })
    if (items.value.length > MAX_RECORDS) {
      items.value.splice(MAX_RECORDS)
    }
    uni.setStorageSync(HISTORY_KEY, JSON.stringify(items.value))
  }

  function clearHistory() {
    items.value = []
    uni.removeStorageSync(HISTORY_KEY)
  }

  function formatTime(dateStr) {
    const d = new Date(dateStr)
    const pad = n => String(n).padStart(2, '0')
    return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
  }

  return { items, loadHistory, addEntry, clearHistory, formatTime }
})
