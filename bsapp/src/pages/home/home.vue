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

      <view class="hero-panel" @tap="goHealthDashboard">
        <view class="hero-copy">
          <text class="hero-label">ByteSavor AI 今日建议</text>
          <text class="hero-title">{{ statusCopy }}</text>
          <view class="hero-actions">
            <button class="hero-primary" @tap.stop="goIngredientRecognition">拍照识别</button>
            <button class="hero-secondary" @tap.stop="refreshRecommendations">生成推荐</button>
          </view>
        </view>
        <view class="hero-orb">
          <text class="orb-label">实时缺口</text>
          <view class="score-ring" :style="{ background: ringGradient }">
            <view class="score-ring-inner">
              <text>{{ nutritionScore }}</text>
              <text>score</text>
            </view>
          </view>
        </view>
      </view>

      <view class="status-strip">
        <view class="score-mini">
          <view>
            <text class="eyebrow">今日营养</text>
            <view class="score-line">
              <text class="score">{{ nutritionScore }}</text>
              <text class="score-unit">/100</text>
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
      <view class="quick-actions">
        <view class="quick-action scan-card" @tap="goIngredientRecognition">
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
        <view class="quick-action ask-card" @tap="agentMessage = agentMessage || '牛肉南瓜减脂30分钟'">
          <view class="ask-icon">AI</view>
          <view>
            <text class="ask-title">问 AI 助手</text>
            <text class="ask-desc">目标、时间、食材都可以直接说</text>
          </view>
        </view>
        <view class="byte-card">
          <view class="byte-card-head">
            <view>
              <text class="byte-title">B-Y-T-E</text>
              <text class="byte-desc">{{ byteStageText }}</text>
            </view>
            <text class="byte-percent">{{ byteProgress }}%</text>
          </view>
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
        <text>功能中枢</text>
        <text class="section-sub">完整入口都在这里</text>
      </view>
      <view class="hub-grid">
        <view v-for="item in hubItems" :key="item.key" class="hub-card" :class="item.tone" @tap="goHub(item.key)">
          <view class="hub-icon">
            <image :src="item.icon" mode="aspectFit" />
          </view>
          <text class="hub-title">{{ item.title }}</text>
          <text class="hub-desc">{{ item.desc }}</text>
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
        <text>今日用餐计划</text>
        <text class="section-sub">完成后才计入营养</text>
      </view>
      <!-- 餐次切换 tabs -->
      <view class="meal-tabs">
        <view v-for="slot in mainMealSlots" :key="slot.key"
          class="meal-tab" :class="{ active: activeMealTab === slot.key }"
          @tap="activeMealTab = slot.key">
          <text>{{ slot.label }}</text>
          <text v-if="slotMeal(slot.key)?.status === 'planned'" class="tab-dot planned"></text>
          <text v-if="slotMeal(slot.key)?.status === 'completed'" class="tab-dot completed"></text>
        </view>
      </view>
      <view class="plan-card">
        <view v-for="slot in activeMealSlots" :key="slot.key" class="plan-row" :class="slotMeal(slot.key)?.status || 'empty'">
          <view class="plan-slot">
            <text class="plan-name">{{ slot.label }}</text>
            <text class="plan-status" :class="slotMeal(slot.key)?.status">{{ mealStatusText(slotMeal(slot.key)) }}</text>
          </view>
          <view class="plan-main">
            <text class="plan-title">{{ slotMeal(slot.key)?.recipe?.title || '还未选择' }}</text>
            <text class="plan-meta">{{ slotMeal(slot.key)?.nutrition?.calories || 0 }} kcal · {{ slotMeal(slot.key)?.nutrition?.protein || 0 }}g 蛋白</text>
          </view>
          <view class="plan-buttons">
            <button v-if="slotMeal(slot.key)?.status === 'planned'" class="plan-done" @tap.stop="completePlannedMeal(slotMeal(slot.key))">完成</button>
            <button v-if="slotMeal(slot.key)?.status === 'planned'" class="plan-switch" @tap.stop="switchMealSlot(slotMeal(slot.key))">切换</button>
            <button v-if="!slotMeal(slot.key)" class="plan-add" @tap.stop="goExploreAddMeal(slot.key)">+ 添加</button>
          </view>
        </view>
      </view>

      <view v-if="latestAgentAdoption" class="adoption-card">
        <view class="adoption-head">
          <view>
            <text class="adoption-kicker">AGENT ACTION</text>
            <text class="adoption-title">{{ latestAgentAdoption.title }}</text>
          </view>
          <text class="adoption-clear" @tap="latestAgentAdoption = null">收起</text>
        </view>
        <view class="adoption-timeline">
          <view v-for="(event, idx) in latestAgentAdoption.events" :key="idx" class="adoption-event" :class="event.status">
            <view class="adoption-dot"></view>
            <view class="adoption-copy">
              <text>{{ event.title || agentAdoptionEventTitle(event) }}</text>
              <text>{{ event.detail || agentAdoptionEventDetail(event) }}</text>
            </view>
          </view>
        </view>
        <view v-if="latestAgentAdoption.shoppingList.length" class="adoption-shopping" @tap="openTodayShoppingList">
          <text>补购清单 {{ latestAgentAdoption.shoppingList.length }} 项</text>
          <text>查看</text>
        </view>
      </view>

      <view class="section-head">
        <text>推荐下一餐</text>
        <text class="section-link" @tap="refreshRecommendations">刷新</text>
      </view>
      <scroll-view v-if="recipes.length" class="meal-scroll" scroll-x :show-scrollbar="false">
        <view v-for="recipe in recipes.slice(0, 8)" :key="recipe.recipe_id || recipe.recipeId" class="meal-card" @tap="goRecipeDetail(recipe)">
          <view class="meal-visual">
            <text>{{ recipe.imageEmoji || '食' }}</text>
          </view>
          <view class="meal-info">
            <text class="meal-kicker">AI NEXT MEAL</text>
            <text class="meal-title">{{ recipe.title }}</text>
            <text class="meal-meta">{{ recipe.cookTime || '--' }} min · {{ recipe.calories || '--' }} kcal</text>
            <view class="reason-row">
              <text v-for="reason in recipeReasonsFor(recipe)" :key="reason" class="reason-chip">{{ reason }}</text>
            </view>
            <view v-if="recipeExplainChips(recipe).length" class="explain-row">
              <text v-for="chip in recipeExplainChips(recipe)" :key="chip" class="explain-chip">{{ chip }}</text>
              <text class="explain-more" @tap.stop="showRecipeExplain(recipe)">详情</text>
            </view>
          </view>
          <view class="match-badge">
            <text>{{ matchPercent(recipe) }}%</text>
            <text>match</text>
          </view>
          <view class="meal-actions">
            <button @tap.stop="favoriteRecipe(recipe)">收藏</button>
            <button @tap.stop="checkRecipe(recipe)">清点</button>
            <button class="primary" @tap.stop="askPlanMeal(recipe)">计划</button>
          </view>
        </view>
      </scroll-view>
      <view v-else class="empty-card">
        <text>暂无推荐，识别食材后生成更准确的菜谱</text>
      </view>

      <view v-if="explainRecipe" class="explain-mask" @tap="explainRecipe = null">
        <view class="explain-sheet" @tap.stop>
          <view class="explain-sheet-head">
            <view>
              <text class="explain-sheet-kicker">AGENT EXPLAIN</text>
              <text class="explain-sheet-title">{{ explainRecipe.title }}</text>
            </view>
            <text class="explain-close" @tap="explainRecipe = null">×</text>
          </view>
          <view class="explain-block">
            <text class="explain-block-title">已匹配现有食材</text>
            <text class="explain-block-copy">{{ explainText(recipeMatchedIngredients(explainRecipe), '暂未命中库存食材') }}</text>
          </view>
          <view class="explain-block">
            <text class="explain-block-title">缺少与补购建议</text>
            <text class="explain-block-copy">{{ explainText(recipeMissingIngredients(explainRecipe), '主要食材已覆盖') }}</text>
            <text v-if="purchaseSuggestionLabels(explainRecipe).length" class="explain-block-hint">建议补买：{{ purchaseSuggestionLabels(explainRecipe).join('、') }}</text>
          </view>
          <view class="explain-block">
            <text class="explain-block-title">偏好与记忆证据</text>
            <text class="explain-block-copy">{{ explainText(preferenceMatchLabels(explainRecipe), '暂无明确偏好命中') }}</text>
            <text v-if="preferenceEvidenceLabels(explainRecipe).length" class="explain-block-hint">{{ preferenceEvidenceLabels(explainRecipe).join('、') }}</text>
          </view>
        </view>
      </view>

      <view class="section-head ai-section-head">
        <text>AI 助手</text>
        <text class="section-sub">输入目标直接走 Agent</text>
      </view>
      <view class="ai-card">
        <!-- Agent 加载骨架屏 -->
        <view v-if="agentLoading" class="agent-skeleton">
          <view class="skeleton-progress-wrap">
            <view class="skeleton-progress-bar">
              <view class="skeleton-progress-fill" :style="{ width: agentProgress + '%' }"></view>
            </view>
            <text class="skeleton-progress-text">{{ agentProgress < 30 ? '正在规划...' : agentProgress < 60 ? '正在执行工具...' : agentProgress < 85 ? '正在评估结果...' : '分析完成，生成回复...' }}</text>
          </view>
          <view class="skeleton-line long"></view>
          <view class="skeleton-line medium"></view>
          <view class="skeleton-line short"></view>
        </view>
        <view v-if="!agentLoading && agentMessages.length === 0" class="ai-empty">
          <view class="ai-empty-mark">AI</view>
          <view class="ai-empty-copy">
            <text class="ai-empty-title">让 Agent 直接规划下一餐</text>
            <text class="ai-empty-desc">输入"牛肉南瓜减脂30分钟"，我会展示理解、推荐和清单合并过程。</text>
          </view>
        </view>
        <view v-else class="ai-thread">
          <view v-for="msg in agentMessages" :key="msg.id" class="chat-row" :class="msg.role">
            <view class="chat-bubble">
              <text class="chat-text">{{ msg.text }}</text>
              <view v-if="msg.result" class="agent-panel">
                <view v-if="msg.result.events && msg.result.events.length" class="agent-timeline">
                  <view v-for="(event, eventIndex) in msg.result.events" :key="`${event.type}-${event.step}-${eventIndex}`" class="agent-event" :class="event.type">
                    <view class="event-dot"></view>
                    <view class="event-copy">
                      <text class="event-title">{{ agentEventTitle(event) }}</text>
                      <text v-if="agentEventDetail(event)" class="event-detail">{{ agentEventDetail(event) }}</text>
                    </view>
                    <text v-if="event.latency_ms !== undefined" class="event-latency">{{ event.latency_ms }}ms</text>
                  </view>
                </view>
                <view v-else class="agent-stages">
                  <view v-for="stage in msg.result.stages || []" :key="stage.stage" class="agent-stage" :class="stage.status">
                    <text class="stage-name">{{ stageLabel(stage.stage) }}</text>
                    <text class="stage-status">{{ stageStatusLabel(stage.status) }}</text>
                  </view>
                </view>
                <!-- memory_used 展示 -->
                <view v-if="msg.result.memory_used && msg.result.memory_used.length" class="agent-memory">
                  <text class="memory-head">本次参考记忆</text>
                  <view v-for="(mem, mi) in msg.result.memory_used" :key="mi" class="memory-chip" :class="mem.type">
                    <text class="memory-chip-label">[{{ mem.type }}]</text>
                    <text>{{ mem.summary }}</text>
                  </view>
                </view>
                <!-- L2 用户确认 -->
                <view v-if="msg.result.confirmation_prompts && msg.result.confirmation_prompts.length" class="agent-confirm">
                  <view v-for="(prompt, pi) in msg.result.confirmation_prompts" :key="pi" class="confirm-card">
                    <text class="confirm-question">{{ prompt.question }}</text>
                    <view class="confirm-options">
                      <button v-for="opt in prompt.options" :key="opt.key" class="confirm-btn" @tap.stop="handleConfirmation(pi, opt, msg)">{{ opt.label }}</button>
                    </view>
                  </view>
                </view>
                <view v-if="msg.result.parsed_intent" class="ai-intent-row">
                  <text class="ai-intent-chip">{{ msg.result.parsed_intent.time_limit || msg.result.parsed_intent.time || 30 }}min</text>
                  <text class="ai-intent-chip">{{ goalLabel(msg.result.parsed_intent.goal) }}</text>
                  <text v-for="item in intentIngredients(msg.result)" :key="item" class="ai-intent-chip">{{ item }}</text>
                </view>
                <view v-if="msg.result.recipes && msg.result.recipes.length" class="agent-recipes">
                  <view v-for="recipe in msg.result.recipes.slice(0, 2)" :key="recipe.recipe_id || recipe.recipeId" class="agent-recipe" :class="{ adopted: isAgentRecipeAdopted(msg.result, recipe) }">
                    <view class="agent-recipe-main" @tap="goRecipeDetail(recipe)">
                      <text class="agent-recipe-title">{{ recipe.title }}</text>
                      <text class="agent-recipe-meta">{{ matchPercent(recipe) }}% 匹配 · {{ recipe.cookTime || recipe.cook_time || '--' }}min · {{ recipe.calories || '--' }}kcal</text>
                      <view v-if="recipeExplainChips(recipe).length" class="agent-recipe-explain">
                        <text v-for="chip in recipeExplainChips(recipe)" :key="chip">{{ chip }}</text>
                      </view>
                      <view v-if="recipeIngredientsPreview(recipe).length" class="agent-ingredient-strip">
                        <text v-for="item in recipeIngredientsPreview(recipe)" :key="item.name">{{ item.name }}{{ item.amount ? ' ' + item.amount : '' }}</text>
                      </view>
                    </view>
                    <button v-if="!isAgentRecipeAdopted(msg.result, recipe)" class="agent-mini-btn primary" @tap.stop="adoptAgentRecipe(recipe, msg)">加入</button>
                    <button v-else class="agent-mini-btn done" @tap.stop="showAgentAdoptedMeal(msg.result)">已加</button>
                  </view>
                </view>
                <view v-if="msg.result.adopted_meal" class="agent-meal-flow">
                  <view class="agent-meal-head">
                    <view>
                      <text class="agent-meal-kicker">已加入 {{ mealSlotLabel(msg.result.adopted_meal.meal_slot) }}</text>
                      <text class="agent-meal-title">{{ agentAdoptedMealTitle(msg.result) }}</text>
                    </view>
                    <text class="agent-meal-status" :class="msg.result.adopted_meal.status">{{ mealStatusText(msg.result.adopted_meal) }}</text>
                  </view>
                  <view v-if="agentAdoptionEvents(msg.result).length" class="agent-flow-events">
                    <view v-for="(event, idx) in agentAdoptionEvents(msg.result)" :key="idx" class="agent-flow-event" :class="event.status">
                      <view class="flow-dot"></view>
                      <view class="flow-copy">
                        <text>{{ event.title || agentAdoptionEventTitle(event) }}</text>
                        <text>{{ event.detail || agentAdoptionEventDetail(event) }}</text>
                      </view>
                    </view>
                  </view>
                  <view class="agent-meal-lists">
                    <view v-if="agentAdoptedIngredients(msg.result).length" class="agent-mini-list">
                      <text class="mini-list-title">菜品食材</text>
                      <text v-for="item in agentAdoptedIngredients(msg.result)" :key="item.name">{{ item.name }}{{ item.amount ? ' ' + item.amount : '' }}</text>
                    </view>
                    <view v-if="agentShoppingItems(msg.result).length" class="agent-mini-list shopping" @tap.stop="openTodayShoppingList">
                      <text class="mini-list-title">补购清单</text>
                      <text v-for="item in agentShoppingItems(msg.result).slice(0, 4)" :key="item.name || item.ingredient_name || item.title">{{ item.name || item.ingredient_name || item.title }}{{ item.amount ? ' ' + item.amount : '' }}</text>
                      <text v-if="agentShoppingItems(msg.result).length > 4" class="mini-list-more">还有 {{ agentShoppingItems(msg.result).length - 4 }} 项，点此查看</text>
                    </view>
                  </view>
                  <view class="agent-meal-actions">
                    <button class="agent-flow-btn ghost" @tap.stop="openTodayShoppingList">查看清单</button>
                    <button v-if="msg.result.adopted_meal.status === 'planned'" class="agent-flow-btn complete" @tap.stop="completeAgentMeal(msg)">完成这一餐</button>
                    <button v-else class="agent-flow-btn complete done" @tap.stop="openFeedbackSheet(msg.result.adopted_meal.recipe || msg.result.adopted_recipe || {})">记录偏好</button>
                  </view>
                </view>
                <view v-if="msg.result.shopping_list && msg.result.shopping_list.length && !msg.result.adopted_meal" class="agent-shopping">
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

    <view v-if="feedbackSheet.visible" class="feedback-mask" @tap="closeFeedbackSheet">
      <view class="feedback-sheet" @tap.stop>
        <view class="feedback-handle"></view>
        <view class="feedback-head">
          <text>这餐记忆一下</text>
          <text>{{ feedbackSheet.recipe?.title || '今日用餐' }}</text>
        </view>
        <view class="feedback-ratings">
          <view v-for="item in feedbackRatings" :key="item.rating" class="feedback-rating" :class="{ active: feedbackSheet.rating === item.rating }" @tap="feedbackSheet.rating = item.rating">
            <text>{{ item.label }}</text>
          </view>
        </view>
        <view class="feedback-chips">
          <text v-for="chip in feedbackChips" :key="chip" :class="{ active: feedbackSheet.tags.includes(chip) }" @tap="toggleFeedbackChip(chip)">{{ chip }}</text>
        </view>
        <textarea class="feedback-input" v-model="feedbackSheet.comment" placeholder="比如：喜欢快炒少油、韭黄口感好；或者太油、分量偏大" maxlength="500" />
        <view class="feedback-actions">
          <button class="feedback-skip" @tap="closeFeedbackSheet">跳过</button>
          <button class="feedback-submit" @tap="submitMealFeedback">提交并学习</button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { ApiService } from '@/api/index'
