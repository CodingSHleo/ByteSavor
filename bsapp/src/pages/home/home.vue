<template>
  <view class="home-page">
    <!-- Header: Avatar + Greeting + Streak -->
    <view class="header">
      <view class="h-left">
        <view class="h-avatar"><image class="h-avatar-img" src="/static/icons/icon_avatar.svg" mode="widthFix" /></view>
        <view class="h-greeting">
          <text class="h-hi">{{ greeting }}</text>
          <text class="h-date">{{ todayDate }}</text>
        </view>
      </view>
      <view class="h-streak">
        <image class="h-streak-icon" src="/static/icons/icon_fire.svg" mode="widthFix" />
        <text class="h-streak-num">7</text>
        <text class="h-streak-label">天</text>
      </view>
    </view>

    <scroll-view class="home-body" scroll-y refresher-enabled :refresher-triggered="refreshing" @refresherrefresh="onRefresh">

      <!-- Today's Focus Card -->
      <view class="focus-card">
        <view class="fc-top">
          <text class="fc-label">今日聚焦</text>
          <text class="fc-badge">AI 推荐</text>
        </view>
        <view class="fc-main">
          <view class="fc-info">
            <text class="fc-score">{{ nutritionScore }}</text>
            <text class="fc-unit">健康分</text>
          </view>
          <text class="fc-emoji">🥗</text>
        </view>
        <view class="fc-bars">
          <view class="fc-bar">
            <view class="fc-bar-head"><text>🥩 蛋白</text><text>{{ proteinPct }}%</text></view>
            <view class="fc-bar-track"><view class="fc-bar-fill p" :style="{width:proteinPct+'%'}"></view></view>
          </view>
          <view class="fc-bar">
            <view class="fc-bar-head"><text>🍚 碳水</text><text>{{ carbPct }}%</text></view>
            <view class="fc-bar-track"><view class="fc-bar-fill c" :style="{width:carbPct+'%'}"></view></view>
          </view>
          <view class="fc-bar">
            <view class="fc-bar-head"><text>🥑 脂肪</text><text>{{ fatPct }}%</text></view>
            <view class="fc-bar-track"><view class="fc-bar-fill f" :style="{width:fatPct+'%'}"></view></view>
          </view>
        </view>
        <view class="fc-cta" @tap="goIngredientRecognition">
          <text>📸 拍照识别食材</text>
          <text class="fc-arrow">›</text>
        </view>
      </view>

      <!-- Progress Section -->
      <view class="section-title">本周进度</view>
      <view class="progress-row">
        <view class="pr-card">
          <text class="pr-num">78%</text>
          <text class="pr-label">完成率</text>
        </view>
        <view class="pr-card">
          <text class="pr-num">12</text>
          <text class="pr-label">道菜谱</text>
        </view>
        <view class="pr-card">
          <text class="pr-num up">↑8%</text>
          <text class="pr-label">比上周</text>
        </view>
      </view>

      <!-- Quick Actions -->
      <view class="section-title">快捷操作</view>
      <view class="quick-row">
        <view class="q-item" @tap="goIngredientRecognition">
          <image class="q-icon" src="/static/icons/icon_export.svg" mode="widthFix" />
          <text class="q-label">食材识别</text>
        </view>
        <view class="q-item" @tap="goHealthDashboard">
          <image class="q-icon" src="/static/icons/icon_heart.svg" mode="widthFix" />
          <text class="q-label">健康看板</text>
        </view>
        <view class="q-item" @tap="goListExport">
          <image class="q-icon" src="/static/icons/icon_copy.svg" mode="widthFix" />
          <text class="q-label">导出清单</text>
        </view>
        <view class="q-item" @tap="goHistory">
          <image class="q-icon" src="/static/icons/icon_clock.svg" mode="widthFix" />
          <text class="q-label">历史记录</text>
        </view>
      </view>

      <!-- Recommended Next Step -->
      <view class="section-title">AI 推荐下一步</view>
      <view class="next-card" @tap="goIngredientRecognition">
        <image class="nx-emoji" src="/static/icons/icon_share.svg" mode="widthFix" />
        <view class="nx-body">
          <text class="nx-title">扫描你的食材</text>
          <text class="nx-desc">拍照识别冰箱里的食材，AI 为你定制今日菜谱</text>
        </view>
        <text class="nx-go">→</text>
      </view>

      <!-- Current Ingredients -->
      <view class="section-title">{{ $t('currentIngredients') }}</view>
      <view v-if="ingredients.length > 0" class="ing-row">
        <view v-for="(item, idx) in ingredients" :key="idx" class="ing-chip">
          <text class="ing-chip-dot"></text>
          <text>{{ item.name }}</text>
        </view>
      </view>
      <text v-else class="empty-hint">暂无食材，请先扫描识别</text>

      <!-- AI Assistant -->
      <view class="section-title">{{ $t('aiAssistant') }}</view>
      <view class="ai-box">
        <view class="ai-input-row">
          <input class="ai-input" v-model="agentMessage" :placeholder="$t('aiPlaceholder')" placeholder-class="ph" @confirm="sendAgentMessage" />
          <button class="ai-send" @tap="sendAgentMessage">{{ $t('send') }}</button>
        </view>
        <view v-if="agentResult" class="ai-result">
          <view v-if="agentResult.parsed_intent" class="ai-intent-row">
            <text class="ai-intent-chip">⏱ {{ agentResult.parsed_intent.time_limit || agentResult.parsed_intent.time }}min</text>
            <text class="ai-intent-chip">🎯 {{ goalLabel(agentResult.parsed_intent.goal) }}</text>
            <text v-for="item in (agentResult.parsed_intent.ingredients || agentResult.parsed_intent.core_items || [])" :key="item" class="ai-intent-chip">{{ item }}</text>
          </view>
          <view v-if="agentResult.cot_reasoning && agentResult.cot_reasoning.length > 0" class="ai-cot">
            <view v-for="(step, idx) in agentResult.cot_reasoning.slice(0,3)" :key="idx" class="ai-cot-row">
              <text class="ai-cot-num">{{ idx+1 }}</text><text class="ai-cot-text">{{ step }}</text>
            </view>
          </view>
        </view>
      </view>

      <!-- Recommended Recipes -->
      <view class="section-title">{{ $t('recommendedRecipes') }}</view>
      <view v-for="(r, idx) in recipes" :key="idx" class="recipe-row" @tap="goRecipeDetail(r)">
        <text class="rr-emoji">{{ r.imageEmoji || '🍽️' }}</text>
        <view class="rr-info">
          <text class="rr-title">{{ r.title }}</text>
          <text class="rr-meta">⏱ {{ r.cookTime||'--' }}' · 🔥 {{ r.calories||'--' }}kcal</text>
        </view>
        <view class="rr-score">{{ ((r.matchScore||0)*100).toFixed(0) }}%</view>
      </view>

      <view style="height: 30rpx;"></view>
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

