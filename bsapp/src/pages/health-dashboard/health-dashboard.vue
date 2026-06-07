<template>
  <view class="hd-page" v-if="!isLoading">
    <view class="hd-header">
      <text class="hd-title">数据统计</text>
      <text class="hd-date">{{ todayDate }}</text>
    </view>

    <view class="summary-grid">
      <view class="summary-card main">
        <text class="summary-label">健康分</text>
        <text class="summary-value">{{ score }}</text>
        <view class="summary-tag" :class="'tag-' + ratingClass">{{ ratingLabel }}</view>
      </view>
      <view class="summary-card">
        <text class="summary-label">食材数</text>
        <text class="summary-value">{{ ingredients.length }}</text>
        <text class="summary-foot">来自本次识别</text>
      </view>
      <view class="summary-card">
        <text class="summary-label">推荐数</text>
        <text class="summary-value">{{ recommendations.length }}</text>
        <text class="summary-foot">可生成清单</text>
      </view>
    </view>

    <view v-if="errorNotice" class="notice-card">
      <image src="/static/icons/icon_flash.svg" mode="aspectFit" />
      <text>{{ errorNotice }}</text>
    </view>

    <view class="explain-card">
      <view class="explain-item">
        <text class="explain-key">Y</text>
        <view>
          <text class="explain-title">约束推理</text>
          <text class="explain-copy">把目标、偏好、食材和营养缺口合并成推荐依据。</text>
        </view>
      </view>
      <view class="explain-item">
        <text class="explain-key">E</text>
        <view>
          <text class="explain-title">反馈优化</text>
          <text class="explain-copy">评分、收藏和清单行为会成为下一轮优化信号。</text>
        </view>
      </view>
    </view>

    <view class="chart-card">
      <view class="card-head">
        <text>营养完成情况</text>
        <text>{{ scorePercent }}%</text>
      </view>
      <view class="chart-body">
        <view class="donut" :style="{ background: ringGradient }">
          <view class="donut-inner">
            <text>{{ scorePercent }}%</text>
            <text>已完成</text>
          </view>
        </view>
        <view class="legend-list">
          <view v-for="m in metrics" :key="m.label" class="legend-row">
            <view class="legend-dot" :style="{ background: m.color }"></view>
            <text class="legend-label">{{ m.label }}</text>
            <text class="legend-val">{{ m.value }}%</text>
          </view>
        </view>
      </view>
    </view>

    <view class="trend-card">
      <view class="card-head">
        <text>本周趋势</text>
        <text>AI 估算</text>
      </view>
      <view class="trend-bars">
        <view v-for="day in trendDays" :key="day.label" class="trend-day">
          <view class="trend-track">
            <view class="trend-fill" :style="{ height: day.value + '%' }"></view>
          </view>
          <text>{{ day.label }}</text>
        </view>
      </view>
    </view>

    <view class="card">
      <view class="card-head">
        <text>{{ $t('nutritionGap') }}</text>
        <text>今日参考</text>
      </view>
      <view v-for="gap in nutritionGaps" :key="gap.label" class="gap-row">
        <view class="gap-top">
          <text class="gap-label">{{ gap.label }}</text>
          <text class="gap-pct">{{ gap.progress }}%</text>
        </view>
        <view class="bar"><view class="bar-fill" :style="{ width: gap.progress + '%', background: gap.color }"></view></view>
        <view class="gap-foot">
          <text>{{ gap.current }}</text>
          <text>{{ gap.needed }}</text>
        </view>
      </view>
    </view>

    <view class="card">
      <view class="card-head">
        <text>微量营养素</text>
        <text>来自推荐菜谱</text>
      </view>
      <view v-if="micronutrientTiles.length > 0" class="micro-grid">
        <view v-for="m in micronutrientTiles" :key="m.key" class="micro-tile">
          <view class="micro-top">
            <text class="micro-name">{{ m.label }}</text>
            <text class="micro-value">{{ m.value }}{{ m.unit }}</text>
          </view>
          <view class="micro-bar"><view :style="{ width: m.progress + '%', background: m.color }"></view></view>
          <text class="micro-note">{{ m.note }}</text>
        </view>
      </view>
      <view v-else class="micro-empty">
        <text>暂无后端微量营养素数据</text>
      </view>
    </view>

    <view class="card" v-if="recommendedRecipe">
      <view class="card-head">
        <text>{{ $t('recommendedRecipe') }}</text>
        <text>{{ matchPercent }}% 匹配</text>
      </view>
      <view class="recipe-row">
        <view class="recipe-icon"><image src="/static/icons/icon_plate.svg" mode="widthFix" /></view>
        <view class="recipe-info">
          <text class="recipe-title">{{ recommendedRecipe.title }}</text>
          <text class="recipe-sub">根据当前食材与营养缺口推荐</text>
        </view>
      </view>
    </view>

    <view class="card">
      <view class="card-head"><text>{{ $t('coreInsights') }}</text></view>
      <view class="insight-row">
        <view class="insight-icon red"></view>
        <text class="insight-label">{{ $t('heatDeficit') }}</text>
        <text class="insight-value">~320 kcal</text>
      </view>
      <view class="insight-row">
        <view class="insight-icon blue"></view>
        <text class="insight-label">{{ $t('proteinNeeded') }}</text>
        <text class="insight-value">~18g</text>
      </view>
      <view class="insight-row">
        <view class="insight-icon green"></view>
        <text class="insight-label">{{ $t('vitaminDeficit') }}</text>
        <text class="insight-value">{{ $t('vitaminDeficitItems') }}</text>
      </view>
    </view>

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
const errorNotice = ref('')

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
const matchPercent = computed(() => recommendedRecipe.value ? ((recommendedRecipe.value.matchScore || recommendedRecipe.value.match_score || 0) * 100).toFixed(0) : 0)
const todayDate = computed(() => {
  const d = new Date()
  return `${d.getFullYear()}/${d.getMonth()+1}/${d.getDate()}`
})
const username = computed(() => settingsStore.displayName || $t('defaultName'))
const welcomeText = computed(() => ($t('welcomeUser') || '').replace(/\{|\}/g, '').trim())
const ringGradient = computed(() => {
  const scoreValue = scorePercent.value
  return `conic-gradient(var(--teal) 0 ${scoreValue}%, var(--amber) ${scoreValue}% ${Math.min(100, scoreValue + 14)}%, #E8F1ED ${Math.min(100, scoreValue + 14)}% 100%)`
})

