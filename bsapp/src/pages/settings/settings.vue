<template>
  <view class="settings-page">
    <!-- 语言 -->
    <text class="section-title">{{ $t('language') }}</text>
    <view class="card">
      <label class="radio-row" @tap="changeLang('zh')">
        <text>{{ $t('chinese') }}</text>
        <view class="radio" :class="{ active: language === 'zh' }"></view>
      </label>
      <view class="radio-divider"></view>
      <label class="radio-row" @tap="changeLang('en')">
        <text>{{ $t('english') }}</text>
        <view class="radio" :class="{ active: language === 'en' }"></view>
      </label>
    </view>

    <!-- 个人信息 -->
    <text class="section-title">{{ $t('personalInfo') }}</text>
    <view class="card">
      <view class="info-row">
        <text>{{ $t('displayName') }}</text>
        <view class="info-right">
          <text class="info-value">{{ displayName || $t('defaultName') }}</text>
          <text class="info-edit" @tap="editDisplayName">{{ $t('edit') }}</text>
        </view>
      </view>
    </view>

    <!-- 通知 -->
    <text class="section-title">{{ $t('notificationSettings') }}</text>
    <view class="card">
      <view class="switch-row">
        <text>{{ $t('recipeRecommendations') }}</text>
        <switch :checked="recipeNotif" @change="onRecipeNotif" color="#165DFF" />
      </view>
      <view class="radio-divider"></view>
      <view class="switch-row">
        <text>{{ $t('nutritionReminders') }}</text>
        <switch :checked="nutritionNotif" @change="onNutritionNotif" color="#165DFF" />
      </view>
    </view>

    <!-- 偏好 -->
    <text class="section-title">{{ $t('systemPreferences') }}</text>
    <view class="card">
      <view class="switch-row">
        <view>
          <text>{{ $t('syncOverWifiOnly') }}</text>
          <text class="switch-hint">{{ $t('syncOverWifiOnlyTip') }}</text>
        </view>
        <switch :checked="wifiOnly" @change="onWifiOnly" color="#165DFF" />
      </view>
    </view>

    <!-- 安全 -->
    <text class="section-title">{{ $t('privacyAndSecurity') }}</text>
    <view class="card">
      <view class="info-row" @tap="clearCache">
        <text>{{ $t('clearCache') }}</text>
        <view class="info-right">
          <text class="info-value">{{ $t('cacheSize') }}</text>
          <text class="info-edit">{{ $t('clear') }}</text>
        </view>
      </view>
      <view class="radio-divider"></view>
      <view class="info-row" @tap="showPrivacy">
        <text>{{ $t('privacyPolicy') }}</text>
        <text class="menu-arrow">›</text>
      </view>
    </view>

    <!-- 账户 -->
    <text class="section-title">{{ $t('account') }}</text>
    <button class="btn-logout" @tap="handleLogout">{{ $t('logout') }}</button>

    <!-- 关于 -->
    <text class="section-title">{{ $t('aboutApp') }}</text>
    <view class="card">
      <view class="info-row">
        <text>{{ $t('appVersion') }}</text>
        <text class="info-value">{{ $t('versionInfo') }}</text>
      </view>
    </view>

    <view style="height: 60rpx;"></view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { useSettingsStore } from '@/store/settings'
import { useAuthStore } from '@/store/auth'
import { ApiService } from '@/api/index'
import { t } from '@/utils/i18n'

const $t = key => t(key)
const settingsStore = useSettingsStore()
const authStore = useAuthStore()

const language = ref('zh')
const darkMode = ref(false)
const displayName = ref('')
const recipeNotif = ref(true)
const nutritionNotif = ref(true)
const wifiOnly = ref(true)

onShow(() => {
  language.value = settingsStore.language
  darkMode.value = settingsStore.darkMode
  displayName.value = settingsStore.displayName
  recipeNotif.value = settingsStore.recipeNotifications
  nutritionNotif.value = settingsStore.nutritionNotifications
  wifiOnly.value = settingsStore.wifiSyncOnly
})

