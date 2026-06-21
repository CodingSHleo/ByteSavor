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
            <view class="profile-avatar" @tap="chooseAvatar">
              <image v-if="avatarUrl" :src="avatarUrl" mode="aspectFill" />
              <image v-else src="/static/icons/icon_avatar.svg" mode="aspectFit" />
            </view>
            <view>
              <text class="row-title">{{ $t('displayName') }}</text>
              <text class="row-hint">{{ displayName || $t('defaultName') }}</text>
            </view>
          </view>
          <text class="info-edit" @tap="editDisplayName">{{ $t('edit') }}</text>
        </view>
        <view class="divider"></view>
        <view class="info-row" @tap="chooseAvatar">
          <view class="row-left">
            <view class="row-icon blue"><image src="/static/icons/icon_camera.svg" mode="aspectFit" /></view>
            <view>
              <text class="row-title">社区头像</text>
              <text class="row-hint">用于社区卡片和详情页展示</text>
            </view>
          </view>
          <text class="info-edit">选择</text>
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
        <view class="info-row">
          <view class="row-left">
            <view class="row-icon"><image src="/static/icons/icon_bookmark.svg" mode="aspectFit" /></view>
            <view>
              <text class="row-title">社区正文</text>
              <text class="row-hint">{{ communityTextMode === 'summary' ? '列表只展示摘要，详情看全文' : '列表展示更多正文内容' }}</text>
            </view>
          </view>
          <view class="mini-toggle">
            <text :class="{ active: communityTextMode === 'summary' }" @tap="setCommunityMode('summary')">摘要</text>
            <text :class="{ active: communityTextMode === 'full' }" @tap="setCommunityMode('full')">完整</text>
          </view>
        </view>
        <view class="divider"></view>
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
      <text class="section-title">API 服务器地址</text>
      <text class="row-hint" style="margin-bottom:12rpx;padding:0 4rpx">修改后立即生效。手机端请使用局域网 IP（如 192.168.x.x），确保手机和服务器在同一网络。</text>
      <view class="card">
        <view class="info-row">
          <view class="row-left">
            <view class="row-icon amber"><image src="/static/icons/icon_flash.svg" mode="aspectFit" /></view>
            <view>
              <text class="row-title">当前地址</text>
              <text class="row-hint">{{ apiBaseUrl }}</text>
            </view>
          </view>
          <text class="info-edit" @tap="editApiUrl">修改</text>
        </view>
        <view class="divider"></view>
        <view class="info-row" @tap="resetApiUrl">
          <view class="row-left">
            <view class="row-icon"><image src="/static/icons/icon_clock.svg" mode="aspectFit" /></view>
            <view>
              <text class="row-title">重置为默认</text>
              <text class="row-hint">恢复为自动检测地址</text>
            </view>
          </view>
          <text class="info-edit">重置</text>
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

    <view class="settings-group">
      <text class="section-title">饮食偏好</text>
      <view class="card">
        <text class="row-title" style="margin-bottom:12rpx">自由输入（输入菜名或口味描述，AI解析）</text>
        <view style="display:flex;gap:12rpx;margin-bottom:16rpx">
          <input v-model="freeText" placeholder="比如：我喜欢川菜和粤菜，不喜欢太油腻的，经常吃牛肉和西兰花" style="flex:1;height:72rpx;background:#f9fafb;border-radius:16rpx;padding:0 16rpx;font-size:24rpx" />
          <button @tap="parseFreeText" :disabled="parsing" style="width:140rpx;height:72rpx;background:#059669;color:#fff;border:none;border-radius:16rpx;font-size:24rpx">{{ parsing ? '解析中' : 'AI解析' }}</button>
        </view>
        <text v-if="parseResult" style="display:block;font-size:22rpx;color:#059669;margin-bottom:16rpx">{{ parseResult }}</text>
        <view class="divider" style="margin:0 0 20rpx 0"></view>
        <text class="row-title" style="margin-bottom:16rpx">健康目标</text>
        <view style="display:flex;gap:16rpx;margin-bottom:24rpx">
          <view v-for="g in goals" :key="g.key" @tap="setGoal(g.key)" :style="{padding:'12rpx 28rpx',borderRadius:'20rpx',fontSize:'26rpx',background:currentGoal===g.key?'#059669':'#f3f4f6',color:currentGoal===g.key?'#fff':'#374151'}">{{ g.label }}</view>
        </view>
        <text class="row-title" style="margin-bottom:16rpx">身体数据（用于自动计算目标）</text>
        <view class="form-grid">
          <view class="form-field">
            <text>性别</text>
            <view class="mini-seg">
              <view :class="{ active: bodyMetrics.sex === 'male' }" @tap="bodyMetrics.sex = 'male'">男</view>
              <view :class="{ active: bodyMetrics.sex === 'female' }" @tap="bodyMetrics.sex = 'female'">女</view>
            </view>
          </view>
          <view class="form-field"><text>年龄</text><input v-model="bodyMetrics.age" type="number" placeholder="22" /></view>
          <view class="form-field"><text>身高 cm</text><input v-model="bodyMetrics.height_cm" type="number" placeholder="175" /></view>
          <view class="form-field"><text>体重 kg</text><input v-model="bodyMetrics.weight_kg" type="digit" placeholder="70" /></view>
          <view class="form-field wide"><text>每周运动次数</text><input v-model="bodyMetrics.exercise_per_week" type="number" placeholder="3" /></view>
        </view>
        <text class="row-title" style="margin:20rpx 0 8rpx">每日营养目标（可选手动覆盖）</text>
        <text class="row-hint" style="margin-bottom:14rpx">留空则按身体数据和目标自动计算；填写后优先使用你的自定义数值。</text>
        <view class="target-grid">
          <view v-for="target in targetFields" :key="target.key" class="form-field">
            <text>{{ target.label }}</text>
            <input v-model="nutritionTargets[target.key]" type="digit" :placeholder="String(autoTargets[target.key] || target.placeholder)" />
          </view>
        </view>
        <view class="computed-card">
          <text>{{ hasCustomTargets ? '当前目标（含手动覆盖）' : '当前自动计算目标' }}</text>
          <text>{{ targetSummary }}</text>
        </view>
        <button v-if="hasCustomTargets" class="btn-clear-targets" @tap="clearCustomTargets">清空手动目标，改用自动计算</button>
        <text class="row-title" style="margin-bottom:16rpx">口味偏好（多选）</text>
        <view style="display:flex;flex-wrap:wrap;gap:14rpx;margin-bottom:24rpx">
          <view v-for="p in prefOptions" :key="p.key" @tap="togglePref(p.key)" :style="{padding:'10rpx 24rpx',borderRadius:'20rpx',fontSize:'24rpx',background:currentPrefs.includes(p.key)?'#059669':'#f3f4f6',color:currentPrefs.includes(p.key)?'#fff':'#374151'}">{{ p.label }}</view>
        </view>
        <button @tap="savePreferences" style="width:100%;height:72rpx;background:#059669;color:#fff;border:none;border-radius:16rpx;font-size:28rpx">保存偏好</button>
      </view>
    </view>

    <button class="btn-logout" @tap="handleLogout">{{ $t('logout') }}</button>
    <view class="bottom-space"></view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { useSettingsStore } from '@/store/settings'