import { useAuthStore } from '@/store/auth'
import { useHistoryStore } from '@/store/history'
import { t, currentLang } from '@/utils/i18n'
import { buildNutritionOverview, extractIngredientNames, missingIngredients, normalizeRecipe, recipeIngredientsForUse } from '@/utils/food-analysis'

const $t = key => t(key)
const authStore = useAuthStore()
const historyStore = useHistoryStore()

const nutritionScore = ref(65)
const ingredients = ref([])
const recipes = ref([])
const todayMeals = ref([])
const inventoryItems = ref([])
const nutritionSummary = ref(null)
const isLoading = ref(false)
const refreshing = ref(false)
const agentMessage = ref('')
const agentResult = ref(null)
const agentMessages = ref([])
const latestAgentAdoption = ref(null)
const explainRecipe = ref(null)
const feedbackSheet = ref({ visible: false, recipe: null, rating: 5, tags: [], comment: '' })
const agentLoading = ref(false)          // Agent 请求进行中
const agentProgress = ref(0)            // 假进度 0-85
const replayingEvents = ref(false)      // 正在逐条回放 events
const replayEvents = ref([])            // 回放中的 events 列表
const replayIndex = ref(0)              // 当前回放到第几条
const agentConversationId = ref(uni.getStorageSync('agent_conversation_id') || `conv_${Date.now()}_${Math.random().toString(16).slice(2)}`)
const apiNotice = ref('')
const nutritionOverview = computed(() => buildNutritionOverview(recipes.value))
const byteFlow = [
  { key: 'B', label: '食材感知' },
  { key: 'Y', label: '约束推理' },
  { key: 'T', label: '任务执行' },
  { key: 'E', label: '反馈优化' }
]
const feedbackRatings = [
  { rating: 5, label: '很喜欢' },
  { rating: 4, label: '还可以' },
  { rating: 3, label: '一般' },
  { rating: 2, label: '不喜欢' }
]
const feedbackChips = ['快炒', '少油', '清淡', '高蛋白', '分量刚好', '太油', '太咸', '下次还想吃']