const metrics = [
  { label: $t('calorieIntake'), value: 75, color: 'var(--blue)' },
  { label: $t('protein'), value: 82, color: 'var(--teal)' },
  { label: $t('fiber'), value: 45, color: 'var(--amber)' },
  { label: $t('vitamins'), value: 68, color: 'var(--berry)' }
]
const trendDays = [
  { label: '一', value: 42 },
  { label: '二', value: 58 },
  { label: '三', value: 50 },
  { label: '四', value: 72 },
  { label: '五', value: 64 },
  { label: '六', value: 84 },
  { label: '日', value: 68 }
]
const nutritionGaps = [
  { label: $t('calories'), needed: `${$t('dailyTarget')} 2400`, current: `${$t('currentIntake')} 1800`, progress: 75, color: 'var(--blue)' },
  { label: $t('protein'), needed: `${$t('dailyTarget')} 70g`, current: `${$t('currentIntake')} 55g`, progress: 78, color: 'var(--teal)' },
  { label: $t('fiber'), needed: `${$t('dailyTarget')} 30g`, current: `${$t('currentIntake')} 12g`, progress: 40, color: 'var(--tomato)' },
  { label: `${$t('vitamins')} C`, needed: `${$t('dailyTarget')} 90mg`, current: `${$t('currentIntake')} 45mg`, progress: 50, color: 'var(--amber)' },
  { label: $t('iron'), needed: `${$t('dailyTarget')} 18mg`, current: `${$t('currentIntake')} 8mg`, progress: 44, color: 'var(--berry)' }
]
const microTargets = {
  vitamin_c: { label: '维生素C', unit: 'mg', target: 90, color: 'var(--amber)', note: '抗氧化与免疫支持' },
  iron: { label: '铁', unit: 'mg', target: 18, color: 'var(--berry)', note: '关注补铁与能量状态' },
  calcium: { label: '钙', unit: 'mg', target: 800, color: 'var(--blue)', note: '骨骼与肌肉支持' },
  fiber: { label: '膳食纤维', unit: 'g', target: 30, color: 'var(--teal)', note: '饱腹感与肠道友好' },
  potassium: { label: '钾', unit: 'mg', target: 2000, color: 'var(--tomato)', note: '电解质与心血管支持' },
  omega3: { label: 'Omega-3', unit: 'g', target: 1.1, color: 'var(--ink-green)', note: '优先来自鱼虾海产' }
}
const micronutrientTotals = computed(() => {
  const totals = {}
  recommendations.value.forEach(recipe => {
    const micro = recipe.micronutrients || {}
    Object.keys(microTargets).forEach(key => {
      totals[key] = (totals[key] || 0) + Number(micro[key] || 0)
    })
  })
  return totals
})
const micronutrientTiles = computed(() => Object.entries(microTargets).map(([key, meta]) => {
  const raw = micronutrientTotals.value[key] || 0
  const value = key === 'omega3' || key === 'iron' ? Number(raw.toFixed(1)) : Math.round(raw)
  return {
    key,
    ...meta,
    value,
    progress: Math.min(100, Math.round((raw / meta.target) * 100))
  }
}).filter(item => item.value > 0))