import { useAuthStore } from '@/store/auth'
import { ApiService } from '@/api/index'
import { t } from '@/utils/i18n'
import { parsePreferenceText } from '@/utils/food-analysis'

const $t = key => t(key)
const settingsStore = useSettingsStore()
const authStore = useAuthStore()

const language = ref('zh')
const darkMode = ref(false)
const displayName = ref('')
const avatarUrl = ref('')
const communityTextMode = ref('summary')
const recipeNotif = ref(true)
const nutritionNotif = ref(true)
const wifiOnly = ref(true)

const apiBaseUrl = ref('')

onShow(() => {
  language.value = settingsStore.language
  darkMode.value = settingsStore.darkMode
  displayName.value = settingsStore.displayName
  avatarUrl.value = settingsStore.avatarUrl
  communityTextMode.value = settingsStore.communityTextMode
  recipeNotif.value = settingsStore.recipeNotifications
  nutritionNotif.value = settingsStore.nutritionNotifications
  wifiOnly.value = settingsStore.wifiSyncOnly
  apiBaseUrl.value = uni.getStorageSync('api_base_url') || '自动检测'
  loadPreferences()
})

const currentGoal = ref('balanced')
const currentPrefs = ref([])
const bodyMetrics = ref({ sex: 'male', age: 22, height_cm: 175, weight_kg: 70, exercise_per_week: 3 })
const nutritionTargets = ref({})
const computedTargets = ref({})
const freeText = ref('')
const parsing = ref(false)
const parseResult = ref('')
const autoTargets = computed(() => calculateLocalTargets(currentGoal.value, bodyMetrics.value, {}))
const cleanCustomTargets = computed(() => normalizeTargets(nutritionTargets.value || {}))
const hasCustomTargets = computed(() => Object.keys(cleanCustomTargets.value).length > 0)
const effectiveTargets = computed(() => ({
  ...autoTargets.value,
  ...cleanCustomTargets.value,
  source: hasCustomTargets.value ? 'custom' : 'calculated'
}))
const targetSummary = computed(() => {
  const t = effectiveTargets.value || {}
  return `${t.calories || '-'} kcal · P ${t.protein || '-'}g · C ${t.carbs || '-'}g · F ${t.fat || '-'}g`
})

