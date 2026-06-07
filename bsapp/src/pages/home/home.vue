<template>
  <view class="home-page">
    <view class="home-top">
      <view class="user-row">
        <view class="user-left">
          <image class="avatar" src="/static/icons/icon_avatar.svg" mode="aspectFill" />
          <view>
            <text class="greeting">{{ greeting }}</text>
            <text class="date-text">{{ todayDate }}</text>
          </view>
        </view>
        <view class="streak-pill">
          <image src="/static/icons/icon_fire.svg" class="streak-icon" mode="widthFix" />
          <text>7 天</text>
        </view>
      </view>

      <view class="status-card" @tap="goHealthDashboard">
        <view class="status-main">
          <view>
            <text class="eyebrow">今日营养状态</text>
            <view class="score-line">
              <text class="score">{{ nutritionScore }}</text>
              <text class="score-unit">/100</text>
            </view>
            <text class="status-copy">{{ statusCopy }}</text>
          </view>
          <view class="score-ring" :style="{ background: ringGradient }">
            <view class="score-ring-inner">
              <text>{{ nutritionScore }}%</text>
            </view>
          </view>
        </view>
        <view class="macro-grid">
          <view class="macro-card protein">
            <text class="macro-value">{{ proteinPct }}%</text>
            <text class="macro-label">蛋白</text>
          </view>
          <view class="macro-card carbs">
            <text class="macro-value">{{ carbPct }}%</text>
            <text class="macro-label">碳水</text>
          </view>
          <view class="macro-card fat">
            <text class="macro-value">{{ fatPct }}%</text>
            <text class="macro-label">脂肪</text>
          </view>
        </view>
      </view>
    </view>

    <scroll-view class="home-body" scroll-y refresher-enabled :refresher-triggered="refreshing" @refresherrefresh="onRefresh">
      <view class="action-grid">
        <view class="scan-card" @tap="goIngredientRecognition">
          <view class="scan-icon-wrap">
            <image src="/static/icons/icon_scan.svg" class="scan-icon" mode="widthFix" />
          </view>
          <view class="scan-text">
            <text class="scan-title">拍照识别食材</text>
            <text class="scan-desc">识别新鲜度、分量和可做菜谱</text>
          </view>
          <text class="chevron">›</text>
        </view>
        <view class="byte-card">
          <text class="byte-title">B-Y-T-E</text>
          <text class="byte-desc">{{ byteStageText }}</text>
          <view class="byte-track">
            <view class="byte-fill" :style="{ width: byteProgress + '%' }"></view>
          </view>
        </view>
      </view>

      <view v-if="apiNotice" class="notice-card">
        <image src="/static/icons/icon_flash.svg" mode="aspectFit" />
        <text>{{ apiNotice }}</text>
      </view>

      <view class="byte-flow-card">
        <view v-for="(step, idx) in byteFlow" :key="step.key" class="byte-flow-step" :class="{ active: byteFlowActive(idx) }">
          <view class="flow-dot">{{ step.key }}</view>
          <text>{{ step.label }}</text>
        </view>
      </view>

      <view class="section-head">
        <text>当前食材</text>
        <text class="section-link" @tap="goIngredientRecognition">{{ ingredients.length ? '去校正' : '去识别' }}</text>
      </view>
      <view class="ingredient-card">
        <view v-if="ingredients.length > 0" class="ingredient-list">
          <view v-for="(item, idx) in ingredients" :key="idx" class="ingredient-chip" :class="freshnessClass(item.freshness)">
            <text class="ingredient-name">{{ item.name }}</text>
            <text class="ingredient-meta">{{ freshnessLabel(item.freshness) }}</text>
          </view>
        </view>
        <view v-else class="empty-row">
          <image src="/static/icons/icon_camera.svg" class="empty-icon" mode="widthFix" />
          <text>还没有食材记录，先拍一张冰箱或食材照片</text>
        </view>
      </view>

      <view class="section-head">
        <text>推荐下一餐</text>
        <text class="section-link" @tap="refreshRecommendations">刷新</text>
      </view>
      <view v-if="topRecipe" class="meal-card" @tap="goRecipeDetail(topRecipe)">
        <view class="meal-visual">
          <text>{{ topRecipe.imageEmoji || '食' }}</text>
        </view>
        <view class="meal-info">
          <text class="meal-title">{{ topRecipe.title }}</text>
          <text class="meal-meta">{{ topRecipe.cookTime || '--' }} min · {{ topRecipe.calories || '--' }} kcal</text>
          <view class="reason-row">
            <text v-for="reason in recipeReasons" :key="reason" class="reason-chip">{{ reason }}</text>
          </view>
        </view>
        <view class="match-badge">{{ matchPercent(topRecipe) }}%</view>
      </view>
      <view v-else class="empty-card">
        <text>暂无推荐，识别食材后生成更准确的菜谱</text>
      </view>

      <view class="mini-grid">
        <view class="mini-card" @tap="goListExport">
          <image src="/static/icons/icon_cart.svg" class="mini-icon" mode="widthFix" />
          <text class="mini-title">购物清单</text>
          <text class="mini-desc">{{ recipes.length || 0 }} 道菜可合并</text>
        </view>
        <view class="mini-card" @tap="goHistory">
          <image src="/static/icons/icon_clock.svg" class="mini-icon" mode="widthFix" />
          <text class="mini-title">历史记录</text>
          <text class="mini-desc">回看识别与推荐</text>
        </view>
      </view>

      <view class="section-head ai-section-head">
        <text>AI 助手</text>
        <text class="section-sub">输入目标直接走 Agent</text>
      </view>
      <view class="ai-card">
        <view class="ai-input-row">
          <image src="/static/icons/icon_ai.svg" class="ai-icon" mode="widthFix" />
          <input class="ai-input" v-model="agentMessage" :placeholder="$t('aiPlaceholder')" placeholder-class="ph" @confirm="sendAgentMessage" />
          <button class="ai-send" @tap="sendAgentMessage">{{ $t('send') }}</button>
        </view>
        <view v-if="agentResult" class="ai-result">
          <view v-if="agentResult.parsed_intent" class="ai-intent-row">
            <text class="ai-intent-chip">{{ agentResult.parsed_intent.time_limit || agentResult.parsed_intent.time || 30 }}min</text>
            <text class="ai-intent-chip">{{ goalLabel(agentResult.parsed_intent.goal) }}</text>
            <text v-for="item in (agentResult.parsed_intent.ingredients || agentResult.parsed_intent.core_items || [])" :key="item" class="ai-intent-chip">{{ item }}</text>
          </view>
          <view v-if="agentResult.cot_reasoning && agentResult.cot_reasoning.length > 0" class="ai-cot">
            <view v-for="(step, idx) in agentResult.cot_reasoning.slice(0,3)" :key="idx" class="ai-cot-row">
              <text class="ai-cot-num">{{ idx + 1 }}</text>
              <text class="ai-cot-text">{{ step }}</text>
            </view>
          </view>
        </view>
      </view>

      <view class="bottom-safe"></view>
    </scroll-view>
  </view>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { ApiService } from '@/api/index'
