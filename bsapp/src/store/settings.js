import { defineStore } from 'pinia'
import { ref } from 'vue'
import { currentLang, setAppLanguage } from '@/utils/i18n'

export const useSettingsStore = defineStore('settings', () => {
  const language = ref(currentLang.value)
  const darkMode = ref(false)
  const displayName = ref('')
  const avatarUrl = ref('')
  const communityTextMode = ref('summary')
  const recipeNotifications = ref(true)
  const nutritionNotifications = ref(true)
  const wifiSyncOnly = ref(true)

  async function init() {
    try {
      language.value = uni.getStorageSync('app_language') || 'zh'
      darkMode.value = uni.getStorageSync('pref_dark_mode') || false
      displayName.value = uni.getStorageSync('pref_display_name') || ''
      avatarUrl.value = uni.getStorageSync('pref_avatar_url') || ''
      communityTextMode.value = uni.getStorageSync('pref_community_text_mode') || 'summary'
      recipeNotifications.value = uni.getStorageSync('pref_notification_recipes') !== false
      nutritionNotifications.value = uni.getStorageSync('pref_notification_nutrition') !== false
      wifiSyncOnly.value = uni.getStorageSync('pref_wifi_sync_only') !== false
    } catch (e) {
      console.error('Settings init error:', e)
    }
  }

  function setLanguage(lang) {
    language.value = lang
    setAppLanguage(lang)
  }

  function setDarkMode(value) {
    darkMode.value = value
    uni.setStorageSync('pref_dark_mode', value)
  }

  function setDisplayName(name) {
    displayName.value = name
    uni.setStorageSync('pref_display_name', name)
  }

  function setAvatarUrl(url) {
    avatarUrl.value = url || ''
    uni.setStorageSync('pref_avatar_url', avatarUrl.value)
  }

  function setCommunityTextMode(mode) {
    communityTextMode.value = mode === 'full' ? 'full' : 'summary'
    uni.setStorageSync('pref_community_text_mode', communityTextMode.value)
  }

  function setRecipeNotifications(value) {
    recipeNotifications.value = value
    uni.setStorageSync('pref_notification_recipes', value)
  }

  function setNutritionNotifications(value) {
    nutritionNotifications.value = value
    uni.setStorageSync('pref_notification_nutrition', value)
  }

  function setWifiSyncOnly(value) {
    wifiSyncOnly.value = value
    uni.setStorageSync('pref_wifi_sync_only', value)
  }

  return {
    language, darkMode, displayName, avatarUrl, communityTextMode,
    recipeNotifications, nutritionNotifications, wifiSyncOnly,
    init, setLanguage, setDarkMode, setDisplayName,
    setAvatarUrl, setCommunityTextMode,
    setRecipeNotifications, setNutritionNotifications, setWifiSyncOnly
  }
})