const proteinPct = computed(() => Math.min(100, Math.round(nutritionScore.value * 1.15)))
const carbPct = computed(() => Math.min(100, Math.round(nutritionScore.value * 0.9)))
const fatPct = computed(() => Math.min(100, Math.round(nutritionScore.value * 0.7)))

const greeting = computed(() => {
  const h = new Date().getHours()
  const name = authStore.currentUser?.username || ''
  const hi = h < 12 ? '☀️ 早上好' : h < 18 ? '🌤 下午好' : '🌙 晚上好'
  return hi + (name ? '，' + name : '')
})
const todayDate = computed(() => {
  const d = new Date()
  return `${d.getFullYear()}/${d.getMonth()+1}/${d.getDate()} 周${['日','一','二','三','四','五','六'][d.getDay()]}`
})

watch(currentLang, () => { loadIngredients(); loadNutrition(); generateRecommendations() })

async function loadIngredients() {
  // 首页不传空 image_url 调 API，直接从本地缓存恢复或保持空
  try {
    const cached = uni.getStorageSync('last_ingredients')
    if (cached) ingredients.value = JSON.parse(cached)
  } catch (e) { /* ignore */ }
}
async function loadNutrition() { const d = await ApiService.getNutritionStatus(); nutritionScore.value = d.score || 65 }
async function generateRecommendations() { isLoading.value = true; const n = ingredients.value.map(i => i.name); recipes.value = await ApiService.generateMealPlan(n); isLoading.value = false }
async function onRefresh() { refreshing.value = true; await generateRecommendations(); refreshing.value = false }
async function refreshRecommendations() { await generateRecommendations(); historyStore.addEntry({ type: 'recommendation', title: $t('refreshTitle'), detail: t('refreshDetail',{n:ingredients.value.length}) }) }
async function sendAgentMessage() {
  const m = agentMessage.value.trim(); if (!m) return
  isLoading.value = true; const r = await ApiService.agentExecute(m); agentResult.value = r; agentMessage.value = ''; isLoading.value = false
}
function goalLabel(g) { const m = { fat_loss:'减脂', muscle_gain:'增肌', maintain:'保持' }; return m[g]||g }
function goRecipeDetail(r) { uni.navigateTo({ url: `/pages/recipe-detail/recipe-detail?recipeId=${r.recipe_id || r.recipeId}&title=${encodeURIComponent(r.title)}` }) }
function goIngredientRecognition() { uni.navigateTo({ url: '/pages/ingredient-recognition/ingredient-recognition' }) }
function goHealthDashboard() { uni.navigateTo({ url: `/pages/health-dashboard/health-dashboard?ingredients=${encodeURIComponent(JSON.stringify(ingredients.value))}` }) }
function goListExport() { uni.navigateTo({ url: `/pages/list-export/list-export?recipes=${encodeURIComponent(JSON.stringify(recipes.value))}` }) }
function goHistory() { uni.navigateTo({ url: '/pages/history/history' }) }
function goExplore() { uni.switchTab({ url: '/pages/explore/explore' }) }