import { useAuthStore } from '@/store/auth'
import { useHistoryStore } from '@/store/history'
import { t, currentLang } from '@/utils/i18n'

const $t = key => t(key)
const authStore = useAuthStore()
const historyStore = useHistoryStore()

const nutritionScore = ref(65)
const ingredients = ref([])
const recipes = ref([])
const isLoading = ref(false)
const refreshing = ref(false)
const agentMessage = ref('')
const agentResult = ref(null)
const apiNotice = ref('')
const byteFlow = [
  { key: 'B', label: '食材感知' },
  { key: 'Y', label: '约束推理' },
  { key: 'T', label: '任务执行' },
  { key: 'E', label: '反馈优化' }
]

const proteinPct = computed(() => Math.min(100, Math.round(nutritionScore.value * 1.15)))
const carbPct = computed(() => Math.min(100, Math.round(nutritionScore.value * 0.9)))
const fatPct = computed(() => Math.min(100, Math.round(nutritionScore.value * 0.7)))
const topRecipe = computed(() => recipes.value[0] || null)
const byteProgress = computed(() => {
  if (agentResult.value) return 100
  if (recipes.value.length > 0 && ingredients.value.length > 0) return 75
  if (recipes.value.length > 0) return 50
  if (ingredients.value.length > 0) return 25
  return 10
})
const byteStageText = computed(() => {
  if (byteProgress.value >= 100) return '反馈闭环已生成'
  if (byteProgress.value >= 75) return '已完成推荐，待执行'
  if (byteProgress.value >= 50) return '探索模式推荐中'
  if (byteProgress.value >= 25) return '已感知食材'
  return '等待输入'
})
const statusCopy = computed(() => {
  if (nutritionScore.value >= 80) return '状态很好，保持当前饮食节奏'
  if (nutritionScore.value >= 60) return '整体平稳，建议补足蛋白和纤维'
  return '今日缺口较多，建议生成一餐均衡食谱'
})
const ringGradient = computed(() => {
  const score = Math.max(0, Math.min(100, nutritionScore.value))
  return `conic-gradient(var(--teal) 0 ${score}%, var(--amber) ${score}% ${Math.min(100, score + 14)}%, #E8F1ED ${Math.min(100, score + 14)}% 100%)`
})
const recipeReasons = computed(() => {
  const r = topRecipe.value
  if (!r) return []
  const out = []
  if (r.cookTime) out.push(`${r.cookTime}分钟`)
  if (r.calories) out.push(`${r.calories}kcal`)
  out.push('适合今日目标')
  return out.slice(0, 3)
})
function byteFlowActive(idx) {
  const thresholds = [25, 50, 75, 100]
  return byteProgress.value >= thresholds[idx]
}

