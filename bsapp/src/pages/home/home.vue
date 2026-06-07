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
            <image src="/static/icons/icon_scan.svg" class="scan-icon" mode="aspectFit" />
            <text>扫</text>
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
        <view v-if="agentMessages.length === 0" class="ai-empty">
          <text>告诉我你的目标、食材和时间，我会展示推理过程并给出可导出的食谱。</text>
        </view>
        <view v-else class="ai-thread">
          <view v-for="msg in agentMessages" :key="msg.id" class="chat-row" :class="msg.role">
            <view class="chat-bubble">
              <text class="chat-text">{{ msg.text }}</text>
              <view v-if="msg.result" class="agent-panel">
                <view class="agent-stages">
                  <view v-for="stage in msg.result.stages || []" :key="stage.stage" class="agent-stage" :class="stage.status">
                    <text class="stage-name">{{ stageLabel(stage.stage) }}</text>
                    <text class="stage-status">{{ stageStatusLabel(stage.status) }}</text>
                  </view>
                </view>
                <view v-if="msg.result.parsed_intent" class="ai-intent-row">
                  <text class="ai-intent-chip">{{ msg.result.parsed_intent.time_limit || msg.result.parsed_intent.time || 30 }}min</text>
                  <text class="ai-intent-chip">{{ goalLabel(msg.result.parsed_intent.goal) }}</text>
                  <text v-for="item in intentIngredients(msg.result)" :key="item" class="ai-intent-chip">{{ item }}</text>
                </view>
                <view v-if="msg.result.recipes && msg.result.recipes.length" class="agent-recipes">
                  <view v-for="recipe in msg.result.recipes.slice(0, 2)" :key="recipe.recipe_id || recipe.recipeId" class="agent-recipe">
                    <view class="agent-recipe-main" @tap="goRecipeDetail(recipe)">
                      <text class="agent-recipe-title">{{ recipe.title }}</text>
                      <text class="agent-recipe-meta">{{ matchPercent(recipe) }}% 匹配 · {{ recipe.cookTime || recipe.cook_time || '--' }}min · {{ recipe.calories || '--' }}kcal</text>
                    </view>
                    <button class="agent-mini-btn" @tap.stop="saveAgentRecipe(recipe, msg.result)">记录</button>
                  </view>
                </view>
                <view v-if="msg.result.shopping_list && msg.result.shopping_list.length" class="agent-shopping">
                  <text>已合并 {{ msg.result.shopping_list.length }} 项清单</text>
                  <button @tap.stop="exportAgentList(msg.result)">导出</button>
                </view>
              </view>
            </view>
          </view>
        </view>
        <view class="ai-input-row">
          <image src="/static/icons/icon_ai.svg" class="ai-icon" mode="widthFix" />
          <input class="ai-input" v-model="agentMessage" :placeholder="$t('aiPlaceholder')" placeholder-class="ph" @confirm="sendAgentMessage" />
          <button class="ai-send" @tap="sendAgentMessage">{{ $t('send') }}</button>
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
const agentMessages = ref([])
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
    nutritionScore.value = d.score || 0
  } catch (e) {
    apiNotice.value = '后端营养服务暂不可用，未使用本地 mock 数据。'
    nutritionScore.value = 0
  }
}
async function generateRecommendations() {
  isLoading.value = true
  try {
    const n = ingredients.value.map(i => i.name)
    recipes.value = await ApiService.generateMealPlan(n)
  } catch (e) {
    apiNotice.value = '推荐服务暂不可用，未使用本地 mock 菜谱。'
    recipes.value = []
  } finally {
    isLoading.value = false
  }
}
async function onRefresh() { refreshing.value = true; await loadNutrition(); await generateRecommendations(); refreshing.value = false }
async function refreshRecommendations() { await generateRecommendations(); historyStore.addEntry({ type: 'recommendation', title: $t('refreshTitle'), detail: t('refreshDetail',{n:ingredients.value.length}) }) }
async function sendAgentMessage() {
  const m = agentMessage.value.trim(); if (!m) return
  const userMsg = { id: 'u_' + Date.now(), role: 'user', text: m }
  agentMessages.value.push(userMsg)
  isLoading.value = true
  try {
    const r = await ApiService.agentExecute(m)
    agentResult.value = r
    if (r.recipes && r.recipes.length) recipes.value = r.recipes
    if (r.parsed_intent?.ingredients) ingredients.value = r.parsed_intent.ingredients.map(i => typeof i === 'string' ? { name: i } : i)
    agentMessages.value.push({
      id: 'a_' + Date.now(),
      role: 'assistant',
      text: r.reply || '我已完成分析，并整理了推荐食谱。',
      result: r
    })
    saveAgentSession(r)
    agentMessage.value = ''
  } catch (e) {
    apiNotice.value = 'AI Agent 暂未连通，请稍后重试或检查后端服务。'
    agentMessages.value.push({ id: 'e_' + Date.now(), role: 'assistant', text: e.message || apiNotice.value })
  } finally {
    isLoading.value = false
  }
}
function intentIngredients(result) {
  const intent = result?.parsed_intent || {}
  return (intent.ingredients || intent.core_items || []).map(i => typeof i === 'string' ? i : i.name).filter(Boolean)
}
function stageLabel(stage) { return ({ sense: '感知', decision: '推荐', task: '清单' })[stage] || stage }
function stageStatusLabel(status) { return ({ success: '完成', skipped: '跳过', empty: '空', error: '异常', failed: '失败' })[status] || status }
function saveAgentSession(result) {
  const first = result.recipes?.[0]
  historyStore.addEntry({
    type: 'agent_recipe',
    title: first?.title || 'AI 助手推荐',
    detail: result.reply || `生成 ${result.recipes?.length || 0} 个推荐`,
    recipeId: first?.recipe_id || first?.recipeId || '',
    recipes: result.recipes || [],
    shoppingList: result.shopping_list || []
  })
}
function saveAgentRecipe(recipe, result) {
  historyStore.addEntry({
    type: 'agent_recipe',
    title: recipe.title,
    detail: `AI 推荐 · ${matchPercent(recipe)}% 匹配`,
    recipeId: recipe.recipe_id || recipe.recipeId || '',
    recipes: [recipe],
    shoppingList: result.shopping_list || []
  })
  uni.showToast({ title: '已记录到历史', icon: 'success' })
}
function exportAgentList(result) {
  const payload = result.recipes?.length ? result.recipes : recipes.value
  uni.navigateTo({ url: `/pages/list-export/list-export?recipes=${encodeURIComponent(JSON.stringify(payload))}` })
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
.home-page {
  min-height: 100vh;
  background:
    radial-gradient(circle at 12% 0%, rgba(35,169,120,.12), transparent 32%),
    linear-gradient(180deg, #F8FCFA 0%, var(--bg) 42%);
  overflow-x: hidden;
}
.home-top { padding: calc(24rpx + var(--status-bar-height, 0px)) 28rpx 18rpx; position: relative; }
.user-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 22rpx; }
.user-left { display: flex; align-items: center; gap: 16rpx; min-width: 0; flex: 1; }
.user-left > view { min-width: 0; }
.avatar { width: 74rpx; height: 74rpx; border-radius: 50%; background: #fff; box-shadow: var(--shadow-sm), var(--hairline); }
.greeting { display: block; max-width: 500rpx; font-size: 33rpx; font-weight: 900; color: var(--text); letter-spacing: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.date-text { display: block; font-size: 23rpx; color: var(--text-muted); margin-top: 2rpx; }
.streak-pill { height: 58rpx; padding: 0 18rpx; border-radius: var(--radius-full); background: rgba(255,255,255,.88); display: flex; align-items: center; gap: 6rpx; color: var(--teal); font-size: 24rpx; font-weight: 800; box-shadow: var(--shadow-sm), var(--hairline); backdrop-filter: blur(12rpx); }
.streak-icon { width: 26rpx; height: 26rpx; }

.status-card {
  background:
    radial-gradient(circle at 88% 18%, rgba(88,207,160,.24), transparent 28%),
    linear-gradient(145deg, rgba(255,255,255,.96), rgba(248,252,250,.92));
  border-radius: var(--radius-xl);
  padding: 28rpx;
  box-shadow: var(--shadow-lg), var(--hairline);
  position: relative;
  overflow: hidden;
  animation: soft-pop .36s var(--ease) both;
}
.status-card::after {
  content: "";
  position: absolute;
  top: -80rpx;
  right: -70rpx;
  width: 220rpx;
  height: 220rpx;
  border-radius: 50%;
  background: rgba(35,169,120,.08);
  pointer-events: none;
}
.status-main { display: flex; justify-content: space-between; align-items: center; gap: 20rpx; }
.eyebrow { display: block; font-size: 23rpx; color: var(--text-secondary); margin-bottom: 8rpx; font-weight: 800; }
.score-line { display: flex; align-items: flex-end; }
.score { font-size: 76rpx; line-height: .96; font-weight: 950; color: var(--text); }
.score-unit { font-size: 28rpx; color: var(--text-muted); margin-left: 4rpx; margin-bottom: 6rpx; }
.status-copy { display: block; margin-top: 10rpx; font-size: 24rpx; color: var(--text-secondary); line-height: 1.45; max-width: 390rpx; }
.score-ring { width: 154rpx; height: 154rpx; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0; box-shadow: 0 16rpx 30rpx rgba(35,169,120,.12); animation: float-breathe 3.8s ease-in-out infinite; position: relative; z-index: 1; }
.score-ring-inner { width: 102rpx; height: 102rpx; border-radius: 50%; background: rgba(255,255,255,.96); display: flex; align-items: center; justify-content: center; color: var(--teal); font-size: 24rpx; font-weight: 950; box-shadow: inset 0 0 0 1px var(--border-light), var(--shadow-xs); }
.macro-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12rpx; margin-top: 22rpx; }
.macro-card { border-radius: 20rpx; padding: 17rpx 15rpx; box-shadow: inset 0 0 0 1rpx rgba(255,255,255,.52); }
.macro-card.protein { background: var(--green-bg); }
.macro-card.carbs { background: var(--amber-bg); }
.macro-card.fat { background: var(--purple-bg); }
.macro-value { display: block; font-size: 30rpx; font-weight: 900; color: var(--text); }
.macro-label { display: block; margin-top: 4rpx; font-size: 22rpx; color: var(--text-muted); }

.home-body { padding: 0 28rpx; height: calc(100vh - 370rpx - var(--status-bar-height, 0px)); }
.action-grid { display: grid; grid-template-columns: 1.25fr .75fr; gap: 16rpx; margin-bottom: 24rpx; }
.scan-card, .byte-card, .ingredient-card, .meal-card, .mini-card, .ai-card, .empty-card { background: rgba(255,255,255,.94); border-radius: var(--radius-md); box-shadow: var(--shadow-sm), var(--hairline); }
.scan-card { min-height: 150rpx; padding: 23rpx; display: flex; align-items: center; gap: 16rpx; position: relative; overflow: hidden; }
.scan-card::after, .ai-card::after {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(105deg, transparent 0%, rgba(255,255,255,.62) 42%, transparent 70%);
  transform: translateX(-120%);
  animation: shimmer-sweep 5.8s ease-in-out infinite;
  pointer-events: none;
}
.scan-icon-wrap { width: 70rpx; height: 70rpx; border-radius: 22rpx; background: var(--teal-bg); display: flex; align-items: center; justify-content: center; flex-shrink: 0; position: relative; box-shadow: inset 0 0 0 1rpx rgba(35,169,120,.08); }
.scan-icon-wrap text { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; color: var(--teal); font-size: 24rpx; font-weight: 900; opacity: .28; }
.scan-icon { width: 42rpx; height: 42rpx; position: relative; z-index: 1; }
.scan-text { flex: 1; min-width: 0; }
.scan-title { display: block; font-size: 28rpx; font-weight: 800; color: var(--text); }
.scan-desc { display: block; font-size: 22rpx; color: var(--text-muted); margin-top: 6rpx; line-height: 1.4; }
.chevron { color: var(--text-muted); font-size: 38rpx; }
.byte-card { padding: 22rpx; background: linear-gradient(160deg, #FFFFFF 0%, #F4FBF7 100%); }
.byte-title { display: block; font-size: 30rpx; font-weight: 900; color: var(--text); }
.byte-desc { display: block; margin-top: 8rpx; color: var(--text-secondary); font-size: 22rpx; min-height: 56rpx; }
.byte-track { height: 10rpx; border-radius: 10rpx; background: var(--border-light); overflow: hidden; margin-top: 14rpx; }
.byte-fill { height: 100%; border-radius: 10rpx; background: linear-gradient(90deg, var(--teal), var(--teal-light)); transition: width .35s var(--ease); transform-origin: left center; animation: bar-grow .5s var(--ease) both; }
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
  background: rgba(255,255,255,.92);
  border-radius: var(--radius-md);
  padding: 14rpx;
  margin-bottom: 22rpx;
  box-shadow: var(--shadow-sm), var(--hairline);
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
.byte-flow-step.active { background: linear-gradient(180deg, var(--teal-bg), #F4FCF8); color: var(--accent); box-shadow: inset 0 0 0 1rpx rgba(35,169,120,.10); }
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
.section-head text:first-child { font-size: 31rpx; font-weight: 950; color: var(--text); }
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
.ingredient-chip { padding: 12rpx 16rpx; border-radius: var(--radius-full); display: flex; align-items: center; gap: 8rpx; box-shadow: inset 0 0 0 1rpx rgba(255,255,255,.55); animation: soft-pop .28s var(--ease) both; }
.ingredient-chip.fresh-high { background: var(--green-bg); color: var(--teal); }
.ingredient-chip.fresh-normal { background: var(--amber-bg); color: #9A651B; }
.ingredient-chip.fresh-low { background: var(--red-bg); color: var(--red); }
.ingredient-name { font-size: 25rpx; font-weight: 800; }
.ingredient-meta { font-size: 21rpx; opacity: .75; }
.empty-row { min-height: 88rpx; display: flex; align-items: center; gap: 14rpx; color: var(--text-muted); font-size: 25rpx; line-height: 1.45; }
.empty-icon { width: 48rpx; height: 48rpx; }

.meal-card { padding: 20rpx; display: flex; align-items: center; gap: 18rpx; background: linear-gradient(145deg, #FFFFFF, #F8FCFA); }
.meal-visual { width: 84rpx; height: 84rpx; border-radius: 25rpx; background: linear-gradient(150deg, var(--teal-bg), #FFFFFF); display: flex; align-items: center; justify-content: center; flex-shrink: 0; font-size: 38rpx; box-shadow: inset 0 0 0 1rpx rgba(35,169,120,.08); }
.meal-info { flex: 1; min-width: 0; }
.meal-title { display: block; font-size: 29rpx; font-weight: 900; color: var(--text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.meal-meta { display: block; font-size: 23rpx; color: var(--text-muted); margin-top: 6rpx; }
.reason-row { display: flex; gap: 8rpx; flex-wrap: wrap; margin-top: 10rpx; }
.reason-chip { font-size: 20rpx; color: var(--text-secondary); background: var(--bg); border-radius: var(--radius-full); padding: 4rpx 10rpx; }
.match-badge { min-width: 68rpx; height: 56rpx; border-radius: 19rpx; background: var(--green-bg); color: var(--teal); font-size: 25rpx; font-weight: 950; display: flex; align-items: center; justify-content: center; box-shadow: inset 0 0 0 1rpx rgba(35,169,120,.12); }
.empty-card { padding: 26rpx; color: var(--text-muted); font-size: 25rpx; }

.mini-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16rpx; margin-top: 24rpx; }
.mini-card { padding: 22rpx; min-height: 142rpx; background: linear-gradient(180deg, #FFFFFF, #F9FCFA); }
.mini-icon { width: 42rpx; height: 42rpx; margin-bottom: 14rpx; }
.mini-title { display: block; font-size: 27rpx; font-weight: 850; color: var(--text); }
.mini-desc { display: block; margin-top: 6rpx; font-size: 22rpx; color: var(--text-muted); }

.ai-card { padding: 18rpx; position: relative; overflow: hidden; background: linear-gradient(150deg, #FFFFFF 0%, #FBFAFF 100%); }
.ai-empty { background: linear-gradient(135deg, var(--purple-bg), #FFFFFF); border-radius: 22rpx; padding: 20rpx; margin-bottom: 14rpx; color: var(--text-secondary); font-size: 24rpx; line-height: 1.45; box-shadow: inset 0 0 0 1rpx rgba(141,122,230,.08); }
.ai-thread { display: flex; flex-direction: column; gap: 12rpx; margin-bottom: 14rpx; max-height: 560rpx; overflow: hidden; }
.chat-row { display: flex; }
.chat-row.user { justify-content: flex-end; }
.chat-row.assistant { justify-content: flex-start; }
.chat-bubble { max-width: 92%; border-radius: 24rpx; padding: 17rpx 19rpx; box-sizing: border-box; animation: soft-pop .24s var(--ease) both; }
.chat-row.user .chat-bubble { background: linear-gradient(135deg, var(--teal), var(--teal-light)); color: #fff; border-bottom-right-radius: 8rpx; box-shadow: 0 12rpx 24rpx rgba(35,169,120,.16); }
.chat-row.assistant .chat-bubble { background: rgba(248,252,250,.96); color: var(--text); border-bottom-left-radius: 8rpx; box-shadow: var(--shadow-xs), var(--hairline); }
.chat-text { display: block; font-size: 24rpx; line-height: 1.5; }
.agent-panel { margin-top: 14rpx; display: flex; flex-direction: column; gap: 12rpx; }
.agent-stages { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8rpx; }
.agent-stage { border-radius: 17rpx; padding: 11rpx 8rpx; background: #fff; border: 1rpx solid var(--border-light); box-shadow: var(--shadow-xs); }
.agent-stage.success { background: var(--green-bg); border-color: rgba(35,169,120,.18); }
.agent-stage.error, .agent-stage.failed { background: var(--red-bg); border-color: rgba(239,68,68,.18); }
.stage-name { display: block; font-size: 20rpx; font-weight: 900; color: var(--text); text-align: center; }
.stage-status { display: block; margin-top: 4rpx; font-size: 18rpx; color: var(--text-muted); text-align: center; }
.agent-recipes { display: flex; flex-direction: column; gap: 8rpx; }
.agent-recipe { background: #fff; border-radius: 19rpx; padding: 14rpx; display: flex; align-items: center; gap: 12rpx; border: 1rpx solid var(--border-light); box-shadow: var(--shadow-xs); }
.agent-recipe-main { flex: 1; min-width: 0; }
.agent-recipe-title { display: block; font-size: 25rpx; font-weight: 900; color: var(--text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.agent-recipe-meta { display: block; margin-top: 6rpx; font-size: 20rpx; color: var(--text-muted); }
.agent-mini-btn { width: 78rpx; height: 52rpx; margin: 0; padding: 0; border-radius: var(--radius-full); background: var(--berry); color: #fff; font-size: 21rpx; font-weight: 900; border: none; display: flex; align-items: center; justify-content: center; line-height: 1; flex-shrink: 0; }
.agent-shopping { background: #fff; border-radius: 19rpx; padding: 12rpx 14rpx; display: flex; align-items: center; justify-content: space-between; gap: 12rpx; border: 1rpx solid var(--border-light); box-shadow: var(--shadow-xs); }
.agent-shopping text { color: var(--text-secondary); font-size: 22rpx; }
.agent-shopping button { width: 82rpx; height: 52rpx; margin: 0; padding: 0; border-radius: var(--radius-full); background: var(--teal); color: #fff; font-size: 21rpx; font-weight: 900; border: none; line-height: 1; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.ai-input-row { display: flex; align-items: center; gap: 10rpx; }
.ai-icon { width: 42rpx; height: 42rpx; flex-shrink: 0; }
.ai-input { flex: 1; min-width: 0; height: 74rpx; background: #fff; border: 1px solid var(--border-light); border-radius: var(--radius-full); padding: 0 22rpx; font-size: 26rpx; color: var(--text); box-sizing: border-box; box-shadow: inset 0 0 0 1rpx rgba(19,35,29,.02); }
.ai-send { width: 98rpx; height: 74rpx; margin: 0; padding: 0; background: linear-gradient(135deg, var(--berry), #A996FF); color: #fff; border: none; border-radius: var(--radius-full); font-size: 25rpx; font-weight: 900; line-height: 1; display: flex; align-items: center; justify-content: center; box-sizing: border-box; flex-shrink: 0; box-shadow: 0 12rpx 24rpx rgba(141,122,230,.20); }
.ai-intent-row { display: flex; flex-wrap: wrap; gap: 8rpx; margin-bottom: 12rpx; }
.ai-intent-chip { font-size: 22rpx; background: var(--purple-bg); color: var(--berry); padding: 7rpx 14rpx; border-radius: var(--radius-full); }
.ph { color: var(--text-placeholder); }
.bottom-safe { height: 132rpx; }
</style>
