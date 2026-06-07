<template>
  <view class="settings-page">
    <view class="settings-header">
      <text class="page-title">{{ $t('systemSettings') }}</text>
      <text class="page-sub">语言、提醒和本地偏好集中管理</text>
    </view>

    <view class="settings-group">
      <text class="section-title">{{ $t('language') }}</text>
      <view class="segmented">
        <view class="seg-item" :class="{ active: language === 'zh' }" @tap="changeLang('zh')">
          <text>{{ $t('chinese') }}</text>
        </view>
        <view class="seg-item" :class="{ active: language === 'en' }" @tap="changeLang('en')">
          <text>{{ $t('english') }}</text>
        </view>
      </view>
    </view>

    <view class="settings-group">
      <text class="section-title">{{ $t('personalInfo') }}</text>
      <view class="card">
        <view class="info-row">
          <view class="row-left">
            <view class="row-icon"><image src="/static/icons/icon_avatar.svg" mode="aspectFit" /></view>
            <view>
              <text class="row-title">{{ $t('displayName') }}</text>
              <text class="row-hint">{{ displayName || $t('defaultName') }}</text>
            </view>
          </view>
          <text class="info-edit" @tap="editDisplayName">{{ $t('edit') }}</text>
        </view>
      </view>
    </view>

    <view class="settings-group">
      <text class="section-title">{{ $t('notificationSettings') }}</text>
      <view class="card">
        <view class="switch-row">
          <view class="row-left">
            <view class="row-icon amber"><image src="/static/icons/icon_plate.svg" mode="aspectFit" /></view>
            <view>
              <text class="row-title">{{ $t('recipeRecommendations') }}</text>
              <text class="row-hint">新食材可组合时提醒</text>
            </view>
          </view>
          <switch :checked="recipeNotif" @change="onRecipeNotif" color="#23A978" />
        </view>
        <view class="divider"></view>
        <view class="switch-row">
          <view class="row-left">
            <view class="row-icon blue"><image src="/static/icons/icon_chart.svg" mode="aspectFit" /></view>
            <view>
              <text class="row-title">{{ $t('nutritionReminders') }}</text>
              <text class="row-hint">营养缺口和饮食节奏提醒</text>
            </view>
          </view>
          <switch :checked="nutritionNotif" @change="onNutritionNotif" color="#23A978" />
        </view>
      </view>
    </view>

    <view class="settings-group">
      <text class="section-title">{{ $t('systemPreferences') }}</text>
      <view class="card">
        <view class="switch-row">
          <view class="row-left">
            <view class="row-icon"><image src="/static/icons/icon_flash.svg" mode="aspectFit" /></view>
            <view>
              <text class="row-title">{{ $t('syncOverWifiOnly') }}</text>
              <text class="row-hint">{{ $t('syncOverWifiOnlyTip') }}</text>
            </view>
          </view>
          <switch :checked="wifiOnly" @change="onWifiOnly" color="#23A978" />
        </view>
      </view>
    </view>

    <view class="settings-group">
      <text class="section-title">{{ $t('privacyAndSecurity') }}</text>
      <view class="card">
        <view class="info-row" @tap="clearCache">
          <view class="row-left">
            <view class="row-icon purple"><image src="/static/icons/icon_delete.svg" mode="aspectFit" /></view>
            <view>
              <text class="row-title">{{ $t('clearCache') }}</text>
              <text class="row-hint">{{ $t('cacheSize') }}</text>
            </view>
          </view>
          <text class="info-edit">{{ $t('clear') }}</text>
        </view>
        <view class="divider"></view>
        <view class="info-row" @tap="showPrivacy">
          <view class="row-left">
            <view class="row-icon blue"><image src="/static/icons/icon_bookmark.svg" mode="aspectFit" /></view>
            <view>
              <text class="row-title">{{ $t('privacyPolicy') }}</text>
              <text class="row-hint">查看数据使用说明</text>
            </view>
          </view>
          <text class="menu-arrow">›</text>
        </view>
      </view>
    </view>

    <view class="settings-group">
      <text class="section-title">{{ $t('aboutApp') }}</text>
      <view class="card">
        <view class="info-row">
          <view class="row-left">
            <view class="row-icon"><image src="/static/icons/icon_leaf.svg" mode="aspectFit" /></view>
            <view>
              <text class="row-title">{{ $t('appVersion') }}</text>
              <text class="row-hint">{{ $t('versionInfo') }}</text>
            </view>
          </view>
        </view>
      </view>
    </view>

    <button class="btn-logout" @tap="handleLogout">{{ $t('logout') }}</button>
    <view class="bottom-space"></view>
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
.settings-page { min-height: 100vh; background: var(--bg); padding: 28rpx; }
.settings-header { margin-bottom: 26rpx; }
.page-title { display: block; font-size: 42rpx; font-weight: 800; color: var(--text); line-height: 1.1; }
.page-sub { display: block; margin-top: 10rpx; font-size: 24rpx; color: var(--text-secondary); }
.settings-group { margin-bottom: 24rpx; }
.section-title { margin: 0 0 14rpx; font-size: 28rpx; }
.segmented {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10rpx;
  background: var(--bg-card);
  border-radius: var(--radius);
  padding: 10rpx;
  box-shadow: var(--shadow-sm);
}
.seg-item {
  height: 72rpx;
  border-radius: 18rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  font-size: 26rpx;
  font-weight: 700;
}
.seg-item.active { background: var(--teal-bg); color: var(--accent); }
.card {
  background: var(--bg-card);
  border-radius: var(--radius);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}
.info-row,
.switch-row {
  min-height: 96rpx;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 18rpx;
  padding: 20rpx 22rpx;
}
.row-left { display: flex; align-items: center; gap: 16rpx; flex: 1; min-width: 0; }
.row-icon {
  width: 58rpx;
  height: 58rpx;
  border-radius: 18rpx;
  background: var(--teal-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.row-icon.amber { background: var(--amber-bg); }
.row-icon.blue { background: var(--blue-bg); }
.row-icon.purple { background: var(--purple-bg); }
.row-icon image { width: 31rpx; height: 31rpx; }
.row-title { display: block; font-size: 27rpx; color: var(--text); font-weight: 700; }
.row-hint { display: block; margin-top: 4rpx; font-size: 21rpx; color: var(--text-secondary); line-height: 1.35; }
.info-edit { color: var(--accent); font-size: 25rpx; font-weight: 800; flex-shrink: 0; }
.menu-arrow { font-size: 36rpx; color: var(--text-muted); }
.divider { height: 1rpx; background: var(--border-light); margin-left: 96rpx; }
.btn-logout {
  width: 100%;
  height: 88rpx;
  background: var(--red-bg);
  color: var(--danger);
  border: none;
  border-radius: var(--radius);
  font-size: 30rpx;
  font-weight: 800;
  margin-top: 8rpx;
}
.bottom-space { height: 56rpx; }
</style>