function positiveNumber(value, fallback) {
  const n = Number(value)
  return Number.isFinite(n) && n > 0 ? n : fallback
}

function calculateLocalTargets(goal = 'balanced', metrics = {}, custom = {}) {
  const sex = metrics.sex || 'male'
  const age = positiveNumber(metrics.age, 22)
  const height = positiveNumber(metrics.height_cm, 175)
  const weight = positiveNumber(metrics.weight_kg, 70)
  const exercise = positiveNumber(metrics.exercise_per_week, 3)
  const bmr = 10 * weight + 6.25 * height - 5 * age + (sex === 'male' ? 5 : -161)
  let activity = 1.2
  if (exercise >= 6) activity = 1.725
  else if (exercise >= 4) activity = 1.55
  else if (exercise >= 2) activity = 1.375
  const maintenance = bmr * activity
  let calories = maintenance
  let proteinPerKg = 1.4
  let fatRatio = 0.28
  if (goal === 'fat_loss') {
    calories = maintenance * 0.82
    proteinPerKg = 1.8
    fatRatio = 0.25
  } else if (goal === 'muscle_gain') {
    calories = maintenance * 1.12
    proteinPerKg = 2.0
    fatRatio = 0.25
  }
  const protein = weight * proteinPerKg
  const fat = calories * fatRatio / 9
  const carbs = Math.max(0, (calories - protein * 4 - fat * 9) / 4)
  const targets = {
    calories: Math.round(calories),
    protein: Math.round(protein),
    carbs: Math.round(carbs),
    fat: Math.round(fat),
    fiber: calories >= 1800 ? 30 : 25,
    vitamin_c: 90,
    iron: sex === 'female' ? 18 : 8,
    source: 'calculated'
  }
  return { ...targets, ...normalizeTargets(custom) }
}

function normalizeTargets(targets = {}) {
  const cleaned = {}
  Object.entries(targets || {}).forEach(([key, value]) => {
    if (value !== '' && value !== null && value !== undefined && key !== 'source') {
      const n = Number(value)
      if (Number.isFinite(n) && n > 0) cleaned[key] = Math.round(n)
    }
  })
  return cleaned
}

async function parseFreeText() {
  const t = freeText.value.trim(); if (!t) return
  parsing.value = true; parseResult.value = ''
  try {
    const d = await ApiService.assistantChat(`只分析饮食偏好，必须只返回JSON，不要解释。格式: {"goal":"fat_loss/muscle_gain/balanced","preferences":["spicy","light","high_protein","low_carb","vegetarian","comfort_food","seafood"]}。\n用户输入: ${t}`)
    const reply = d?.reply || ''
    // 提取JSON
    let json = reply.trim()
    if (reply.includes('```')) json = reply.split('```')[1].split('```')[0].trim()
    if (json.startsWith('json')) json = json.slice(4).trim()
    if (json.includes('{') && json.includes('}')) json = json.slice(json.indexOf('{'), json.lastIndexOf('}') + 1)
    const parsed = JSON.parse(json)
    if (parsed.goal) currentGoal.value = parsed.goal
    if (Array.isArray(parsed.preferences)) currentPrefs.value = parsed.preferences.filter(p => prefOptions.some(o => o.key === p))
    if (!currentPrefs.value.length) {
      currentPrefs.value = parsePreferenceText(t).preferences.filter(p => prefOptions.some(o => o.key === p))
    }
    parseResult.value = `已解析: 目标=${goalText(currentGoal.value)} 偏好=${prefText(currentPrefs.value)}`
  } catch (e) {
    const parsed = parsePreferenceText(t)
    currentGoal.value = parsed.goal
    currentPrefs.value = parsed.preferences.filter(p => prefOptions.some(o => o.key === p))
    parseResult.value = `已用本地规则解析: 目标=${goalText(currentGoal.value)} 偏好=${prefText(currentPrefs.value)}`
  }
  parsing.value = false
}
const goals = [{ key: 'fat_loss', label: '减脂' }, { key: 'muscle_gain', label: '增肌' }, { key: 'balanced', label: '均衡' }]
const targetFields = [
  { key: 'calories', label: '热量 kcal', placeholder: 1800 },
  { key: 'protein', label: '蛋白 g', placeholder: 70 },
  { key: 'carbs', label: '碳水 g', placeholder: 220 },
  { key: 'fat', label: '脂肪 g', placeholder: 60 },
  { key: 'fiber', label: '纤维 g', placeholder: 30 },
  { key: 'vitamin_c', label: '维C mg', placeholder: 90 },
  { key: 'iron', label: '铁 mg', placeholder: 18 }
]
const prefOptions = [
  { key: 'spicy', label: '辣' }, { key: 'light', label: '清淡' }, { key: 'high_protein', label: '高蛋白' },
  { key: 'low_carb', label: '低碳水' }, { key: 'vegetarian', label: '素食' }
]
function goalText(goal) { return goals.find(g => g.key === goal)?.label || goal }
function prefText(prefs) {
  return (prefs || []).map(p => prefOptions.find(o => o.key === p)?.label || p).join('、') || '无'
}