function changeLang(lang) {
  if (lang === language.value) return
  language.value = lang
  settingsStore.setLanguage(lang)
  uni.showToast({ title: lang === 'zh' ? '已切换为中文' : 'Switched to English', icon: 'success' })
}

function onDarkMode(e) {
  const isDark = e.detail.value
  darkMode.value = isDark
  settingsStore.setDarkMode(isDark)
  // 立即生效暗色模式
  if (uni.$applyDarkMode) {
    uni.$applyDarkMode(isDark)
  }
}
function onRecipeNotif(e) {
  recipeNotif.value = e.detail.value
  settingsStore.setRecipeNotifications(e.detail.value)
}
function onNutritionNotif(e) {
  nutritionNotif.value = e.detail.value
  settingsStore.setNutritionNotifications(e.detail.value)
}
function onWifiOnly(e) {
  wifiOnly.value = e.detail.value
  settingsStore.setWifiSyncOnly(e.detail.value)
}

function editDisplayName() {
  uni.showModal({
    title: $t('changeDisplayName'),
    content: '',
    editable: true,
    placeholderText: $t('enterNewDisplayName'),
    success: (res) => {
      if (res.confirm && res.content && res.content.trim()) {
        const newDisplayName = res.content.trim()
        displayName.value = newDisplayName
        settingsStore.setDisplayName(newDisplayName)
        uni.showToast({ title: $t('nameUpdated'), icon: 'success' })
      }
    }
  })
}

function clearCache() {
  uni.showToast({ title: $t('cacheCleared'), icon: 'success' })
}

function showPrivacy() {
  uni.showToast({ title: $t('privacyPolicyComingSoon'), icon: 'none' })
}

async function handleLogout() {
  const res = await new Promise(r => {
    uni.showModal({
      title: $t('logoutConfirmTitle'),
      content: $t('logoutConfirmMessage'),
      success: r
    })
  })
  if (res.confirm) {
    await ApiService.logout()
    await authStore.logout()
    uni.redirectTo({ url: '/pages/login/login' })
  }
}
</script>

<style scoped>
.settings-page {
  min-height: 100vh;
  background: var(--bg-color);
  padding: 24rpx;
}
.section-title {
  font-size: 32rpx;
  font-weight: bold;
  color: var(--text-color);
  margin: 28rpx 0 16rpx;
  display: block;
}
.card {
  background: var(--card-bg);
  border-radius: 16rpx;
  overflow: hidden;
}
.radio-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 28rpx 24rpx;
  font-size: 28rpx;
  color: var(--text-color);
}
.radio-divider {
  height: 1rpx;
  background: var(--border-light);
  margin: 0 24rpx;
}
.radio {
  width: 36rpx;
  height: 36rpx;
  border: 3rpx solid var(--border-color);
  border-radius: 50%;
}
.radio.active {
  border-color: var(--accent);
  background: var(--accent);
  box-shadow: inset 0 0 0 4rpx #fff;
}
.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 28rpx 24rpx;
  font-size: 28rpx;
  color: var(--text-color);
}
.info-right { display: flex; align-items: center; gap: 12rpx; }
.info-value { color: var(--text-secondary); font-size: 26rpx; }
.info-edit { color: var(--accent); font-size: 26rpx; }
.menu-arrow { font-size: 32rpx; color: var(--text-muted); }
.switch-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24rpx;
  color: var(--text-color);
}
.switch-hint {
  font-size: 22rpx;
  color: var(--text-secondary);
  display: block;
  margin-top: 4rpx;
}
.btn-logout {
  width: 100%;
  height: 88rpx;
  background: var(--danger);
  color: #fff;
  border: none;
  border-radius: 16rpx;
  font-size: 32rpx;
  font-weight: bold;
  margin-top: 12rpx;
}
</style>
