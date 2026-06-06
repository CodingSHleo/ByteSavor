<template>
  <view class="hd-page" v-if="!isLoading">
    <!-- 问候 -->
    <view class="hd-greeting">
      <text class="hd-welcome">{{ welcomeText }} {{ username }}</text>
    </view>

    <!-- 营养状态卡 -->
    <view class="hd-hero">
      <view class="hd-hero-left">
        <text class="hd-hero-score">{{ score }}</text>
        <text class="hd-hero-unit">{{ $t('points') }}</text>
        <view class="hd-hero-tag" :class="'tag-' + ratingClass">{{ ratingLabel }}</view>
      </view>
      <view class="hd-hero-right">
        <text class="hd-hero-label">{{ $t('nutritionStatus') }}</text>
        <view class="hd-hero-bar">
          <view class="hd-hero-fill" :style="{ width: scorePercent + '%' }"></view>
        </view>
        <text class="hd-hero-sub">{{ $t('todayCompletion') }} {{ scorePercent }}%</text>
      </view>
    </view>

    <!-- 营养素指标 -->
    <view class="card">
      <text class="card-title">{{ $t('healthScore') }}</text>
      <view class="hd-metrics">
        <view v-for="m in metrics" :key="m.label" class="hd-metric">
          <view class="hd-metric-head">
            <text class="hd-metric-label">{{ m.label }}</text>
            <text class="hd-metric-val">{{ m.value }}%</text>
          </view>
          <view class="hd-bar"><view class="hd-bar-fill" :style="{ width: m.value + '%', background: m.color }"></view></view>
        </view>
      </view>
    </view>

    <!-- 营养缺口 -->
    <view class="card">
      <text class="card-title">{{ $t('nutritionGap') }}</text>
      <view v-for="gap in nutritionGaps" :key="gap.label" class="hd-gap">
        <view class="hd-gap-head">
          <text class="hd-gap-label">{{ gap.label }}</text>
          <text class="hd-gap-pct">{{ gap.progress }}%</text>
        </view>
        <view class="hd-bar"><view class="hd-bar-fill" :style="{ width: gap.progress + '%', background: gap.color }"></view></view>
        <view class="hd-gap-foot">
          <text class="hd-gap-need">{{ gap.needed }}</text>
          <text class="hd-gap-curr">{{ gap.current }}</text>
        </view>
      </view>
    </view>

    <!-- 推荐食谱 -->
    <view class="card" v-if="recommendedRecipe">
      <text class="card-title">{{ $t('recommendedRecipe') }}</text>
      <view class="hd-recipe">
        <text class="hd-recipe-title">{{ recommendedRecipe.title }}</text>
        <text class="hd-recipe-match">⭐ {{ $t('matchScore') }} {{ matchPercent }}%</text>
        <text class="hd-recipe-reason">{{ $t('recommendReason') }}</text>
      </view>
    </view>

    <!-- 核心洞察 -->
    <view class="card">
      <text class="card-title">{{ $t('coreInsights') }}</text>
      <view class="hd-insight-row">
        <view class="hd-dot" style="background:var(--red);"></view>
        <text class="hd-insight-label">{{ $t('heatDeficit') }}</text>
        <text class="hd-insight-val">~320 kcal</text>
      </view>
      <view class="hd-insight-row">
        <view class="hd-dot" style="background:var(--blue);"></view>
        <text class="hd-insight-label">{{ $t('proteinNeeded') }}</text>
        <text class="hd-insight-val">~18g</text>
      </view>
      <view class="hd-insight-row">
        <view class="hd-dot" style="background:var(--green);"></view>
        <text class="hd-insight-label">{{ $t('vitaminDeficit') }}</text>
        <text class="hd-insight-val">{{ $t('vitaminDeficitItems') }}</text>
      </view>
    </view>

    <!-- 操作 -->
    <view class="hd-actions">
      <button class="btn-outline" @tap="goBack">{{ $t('backToScan') }}</button>
      <button class="btn-primary" @tap="exportList">{{ $t('listExport') }}</button>
    </view>
    <view style="height: 30rpx;"></view>
  </view>
  <view v-else class="loading-page"><text>{{ $t('loading') }}</text></view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { ApiService } from '@/api/index'