const proteinPct = computed(() => nutritionOverview.value.proteinPct || Math.min(100, Math.round(nutritionScore.value * 1.15)))
const carbPct = computed(() => nutritionOverview.value.carbsPct || Math.min(100, Math.round(nutritionScore.value * 0.9)))
const fatPct = computed(() => nutritionOverview.value.fatPct || Math.min(100, Math.round(nutritionScore.value * 0.7)))
const topRecipe = computed(() => recipes.value[0] || null)
const mealSlots = [
  { key: 'breakfast', label: '早餐' },
  { key: 'lunch', label: '午餐' },
  { key: 'dinner', label: '晚餐' },
  { key: 'snack', label: '加餐' },
  { key: 'late_night', label: '宵夜' }
]
const activeMealTab = ref('lunch')
const planMealSlots = mealSlots
const mainMealSlots = planMealSlots
const activeMealSlots = computed(() => {
  return planMealSlots.filter(s => s.key === activeMealTab.value)
})
const selectedMealSlot = ref('lunch')
const visibleMealSlots = computed(() => {
  const known = new Set(mealSlots.map(item => item.key))
  const custom = todayMeals.value
    .filter(meal => meal.meal_slot && !known.has(meal.meal_slot) && meal.status !== 'cancelled')
    .map(meal => ({ key: meal.meal_slot, label: mealSlotLabel(meal.meal_slot) }))
  return [...mealSlots, ...custom]
})
const hubItems = computed(() => [
  { key: 'health', title: '状态看板', desc: '营养缺口与趋势', icon: '/static/icons/icon_chart.svg', tone: 'green' },
  { key: 'scan', title: '拍照识别', desc: '食材新鲜度和分量', icon: '/static/icons/icon_scan.svg', tone: 'teal' },
  { key: 'nutrition', title: '营养分析', desc: '一餐热量与宏量', icon: '/static/icons/icon_plate.svg', tone: 'blue' },
  { key: 'quality', title: '品质鉴定', desc: '水果食材优中差', icon: '/static/icons/icon_leaf.svg', tone: 'green' },
  { key: 'guide', title: '探店向导', desc: '菜品故事与吃法', icon: '/static/icons/icon_fish.svg', tone: 'purple' },
  { key: 'text', title: '文本导入', desc: '手输食材和数量', icon: '/static/icons/icon_edit.svg', tone: 'amber' },
  { key: 'explore', title: '探索菜谱', desc: '按目标找下一餐', icon: '/static/icons/icon_search.svg', tone: 'blue' },
  { key: 'list', title: '购物清单', desc: `${recipes.value.length || 0} 道菜可合并`, icon: '/static/icons/icon_cart.svg', tone: 'amber' },
  { key: 'history', title: '历史记录', desc: '识别、推荐与导出', icon: '/static/icons/icon_clock.svg', tone: 'purple' },
  { key: 'knowledge', title: '美食知识', desc: '营养与烹饪指南', icon: '/static/icons/icon_leaf.svg', tone: 'green' },
  { key: 'settings', title: '系统设置', desc: '语言、通知和偏好', icon: '/static/icons/icon_edit.svg', tone: 'amber' },
  { key: 'profile', title: '我的档案', desc: '目标和个人画像', icon: '/static/icons/icon_avatar.svg', tone: 'blue' }
])
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
  const cookTime = r.cookTime || r.cook_time
  if (cookTime) out.push(`${cookTime}分钟`)
  if (r.calories) out.push(`${r.calories}kcal`)
  const missing = missingIngredients(r, ingredients.value).slice(0, 2)
  if (missing.length) out.push(`需补 ${missing.join('、')}`)
  else out.push('现有食材可做')
  return out.slice(0, 3)
})
function recipeReasonsFor(r) {
  if (!r) return []
  const out = []
  const cookTime = r.cookTime || r.cook_time
  if (cookTime) out.push(`${cookTime}分钟`)
  if (r.calories) out.push(`${r.calories}kcal`)
  const missing = recipeMissingIngredients(r).slice(0, 2)
  out.push(missing.length ? `需补 ${missing.join('、')}` : '现有食材可做')
  return out.slice(0, 3)
}
function listFromMeta(value) {
  if (!value) return []
  if (Array.isArray(value)) {
    return value.map(item => {
      if (typeof item === 'string') return item
      return item?.name || item?.label || item?.display || ''
    }).filter(Boolean)
  }
  if (typeof value === 'string') return value ? [value] : []
  if (typeof value === 'object') return [value.name || value.label || value.display || ''].filter(Boolean)
  return []
}
function recipeMatchedIngredients(r) {
  const meta = r?._meta || {}
  const direct = listFromMeta(meta.matched_user_ingredients || meta.matched_ingredients || r?.matched_ingredients)
  if (direct.length) return direct
  const owned = new Set(ingredients.value.map(item => String(item?.name || item || '').trim()).filter(Boolean))
  return recipeIngredientNamesForExplain(r).filter(name => owned.has(name))
}
function recipeMissingIngredients(r) {
  const meta = r?._meta || {}
  const direct = listFromMeta(meta.missing_user_ingredients || meta.missing_ingredients || r?.missing_ingredients)
  if (direct.length) return direct
  return missingIngredients(r, ingredients.value)
}
function recipeIngredientNamesForExplain(r = {}) {
  return (r.ingredients || []).map(item => typeof item === 'string' ? item : item?.name).filter(Boolean)
}
function purchaseSuggestionLabels(r) {
  const meta = r?._meta || {}
  return listFromMeta(meta.purchase_suggestions || r?.purchase_suggestions).slice(0, 2)
}
function preferenceMatchLabels(r) {
  const meta = r?._meta || {}
  return listFromMeta(meta.preference_matches || r?.preference_matches || r?.matched_preferences).slice(0, 2)
}
function preferenceEvidenceLabels(r) {
  const meta = r?._meta || {}
  return listFromMeta(meta.preference_evidence || r?.preference_evidence).slice(0, 1)
}
function recipeExplainChips(r) {
  const chips = []
  const matched = recipeMatchedIngredients(r).slice(0, 2)
  const missing = recipeMissingIngredients(r).slice(0, 2)
  const purchase = purchaseSuggestionLabels(r)
  const prefs = preferenceMatchLabels(r)
  const evidence = preferenceEvidenceLabels(r)
  if (matched.length) chips.push(`已用 ${matched.join('、')}`)
  if (missing.length) chips.push(`缺 ${missing.join('、')}`)
  if (purchase.length) chips.push(`补买 ${purchase.join('、')}`)
  if (prefs.length) chips.push(`偏好 ${prefs.join('、')}`)
  if (evidence.length) chips.push(`记忆 ${evidence[0]}`)
  if (r?.llm_reranked) chips.push('AI重排')
  return chips.slice(0, 5)
}
function showRecipeExplain(recipe) {
  explainRecipe.value = recipe
}
function explainText(list, fallback) {
  const values = listFromMeta(list)
  return values.length ? values.join('、') : fallback
}
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
    const inv = await ApiService.getInventory()
    if (inv.length) {
      inventoryItems.value = inv
      ingredients.value = inv.map(item => ({ ...item, name: item.name, freshness: item.freshness || 'normal' }))
      uni.setStorageSync('last_ingredients', JSON.stringify(ingredients.value))
      return
    }
    inventoryItems.value = []
    ingredients.value = []
    uni.removeStorageSync('last_ingredients')
  } catch (e) {
    const cached = uni.getStorageSync('last_ingredients')
    if (cached) ingredients.value = JSON.parse(cached)
  }
}
async function loadNutrition() {
  try {
    const summary = await ApiService.getNutritionSummary('day')
    nutritionSummary.value = summary
    nutritionScore.value = summary.score || 0
  } catch (e) {
    try {
      const d = await ApiService.getNutritionStatus()
      if (!recipes.value.length) nutritionScore.value = d.score || 0
    } catch (_) {
      apiNotice.value = '后端营养服务暂不可用，未使用本地 mock 数据。'
      if (!recipes.value.length) nutritionScore.value = 0
    }
  }
}
async function loadTodayMeals() {
  try {
    todayMeals.value = await ApiService.getTodayMeals()
  } catch (e) {
    todayMeals.value = []
  }
}
async function generateRecommendations(options = {}) {
  isLoading.value = true
  try {
    const n = ingredients.value.map(i => i.name)
    const excludeRecipeIds = options.refresh
      ? recipes.value.map(r => r.recipe_id || r.recipeId).filter(Boolean)
      : []
    recipes.value = (await ApiService.generateMealPlan(n, {
      refresh: !!options.refresh,
      excludeRecipeIds
    })).map(normalizeRecipe)
  } catch (e) {
    apiNotice.value = '推荐服务暂不可用，未使用本地 mock 菜谱。'
    recipes.value = []
  } finally {
    isLoading.value = false
  }
}
async function onRefresh() { refreshing.value = true; await loadNutrition(); await generateRecommendations(); refreshing.value = false }
async function refreshRecommendations() {
  if (isLoading.value) return
  await generateRecommendations({ refresh: true })
  if (recipes.value.length) {
    historyStore.addEntry({
      type: 'recommendation',
      title: $t('refreshTitle'),
      detail: t('refreshDetail', { n: ingredients.value.length }),
      recipeId: recipes.value[0].recipe_id || recipes.value[0].recipeId || '',
      recipes: recipes.value
    })
    uni.showToast({ title: `已生成 ${recipes.value.length} 个推荐`, icon: 'success' })
  } else {
    uni.showToast({ title: '暂无可推荐菜谱', icon: 'none' })
  }
}
function slotMeal(slot) {
  return todayMeals.value.find(m => m.meal_slot === slot && m.status !== 'cancelled')
}
function mealSlotLabel(slot) {
  return mealSlots.find(item => item.key === slot)?.label || slot || '本餐'
}
function mealStatusText(meal) {
  if (!meal) return '未计划'
  if (meal.status === 'completed') return '已完成'
  if (meal.status === 'planned') return '待完成'
  return meal.status
}
function nextEmptyMealSlot() {
  return mealSlots.find(slot => !slotMeal(slot.key))?.key || selectedMealSlot.value || 'lunch'
}
function setMealTabForSlot(slot) {
  if (planMealSlots.some(item => item.key === slot)) activeMealTab.value = slot
}
function setActiveMealSlot(slot) {
  selectedMealSlot.value = slot
}
async function switchMealSlot(meal) {
  const slots = mainMealSlots.filter(s => s.key !== (meal.meal_slot || 'lunch'))
  uni.showActionSheet({
    itemList: slots.map(s => s.label),
    success: async (res) => {
      const target = slots[res.tapIndex]
      if (!target) return
      try {
        await ApiService.changeMealSlot(meal.id, target.key)
        await loadTodayMeals()
        uni.showToast({ title: `已切换到${target.label}`, icon: 'success' })
      } catch (e) {
        uni.showToast({ title: '切换失败', icon: 'none' })
      }
    }
  })
}
function goExploreAddMeal(slot) {
  uni.setStorageSync('plan_meal_slot', slot)
  uni.switchTab({ url: '/pages/explore/explore' })
}
function askPlanMeal(recipe) {
  const options = [...mealSlots, { key: 'custom', label: '自定义餐时' }]
  uni.showActionSheet({
    itemList: options.map(item => item.label),
    success: (res) => {
      const option = options[res.tapIndex]
      if (!option) return
      if (option.key === 'custom') {
        uni.showModal({
          title: '自定义餐时',
          editable: true,
          placeholderText: '比如：训练后加餐、下午茶',
          cancelText: '取消',
          confirmText: '加入',
          success: async (modal) => {
            const slot = modal.content?.trim()
            if (modal.confirm && slot) await confirmPlanRecipe(recipe, slot)
          }
        })
        return
      }
      confirmPlanRecipe(recipe, option.key)
    }
  })
}
function confirmPlanRecipe(recipe, slot) {
  uni.showModal({
    title: `采纳到${mealSlotLabel(slot)}`,
    content: `Agent 会把「${recipe.title}」加入今日计划，同步扣减现有库存，并为缺少的食材生成补购清单。完成用餐后再写入营养和偏好记忆。`,
    cancelText: '取消',
    confirmText: '采纳',
    success: async (res) => {
      if (res.confirm) await planRecipe(recipe, slot)
    }
  })
}
async function planRecipe(recipe, slot = nextEmptyMealSlot()) {
  try {
    const result = await ApiService.adoptMeal(slot, recipe)
    const meal = result.meal
    selectedMealSlot.value = meal.meal_slot || slot
    setMealTabForSlot(meal.meal_slot || slot)
    const shoppingList = result.shopping_list || []
    await loadTodayMeals()
    await loadIngredients()
    latestAgentAdoption.value = {
      title: meal.recipe?.title || recipe.title,
      events: result.agent_events || [],
      shoppingList
    }
    historyStore.addEntry({
      type: 'meal_plan',
      title: meal.recipe?.title || recipe.title,
      detail: shoppingList.length ? `已采纳，需补 ${shoppingList.length} 项食材` : '已采纳，库存已同步',
      recipeId: recipe.recipe_id || recipe.recipeId || '',
      recipes: [recipe],
      shoppingList
    })
    uni.showToast({ title: shoppingList.length ? `已采纳，需补${shoppingList.length}项` : `已采纳到${mealSlotLabel(slot)}`, icon: 'success' })
    return result
  } catch (e) {
    uni.showToast({ title: e.message || '采纳失败', icon: 'none' })
    return null
  }
}
async function completePlannedMeal(meal) {
  uni.showModal({
    title: '完成这一餐',
    content: `确认已经吃完「${meal.recipe?.title || '这一餐'}」？确认后会写入今日营养，并从库存扣减食材。`,
    cancelText: '还没吃',
    confirmText: '已完成',
    success: async (res) => {
      if (!res.confirm) return
      try {
        await ApiService.completeMeal(meal.id)
        uni.removeStorageSync('last_ingredients')
        ingredients.value = []
        recipes.value = []
        await loadIngredients()
        await loadTodayMeals()
        await loadNutrition()
        await generateRecommendations()
        uni.showToast({ title: '已写入今日营养', icon: 'success' })
        setTimeout(() => openFeedbackSheet(meal.recipe || meal.recipe_snapshot || {}), 450)
      } catch (e) {
        uni.showToast({ title: e.message || '完成失败', icon: 'none' })
      }
    }
  })
}
function openFeedbackSheet(recipe) {
  feedbackSheet.value = { visible: true, recipe, rating: 5, tags: [], comment: '' }
}
function closeFeedbackSheet() {
  feedbackSheet.value.visible = false
}
function toggleFeedbackChip(chip) {
  const tags = feedbackSheet.value.tags
  const idx = tags.indexOf(chip)
  if (idx >= 0) tags.splice(idx, 1)
  else tags.push(chip)
}
async function submitMealFeedback() {
  const recipe = feedbackSheet.value.recipe || {}
  const tags = feedbackSheet.value.tags.join('，')
  const free = (feedbackSheet.value.comment || '').trim()
  const comment = [tags, free].filter(Boolean).join('；') || `本次用餐评分 ${feedbackSheet.value.rating} 分`
  try {
    await ApiService.submitFeedback(recipe.recipe_id || recipe.recipeId || '', feedbackSheet.value.rating, comment, recipe)
    closeFeedbackSheet()
    uni.showToast({ title: '偏好已学习', icon: 'success' })
  } catch (e) {
    uni.showToast({ title: '用餐已记录，偏好学习失败', icon: 'none' })
  }
}
function agentAdoptionEventTitle(event) {
  return event.stage === 'inventory' ? '已同步库存' : event.stage === 'shopping_list' ? '已生成补购清单' : '已采纳菜谱'
}
function agentAdoptionEventDetail(event) {
  if (event.summary?.deducted_count !== undefined) return `扣减 ${event.summary.deducted_count} 项库存`
  if (event.summary?.shopping_item_count !== undefined) return `缺少 ${event.summary.shopping_item_count} 项食材`
  return event.detail || ''
}
function recipeStableId(recipe = {}) {
  return recipe.recipe_id || recipe.recipeId || recipe.id || recipe.title || ''
}
function recipeIngredientsPreview(recipe = {}) {
  return recipeIngredientsForUse(recipe).slice(0, 4)
}
function isAgentRecipeAdopted(result = {}, recipe = {}) {
  const adoptedId = result._adopted_recipe_id || recipeStableId(result.adopted_recipe || {})
  return !!adoptedId && adoptedId === recipeStableId(recipe)
}
function refreshAgentMessages() {
  agentMessages.value = [...agentMessages.value]
}
async function adoptAgentRecipe(recipe, msg) {
  if (!msg?.result) return
  const options = planMealSlots
  uni.showActionSheet({
    itemList: options.map(item => item.label),
    success: async (res) => {
      const option = options[res.tapIndex]
      if (!option) return
      try {
        const result = await planRecipe(recipe, option.key)
        if (!result) return
        const meal = result.meal || {}
        msg.result.adopted_meal = meal
        msg.result.adopted_recipe = meal.recipe || recipe
        msg.result._adopted_recipe_id = recipeStableId(recipe)
        msg.result.adoption_events = result.agent_events || []
        msg.result.shopping_list = result.shopping_list || msg.result.shopping_list || []
        msg.result.events = [
          ...(msg.result.events || []),
          { type: 'tool_result', tool: 'task', status: 'success', message: `已加入${mealSlotLabel(meal.meal_slot || option.key)}` }
        ]
        refreshAgentMessages()
      } catch (_) {
        // planRecipe already shows the failure toast.
      }
    }
  })
}
function showAgentAdoptedMeal(result = {}) {
  const meal = result.adopted_meal || {}
  if (meal.meal_slot) {
    selectedMealSlot.value = meal.meal_slot
    setMealTabForSlot(meal.meal_slot)
  }
  uni.showToast({ title: `${mealSlotLabel(meal.meal_slot)}已加入`, icon: 'success' })
}
function agentAdoptionEvents(result = {}) {
  return result.adoption_events || []
}
function agentAdoptedMealTitle(result = {}) {
  const meal = result.adopted_meal || {}
  const recipe = meal.recipe || result.adopted_recipe || {}
  return recipe.title || meal.recipe_snapshot?.title || '这一餐'
}
function agentAdoptedIngredients(result = {}) {
  const meal = result.adopted_meal || {}
  const recipe = meal.recipe || result.adopted_recipe || {}
  return recipeIngredientsForUse(recipe).slice(0, 6)
}
function agentShoppingItems(result = {}) {
  return result.shopping_list || result.adopted_meal?.shopping_list || []
}
async function completeAgentMeal(msg) {
  const meal = msg?.result?.adopted_meal
  if (!meal?.id) {
    uni.showToast({ title: '请先加入这一餐', icon: 'none' })
    return
  }
  uni.showModal({
    title: '完成这一餐',
    content: `确认已经吃完「${agentAdoptedMealTitle(msg.result)}」？完成后会写入营养，并进入偏好反馈。`,
    cancelText: '还没吃',
    confirmText: '已完成',
    success: async (res) => {
      if (!res.confirm) return
      try {
        const completed = await ApiService.completeMeal(meal.id)
        msg.result.adopted_meal = completed || { ...meal, status: 'completed' }
        await loadIngredients()
        await loadTodayMeals()
        await loadNutrition()
        refreshAgentMessages()
        uni.showToast({ title: '已写入今日营养', icon: 'success' })
        setTimeout(() => openFeedbackSheet(completed?.recipe || msg.result.adopted_recipe || {}), 450)
      } catch (e) {
        uni.showToast({ title: e.message || '完成失败', icon: 'none' })
      }
    }
  })
}
async function openTodayShoppingList() {
  try {
    const data = await ApiService.getTodayShoppingList()
    uni.navigateTo({ url: `/pages/list-export/list-export?items=${encodeURIComponent(JSON.stringify(data.items || []))}&title=${encodeURIComponent('今日补购清单')}` })
  } catch (e) {
    uni.showToast({ title: e.message || '清单打开失败', icon: 'none' })
  }
}
async function sendAgentMessage() {
  const m = agentMessage.value.trim(); if (!m) return
  const typedIngredients = extractIngredientNames(m)
  if (typedIngredients.length) {
    agentConversationId.value = `conv_${Date.now()}_${Math.random().toString(16).slice(2)}`
    uni.setStorageSync('agent_conversation_id', agentConversationId.value)
    agentMessages.value = []
  }
  const userMsg = { id: 'u_' + Date.now(), role: 'user', text: m }
  agentMessages.value.push(userMsg)
  agentLoading.value = true
  agentProgress.value = 0

  // 假进度条：0 → 85%，模拟 Agent 工作过程
  const progressTimer = setInterval(() => {
    if (agentProgress.value < 30) agentProgress.value += 3
    else if (agentProgress.value < 60) agentProgress.value += 1.5
    else if (agentProgress.value < 85) agentProgress.value += 0.8
  }, 200)

  try {
    const r = await ApiService.agentExecute(m, null, agentConversationId.value)
    clearInterval(progressTimer)
    agentProgress.value = 100

    if (r.conversation_id) {
      agentConversationId.value = r.conversation_id
      uni.setStorageSync('agent_conversation_id', r.conversation_id)
    }
    agentResult.value = r
    if (r.recipes && r.recipes.length) {
      recipes.value = r.recipes.map(normalizeRecipe)
    }
    if (typedIngredients.length) {
      ingredients.value = typedIngredients.map(name => ({ name }))
      uni.setStorageSync('last_ingredients', JSON.stringify(ingredients.value))
    }

    // 先发布初始回复，events 设为空，后续逐条回放
    const msgId = 'a_' + Date.now()
    agentMessages.value.push({
      id: msgId,
      role: 'assistant',
      text: r.reply || '我已完成分析，并整理了推荐食谱。',
      sourceText: m,
      result: { ...r, events: [], _fullEvents: r.events }
    })
    saveAgentSession(r)
    agentMessage.value = ''
    agentLoading.value = false

    // 逐条回放 events，每条 500ms
    if (r.events && r.events.length) {
      replayEvents.value = r.events
      replayIndex.value = 0
      replayingEvents.value = true
      const msg = agentMessages.value.find(x => x.id === msgId)
      const replayInterval = setInterval(() => {
        if (replayIndex.value >= replayEvents.value.length) {
          clearInterval(replayInterval)
          replayingEvents.value = false
          if (msg && msg.result) {
            msg.result.events = replayEvents.value
            msg.result._fullEvents = undefined
          }
          return
        }
        if (msg && msg.result) {
          msg.result.events = replayEvents.value.slice(0, replayIndex.value + 1)
        }
        replayIndex.value++
      }, 500)
    }
  } catch (e) {
    clearInterval(progressTimer)
    agentLoading.value = false
    agentProgress.value = 0
    apiNotice.value = 'AI Agent 暂未连通，请稍后重试或检查后端服务。'
    agentMessages.value.push({ id: 'e_' + Date.now(), role: 'assistant', text: e.message || apiNotice.value })
  }
}
function intentIngredients(result) {
  const intent = result?.parsed_intent || {}
  return (intent.ingredients || intent.core_items || []).map(i => typeof i === 'string' ? i : i.name).filter(Boolean)
}
function stageLabel(stage) { return ({ sense: '感知', decision: '推荐', task: '清单' })[stage] || stage }
function stageStatusLabel(status) { return ({ success: '完成', skipped: '跳过', empty: '空', error: '异常', failed: '失败' })[status] || status }
function agentEventTitle(event) {
  const phaseLabel = event.phase ? ` [${event.phase}]` : ''
  if (event.type === 'plan') {
    const source = event.planner_source ? ` · ${plannerSourceLabel(event.planner_source)}` : ''
    return `规划${phaseLabel}：${stageLabel(event.tool)}${source}`
  }
  if (event.type === 'tool_start') return `执行${phaseLabel}：${stageLabel(event.tool)}`
  if (event.type === 'tool_result') {
    const cat = event.skill?.category ? ` · ${skillCategoryLabel(event.skill.category)}` : ''
    return `${stageLabel(event.tool)}${event.status === 'success' ? '完成' : '失败'}${cat}`
  }
  if (event.type === 'evaluation') {
    const v = event.verdict || ''
    const vl = { PASS: '通过', PARTIAL: '部分通过', CONFLICT: '存在冲突', FAIL: '未通过' }[v] || v
    return `评估${phaseLabel}：${vl}`
  }
  if (event.type === 'soft_judge') {
    const v = event.verdict || ''
    const vl = { PASS: '通过', WARN: '提醒', SKIPPED: '跳过' }[v] || v
    return `软评审${phaseLabel}：${vl}`
  }
  if (event.type === 'ask_user') return '需要补充信息'
  if (event.type === 'final') return `完成${phaseLabel}`
  return event.type
}
function agentEventDetail(event) {
  if (event.type === 'plan') {
    const parts = []
    if (event.reason) parts.push(event.reason)
    if (event.candidate_tools?.length) parts.push(`候选 ${event.candidate_tools.map(stageLabel).join('、')}`)
    if (event.llm_reason) parts.push(`LLM ${event.llm_reason}`)
    return parts.join('；')
  }
  if (event.type === 'tool_result') {
    const parts = []
    if (event.summary?.ingredient_count !== undefined) parts.push(`识别 ${event.summary.ingredient_count} 种`)
    if (event.summary?.recipe_count !== undefined) parts.push(`推荐 ${event.summary.recipe_count} 个`)
    if (event.summary?.shopping_item_count !== undefined) parts.push(`清单 ${event.summary.shopping_item_count} 项`)
    if (event.summary?.cache_hit !== undefined || event.cache_hit !== undefined) parts.push((event.summary?.cache_hit || event.cache_hit) ? '缓存命中' : '实时推理')
    if (event.retry_count) parts.push(`重试 ${event.retry_count} 次`)
    if (event.error_code) parts.push(`${event.error_code}: ${event.message || '工具调用失败'}`)
    return parts.join('；')
  }
  if (event.type === 'evaluation') {
    const issues = event.issues || []
    return issues.map(i => `${i.code}: ${i.message}`).join('；') || ''
  }
  if (event.type === 'soft_judge') {
    const scoreText = event.scores
      ? Object.entries(event.scores).slice(0, 3).map(([k, v]) => `${judgeScoreLabel(k)} ${v}`).join('；')
      : ''
    const issues = (event.issues || []).map(i => typeof i === 'string' ? i : i.message || i.code).filter(Boolean).join('；')
    return [scoreText, issues].filter(Boolean).join('；')
  }
  if (event.reason) return event.reason
  if (event.message) return event.message
  if (event.summary?.ingredient_count !== undefined) return `识别到 ${event.summary.ingredient_count} 种食材`
  if (event.summary?.recipe_count !== undefined) return `生成 ${event.summary.recipe_count} 个推荐`
  if (event.summary?.shopping_item_count !== undefined) return `合并 ${event.summary.shopping_item_count} 项清单`
  if (event.error_code) return `${event.error_code}：${event.message || '工具调用失败'}`
  return ''
}
function plannerSourceLabel(source) { return ({ rule: '规则', llm: 'LLM', rule_fallback: '规则回退' })[source] || source }
function skillCategoryLabel(category) { return ({ perception: '感知', decision: '决策', task: '任务', memory: '记忆', evaluation: '评估', domain: '领域' })[category] || category }
function judgeScoreLabel(key) { return ({ instruction_following: '指令', ingredient_relevance: '食材', preference_alignment: '偏好', actionability: '可做' })[key] || key }
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
function handleConfirmation(promptIndex, option, msg) {
  const text = option.label || option.action
  if (option.action === 'retry') {
    // 使用原始用户输入，不是助手回复
    const lastUser = [...agentMessages.value].reverse().find(x => x.role === 'user')
    agentMessage.value = msg.sourceText || (lastUser ? lastUser.text : '')
    if (agentMessage.value.trim()) sendAgentMessage()
  } else if (option.action === 'confirm' || option.action === 'accept') {
    uni.showToast({ title: `已确认：${text}`, icon: 'success' })
  } else {
    uni.showToast({ title: `已跳过`, icon: 'none' })
  }
}