async function loadPreferences() {
  try {
    const p = await ApiService.getUserProfile()
    if (p) {
      currentGoal.value = p.goal || 'balanced'
      displayName.value = p.name || displayName.value
      avatarUrl.value = p.avatar_url || avatarUrl.value
      settingsStore.setDisplayName(displayName.value)
      settingsStore.setAvatarUrl(avatarUrl.value)
      currentPrefs.value = p.preferences || []
      bodyMetrics.value = { ...bodyMetrics.value, ...(p.body_metrics || {}) }
      nutritionTargets.value = { ...(p.nutrition_targets || {}) }
      computedTargets.value = p.computed_targets || {}
    }
  } catch (e) { /* 未登录时用默认值 */ }
}
function setGoal(g) { currentGoal.value = g }
function togglePref(p) {
  const idx = currentPrefs.value.indexOf(p)
  if (idx >= 0) currentPrefs.value.splice(idx, 1)
  else currentPrefs.value.push(p)
}
async function savePreferences() {
  try {
    const cleanTargets = cleanCustomTargets.value
    const saved = await ApiService.updateProfile(
      currentGoal.value,
      currentPrefs.value,
      normalizedBodyMetrics(),
      cleanTargets,
      { name: displayName.value, avatar_url: avatarUrl.value }
    )
    computedTargets.value = saved.computed_targets || computedTargets.value
    uni.showToast({ title: '偏好已保存', icon: 'success' })
  } catch (e) { uni.showToast({ title: '保存失败', icon: 'none' }) }
}
function clearCustomTargets() {
  nutritionTargets.value = {}
  computedTargets.value = autoTargets.value
}
function normalizedBodyMetrics() {
  return {
    sex: bodyMetrics.value.sex || 'male',
    age: Number(bodyMetrics.value.age || 22),
    height_cm: Number(bodyMetrics.value.height_cm || 175),
    weight_kg: Number(bodyMetrics.value.weight_kg || 70),
    exercise_per_week: Number(bodyMetrics.value.exercise_per_week || 0)
  }
}

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
    success: async (res) => {
      if (res.confirm && res.content && res.content.trim()) {
        const newDisplayName = res.content.trim()
        displayName.value = newDisplayName
        settingsStore.setDisplayName(newDisplayName)
        await saveDisplayProfile()
      }
    }
  })
}

function chooseAvatar() {
  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    success: async (res) => {
      const path = (res.tempFilePaths || [])[0]
      const file = (res.tempFiles || [])[0]
      if (!path) return
      avatarUrl.value = await imageToDataUrl(path, file)
      settingsStore.setAvatarUrl(avatarUrl.value)
      await saveDisplayProfile()
    }
  })
}

function imageToDataUrl(path, fileInfo) {
  const file = fileInfo?.file || fileInfo
  if (path && String(path).startsWith('data:')) return Promise.resolve(path)
  if (typeof FileReader !== 'undefined' && file instanceof Blob) {
    return new Promise(resolve => {
      const reader = new FileReader()
      reader.onload = () => resolve(reader.result)
      reader.onerror = () => resolve(path)
      reader.readAsDataURL(file)
    })
  }
  return Promise.resolve(path)
}