import { useSettingsStore } from '@/store/settings'
import { t } from '@/utils/i18n'

const $t = key => t(key)
const settingsStore = useSettingsStore()
const isLoading = ref(true)
const profile = ref(null)
const nutrition = ref(null)
const ingredients = ref([])
const recommendations = ref([])
const recommendedRecipe = ref(null)

const score = computed(() => nutrition.value?.score || 0)
const scorePercent = computed(() => Math.min(100, Math.max(0, score.value)))
const ratingLabel = computed(() => {
  if (score.value >= 80) return $t('veryGood')
  if (score.value >= 50) return $t('okay')
  return $t('needFix')
})
const ratingClass = computed(() => {
  if (score.value >= 80) return 'good'
  if (score.value >= 50) return 'medium'
  return 'bad'
})
const matchPercent = computed(() => {
  return recommendedRecipe.value ? ((recommendedRecipe.value.matchScore || 0) * 100).toFixed(0) : 0
})
const todayDate = computed(() => {
  const d = new Date()
  return `${d.getFullYear()}/${d.getMonth()+1}/${d.getDate()}`
})
const username = computed(() => settingsStore.displayName || $t('defaultName'))
const welcomeText = computed(() => ($t('welcomeUser') || '').replace(/\{|\}/g, '').trim())

const metrics = [
  { label: $t('calorieIntake'), value: 75, color: '#4F6EF7' },
  { label: $t('protein'), value: 82, color: '#34C759' },
  { label: $t('fiber'), value: 45, color: '#FF9500' },
  { label: $t('vitamins'), value: 68, color: '#AF52DE' }
]
const nutritionGaps = [
  { label: $t('calories'), needed: `${$t('dailyTarget')} 2400`, current: `${$t('currentIntake')} 1800`, progress: 75, color: '#4F6EF7' },
  { label: $t('protein'), needed: `${$t('dailyTarget')} 70g`, current: `${$t('currentIntake')} 55g`, progress: 78, color: '#34C759' },
  { label: $t('fiber'), needed: `${$t('dailyTarget')} 30g`, current: `${$t('currentIntake')} 12g`, progress: 40, color: '#FF3B30' },
  { label: `${$t('vitamins')} C`, needed: `${$t('dailyTarget')} 90mg`, current: `${$t('currentIntake')} 45mg`, progress: 50, color: '#FF9500' },
  { label: $t('iron'), needed: `${$t('dailyTarget')} 18mg`, current: `${$t('currentIntake')} 8mg`, progress: 44, color: '#AF52DE' }
]

onLoad(async (options) => {
  try { if (options?.ingredients) ingredients.value = JSON.parse(decodeURIComponent(options.ingredients)) } catch (e) {}
  profile.value = await ApiService.getUserProfile()
  nutrition.value = await ApiService.getNutritionStatus()
  const names = ingredients.value.map(i => i.name)
  recommendations.value = await ApiService.generateMealPlan(names)
  if (recommendations.value.length > 0) {
    recommendedRecipe.value = recommendations.value[0]
  } else if (ingredients.value.length > 0) {
    recommendedRecipe.value = { recipeId: 'r_health_01', title: ingredients.value.map(i => i.name).join('、'), matchScore: 0.92 }
  }
  isLoading.value = false
})

function exportList() {
  uni.navigateTo({ url: `/pages/list-export/list-export?recipes=${encodeURIComponent(JSON.stringify(recommendations.value))}` })
}
function goBack() { uni.navigateBack() }
</script>

<style scoped>
.hd-page { min-height: 100vh; background: var(--bg); padding: 20rpx 24rpx; }
.loading-page { display: flex; align-items: center; justify-content: center; height: 100vh; color: var(--text-muted); font-size: 28rpx; }

/* 问候 */
.hd-greeting { padding: 8rpx 0 18rpx; }
.hd-welcome { font-size: 34rpx; font-weight: 800; color: var(--text); display: block; letter-spacing: -0.02em; }
.hd-date { font-size: 24rpx; color: var(--text-muted); margin-top: 6rpx; display: block; }