function exportAgentList(result) {
  if (result.shopping_list?.length) {
    uni.navigateTo({ url: `/pages/list-export/list-export?items=${encodeURIComponent(JSON.stringify(result.shopping_list))}&title=${encodeURIComponent('AI助手清单')}` })
    return
  }
  const payload = result.recipes?.length ? result.recipes.map(normalizeRecipe) : recipes.value
  uni.navigateTo({ url: `/pages/list-export/list-export?recipes=${encodeURIComponent(JSON.stringify(payload))}` })
}
function goalLabel(g) { const m = { fat_loss:'减脂', muscle_gain:'增肌', maintain:'保持', balanced:'均衡', healthy:'健康' }; return m[g]||g }
function matchPercent(r) { return ((r?.matchScore || r?.match_score || 0) * 100).toFixed(0) }
function freshnessLabel(f) { return ({ high: '新鲜', normal: '冷藏', medium: '普通', low: '待确认' })[f] || f || '待确认' }
function freshnessClass(f) { return f === 'high' ? 'fresh-high' : f === 'low' ? 'fresh-low' : 'fresh-normal' }
function goRecipeDetail(r) { uni.navigateTo({ url: `/pages/recipe-detail/recipe-detail?recipeId=${r.recipe_id || r.recipeId}&title=${encodeURIComponent(r.title)}` }) }
async function favoriteRecipe(recipe) {
  try {
    await ApiService.addFavorite('system_recipe', recipe.recipe_id || recipe.recipeId, recipe)
    uni.showToast({ title: '已收藏', icon: 'success' })
  } catch (e) {
    uni.showToast({ title: e.message || '收藏失败', icon: 'none' })
  }
}
function checkRecipe(recipe) {
  uni.navigateTo({ url: `/pages/recipe-checker/recipe-checker?targetType=system_recipe&targetId=${recipe.recipe_id || recipe.recipeId}` })
}
function goIngredientRecognition() { uni.switchTab({ url: '/pages/ingredient-recognition/ingredient-recognition' }) }
function goHealthDashboard() { uni.navigateTo({ url: `/pages/health-dashboard/health-dashboard?ingredients=${encodeURIComponent(JSON.stringify(ingredients.value))}` }) }
function goListExport() {
  if (!recipes.value.length) {
    uni.showToast({ title: '请先生成推荐菜谱', icon: 'none' })
    return
  }
  uni.navigateTo({ url: `/pages/list-export/list-export?recipes=${encodeURIComponent(JSON.stringify(recipes.value))}` })
}
function goHistory() { uni.navigateTo({ url: '/pages/history/history' }) }
function goHub(key) {
  const routes = {
    health: () => goHealthDashboard(),
    scan: () => goIngredientRecognition(),
    nutrition: () => uni.navigateTo({ url: '/pages/meal-nutrition/meal-nutrition' }),
    quality: () => uni.navigateTo({ url: '/pages/quality-assessment/quality-assessment' }),
    guide: () => uni.navigateTo({ url: '/pages/food-guide/food-guide' }),
    text: () => uni.navigateTo({ url: '/pages/text-import/text-import' }),
    explore: () => uni.switchTab({ url: '/pages/explore/explore' }),
    list: () => goListExport(),
    history: () => goHistory(),
    knowledge: () => uni.navigateTo({ url: '/pages/food-knowledge/food-knowledge' }),
    settings: () => uni.navigateTo({ url: '/pages/settings/settings' }),
    profile: () => uni.switchTab({ url: '/pages/profile/profile' })
  }
  routes[key]?.()
}