onShow(() => {
  if (!authStore.isLoggedIn) { uni.redirectTo({ url: '/pages/login/login' }); return }
  loadIngredients(); loadNutrition(); generateRecommendations()
})
</script>

<style scoped>
.home-page { min-height: 100vh; background: var(--bg); overflow-x: hidden; }

/* ======== Header ======== */
.header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16rpx 28rpx; padding-top: calc(16rpx + var(--status-bar-height, 0px));
  background: #fff; border-bottom: 1px solid var(--border-light);
  position: sticky; top: 0; z-index: 100;
}
.h-left { display: flex; align-items: center; gap: 14rpx; }
.h-avatar { width: 72rpx; height: 72rpx; background: var(--teal-bg); border-radius: 50%; display: flex; align-items: center; justify-content: center; }
.h-avatar-img { width: 64rpx; height: 64rpx; border-radius: 50%; }
.h-greeting { display: flex; flex-direction: column; }
.h-hi { font-size: 30rpx; font-weight: 700; color: var(--text); }
.h-date { font-size: 24rpx; color: var(--text-muted); margin-top: 2rpx; }
.h-streak { display: flex; align-items: center; gap: 4rpx; background: var(--teal-bg); padding: 10rpx 18rpx; border-radius: var(--radius-full); }
.h-streak-icon { width: 28rpx; height: 28rpx; }
.h-streak-num { font-size: 26rpx; font-weight: 800; color: var(--teal); }
.h-streak-label { font-size: 20rpx; color: var(--teal); }

.home-body { padding: 20rpx 24rpx; height: calc(100vh - 120rpx - var(--status-bar-height, 0px)); }

/* ======== Focus Card ======== */
.focus-card {
  background: #fff; border-radius: var(--radius); padding: 24rpx; margin-bottom: 24rpx;
  box-shadow: var(--shadow-md);
}
.fc-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 18rpx; }
.fc-label { font-size: 30rpx; font-weight: 700; color: var(--text); }
.fc-badge { font-size: 22rpx; background: var(--teal-bg); color: var(--teal); padding: 6rpx 16rpx; border-radius: var(--radius-full); font-weight: 600; }
.fc-main { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20rpx; }
.fc-info { display: flex; flex-direction: column; }
.fc-score { font-size: 64rpx; font-weight: 800; color: var(--text); line-height: 1; }
.fc-unit { font-size: 26rpx; color: var(--text-muted); margin-top: 4rpx; }
.fc-emoji { width: 88rpx; height: 88rpx; }
.fc-bars { display: flex; flex-direction: column; gap: 10rpx; margin-bottom: 18rpx; }
.fc-bar-head { display: flex; justify-content: space-between; font-size: 24rpx; color: var(--text-secondary); margin-bottom: 4rpx; }
.fc-bar-track { height: 8rpx; background: var(--border-light); border-radius: 4rpx; overflow: hidden; }
.fc-bar-fill { height: 100%; border-radius: 4rpx; }
.fc-bar-fill.p { background: var(--tomato); }
.fc-bar-fill.c { background: var(--cheese); }
.fc-bar-fill.f { background: var(--berry); }
.fc-cta {
  display: flex; align-items: center; justify-content: space-between;
  background: var(--avocado); color: #fff;
  padding: 18rpx 24rpx; border-radius: 16rpx;
  font-size: 28rpx; font-weight: 600;
}
.fc-arrow { font-size: 34rpx; }

