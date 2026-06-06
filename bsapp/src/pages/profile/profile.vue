<template>
  <view class="profile-page">
    <scroll-view scroll-y class="profile-body">
      <!-- 头像 -->
      <view class="avatar-box">
        <view class="avatar">
          <image class="avatar-img" src="/static/icons/icon_avatar.svg" mode="widthFix" />
        </view>
      </view>

      <!-- 用户信息 -->
      <view class="user-info" v-if="profile">
        <text class="user-name">{{ displayName }}</text>
        <text class="user-goal">{{ $t('currentRating') }}: {{ goalLabel }}</text>
        <view class="pref-tags">
          <text
            v-for="(p, idx) in profile.preferences"
            :key="idx"
            class="pref-tag"
          >{{ prefLabel(p) }}</text>
        </view>
      </view>

      <view class="divider"></view>

      <!-- 健康数据 -->
      <text class="section-title">{{ $t('nutritionInfo') }}</text>
      <view class="card" v-if="nutrition">
        <view class="health-row">
          <text>{{ $t('healthScore') }}</text>
          <text class="health-value">{{ nutrition.score }}/100</text>
        </view>
        <view class="progress-bar">
          <view class="progress-fill" :style="{ width: (nutrition.score || 0) + '%' }"></view>
        </view>
        <view v-if="deficits.length > 0" style="margin-top: 16rpx;">
          <text class="gap-label">{{ $t('vitaminDeficit') }}:</text>
          <view class="gap-tags">
            <text v-for="d in deficits" :key="d" class="gap-tag">{{ deficitLabel(d) }}</text>
          </view>
        </view>
      </view>

      <view class="divider"></view>

      <!-- 菜单 -->
      <text class="section-title">{{ $t('settings') }}</text>
      <view class="menu-list">
        <view class="menu-item" @tap="showDietPrefs">
          <image class="menu-icon-img" src="/static/icons/icon_plate.svg" mode="widthFix" />
          <text class="menu-label">{{ $t('dietPreferences') }}</text>
          <text class="menu-arrow">›</text>
        </view>
        <view class="menu-item" @tap="goHistory">
          <image class="menu-icon-img" src="/static/icons/icon_clock.svg" mode="widthFix" />
          <text class="menu-label">{{ $t('history') }}</text>
          <text class="menu-arrow">›</text>
        </view>
        <view class="menu-item" @tap="goSettings">
          <text class="menu-icon">⚙️</text>
          <text class="menu-label">{{ $t('systemSettings') }}</text>
          <text class="menu-arrow">›</text>
        </view>
        <view class="menu-item" @tap="showNotifications">
          <image class="menu-icon-img" src="/static/icons/icon_bell.svg" mode="widthFix" />
          <text class="menu-label">{{ $t('notificationSettings') }}</text>
          <text class="menu-arrow">›</text>
        </view>
        <view class="menu-item" @tap="showAbout">
          <image class="menu-icon-img" src="/static/icons/icon_export.svg" mode="widthFix" />
          <text class="menu-label">{{ $t('aboutApp') }}</text>
          <text class="menu-arrow">›</text>
        </view>
      </view>

      <!-- 登出按钮 -->
      <button class="btn-logout" @tap="handleLogout">{{ $t('logout') }}</button>
      <view style="height: 40rpx;"></view>
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

const displayName = computed(() => settingsStore.displayName || $t('defaultName'))
const goalLabel = computed(() => {
  if (!profile.value) return ''
  const map = { fat_loss: '减脂', muscle_gain: '增肌', maintain: '保持' }
  return map[profile.value.goal] || profile.value.goal
})
const deficits = computed(() => nutrition.value?.deficits || [])

onShow(async () => { await loadProfile() })
async function loadProfile() {
  profile.value = await ApiService.getUserProfile()
  nutrition.value = await ApiService.getNutritionStatus()
}
watch(currentLang, () => { loadProfile() })

function prefLabel(p) {
  const map = { spicy: '辣味', high_protein: '高蛋白' }
  return map[p] || p
}
function deficitLabel(d) {
  const map = { vitamin_c: '维生素C', fiber: '膳食纤维' }
  return map[d] || d
}

function goHistory() { uni.navigateTo({ url: '/pages/history/history' }) }
function goSettings() { uni.navigateTo({ url: '/pages/settings/settings' }) }

function showDietPrefs() {
  uni.showModal({
    title: $t('dietPreferences'),
    content: $t('preferenceDesc'),
    showCancel: false
  })
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
.profile-page { min-height: 100vh; background: var(--bg-color); }
.profile-body { padding: 32rpx; }
.avatar-box { display: flex; justify-content: center; margin-bottom: 24rpx; }
.avatar {
  width: 160rpx; height: 160rpx;
  background: var(--accent); border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
}
.avatar-img { width: 100%; height: 100%; border-radius: 50%; }
.avatar-text { font-size: 72rpx; }
.user-info { text-align: center; margin-bottom: 32rpx; }
.user-name {
  font-size: 40rpx; font-weight: bold;
  color: var(--text-color); display: block;
}
.user-goal {
  font-size: 26rpx; color: var(--text-secondary);
  margin-top: 8rpx; display: block;
}
.pref-tags { display: flex; justify-content: center; gap: 16rpx; margin-top: 16rpx; }
.pref-tag {
  background: var(--tag-bg); color: var(--accent);
  font-size: 24rpx; padding: 8rpx 20rpx; border-radius: 24rpx;
}
.divider { height: 1rpx; background: var(--border-color); margin: 24rpx 0; }
.section-title {
  font-size: 32rpx; font-weight: bold;
  color: var(--text-color); margin-bottom: 16rpx; display: block;
}
.card { background: var(--card-bg); border-radius: 16rpx; padding: 24rpx; }
.health-row { display: flex; justify-content: space-between; font-size: 28rpx; color: var(--text-color); }
.health-value { font-weight: bold; }
.progress-bar {
  height: 12rpx; background: var(--border-color);
  border-radius: 6rpx; margin-top: 16rpx; overflow: hidden;
}
.progress-fill {
  height: 100%; background: linear-gradient(90deg, var(--accent), var(--success));
  border-radius: 6rpx; transition: width 0.5s;
}
.gap-label { font-size: 24rpx; color: var(--text-secondary); }
.gap-tags { display: flex; flex-wrap: wrap; gap: 12rpx; margin-top: 12rpx; }
.gap-tag {
  background: var(--danger-bg); color: var(--danger);
  font-size: 22rpx; padding: 6rpx 16rpx; border-radius: 24rpx;
}
.menu-list { background: var(--card-bg); border-radius: 16rpx; overflow: hidden; }
.menu-item {
  display: flex; align-items: center; padding: 28rpx 24rpx;
  border-bottom: 1rpx solid var(--border-light);
}
.menu-item:last-child { border-bottom: none; }
.menu-icon-img { width: 44rpx; height: 44rpx; margin-right: 20rpx; }
.menu-label { flex: 1; font-size: 28rpx; color: var(--text-color); }
.menu-arrow { font-size: 32rpx; color: var(--text-muted); }
.btn-logout {
  width: 100%; height: 88rpx;
  background: var(--danger); color: #fff;
  border: none; border-radius: 16rpx;
  font-size: 32rpx; font-weight: bold; margin-top: 40rpx;
}
</style>