onLoad(async (options) => {
  try { if (options?.ingredients) ingredients.value = JSON.parse(decodeURIComponent(options.ingredients)) } catch (e) {}
  try {
    profile.value = await ApiService.getUserProfile()
    nutrition.value = await ApiService.getNutritionStatus()
    const names = ingredients.value.map(i => i.name)
    recommendations.value = await ApiService.generateMealPlan(names)
    recommendedRecipe.value = recommendations.value[0] || null
  } catch (e) {
    errorNotice.value = '后端健康数据暂未连通，未使用本地 mock 数据。'
    recommendations.value = []
    recommendedRecipe.value = null
  } finally {
    isLoading.value = false
  }
})

function exportList() {
  uni.navigateTo({ url: `/pages/list-export/list-export?recipes=${encodeURIComponent(JSON.stringify(recommendations.value))}` })
}
function goBack() { uni.navigateBack() }
</script>

<style scoped>
.hd-page {
  min-height: 100vh;
  background:
    radial-gradient(circle at 88% 0%, rgba(35,169,120,.13), transparent 30%),
    linear-gradient(180deg, #FAFCFB 0%, var(--bg) 44%);
  padding: 28rpx;
}
.loading-page { display: flex; align-items: center; justify-content: center; height: 100vh; color: var(--text-muted); font-size: 28rpx; }
.hd-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 22rpx; }
.hd-title { font-size: 44rpx; line-height: 1.12; font-weight: 950; color: var(--text); }
.hd-date { color: var(--text-muted); font-size: 24rpx; }
.summary-grid { display: grid; grid-template-columns: 1.25fr .875fr .875fr; gap: 14rpx; margin-bottom: 20rpx; }
.summary-card { background: rgba(255,255,255,.95); border-radius: var(--radius-md); padding: 20rpx; box-shadow: var(--shadow-sm), var(--hairline); min-height: 150rpx; animation: soft-pop .28s var(--ease) both; }
.summary-card.main { background: radial-gradient(circle at 88% 12%, rgba(88,207,160,.24), transparent 34%), linear-gradient(145deg, var(--ink-green), #214F40); color: #fff; box-shadow: 0 22rpx 46rpx rgba(23,59,46,.18); }
.summary-label { display: block; font-size: 22rpx; color: inherit; opacity: .72; }
.summary-value { display: block; margin-top: 8rpx; font-size: 50rpx; font-weight: 950; line-height: 1; }
.summary-foot { display: block; margin-top: 10rpx; color: var(--text-muted); font-size: 20rpx; }
.summary-card.main .summary-foot { color: rgba(255,255,255,.68); }
.summary-tag { margin-top: 12rpx; display: inline-flex; border-radius: var(--radius-full); padding: 5rpx 12rpx; font-size: 20rpx; font-weight: 800; }
.tag-good { background: var(--green-bg); color: var(--teal); }
.tag-medium { background: var(--amber-bg); color: #9A651B; }
.tag-bad { background: var(--red-bg); color: var(--red); }
.notice-card {
  display: flex;
  align-items: center;
  gap: 12rpx;
  background: var(--amber-bg);
  color: #9A651B;
  border-radius: var(--radius);
  padding: 16rpx 18rpx;
  margin-bottom: 20rpx;
  font-size: 23rpx;
  line-height: 1.45;
  box-shadow: var(--shadow-sm);
}
.notice-card image { width: 30rpx; height: 30rpx; flex-shrink: 0; }
.explain-card {
  background: rgba(255,255,255,.94);
  border-radius: var(--radius-md);
  padding: 22rpx;
  margin-bottom: 20rpx;
  box-shadow: var(--shadow-sm), var(--hairline);
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}
.explain-item { display: flex; gap: 14rpx; align-items: flex-start; }
.explain-key {
  width: 42rpx;
  height: 42rpx;
  border-radius: 14rpx;
  background: var(--purple-bg);
  color: var(--berry);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 900;
  flex-shrink: 0;
}
.explain-title { display: block; font-size: 25rpx; font-weight: 900; color: var(--text); }
.explain-copy { display: block; margin-top: 4rpx; font-size: 22rpx; color: var(--text-secondary); line-height: 1.45; }
.chart-card, .card, .trend-card { background: rgba(255,255,255,.95); border-radius: var(--radius-md); padding: 24rpx; margin-bottom: 20rpx; box-shadow: var(--shadow-sm), var(--hairline); animation: soft-pop .3s var(--ease) both; }
.card-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20rpx; }
.card-head text:first-child { font-size: 31rpx; font-weight: 950; color: var(--text); }
.card-head text:last-child { font-size: 23rpx; color: var(--text-muted); font-weight: 700; }
.chart-body { display: flex; align-items: center; gap: 28rpx; }
.donut { width: 184rpx; height: 184rpx; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0; box-shadow: 0 18rpx 34rpx rgba(35,169,120,.12); animation: float-breathe 4s ease-in-out infinite; }
.donut-inner { width: 120rpx; height: 120rpx; border-radius: 50%; background: #fff; display: flex; flex-direction: column; align-items: center; justify-content: center; box-shadow: inset 0 0 0 1px var(--border-light), var(--shadow-xs); }
.donut-inner text:first-child { font-size: 30rpx; font-weight: 900; color: var(--text); }
.donut-inner text:last-child { font-size: 20rpx; color: var(--text-muted); margin-top: 2rpx; }
.legend-list { flex: 1; display: flex; flex-direction: column; gap: 14rpx; }
.legend-row { display: flex; align-items: center; }
.legend-dot { width: 16rpx; height: 16rpx; border-radius: 50%; margin-right: 10rpx; }
.legend-label { flex: 1; color: var(--text-secondary); font-size: 24rpx; }
.legend-val { color: var(--text); font-size: 24rpx; font-weight: 900; }
.trend-bars { height: 180rpx; display: grid; grid-template-columns: repeat(7, 1fr); gap: 14rpx; align-items: end; padding-top: 10rpx; }
.trend-day { display: flex; flex-direction: column; align-items: center; gap: 10rpx; color: var(--text-muted); font-size: 20rpx; font-weight: 800; }
.trend-track { width: 18rpx; height: 136rpx; border-radius: 999rpx; background: var(--border-light); display: flex; align-items: flex-end; overflow: hidden; }
.trend-fill { width: 100%; min-height: 12rpx; border-radius: 999rpx; background: linear-gradient(180deg, var(--teal-light), var(--teal)); transform-origin: bottom center; animation: trend-rise .55s var(--ease) both; }
@keyframes trend-rise {
  from { transform: scaleY(.12); opacity: .4; }
  to { transform: scaleY(1); opacity: 1; }
}
.gap-row { margin-bottom: 20rpx; }
.gap-row:last-child { margin-bottom: 0; }
.gap-top { display: flex; justify-content: space-between; margin-bottom: 8rpx; }
.gap-label { font-size: 27rpx; font-weight: 800; color: var(--text); }
.gap-pct { font-size: 25rpx; font-weight: 900; color: var(--text-secondary); }
.bar { height: 10rpx; background: var(--border-light); border-radius: 10rpx; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 10rpx; transition: width .4s ease; transform-origin: left center; animation: bar-grow .55s var(--ease) both; }
.gap-foot { display: flex; justify-content: space-between; margin-top: 6rpx; }
.gap-foot text { font-size: 21rpx; color: var(--text-muted); }
.micro-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12rpx; }
.micro-tile { background: linear-gradient(180deg, var(--bg-elevated), #FFFFFF); border-radius: 20rpx; padding: 16rpx; min-width: 0; box-shadow: inset 0 0 0 1rpx rgba(19,35,29,.035); }
.micro-top { display: flex; justify-content: space-between; align-items: baseline; gap: 8rpx; }
.micro-name { font-size: 23rpx; font-weight: 900; color: var(--text); }
.micro-value { font-size: 22rpx; font-weight: 900; color: var(--text-secondary); }
.micro-bar { height: 8rpx; background: var(--border-light); border-radius: 8rpx; overflow: hidden; margin-top: 12rpx; }
.micro-bar view { height: 100%; border-radius: 8rpx; transform-origin: left center; animation: bar-grow .5s var(--ease) both; }
.micro-note { display: block; margin-top: 10rpx; font-size: 20rpx; color: var(--text-muted); line-height: 1.35; }
.micro-empty { padding: 28rpx 0; text-align: center; color: var(--text-muted); font-size: 24rpx; }
.recipe-row { display: flex; align-items: center; gap: 16rpx; }
.recipe-icon { width: 76rpx; height: 76rpx; border-radius: 23rpx; background: linear-gradient(145deg, var(--teal-bg), #FFFFFF); display: flex; align-items: center; justify-content: center; box-shadow: inset 0 0 0 1rpx rgba(35,169,120,.08); }
.recipe-icon image { width: 44rpx; height: 44rpx; }
.recipe-info { flex: 1; }
.recipe-title { display: block; font-size: 29rpx; font-weight: 900; color: var(--text); }
.recipe-sub { display: block; margin-top: 6rpx; font-size: 23rpx; color: var(--text-muted); }
.insight-row { display: flex; align-items: center; gap: 12rpx; margin-top: 18rpx; }
.insight-row:first-of-type { margin-top: 0; }
.insight-icon { width: 20rpx; height: 20rpx; border-radius: 7rpx; flex-shrink: 0; }
.insight-icon.red { background: var(--tomato); }
.insight-icon.blue { background: var(--blue); }
.insight-icon.green { background: var(--teal); }
.insight-label { flex: 1; color: var(--text); font-size: 26rpx; font-weight: 800; }
.insight-value { color: var(--text-secondary); font-size: 25rpx; }
.hd-actions { display: flex; gap: 16rpx; margin-top: 8rpx; }
.hd-actions button { flex: 1; height: 90rpx; border-radius: var(--radius-md); font-size: 28rpx; font-weight: 950; box-shadow: var(--shadow-sm); }
</style>