/* Hero */
.hd-hero {
  display: flex; align-items: center; gap: 28rpx;
  background: #fff;
  border-radius: var(--radius); padding: 24rpx 28rpx; margin-bottom: 20rpx;
  box-shadow: var(--shadow-sm);
}
.hd-hero-left { display: flex; flex-direction: column; align-items: center; }
.hd-hero-score { color: var(--text); font-size: 56rpx; font-weight: 800; line-height: 1; }
.hd-hero-unit { color: var(--text-muted); font-size: 20rpx; margin-top: 2rpx; }
.hd-hero-tag { font-size: 20rpx; padding: 4rpx 16rpx; border-radius: var(--radius-full); margin-top: 8rpx; }
.tag-good { background: #E9F9EE; color: #34C759; }
.tag-medium { background: #FFF5E6; color: #FF9500; }
.tag-bad { background: #FFECEB; color: #FF3B30; }
.hd-hero-right { flex: 1; display: flex; flex-direction: column; gap: 10rpx; }
.hd-hero-label { color: var(--text); font-size: 26rpx; font-weight: 700; }
.hd-hero-bar { height: 8rpx; background: var(--bg); border-radius: 4rpx; overflow: hidden; }
.hd-hero-fill { height: 100%; background: #34C759; border-radius: 4rpx; transition: width .4s ease; }
.hd-hero-sub { color: var(--text-muted); font-size: 22rpx; }

/* 卡片 */
.card { background: #fff; border-radius: var(--radius); padding: 24rpx; margin-bottom: 20rpx; box-shadow: var(--shadow-sm); }
.card-title { font-size: 30rpx; font-weight: 800; color: var(--text); display: block; margin-bottom: 20rpx; letter-spacing: -0.02em; }

/* 指标 */
.hd-metrics { display: flex; flex-direction: column; gap: 18rpx; }
.hd-metric-head { display: flex; justify-content: space-between; margin-bottom: 8rpx; }
.hd-metric-label { font-size: 28rpx; font-weight: 600; color: var(--text); }
.hd-metric-val { font-size: 28rpx; font-weight: 700; color: var(--text-secondary); }
.hd-bar { height: 10rpx; background: var(--border); border-radius: 5rpx; overflow: hidden; }
.hd-bar-fill { height: 100%; border-radius: 5rpx; transition: width .4s ease; }

/* 缺口 */
.hd-gap { margin-bottom: 20rpx; }
.hd-gap:last-child { margin-bottom: 0; }
.hd-gap-head { display: flex; justify-content: space-between; margin-bottom: 8rpx; }
.hd-gap-label { font-size: 28rpx; font-weight: 600; color: var(--text); }
.hd-gap-pct { font-size: 26rpx; font-weight: 700; color: var(--text-secondary); }
.hd-gap-foot { display: flex; justify-content: space-between; margin-top: 4rpx; }
.hd-gap-need, .hd-gap-curr { font-size: 22rpx; color: var(--text-muted); }

/* 食谱 */
.hd-recipe { background: var(--blue-bg); border-radius: var(--radius); padding: 20rpx; }
.hd-recipe-title { font-size: 28rpx; font-weight: 700; color: var(--text); display: block; }
.hd-recipe-match { font-size: 26rpx; color: var(--blue); margin-top: 8rpx; display: block; }
.hd-recipe-reason { font-size: 24rpx; color: var(--text-secondary); margin-top: 10rpx; display: block; line-height: 1.5; }

/* 洞察 */
.hd-insight-row { display: flex; align-items: center; margin-top: 16rpx; }
.hd-dot { width: 12rpx; height: 12rpx; border-radius: 3rpx; margin-right: 12rpx; flex-shrink: 0; }
.hd-insight-label { flex: 1; font-weight: 600; font-size: 26rpx; color: var(--text); }
.hd-insight-val { font-size: 26rpx; color: var(--text-secondary); }

/* 操作 */
.hd-actions { display: flex; gap: 16rpx; margin-top: 8rpx; }
.hd-actions button { flex: 1; height: 84rpx; border-radius: var(--radius); font-size: 28rpx; font-weight: 700; }
</style>