const greeting = computed(() => {
  const h = new Date().getHours()
  const name = authStore.currentUser?.username || ''
  const hi = h < 12 ? '早上好' : h < 18 ? '下午好' : '晚上好'
  return hi + (name ? '，' + name : '')
})
const todayDate = computed(() => {
  const d = new Date()
  return `${d.getFullYear()}/${d.getMonth()+1}/${d.getDate()} 周${['日','一','二','三','四','五','六'][d.getDay()]}`
})

watch(currentLang, () => { loadIngredients(); loadNutrition(); generateRecommendations() })

async function loadIngredients() {
  try {
    const cached = uni.getStorageSync('last_ingredients')
    if (cached) ingredients.value = JSON.parse(cached)
  } catch (e) { /* ignore */ }
}
async function loadNutrition() {
  try {
    const d = await ApiService.getNutritionStatus()
    nutritionScore.value = d.score || 65
  } catch (e) {
    apiNotice.value = '后端营养服务暂不可用，当前显示本地演示数据。'
  }
}
async function generateRecommendations() {
  isLoading.value = true
  try {
    const n = ingredients.value.map(i => i.name)
    recipes.value = await ApiService.generateMealPlan(n)
  } catch (e) {
    apiNotice.value = '推荐服务暂不可用，已保留默认菜谱用于界面预览。'
  } finally {
    isLoading.value = false
  }
}
async function onRefresh() { refreshing.value = true; await loadNutrition(); await generateRecommendations(); refreshing.value = false }
async function refreshRecommendations() { await generateRecommendations(); historyStore.addEntry({ type: 'recommendation', title: $t('refreshTitle'), detail: t('refreshDetail',{n:ingredients.value.length}) }) }
async function sendAgentMessage() {
  const m = agentMessage.value.trim(); if (!m) return
  isLoading.value = true
  try {
    const r = await ApiService.agentExecute(m)
    agentResult.value = r
    agentMessage.value = ''
  } catch (e) {
    apiNotice.value = 'AI Agent 暂未连通，请稍后重试或检查后端服务。'
  } finally {
    isLoading.value = false
  }
}
function goalLabel(g) { const m = { fat_loss:'减脂', muscle_gain:'增肌', maintain:'保持', balanced:'均衡', healthy:'健康' }; return m[g]||g }
function matchPercent(r) { return ((r?.matchScore || r?.match_score || 0) * 100).toFixed(0) }
function freshnessLabel(f) { return ({ high: '新鲜', normal: '冷藏', medium: '普通', low: '待确认' })[f] || f || '待确认' }
function freshnessClass(f) { return f === 'high' ? 'fresh-high' : f === 'low' ? 'fresh-low' : 'fresh-normal' }
function goRecipeDetail(r) { uni.navigateTo({ url: `/pages/recipe-detail/recipe-detail?recipeId=${r.recipe_id || r.recipeId}&title=${encodeURIComponent(r.title)}` }) }
function goIngredientRecognition() { uni.navigateTo({ url: '/pages/ingredient-recognition/ingredient-recognition' }) }
function goHealthDashboard() { uni.navigateTo({ url: `/pages/health-dashboard/health-dashboard?ingredients=${encodeURIComponent(JSON.stringify(ingredients.value))}` }) }
function goListExport() { uni.navigateTo({ url: `/pages/list-export/list-export?recipes=${encodeURIComponent(JSON.stringify(recipes.value))}` }) }
function goHistory() { uni.navigateTo({ url: '/pages/history/history' }) }

