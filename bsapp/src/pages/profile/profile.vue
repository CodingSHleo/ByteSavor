<template>
  <view class="profile-page">
    <scroll-view scroll-y class="profile-body">
      <view class="profile-hero">
        <view class="hero-top">
          <view class="avatar">
            <image class="avatar-img" src="/static/icons/icon_avatar.svg" mode="aspectFit" />
          </view>
          <view class="hero-info">
            <text class="user-name">{{ displayName }}</text>
            <text class="user-goal">{{ $t('currentRating') }} · {{ goalLabel }}</text>
          </view>
          <view class="score-pill" v-if="nutrition">
            <text class="score-num">{{ nutrition.score }}</text>
            <text class="score-label">{{ $t('points') }}</text>
          </view>
        </view>

        <view class="pref-tags" v-if="profile && profile.preferences && profile.preferences.length">
          <text v-for="(p, idx) in profile.preferences" :key="idx" class="pref-tag">{{ prefLabel(p) }}</text>
        </view>
      </view>

      <view v-if="errorNotice" class="notice-card">
        <text>{{ errorNotice }}</text>
      </view>

      <view class="dashboard-grid" v-if="nutrition">
        <view class="metric-card">
          <text class="metric-label">{{ $t('healthScore') }}</text>
          <text class="metric-value">{{ nutrition.score }}/100</text>
          <view class="progress-bar">
            <view class="progress-fill" :style="{ width: (nutrition.score || 0) + '%' }"></view>
          </view>
        </view>
        <view class="metric-card warn">
          <text class="metric-label">{{ $t('vitaminDeficit') }}</text>
          <text class="metric-value">{{ deficits.length || 0 }}</text>
          <text class="metric-hint">{{ deficits.length ? deficits.map(deficitLabel).join('、') : '营养状态稳定' }}</text>
        </view>
      </view>

      <view class="section-head">
        <text class="section-title">{{ $t('settings') }}</text>
        <text class="section-sub">Profile & preferences</text>
      </view>

      <view class="menu-list">
        <view class="menu-item" @tap="showDietPrefs">
          <view class="menu-icon"><image src="/static/icons/icon_plate.svg" mode="aspectFit" /></view>
          <view class="menu-copy">
            <text class="menu-label">{{ $t('dietPreferences') }}</text>
            <text class="menu-hint">目标、口味和营养偏好</text>
          </view>
          <text class="menu-arrow">›</text>
        </view>
        <view class="menu-item" @tap="goHistory">
          <view class="menu-icon blue"><image src="/static/icons/icon_clock.svg" mode="aspectFit" /></view>
          <view class="menu-copy">
            <text class="menu-label">{{ $t('history') }}</text>
            <text class="menu-hint">查看识别、推荐和导出记录</text>
          </view>
          <text class="menu-arrow">›</text>
        </view>
        <view class="menu-item" @tap="goSettings">
          <view class="menu-icon amber"><image src="/static/icons/icon_edit.svg" mode="aspectFit" /></view>
          <view class="menu-copy">
            <text class="menu-label">{{ $t('systemSettings') }}</text>
            <text class="menu-hint">语言、通知和同步偏好</text>
          </view>
          <text class="menu-arrow">›</text>
        </view>
        <view class="menu-item" @tap="showNotifications">
          <view class="menu-icon purple"><image src="/static/icons/icon_bell.svg" mode="aspectFit" /></view>
          <view class="menu-copy">
            <text class="menu-label">{{ $t('notificationSettings') }}</text>
            <text class="menu-hint">{{ $t('recipeRecommendations') }} · {{ $t('nutritionReminders') }}</text>
          </view>
          <text class="menu-arrow">›</text>
        </view>
        <view class="menu-item" @tap="showAbout">
          <view class="menu-icon"><image src="/static/icons/icon_export.svg" mode="aspectFit" /></view>
          <view class="menu-copy">
            <text class="menu-label">{{ $t('aboutApp') }}</text>
            <text class="menu-hint">ByteSavor 智能饮食助手</text>
          </view>
          <text class="menu-arrow">›</text>
        </view>
      </view>

      <button class="btn-logout" @tap="handleLogout">{{ $t('logout') }}</button>
      <view class="bottom-space"></view>
    </scroll-view>
  </view>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { ApiService } from '@/api/index'
import { useSettingsStore } from '@/store/settings'
import { useAuthStore } from '@/store/auth'
import { t, currentLang } from '@/utils/i18n'

const $t = key => t(key)
const settingsStore = useSettingsStore()
const authStore = useAuthStore()

const profile = ref(null)
const nutrition = ref(null)
const errorNotice = ref('')

const displayName = computed(() => settingsStore.displayName || $t('defaultName'))
const goalLabel = computed(() => {
  if (!profile.value) return ''
  const map = { fat_loss: '减脂', muscle_gain: '增肌', maintain: '保持' }
  return map[profile.value.goal] || profile.value.goal
})
const deficits = computed(() => nutrition.value?.deficits || [])

onShow(async () => { await loadProfile() })
async function loadProfile() {
  errorNotice.value = ''
  try {
    profile.value = await ApiService.getUserProfile()
  } catch (e) {
    profile.value = null
    errorNotice.value = e.message || '用户画像加载失败'
  }
  try {
    nutrition.value = await ApiService.getNutritionStatus()
  } catch (e) {
    nutrition.value = null
    errorNotice.value = errorNotice.value || (e.message || '营养数据加载失败')
  }
}
watch(currentLang, () => { loadProfile() })