onShow(() => {
  if (!authStore.isLoggedIn) { uni.redirectTo({ url: '/pages/login/login' }); return }
  loadIngredients(); loadNutrition(); loadTodayMeals(); generateRecommendations()
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
.home-top { padding: calc(22rpx + var(--status-bar-height, 0px)) 30rpx 16rpx; position: relative; }
.user-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20rpx; }
.user-left { display: flex; align-items: center; gap: 16rpx; min-width: 0; flex: 1; }
.user-left > view { min-width: 0; }
.avatar { width: 64rpx; height: 64rpx; border-radius: 50%; background: #fff; box-shadow: var(--shadow-sm), var(--hairline); }
.greeting { display: block; max-width: 430rpx; font-size: 29rpx; font-weight: 850; color: var(--text); letter-spacing: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.date-text { display: block; font-size: 21rpx; color: var(--text-muted); margin-top: 0; }
.streak-pill { height: 52rpx; padding: 0 17rpx; border-radius: var(--radius-full); background: rgba(255,255,255,.88); display: flex; align-items: center; gap: 6rpx; color: var(--teal); font-size: 23rpx; font-weight: 850; box-shadow: var(--shadow-sm), var(--hairline); backdrop-filter: blur(12rpx); }
.streak-icon { width: 26rpx; height: 26rpx; }

.hero-panel {
  min-height: 274rpx;
  background:
    radial-gradient(circle at 86% 18%, rgba(88,207,160,.34), transparent 29%),
    radial-gradient(circle at 12% 88%, rgba(242,183,91,.16), transparent 26%),
    linear-gradient(145deg, #173B2E 0%, #1F5744 100%);
  border-radius: 40rpx;
  padding: 30rpx 30rpx 28rpx;
  box-shadow: 0 28rpx 70rpx rgba(23,59,46,.22);
  position: relative;
  overflow: hidden;
  color: #fff;
  display: flex;
  justify-content: space-between;
  gap: 20rpx;
  animation: soft-pop .36s var(--ease) both;
}
.hero-panel::after {
  content: "";
  position: absolute;
  top: -72rpx;
  right: -64rpx;
  width: 240rpx;
  height: 240rpx;
  border-radius: 50%;
  background: rgba(255,255,255,.08);
  pointer-events: none;
}
.hero-copy { flex: 1; min-width: 0; position: relative; z-index: 1; }
.hero-label { display: block; font-size: 21rpx; color: rgba(255,255,255,.72); font-weight: 850; }
.hero-title { display: block; margin-top: 14rpx; max-width: 400rpx; font-size: 33rpx; line-height: 1.28; font-weight: 950; color: #fff; }
.hero-actions { display: flex; gap: 12rpx; margin-top: 24rpx; }
.hero-actions button { height: 62rpx; margin: 0; padding: 0 20rpx; border: none; border-radius: var(--radius-full); font-size: 23rpx; font-weight: 900; line-height: 1; display: flex; align-items: center; justify-content: center; }
.hero-primary { background: var(--accent); color: #fff; font-weight: 700; box-shadow: 0 12rpx 24rpx rgba(0,0,0,.10); }
.hero-secondary { background: rgba(255,255,255,.9); color: var(--accent); font-weight: 600; box-shadow: 0 0 0 1rpx var(--accent); }
.hero-orb { width: 160rpx; display: flex; flex-direction: column; align-items: center; justify-content: center; flex-shrink: 0; position: relative; z-index: 1; gap: 10rpx; }
.orb-label { font-size: 18rpx; color: rgba(255,255,255,.72); font-weight: 850; letter-spacing: 0; }
.status-strip {
  margin-top: 16rpx;
  background: rgba(255,255,255,.94);
  border-radius: var(--radius-lg);
  padding: 18rpx;
  box-shadow: var(--shadow-sm), var(--hairline);
  display: grid;
  grid-template-columns: .78fr 1.22fr;
  gap: 16rpx;
}
.score-mini { display: flex; align-items: center; min-width: 0; }
.status-main { display: flex; justify-content: space-between; align-items: center; gap: 20rpx; }
.eyebrow { display: block; font-size: 23rpx; color: var(--text-secondary); margin-bottom: 8rpx; font-weight: 800; }
.score-line { display: flex; align-items: flex-end; }
.score { font-size: 50rpx; line-height: .96; font-weight: 950; color: var(--text); }
.score-unit { font-size: 28rpx; color: var(--text-muted); margin-left: 4rpx; margin-bottom: 6rpx; }
.status-copy { display: block; margin-top: 10rpx; font-size: 24rpx; color: var(--text-secondary); line-height: 1.45; max-width: 390rpx; }
.score-ring { width: 150rpx; height: 150rpx; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0; box-shadow: 0 16rpx 34rpx rgba(0,0,0,.16); animation: float-breathe 3.8s ease-in-out infinite; position: relative; z-index: 1; }
.score-ring-inner { width: 98rpx; height: 98rpx; border-radius: 50%; background: rgba(255,255,255,.96); display: flex; flex-direction: column; align-items: center; justify-content: center; color: var(--teal); box-shadow: inset 0 0 0 1px var(--border-light), var(--shadow-xs); }
.score-ring-inner text:first-child { font-size: 32rpx; line-height: 1; font-weight: 950; }
.score-ring-inner text:last-child { margin-top: 4rpx; font-size: 17rpx; color: var(--text-muted); font-weight: 800; }
.macro-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10rpx; margin-top: 0; }
.macro-card { border-radius: 20rpx; padding: 15rpx 13rpx; box-shadow: inset 0 0 0 1rpx rgba(255,255,255,.52); transition: transform var(--normal) var(--ease); }
.macro-card.protein { background: var(--green-bg); }
.macro-card.carbs { background: var(--amber-bg); }
.macro-card.fat { background: var(--purple-bg); }
.macro-value { display: block; font-size: 30rpx; font-weight: 900; color: var(--text); }
.macro-label { display: block; margin-top: 4rpx; font-size: 22rpx; color: var(--text-muted); }

.home-body { padding: 0 30rpx; height: calc(100vh - 492rpx - var(--status-bar-height, 0px)); }
.quick-actions { display: grid; grid-template-columns: 1fr 1fr; gap: 14rpx; margin-bottom: 20rpx; }
.scan-card, .byte-card, .ingredient-card, .meal-card, .mini-card, .ai-card, .empty-card { background: rgba(255,255,255,.94); border-radius: var(--radius-md); box-shadow: var(--shadow-sm), var(--hairline); }
.quick-action { min-height: 146rpx; padding: 20rpx; display: flex; align-items: center; gap: 14rpx; position: relative; overflow: hidden; background: #fff; border-radius: var(--radius-md); box-shadow: var(--shadow-sm), var(--hairline); }
.scan-card::after, .ai-card::after, .ask-card::after {
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
.ask-card { background: linear-gradient(145deg, #FFFFFF, #F8F6FF); }
.ask-icon { width: 70rpx; height: 70rpx; border-radius: 22rpx; background: var(--purple-bg); color: var(--berry); display: flex; align-items: center; justify-content: center; font-size: 24rpx; font-weight: 950; flex-shrink: 0; box-shadow: inset 0 0 0 1rpx rgba(141,122,230,.10); }
.ask-title { display: block; font-size: 28rpx; font-weight: 900; color: var(--text); }
.ask-desc { display: block; margin-top: 6rpx; font-size: 21rpx; line-height: 1.35; color: var(--text-muted); }
.byte-card { grid-column: 1 / -1; padding: 20rpx 22rpx; background: linear-gradient(160deg, #FFFFFF 0%, #F4FBF7 100%); position: relative; overflow: hidden; }
.byte-card::after { content: ""; position: absolute; right: -44rpx; top: -52rpx; width: 150rpx; height: 150rpx; border-radius: 50%; background: rgba(35,169,120,.08); pointer-events: none; }
.byte-card-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 16rpx; position: relative; z-index: 1; }
.byte-title { display: block; font-size: 30rpx; font-weight: 900; color: var(--text); }
.byte-desc { display: block; margin-top: 8rpx; color: var(--text-secondary); font-size: 22rpx; min-height: auto; }
.byte-percent { color: var(--teal); font-size: 25rpx; font-weight: 950; }
.byte-track { height: 10rpx; border-radius: 10rpx; background: var(--border-light); overflow: hidden; margin-top: 14rpx; position: relative; z-index: 1; }
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
.hub-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12rpx;
  background: rgba(255,255,255,.92);
  border-radius: var(--radius-lg);
  padding: 14rpx;
  box-shadow: var(--shadow-sm), var(--hairline);
}
.hub-card {
  min-height: 132rpx;
  border-radius: 22rpx;
  padding: 13rpx 8rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  background: var(--bg-elevated);
  box-shadow: inset 0 0 0 1rpx rgba(255,255,255,.5);
}
.hub-card.green, .hub-card.teal { background: linear-gradient(180deg, var(--teal-bg), #F8FCFA); }
.hub-card.blue { background: linear-gradient(180deg, var(--blue-bg), #F8FCFA); }
.hub-card.amber { background: linear-gradient(180deg, var(--amber-bg), #FFFDFC); }
.hub-card.purple { background: linear-gradient(180deg, var(--purple-bg), #FFFEFF); }
.hub-icon {
  width: 46rpx;
  height: 46rpx;
  border-radius: 16rpx;
  background: rgba(255,255,255,.78);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 8rpx;
  box-shadow: var(--shadow-xs), var(--hairline);
}
.hub-icon image { width: 27rpx; height: 27rpx; }
.hub-title { display: block; font-size: 21rpx; font-weight: 900; color: var(--text); line-height: 1.15; }
.hub-desc { display: block; width: 100%; margin-top: 5rpx; font-size: 17rpx; line-height: 1.2; color: var(--text-muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
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

.meal-tabs { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 7rpx; margin-bottom: 12rpx; }
.meal-tab { min-width: 0; text-align: center; padding: 13rpx 0; background: var(--bg-elevated); border-radius: var(--radius); font-size: 22rpx; font-weight: 800; color: var(--text-secondary); position: relative; }
.meal-tab.active { background: var(--teal-bg); color: var(--teal); }
.tab-dot { display: inline-block; width: 10rpx; height: 10rpx; border-radius: 50%; margin-left: 6rpx; vertical-align: middle; }
.tab-dot.planned { background: var(--amber); }
.tab-dot.completed { background: var(--teal); }
.plan-card { background: rgba(255,255,255,.94); border-radius: var(--radius-md); padding: 14rpx; box-shadow: var(--shadow-sm), var(--hairline); display: flex; flex-direction: column; gap: 10rpx; }
.plan-row { min-height: 92rpx; border-radius: 22rpx; padding: 14rpx; background: var(--bg-elevated); display: flex; align-items: center; gap: 12rpx; box-sizing: border-box; }
.plan-row.planned { background: var(--amber-bg); }
.plan-row.completed { background: var(--green-bg); }
.plan-slot { width: 92rpx; flex-shrink: 0; }
.plan-name { display: block; color: var(--text); font-size: 25rpx; font-weight: 950; }
.plan-status { display: block; margin-top: 4rpx; color: var(--text-muted); font-size: 19rpx; font-weight: 800; }
.plan-main { flex: 1; min-width: 0; }
.plan-title { display: block; color: var(--text); font-size: 26rpx; font-weight: 900; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.plan-meta { display: block; margin-top: 5rpx; color: var(--text-muted); font-size: 21rpx; }
.plan-buttons { display: flex; align-items: center; gap: 8rpx; flex-shrink: 0; }
.plan-buttons button { min-width: 72rpx; height: 50rpx; margin: 0; padding: 0 14rpx; border-radius: var(--radius-full); border: none; font-size: 20rpx; font-weight: 900; line-height: 1; display: flex; align-items: center; justify-content: center; box-sizing: border-box; }
.plan-buttons button::after { border: none; }
.plan-done { background: #173B2E !important; color: #fff !important; box-shadow: 0 10rpx 18rpx rgba(23,59,46,.14); }
.plan-switch { background: rgba(255,255,255,.82) !important; color: var(--teal) !important; box-shadow: inset 0 0 0 1rpx rgba(35,169,120,.18); }
.plan-add { min-width: 88rpx !important; background: var(--teal-bg) !important; color: var(--teal) !important; box-shadow: inset 0 0 0 1rpx rgba(35,169,120,.14); }
.adoption-card { margin-top: 14rpx; background: linear-gradient(150deg, #FFFFFF, #F5FBF8); border-radius: var(--radius-md); padding: 20rpx; box-shadow: var(--shadow-sm), var(--hairline); }
.adoption-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 16rpx; margin-bottom: 14rpx; }
.adoption-kicker { display: block; font-size: 18rpx; color: var(--teal); font-weight: 950; }
.adoption-title { display: block; margin-top: 4rpx; font-size: 29rpx; color: var(--text); font-weight: 950; }
.adoption-clear { font-size: 22rpx; color: var(--text-muted); font-weight: 800; }
.adoption-timeline { display: flex; flex-direction: column; gap: 9rpx; }
.adoption-event { display: flex; align-items: flex-start; gap: 12rpx; padding: 13rpx 14rpx; border-radius: 18rpx; background: #fff; border: 1rpx solid var(--border-light); }
.adoption-event.partial { background: var(--amber-bg); }
.adoption-event.skipped { background: var(--bg-elevated); }
.adoption-dot { width: 14rpx; height: 14rpx; margin-top: 7rpx; border-radius: 50%; background: var(--teal); flex-shrink: 0; box-shadow: 0 0 0 6rpx rgba(35,169,120,.10); }
.adoption-copy { flex: 1; min-width: 0; }
.adoption-copy text:first-child { display: block; font-size: 23rpx; color: var(--text); font-weight: 900; }
.adoption-copy text:last-child { display: block; margin-top: 4rpx; font-size: 20rpx; color: var(--text-muted); line-height: 1.35; }
.adoption-shopping { margin-top: 13rpx; height: 64rpx; border-radius: var(--radius-full); background: #173B2E; color: #fff; display: flex; align-items: center; justify-content: space-between; padding: 0 20rpx; box-sizing: border-box; }
.adoption-shopping text:first-child { font-size: 23rpx; font-weight: 850; }
.adoption-shopping text:last-child { font-size: 22rpx; color: rgba(255,255,255,.78); font-weight: 900; }

.meal-scroll { width: 100%; white-space: nowrap; }
.meal-scroll .meal-card { display: inline-flex; vertical-align: top; width: 610rpx; margin-right: 16rpx; white-space: normal; box-sizing: border-box; }
.meal-card { min-height: 162rpx; padding: 20rpx; display: flex; align-items: center; gap: 18rpx; background: linear-gradient(145deg, #FFFFFF, #F8FCFA); position: relative; overflow: hidden; }
.meal-card::before { content: ""; position: absolute; left: 0; top: 22rpx; bottom: 22rpx; width: 6rpx; border-radius: 0 999rpx 999rpx 0; background: linear-gradient(180deg, var(--teal), var(--amber)); }
.meal-visual { width: 84rpx; height: 84rpx; border-radius: 25rpx; background: linear-gradient(150deg, var(--teal-bg), #FFFFFF); display: flex; align-items: center; justify-content: center; flex-shrink: 0; font-size: 38rpx; box-shadow: inset 0 0 0 1rpx rgba(35,169,120,.08); margin-left: 6rpx; }
.meal-info { flex: 1; min-width: 0; padding-bottom: 42rpx; }
.meal-kicker { display: block; color: var(--teal); font-size: 17rpx; font-weight: 950; margin-bottom: 2rpx; }
.meal-title { display: block; font-size: 29rpx; font-weight: 900; color: var(--text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.meal-meta { display: block; font-size: 23rpx; color: var(--text-muted); margin-top: 6rpx; }
.reason-row { display: flex; gap: 8rpx; flex-wrap: wrap; margin-top: 10rpx; }
.reason-chip { font-size: 20rpx; color: var(--text-secondary); background: var(--bg); border-radius: var(--radius-full); padding: 4rpx 10rpx; }
.explain-row { display: flex; gap: 7rpx; flex-wrap: wrap; margin-top: 8rpx; max-width: 100%; }
.explain-chip { max-width: 220rpx; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 19rpx; color: var(--teal); background: var(--green-bg); border-radius: var(--radius-full); padding: 4rpx 9rpx; box-sizing: border-box; }
.explain-more { font-size: 19rpx; color: #fff; background: #173B2E; border-radius: var(--radius-full); padding: 4rpx 11rpx; font-weight: 900; }
.explain-mask { position: fixed; inset: 0; z-index: 50; background: rgba(10, 20, 16, .32); display: flex; align-items: flex-end; }
.explain-sheet { width: 100%; background: #fff; border-radius: 30rpx 30rpx 0 0; padding: 24rpx 26rpx 36rpx; box-sizing: border-box; box-shadow: 0 -18rpx 46rpx rgba(18, 35, 29, .16); }
.explain-sheet-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 20rpx; margin-bottom: 18rpx; }
.explain-sheet-kicker { display: block; font-size: 18rpx; color: var(--teal); font-weight: 950; }
.explain-sheet-title { display: block; margin-top: 5rpx; color: var(--text); font-size: 34rpx; font-weight: 950; line-height: 1.25; }
.explain-close { width: 52rpx; height: 52rpx; border-radius: 50%; background: var(--bg-elevated); display: flex; align-items: center; justify-content: center; color: var(--text-muted); font-size: 38rpx; line-height: 1; flex-shrink: 0; }
.explain-block { background: var(--bg-elevated); border-radius: 20rpx; padding: 17rpx 18rpx; margin-top: 12rpx; }
.explain-block-title { display: block; color: var(--text); font-size: 24rpx; font-weight: 950; }
.explain-block-copy { display: block; margin-top: 7rpx; color: var(--text-secondary); font-size: 23rpx; line-height: 1.42; }
.explain-block-hint { display: block; margin-top: 8rpx; color: var(--teal); font-size: 21rpx; font-weight: 850; line-height: 1.35; }
.match-badge { min-width: 74rpx; height: 66rpx; border-radius: 21rpx; background: var(--green-bg); color: var(--teal); font-weight: 950; display: flex; flex-direction: column; align-items: center; justify-content: center; box-shadow: inset 0 0 0 1rpx rgba(35,169,120,.12); }
.match-badge text:first-child { font-size: 25rpx; line-height: 1; }
.match-badge text:last-child { margin-top: 5rpx; font-size: 15rpx; color: var(--text-muted); }
.meal-actions { position: absolute; right: 18rpx; bottom: 14rpx; display: flex; gap: 8rpx; }
.meal-actions button { width: 72rpx; height: 48rpx; margin: 0; padding: 0; border-radius: var(--radius-full); background: var(--green-bg) !important; color: var(--teal) !important; font-size: 20rpx; font-weight: 900; border: none; line-height: 1; display: flex; align-items: center; justify-content: center; }
.meal-actions button.primary { width: 72rpx; background: #173B2E !important; color: #fff !important; box-shadow: 0 10rpx 20rpx rgba(23,59,46,.14); }
.meal-actions button::after { border: none; }
.empty-card { padding: 26rpx; color: var(--text-muted); font-size: 25rpx; }

.ai-card { padding: 18rpx; position: relative; overflow: hidden; background: linear-gradient(150deg, #FFFFFF 0%, #FBFAFF 100%); }
.ai-card::before { content: ""; position: absolute; top: -80rpx; right: -70rpx; width: 180rpx; height: 180rpx; border-radius: 50%; background: rgba(141,122,230,.08); pointer-events: none; }
.ai-empty { background: linear-gradient(135deg, var(--purple-bg), #FFFFFF); border-radius: 22rpx; padding: 20rpx; margin-bottom: 14rpx; color: var(--text-secondary); font-size: 24rpx; line-height: 1.45; box-shadow: inset 0 0 0 1rpx rgba(141,122,230,.08); }
.ai-thread { display: flex; flex-direction: column; gap: 12rpx; margin-bottom: 14rpx; max-height: 560rpx; overflow-y: auto; }
.chat-row { display: flex; }
.chat-row.user { justify-content: flex-end; }
.chat-row.assistant { justify-content: flex-start; }
.chat-bubble { max-width: 92%; border-radius: 24rpx; padding: 17rpx 19rpx; box-sizing: border-box; animation: soft-pop .24s var(--ease) both; }
.chat-row.user .chat-bubble { background: linear-gradient(135deg, var(--teal), var(--teal-light)); color: #fff; border-bottom-right-radius: 8rpx; box-shadow: 0 12rpx 24rpx rgba(35,169,120,.16); }
.chat-row.assistant .chat-bubble { background: rgba(248,252,250,.96); color: var(--text); border-bottom-left-radius: 8rpx; box-shadow: var(--shadow-xs), var(--hairline); }
.chat-text { display: block; font-size: 24rpx; line-height: 1.5; }
.agent-panel { margin-top: 14rpx; display: flex; flex-direction: column; gap: 12rpx; }
.agent-timeline { display: flex; flex-direction: column; gap: 8rpx; padding: 4rpx 0; }
.agent-event { min-height: 54rpx; display: flex; align-items: flex-start; gap: 10rpx; padding: 10rpx 12rpx; border-radius: 14rpx; background: rgba(255,255,255,.86); border: 1rpx solid var(--border-light); }
.agent-event.tool_result { background: var(--green-bg); }
.agent-event.evaluation { background: var(--purple-bg); }
.agent-event.ask_user { background: var(--amber-bg); }
.event-dot { width: 12rpx; height: 12rpx; margin-top: 7rpx; border-radius: 50%; background: var(--teal); flex-shrink: 0; }
.agent-event.tool_start .event-dot { background: var(--berry); }
.agent-event.evaluation .event-dot { background: var(--berry); }
.agent-event.ask_user .event-dot { background: var(--amber); }
.event-copy { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 3rpx; }
.event-title { font-size: 21rpx; font-weight: 900; color: var(--text); }
.event-detail { font-size: 19rpx; line-height: 1.45; color: var(--text-muted); }
.event-latency { font-size: 18rpx; color: var(--text-muted); flex-shrink: 0; }
.agent-stages { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8rpx; }
.agent-stage { border-radius: 17rpx; padding: 11rpx 8rpx; background: #fff; border: 1rpx solid var(--border-light); box-shadow: var(--shadow-xs); }
.agent-stage.success { background: var(--green-bg); border-color: rgba(35,169,120,.18); }
.agent-stage.error, .agent-stage.failed { background: var(--red-bg); border-color: rgba(239,68,68,.18); }
.stage-name { display: block; font-size: 20rpx; font-weight: 900; color: var(--text); text-align: center; }
.stage-status { display: block; margin-top: 4rpx; font-size: 18rpx; color: var(--text-muted); text-align: center; }
.agent-recipes { display: flex; flex-direction: column; gap: 8rpx; }
.agent-recipe { background: #fff; border-radius: 19rpx; padding: 14rpx; display: flex; align-items: center; gap: 12rpx; border: 1rpx solid var(--border-light); box-shadow: var(--shadow-xs); }
.agent-recipe.adopted { border-color: rgba(35,169,120,.24); background: linear-gradient(135deg, #FFFFFF, #F3FBF7); }
.agent-recipe-main { flex: 1; min-width: 0; }
.agent-recipe-title { display: block; font-size: 25rpx; font-weight: 900; color: var(--text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.agent-recipe-meta { display: block; margin-top: 6rpx; font-size: 20rpx; color: var(--text-muted); }
.agent-recipe-explain { display: flex; flex-wrap: wrap; gap: 6rpx; margin-top: 8rpx; }
.agent-recipe-explain text { max-width: 220rpx; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 18rpx; color: var(--teal); background: var(--green-bg); border-radius: var(--radius-full); padding: 4rpx 8rpx; box-sizing: border-box; }
.agent-ingredient-strip { display: flex; flex-wrap: wrap; gap: 6rpx; margin-top: 8rpx; }
.agent-ingredient-strip text { max-width: 168rpx; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 18rpx; color: var(--text-muted); background: var(--bg-elevated); border-radius: var(--radius-full); padding: 4rpx 8rpx; box-sizing: border-box; }
.agent-mini-btn { width: 86rpx; height: 54rpx; margin: 0; padding: 0; border-radius: var(--radius-full); background: var(--berry); color: #fff; font-size: 21rpx; font-weight: 900; border: none; display: flex; align-items: center; justify-content: center; line-height: 1; flex-shrink: 0; }
.agent-mini-btn.primary { background: var(--teal); box-shadow: 0 10rpx 18rpx rgba(35,169,120,.16); }
.agent-mini-btn.done { background: var(--green-bg); color: var(--teal); box-shadow: inset 0 0 0 1rpx rgba(35,169,120,.16); }
.agent-mini-btn::after { border: none; }
.agent-meal-flow { background: linear-gradient(145deg, #FFFFFF, #F7FCF9); border: 1rpx solid rgba(35,169,120,.18); border-radius: 22rpx; padding: 16rpx; box-shadow: var(--shadow-xs); display: flex; flex-direction: column; gap: 13rpx; }
.agent-meal-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 14rpx; }
.agent-meal-kicker { display: block; color: var(--teal); font-size: 19rpx; font-weight: 950; }
.agent-meal-title { display: block; margin-top: 5rpx; color: var(--text); font-size: 27rpx; line-height: 1.25; font-weight: 950; }
.agent-meal-status { flex-shrink: 0; min-width: 78rpx; text-align: center; border-radius: var(--radius-full); padding: 8rpx 12rpx; color: var(--text-muted); background: var(--bg-elevated); font-size: 19rpx; font-weight: 900; }
.agent-meal-status.planned { color: var(--amber); background: var(--amber-bg); }
.agent-meal-status.completed { color: var(--teal); background: var(--green-bg); }
.agent-flow-events { display: flex; flex-direction: column; gap: 8rpx; }
.agent-flow-event { display: flex; gap: 9rpx; padding: 10rpx 12rpx; border-radius: 15rpx; background: rgba(255,255,255,.86); border: 1rpx solid var(--border-light); }
.agent-flow-event.success { background: var(--green-bg); border-color: rgba(35,169,120,.18); }
.flow-dot { width: 12rpx; height: 12rpx; border-radius: 50%; background: var(--teal); margin-top: 7rpx; flex-shrink: 0; }
.flow-copy { display: flex; flex-direction: column; gap: 3rpx; min-width: 0; }
.flow-copy text:first-child { color: var(--text); font-size: 21rpx; font-weight: 900; }
.flow-copy text:last-child { color: var(--text-muted); font-size: 19rpx; line-height: 1.4; }
.agent-meal-lists { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10rpx; }
.agent-mini-list { min-width: 0; border-radius: 17rpx; padding: 12rpx; background: #fff; border: 1rpx solid var(--border-light); display: flex; flex-direction: column; gap: 6rpx; box-sizing: border-box; }
.agent-mini-list.shopping { background: var(--amber-bg); border-color: rgba(255,178,102,.24); }
.agent-mini-list text { color: var(--text-secondary); font-size: 20rpx; line-height: 1.35; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.agent-mini-list .mini-list-title { color: var(--text); font-size: 21rpx; font-weight: 950; }
.agent-mini-list .mini-list-more { color: var(--amber); font-weight: 900; }
.agent-meal-actions { display: flex; gap: 10rpx; }
.agent-flow-btn { flex: 1; height: 58rpx; margin: 0; padding: 0 12rpx; border-radius: var(--radius-full); border: none; font-size: 22rpx; font-weight: 950; line-height: 1; display: flex; align-items: center; justify-content: center; }
.agent-flow-btn.ghost { background: #fff; color: var(--text-secondary); box-shadow: inset 0 0 0 1rpx var(--border-light); }
.agent-flow-btn.complete { background: #173B2E; color: #fff; box-shadow: 0 12rpx 22rpx rgba(23,59,46,.16); }
.agent-flow-btn.complete.done { background: var(--teal); }
.agent-flow-btn::after { border: none; }
.agent-shopping { background: #fff; border-radius: 19rpx; padding: 12rpx 14rpx; display: flex; align-items: center; justify-content: space-between; gap: 12rpx; border: 1rpx solid var(--border-light); box-shadow: var(--shadow-xs); }
.agent-shopping text { color: var(--text-secondary); font-size: 22rpx; }
.agent-shopping button { width: 82rpx; height: 52rpx; margin: 0; padding: 0; border-radius: var(--radius-full); background: var(--teal); color: #fff; font-size: 21rpx; font-weight: 900; border: none; line-height: 1; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.ai-input-row { display: flex; align-items: center; gap: 10rpx; position: relative; z-index: 1; }
.ai-icon { width: 42rpx; height: 42rpx; flex-shrink: 0; }
.ai-input { flex: 1; min-width: 0; height: 74rpx; background: #fff; border: 1px solid var(--border-light); border-radius: var(--radius-full); padding: 0 22rpx; font-size: 26rpx; color: var(--text); box-sizing: border-box; box-shadow: inset 0 0 0 1rpx rgba(19,35,29,.02); }
.ai-send { width: 98rpx; height: 74rpx; margin: 0; padding: 0; background: linear-gradient(135deg, var(--berry), #A996FF); color: #fff; border: none; border-radius: var(--radius-full); font-size: 25rpx; font-weight: 900; line-height: 1; display: flex; align-items: center; justify-content: center; box-sizing: border-box; flex-shrink: 0; box-shadow: 0 12rpx 24rpx rgba(141,122,230,.20); }
.ai-intent-row { display: flex; flex-wrap: wrap; gap: 8rpx; margin-bottom: 12rpx; }
.ai-intent-chip { font-size: 22rpx; background: var(--purple-bg); color: var(--berry); padding: 7rpx 14rpx; border-radius: var(--radius-full); }
.ph { color: var(--text-placeholder); }
/* skeleton loading */
.agent-skeleton {
  background: #fff;
  border-radius: 22rpx;
  padding: 24rpx;
  margin-bottom: 14rpx;
  box-shadow: var(--shadow-xs), var(--hairline);
}
.skeleton-progress-wrap {
  margin-bottom: 20rpx;
  display: flex;
  align-items: center;
  gap: 14rpx;
}
.skeleton-progress-bar {
  flex: 1;
  height: 10rpx;
  border-radius: 10rpx;
  background: var(--border-light);
  overflow: hidden;
}
.skeleton-progress-fill {
  height: 100%;
  border-radius: 10rpx;
  background: linear-gradient(90deg, var(--teal), var(--teal-light));
  transition: width .25s ease-out;
}
.skeleton-progress-text {
  font-size: 20rpx;
  color: var(--text-muted);
  white-space: nowrap;
  font-weight: 800;
}
.skeleton-line {
  height: 18rpx;
  border-radius: 9rpx;
  background: linear-gradient(90deg, var(--border-light) 25%, var(--bg) 50%, var(--border-light) 75%);
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.5s ease-in-out infinite;
  margin-bottom: 12rpx;
}
.skeleton-line.long { width: 100%; }
.skeleton-line.medium { width: 70%; }
.skeleton-line.short { width: 45%; }
@keyframes skeleton-shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
/* memory chips */
.agent-memory {
  background: var(--green-bg);
  border-radius: 14rpx;
  padding: 14rpx;
  margin-bottom: 10rpx;
}
.memory-head {
  font-size: 20rpx;
  font-weight: 900;
  color: var(--teal);
  margin-bottom: 8rpx;
}
.memory-chip {
  font-size: 19rpx;
  color: var(--text-secondary);
  padding: 5rpx 0;
  display: flex;
  align-items: flex-start;
  gap: 6rpx;
}
.memory-chip-label {
  font-weight: 800;
  color: var(--teal);
  flex-shrink: 0;
}
/* L2 用户确认 */
.agent-confirm {
  display: flex;
  flex-direction: column;
  gap: 10rpx;
  margin-bottom: 10rpx;
}
.confirm-card {
  background: #FFF8F0;
  border: 1rpx solid var(--amber);
  border-radius: 16rpx;
  padding: 14rpx;
}
.confirm-question {
  font-size: 22rpx;
  font-weight: 800;
  color: #9A651B;
  margin-bottom: 10rpx;
}
.confirm-options {
  display: flex;
  gap: 10rpx;
  flex-wrap: wrap;
}
.confirm-btn {
  height: 48rpx;
  padding: 0 18rpx;
  border-radius: var(--radius-full);
  background: #fff;
  border: 1rpx solid var(--amber);
  color: #9A651B;
  font-size: 21rpx;
  font-weight: 700;
}
.feedback-mask { position: fixed; inset: 0; z-index: 99; background: rgba(9, 18, 15, .34); display: flex; align-items: flex-end; animation: fade-in .18s ease both; }
.feedback-sheet { width: 100%; padding: 14rpx 28rpx calc(28rpx + env(safe-area-inset-bottom)); border-radius: 34rpx 34rpx 0 0; background: #fff; box-shadow: 0 -22rpx 60rpx rgba(0,0,0,.16); box-sizing: border-box; animation: sheet-up .22s var(--ease) both; }
.feedback-handle { width: 76rpx; height: 8rpx; border-radius: 999rpx; background: var(--border); margin: 0 auto 18rpx; }
.feedback-head { margin-bottom: 18rpx; }
.feedback-head text:first-child { display: block; font-size: 34rpx; color: var(--text); font-weight: 950; }
.feedback-head text:last-child { display: block; margin-top: 6rpx; font-size: 23rpx; color: var(--text-muted); }
.feedback-ratings { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10rpx; margin-bottom: 16rpx; }
.feedback-rating { height: 66rpx; border-radius: var(--radius-full); background: var(--bg-elevated); color: var(--text-secondary); display: flex; align-items: center; justify-content: center; font-size: 22rpx; font-weight: 900; }
.feedback-rating.active { background: var(--teal-bg); color: var(--teal); box-shadow: inset 0 0 0 1rpx rgba(35,169,120,.16); }
.feedback-chips { display: flex; flex-wrap: wrap; gap: 10rpx; margin-bottom: 16rpx; }
.feedback-chips text { padding: 10rpx 16rpx; border-radius: var(--radius-full); background: var(--bg-elevated); color: var(--text-secondary); font-size: 22rpx; font-weight: 850; }
.feedback-chips text.active { background: #173B2E; color: #fff; }
.feedback-input { width: 100%; min-height: 150rpx; background: var(--bg); border-radius: var(--radius); padding: 18rpx; box-sizing: border-box; font-size: 25rpx; color: var(--text); margin-bottom: 16rpx; }
.feedback-actions { display: flex; gap: 12rpx; }
.feedback-actions button { flex: 1; height: 76rpx; margin: 0; border-radius: var(--radius-full); border: none; font-size: 25rpx; font-weight: 900; display: flex; align-items: center; justify-content: center; }
.feedback-skip { background: var(--bg-elevated); color: var(--text-secondary); }
.feedback-submit { background: var(--teal); color: #fff; box-shadow: 0 12rpx 24rpx rgba(35,169,120,.16); }
@keyframes fade-in { from { opacity: 0; } to { opacity: 1; } }
@keyframes sheet-up { from { transform: translateY(100%); } to { transform: translateY(0); } }
.bottom-safe { height: 132rpx; }
</style>