/* ======== Section ======== */
.section-title { font-size: 32rpx; font-weight: 700; color: var(--text); margin: 28rpx 0 16rpx; }

/* ======== Progress ======== */
.progress-row { display: flex; gap: 14rpx; }
.pr-card {
  flex: 1; background: #fff; border-radius: var(--radius); padding: 24rpx;
  box-shadow: var(--shadow-sm); display: flex; flex-direction: column; align-items: center; gap: 8rpx;
}
.pr-num { font-size: 36rpx; font-weight: 800; color: var(--text); }
.pr-num.up { color: var(--green); }
.pr-label { font-size: 24rpx; color: var(--text-muted); }

/* ======== Quick Actions ======== */
.quick-row { display: flex; gap: 14rpx; }
.q-item {
  flex: 1; background: #fff; border-radius: var(--radius); padding: 24rpx 8rpx;
  box-shadow: var(--shadow-sm); display: flex; flex-direction: column; align-items: center; gap: 10rpx;
}
.q-icon { width: 56rpx; height: 56rpx; }
.q-label { font-size: 24rpx; font-weight: 600; color: var(--text-secondary); }

/* ======== Next Step ======== */
.next-card {
  display: flex; align-items: center; gap: 18rpx;
  background: #fff; border-radius: var(--radius); padding: 24rpx;
  box-shadow: var(--shadow-sm);
}
.nx-emoji { width: 64rpx; height: 64rpx; }
.nx-body { flex: 1; display: flex; flex-direction: column; gap: 6rpx; }
.nx-title { font-size: 28rpx; font-weight: 700; color: var(--text); }
.nx-desc { font-size: 24rpx; color: var(--text-muted); line-height: 1.4; }
.nx-go { font-size: 36rpx; color: var(--text-muted); }

/* ======== Ingredients ======== */
.ing-row { display: flex; flex-wrap: wrap; gap: 10rpx; }
.ing-chip {
  display: flex; align-items: center; gap: 6rpx;
  background: #fff; border-radius: var(--radius-full); padding: 12rpx 20rpx;
  font-size: 26rpx; color: var(--text); box-shadow: var(--shadow-sm);
}
.ing-chip-dot { width: 12rpx; height: 12rpx; border-radius: 50%; background: var(--teal); }
.empty-hint { font-size: 26rpx; color: var(--text-muted); display: block; padding: 10rpx 0; }

/* ======== AI ======== */
.ai-box { background: #fff; border-radius: var(--radius); padding: 22rpx 24rpx; box-shadow: var(--shadow-sm); }
.ai-input-row { display: flex; gap: 10rpx; }
.ai-input { flex: 1; height: 72rpx; background: var(--bg); border: 1px solid var(--border); border-radius: var(--radius-full); padding: 0 24rpx; font-size: 28rpx; color: var(--text); }
.ai-send { width: 100rpx; height: 72rpx; background: var(--berry); color: #fff; border: none; border-radius: var(--radius-full); font-size: 26rpx; font-weight: 700; white-space: nowrap; }
.ai-result { margin-top: 16rpx; }
.ai-intent-row { display: flex; flex-wrap: wrap; gap: 8rpx; margin-bottom: 12rpx; }
.ai-intent-chip { font-size: 22rpx; background: var(--teal-bg); color: var(--teal); padding: 6rpx 16rpx; border-radius: var(--radius-full); }
.ai-cot { display: flex; flex-direction: column; gap: 8rpx; }
.ai-cot-row { display: flex; align-items: flex-start; gap: 8rpx; }
.ai-cot-num { width: 30rpx; height: 30rpx; background: var(--berry); color: #fff; border-radius: 50%; font-size: 20rpx; display: flex; align-items: center; justify-content: center; }
.ai-cot-text { font-size: 24rpx; color: var(--text-secondary); flex: 1; }

/* ======== Recipes ======== */
.recipe-row {
  display: flex; align-items: center; gap: 16rpx;
  background: #fff; border-radius: var(--radius); padding: 20rpx 24rpx; margin-bottom: 14rpx;
  box-shadow: var(--shadow-sm);
}
.rr-emoji { font-size: 44rpx; }
.rr-info { flex: 1; display: flex; flex-direction: column; gap: 6rpx; }
.rr-title { font-size: 28rpx; font-weight: 600; color: var(--text); }
.rr-meta { font-size: 24rpx; color: var(--text-muted); }
.rr-score { font-size: 30rpx; font-weight: 800; color: var(--avocado); }
.ph { color: var(--text-placeholder); }
</style>