function prefLabel(p) {
  const map = { spicy: '辣味', high_protein: '高蛋白' }
  return map[p] || p
}
function deficitLabel(d) {
  const map = { vitamin_c: '维生素C', fiber: '膳食纤维', iron: '铁' }
  return map[d] || d
}

function goHistory() { uni.navigateTo({ url: '/pages/history/history' }) }
function goSettings() { uni.navigateTo({ url: '/pages/settings/settings' }) }

function showDietPrefs() {
  uni.navigateTo({ url: '/pages/settings/settings' })
}
function showNotifications() {
  uni.showModal({
    title: $t('notificationSettings'),
    content: `${$t('recipeRecommendations')}: ✅\n${$t('nutritionReminders')}: ✅`,
    showCancel: false
  })
}
function showAbout() {
  uni.showModal({
    title: $t('aboutApp'),
    content: $t('aboutAppContent'),
    showCancel: false
  })
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
.profile-page { min-height: 100vh; background: var(--bg); }
.profile-body { padding: 28rpx 28rpx 0; }
.profile-hero {
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  padding: 30rpx;
  box-shadow: var(--shadow-md);
}
.hero-top { display: flex; align-items: center; gap: 20rpx; }
.avatar {
  width: 120rpx;
  height: 120rpx;
  background: var(--teal-bg);
  border-radius: 36rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.avatar-img { width: 100%; height: 100%; border-radius: 36rpx; }
.hero-info { flex: 1; min-width: 0; }
.user-name {
  font-size: 42rpx;
  line-height: 1.15;
  font-weight: 800;
  color: var(--text);
  display: block;
}
.user-goal {
  font-size: 24rpx;
  color: var(--text-secondary);
  margin-top: 8rpx;
  display: block;
}
.score-pill {
  min-width: 104rpx;
  padding: 12rpx 14rpx;
  border-radius: 24rpx;
  background: var(--green-bg);
  text-align: center;
}
.score-num { display: block; font-size: 34rpx; font-weight: 800; color: var(--accent); line-height: 1; }
.score-label { display: block; margin-top: 4rpx; font-size: 18rpx; color: var(--text-secondary); }
.pref-tags { display: flex; flex-wrap: wrap; gap: 12rpx; margin-top: 24rpx; }
.pref-tag {
  background: var(--bg-elevated);
  color: var(--ink-green);
  font-size: 23rpx;
  padding: 8rpx 18rpx;
  border-radius: var(--radius-full);
}
.notice-card {
  margin-top: 20rpx;
  background: var(--amber-bg);
  color: var(--text-secondary);
  border-radius: var(--radius);
  padding: 18rpx 20rpx;
  font-size: 24rpx;
  line-height: 1.45;
}
.dashboard-grid { display: grid; grid-template-columns: 1.1fr 0.9fr; gap: 16rpx; margin-top: 20rpx; }
.metric-card {
  background: var(--bg-card);
  border-radius: var(--radius);
  padding: 22rpx;
  box-shadow: var(--shadow-sm);
}
.metric-card.warn { background: var(--amber-bg); }
.metric-label { display: block; font-size: 22rpx; color: var(--text-secondary); }
.metric-value { display: block; margin-top: 6rpx; font-size: 34rpx; color: var(--text); font-weight: 800; }
.metric-hint {
  display: block;
  margin-top: 8rpx;
  font-size: 21rpx;
  color: var(--text-secondary);
  line-height: 1.35;
}
.progress-bar { height: 12rpx; background: var(--border-light); border-radius: 999rpx; margin-top: 14rpx; overflow: hidden; }
.progress-fill { height: 100%; background: linear-gradient(90deg, var(--teal), var(--teal-light)); border-radius: 999rpx; }
.section-head { display: flex; align-items: flex-end; justify-content: space-between; margin: 34rpx 2rpx 16rpx; }
.section-title { margin: 0; }
.section-sub { font-size: 20rpx; color: var(--text-muted); }
.menu-list { display: flex; flex-direction: column; gap: 14rpx; }
.menu-item {
  display: flex;
  align-items: center;
  gap: 18rpx;
  background: var(--bg-card);
  border-radius: var(--radius);
  padding: 22rpx;
  box-shadow: var(--shadow-sm);
}
.menu-icon {
  width: 64rpx;
  height: 64rpx;
  border-radius: 20rpx;
  background: var(--teal-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.menu-icon.blue { background: var(--blue-bg); }
.menu-icon.amber { background: var(--amber-bg); }
.menu-icon.purple { background: var(--purple-bg); }
.menu-icon image { width: 34rpx; height: 34rpx; }
.menu-copy { flex: 1; min-width: 0; }
.menu-label { display: block; font-size: 28rpx; color: var(--text); font-weight: 700; }
.menu-hint {
  display: block;
  font-size: 21rpx;
  color: var(--text-secondary);
  margin-top: 4rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.menu-arrow { font-size: 36rpx; color: var(--text-muted); }
.btn-logout {
  width: 100%;
  height: 88rpx;
  background: var(--red-bg);
  color: var(--danger);
  border: none;
  border-radius: var(--radius);
  font-size: 30rpx;
  font-weight: 800;
  margin-top: 28rpx;
}
.bottom-space { height: 52rpx; }
</style>