onShow(() => {
  if (!authStore.isLoggedIn) { uni.redirectTo({ url: '/pages/login/login' }); return }
  loadIngredients(); loadNutrition(); generateRecommendations()
})
</script>

<style scoped>
.home-page { min-height: 100vh; background: var(--bg); overflow-x: hidden; }
.home-top { padding: calc(22rpx + var(--status-bar-height, 0px)) 28rpx 18rpx; }
.user-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 22rpx; }
.user-left { display: flex; align-items: center; gap: 16rpx; }
.avatar { width: 72rpx; height: 72rpx; border-radius: 50%; background: #fff; box-shadow: var(--shadow-sm); }
.greeting { display: block; font-size: 32rpx; font-weight: 800; color: var(--text); }
.date-text { display: block; font-size: 23rpx; color: var(--text-muted); margin-top: 2rpx; }
.streak-pill { height: 56rpx; padding: 0 18rpx; border-radius: var(--radius-full); background: #fff; display: flex; align-items: center; gap: 6rpx; color: var(--teal); font-size: 24rpx; font-weight: 700; box-shadow: var(--shadow-sm); }
.streak-icon { width: 26rpx; height: 26rpx; }

.status-card { background: #fff; border-radius: var(--radius-lg); padding: 26rpx; box-shadow: var(--shadow-md); }
.status-main { display: flex; justify-content: space-between; align-items: center; gap: 20rpx; }
.eyebrow { display: block; font-size: 24rpx; color: var(--text-secondary); margin-bottom: 8rpx; }
.score-line { display: flex; align-items: flex-end; }
.score { font-size: 68rpx; line-height: 1; font-weight: 900; color: var(--text); }
.score-unit { font-size: 28rpx; color: var(--text-muted); margin-left: 4rpx; margin-bottom: 6rpx; }
.status-copy { display: block; margin-top: 10rpx; font-size: 24rpx; color: var(--text-secondary); line-height: 1.45; max-width: 390rpx; }
.score-ring { width: 150rpx; height: 150rpx; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.score-ring-inner { width: 98rpx; height: 98rpx; border-radius: 50%; background: #fff; display: flex; align-items: center; justify-content: center; color: var(--teal); font-size: 24rpx; font-weight: 900; box-shadow: inset 0 0 0 1px var(--border-light); }
.macro-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12rpx; margin-top: 22rpx; }
.macro-card { border-radius: 18rpx; padding: 16rpx 14rpx; }
.macro-card.protein { background: var(--green-bg); }
.macro-card.carbs { background: var(--amber-bg); }
.macro-card.fat { background: var(--purple-bg); }
.macro-value { display: block; font-size: 30rpx; font-weight: 900; color: var(--text); }
.macro-label { display: block; margin-top: 4rpx; font-size: 22rpx; color: var(--text-muted); }

.home-body { padding: 0 28rpx; height: calc(100vh - 360rpx - var(--status-bar-height, 0px)); }
.action-grid { display: grid; grid-template-columns: 1.25fr .75fr; gap: 16rpx; margin-bottom: 24rpx; }
.scan-card, .byte-card, .ingredient-card, .meal-card, .mini-card, .ai-card, .empty-card { background: #fff; border-radius: var(--radius); box-shadow: var(--shadow-sm); }
.scan-card { min-height: 148rpx; padding: 22rpx; display: flex; align-items: center; gap: 16rpx; }
.scan-icon-wrap { width: 68rpx; height: 68rpx; border-radius: 20rpx; background: var(--teal-bg); display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.scan-icon { width: 42rpx; height: 42rpx; }
.scan-text { flex: 1; min-width: 0; }
.scan-title { display: block; font-size: 28rpx; font-weight: 800; color: var(--text); }
.scan-desc { display: block; font-size: 22rpx; color: var(--text-muted); margin-top: 6rpx; line-height: 1.4; }
.chevron { color: var(--text-muted); font-size: 38rpx; }
.byte-card { padding: 22rpx; }
.byte-title { display: block; font-size: 30rpx; font-weight: 900; color: var(--text); }
.byte-desc { display: block; margin-top: 8rpx; color: var(--text-secondary); font-size: 22rpx; min-height: 56rpx; }
.byte-track { height: 10rpx; border-radius: 10rpx; background: var(--border-light); overflow: hidden; margin-top: 14rpx; }
.byte-fill { height: 100%; border-radius: 10rpx; background: var(--teal); transition: width .35s var(--ease); }
.notice-card {
  display: flex;
  align-items: center;
  gap: 12rpx;
  background: var(--amber-bg);
  color: #9A651B;
  border-radius: var(--radius);
  padding: 16rpx 18rpx;
  margin-bottom: 18rpx;
  font-size: 23rpx;
  line-height: 1.45;
  box-shadow: var(--shadow-sm);
}
.notice-card image { width: 30rpx; height: 30rpx; flex-shrink: 0; }
.byte-flow-card {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8rpx;
  background: #fff;
  border-radius: var(--radius);
  padding: 14rpx;
  margin-bottom: 22rpx;
  box-shadow: var(--shadow-sm);
}
.byte-flow-step {
  min-height: 92rpx;
  border-radius: 18rpx;
  background: var(--bg-elevated);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6rpx;
  color: var(--text-muted);
}
.byte-flow-step.active { background: var(--teal-bg); color: var(--accent); }
.flow-dot {
  width: 34rpx;
  height: 34rpx;
  border-radius: 12rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20rpx;
  font-weight: 900;
  background: #fff;
}
.byte-flow-step text { font-size: 19rpx; font-weight: 800; }

.section-head { display: flex; align-items: baseline; justify-content: space-between; margin: 24rpx 2rpx 14rpx; }
.section-head text:first-child { font-size: 31rpx; font-weight: 900; color: var(--text); }
.section-link { font-size: 24rpx; color: var(--teal); font-weight: 700; }
.section-sub { font-size: 22rpx; color: var(--text-muted); }
.ai-section-head {
  justify-content: flex-start;
  align-items: baseline;
  gap: 14rpx;
}
.ai-section-head .section-sub {
  margin-left: 0;
}
.ingredient-card { padding: 20rpx; }
.ingredient-list { display: flex; flex-wrap: wrap; gap: 12rpx; }
.ingredient-chip { padding: 12rpx 16rpx; border-radius: var(--radius-full); display: flex; align-items: center; gap: 8rpx; }
.ingredient-chip.fresh-high { background: var(--green-bg); color: var(--teal); }
.ingredient-chip.fresh-normal { background: var(--amber-bg); color: #9A651B; }
.ingredient-chip.fresh-low { background: var(--red-bg); color: var(--red); }
.ingredient-name { font-size: 25rpx; font-weight: 800; }
.ingredient-meta { font-size: 21rpx; opacity: .75; }
.empty-row { min-height: 88rpx; display: flex; align-items: center; gap: 14rpx; color: var(--text-muted); font-size: 25rpx; line-height: 1.45; }
.empty-icon { width: 48rpx; height: 48rpx; }

.meal-card { padding: 20rpx; display: flex; align-items: center; gap: 18rpx; }
.meal-visual { width: 82rpx; height: 82rpx; border-radius: 24rpx; background: var(--teal-bg); display: flex; align-items: center; justify-content: center; flex-shrink: 0; font-size: 38rpx; }
.meal-info { flex: 1; min-width: 0; }
.meal-title { display: block; font-size: 29rpx; font-weight: 900; color: var(--text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.meal-meta { display: block; font-size: 23rpx; color: var(--text-muted); margin-top: 6rpx; }
.reason-row { display: flex; gap: 8rpx; flex-wrap: wrap; margin-top: 10rpx; }
.reason-chip { font-size: 20rpx; color: var(--text-secondary); background: var(--bg); border-radius: var(--radius-full); padding: 4rpx 10rpx; }
.match-badge { min-width: 66rpx; height: 54rpx; border-radius: 18rpx; background: var(--green-bg); color: var(--teal); font-size: 25rpx; font-weight: 900; display: flex; align-items: center; justify-content: center; }
.empty-card { padding: 26rpx; color: var(--text-muted); font-size: 25rpx; }

.mini-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16rpx; margin-top: 24rpx; }
.mini-card { padding: 22rpx; min-height: 142rpx; }
.mini-icon { width: 42rpx; height: 42rpx; margin-bottom: 14rpx; }
.mini-title { display: block; font-size: 27rpx; font-weight: 850; color: var(--text); }
.mini-desc { display: block; margin-top: 6rpx; font-size: 22rpx; color: var(--text-muted); }

.ai-card { padding: 18rpx; }
.ai-input-row { display: flex; align-items: center; gap: 10rpx; }
.ai-icon { width: 42rpx; height: 42rpx; flex-shrink: 0; }
.ai-input { flex: 1; min-width: 0; height: 72rpx; background: var(--bg); border: 1px solid var(--border-light); border-radius: var(--radius-full); padding: 0 22rpx; font-size: 26rpx; color: var(--text); box-sizing: border-box; }
.ai-send { width: 96rpx; height: 72rpx; margin: 0; padding: 0; background: var(--berry); color: #fff; border: none; border-radius: var(--radius-full); font-size: 25rpx; font-weight: 800; line-height: 1; display: flex; align-items: center; justify-content: center; box-sizing: border-box; flex-shrink: 0; }
.ai-result { margin-top: 16rpx; }
.ai-intent-row { display: flex; flex-wrap: wrap; gap: 8rpx; margin-bottom: 12rpx; }
.ai-intent-chip { font-size: 22rpx; background: var(--purple-bg); color: var(--berry); padding: 7rpx 14rpx; border-radius: var(--radius-full); }
.ai-cot { display: flex; flex-direction: column; gap: 10rpx; }
.ai-cot-row { display: flex; align-items: flex-start; gap: 10rpx; }
.ai-cot-num { width: 32rpx; height: 32rpx; background: var(--berry); color: #fff; border-radius: 50%; font-size: 20rpx; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.ai-cot-text { font-size: 24rpx; color: var(--text-secondary); flex: 1; line-height: 1.45; }
.ph { color: var(--text-placeholder); }
.bottom-safe { height: 132rpx; }
</style>