async function saveDisplayProfile() {
  try {
    const saved = await ApiService.updateProfile(
      currentGoal.value,
      currentPrefs.value,
      normalizedBodyMetrics(),
      cleanCustomTargets.value,
      { name: displayName.value, avatar_url: avatarUrl.value }
    )
    if (saved?.name) settingsStore.setDisplayName(saved.name)
    if (saved?.avatar_url !== undefined) settingsStore.setAvatarUrl(saved.avatar_url)
    uni.showToast({ title: '资料已保存', icon: 'success' })
  } catch (e) {
    uni.showToast({ title: '资料保存失败', icon: 'none' })
  }
}

function setCommunityMode(mode) {
  communityTextMode.value = mode === 'full' ? 'full' : 'summary'
  settingsStore.setCommunityTextMode(communityTextMode.value)
}

function clearCache() {
  uni.showToast({ title: $t('cacheCleared'), icon: 'success' })
}

function editApiUrl() {
  uni.showModal({
    title: '修改 API 地址',
    content: '请输入后端服务器地址（含端口）',
    editable: true,
    placeholderText: 'http://192.168.1.100:8000',
    success: (res) => {
      if (res.confirm && res.content && res.content.trim()) {
        const url = res.content.trim().replace(/\/+$/, '')
        apiBaseUrl.value = url
        uni.setStorageSync('api_base_url', url)
        uni.showToast({ title: '已更新，下次请求生效', icon: 'success' })
      }
    }
  })
}

function resetApiUrl() {
  uni.removeStorageSync('api_base_url')
  apiBaseUrl.value = '自动检测'
  uni.showToast({ title: '已重置为自动检测', icon: 'success' })
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
.profile-avatar {
  width: 72rpx;
  height: 72rpx;
  border-radius: 50%;
  background: var(--teal-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  flex-shrink: 0;
  box-shadow: var(--hairline);
}
.profile-avatar image { width: 100%; height: 100%; }
.row-title { display: block; font-size: 27rpx; color: var(--text); font-weight: 700; }
.row-hint { display: block; margin-top: 4rpx; font-size: 21rpx; color: var(--text-secondary); line-height: 1.35; }
.form-grid, .target-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12rpx; margin-bottom: 16rpx; }
.target-grid { grid-template-columns: repeat(2, 1fr); }
.form-field { min-width: 0; background: var(--bg-elevated); border-radius: 16rpx; padding: 14rpx; box-sizing: border-box; }
.form-field.wide { grid-column: 1 / -1; }
.form-field text { display: block; color: var(--text-secondary); font-size: 21rpx; margin-bottom: 8rpx; font-weight: 800; }
.form-field input { height: 54rpx; color: var(--text); font-size: 26rpx; }
.mini-seg { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8rpx; }
.mini-seg view { height: 54rpx; border-radius: 14rpx; background: #fff; color: var(--text-secondary); display: flex; align-items: center; justify-content: center; font-size: 24rpx; font-weight: 900; }
.mini-seg view.active { background: var(--teal); color: #fff; }
.mini-toggle {
  display: flex;
  align-items: center;
  gap: 6rpx;
  padding: 6rpx;
  border-radius: 999rpx;
  background: var(--bg-elevated);
  flex-shrink: 0;
}
.mini-toggle text {
  min-width: 72rpx;
  height: 46rpx;
  padding: 0 12rpx;
  border-radius: 999rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  font-size: 22rpx;
  font-weight: 900;
}
.mini-toggle text.active {
  background: var(--teal);
  color: #fff;
}
.computed-card { background: var(--green-bg); border-radius: 18rpx; padding: 16rpx; margin-bottom: 22rpx; }
.computed-card text:first-child { display: block; color: var(--teal); font-size: 21rpx; font-weight: 900; margin-bottom: 6rpx; }
.computed-card text:last-child { display: block; color: var(--text); font-size: 24rpx; font-weight: 950; }
.btn-clear-targets {
  width: 100%;
  height: 68rpx;
  margin: 0 0 22rpx;
  padding: 0;
  border: none;
  border-radius: 16rpx;
  background: #F2F8F5 !important;
  color: #23A978 !important;
  font-size: 24rpx;
  font-weight: 900;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}
.btn-clear-targets::after { border: none; }
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
