<template>
  <view class="le-page" v-if="!isLoading">
    <view class="le-header">
      <text class="le-title">{{ $t('taskAutomation') }}</text>
      <text class="le-desc">{{ $t('mergeDesc') }}</text>
    </view>

    <view class="summary-row">
      <view class="summary-card">
        <text class="summary-num">{{ recipeCount }}</text>
        <text class="summary-label">关联食谱</text>
      </view>
      <view class="summary-card">
        <text class="summary-num">{{ uniqueIngredientCount }}</text>
        <text class="summary-label">食材种类</text>
      </view>
      <view class="summary-card">
        <text class="summary-num">{{ checkedCount }}</text>
        <text class="summary-label">已勾选</text>
      </view>
    </view>

    <view v-if="errorNotice" class="notice-card">
      <image src="/static/icons/icon_flash.svg" mode="aspectFit" />
      <text>{{ errorNotice }}</text>
    </view>

    <view class="nutrition-panel">
      <view class="section-header">
        <view class="section-title-row">
          <image class="section-title-icon" src="/static/icons/icon_chart.svg" mode="aspectFit" />
          <text class="section-label">本次食材营养</text>
        </view>
        <text class="section-count">估算值</text>
      </view>
      <view v-if="!ingredientNutritionRows.length" class="nutrition-empty">
        <text>暂无可计算食材，请先确认识别结果名称和数量。</text>
      </view>
      <view class="nutrition-grid">
        <view v-for="m in batchNutritionTiles" :key="m.key" class="nutrition-tile">
          <text class="nutrition-value">{{ m.value }}{{ m.unit }}</text>
          <text class="nutrition-label">{{ m.label }}</text>
          <view class="nutrition-bar"><view :style="{ width: m.pct + '%' }"></view></view>
          <text class="nutrition-foot">占每日 {{ m.pct }}%</text>
        </view>
      </view>
      <view class="ingredient-nutrition-list">
        <view v-for="row in ingredientNutritionRows" :key="row.name" class="ingredient-nutrition-row">
          <text>{{ row.name }}</text>
          <text>按 {{ row.weight }}g 计算 · {{ row.calories }}kcal · P {{ row.protein }}g</text>
        </view>
      </view>
    </view>

    <view class="nutrition-panel gap-panel">
      <view class="section-header">
        <view class="section-title-row">
          <image class="section-title-icon" src="/static/icons/icon_flash.svg" mode="aspectFit" />
          <text class="section-label">今日摄入与缺口</text>
        </view>
        <text class="section-count">{{ intakeRecorded ? '已更新' : '当前' }}</text>
      </view>
      <view class="gap-list">
        <view v-for="gap in dailyGapRows" :key="gap.key" class="gap-item">
          <view class="gap-copy">
            <text class="gap-name">{{ gap.label }}</text>
            <text class="gap-meta">已摄入 {{ gap.current }}{{ gap.unit }} / 目标 {{ gap.target }}{{ gap.unit }}</text>
          </view>
          <text class="gap-need">{{ gap.need > 0 ? `还缺 ${gap.need}${gap.unit}` : '已达标' }}</text>
        </view>
      </view>
    </view>

    <view class="automation-card">
      <view class="auto-step active">
        <text>1</text>
        <view>
          <text class="auto-title">合并食材</text>
          <text class="auto-copy">按菜谱去重并整理规格</text>
        </view>
      </view>
      <view class="auto-step active">
        <text>2</text>
        <view>
          <text class="auto-title">人工校正</text>
          <text class="auto-copy">支持编辑、删除和勾选</text>
        </view>
      </view>
      <view class="auto-step">
        <text>3</text>
        <view>
          <text class="auto-title">导出复用</text>
          <text class="auto-copy">复制或生成 Markdown</text>
        </view>
      </view>
    </view>

    <view class="section">
      <view class="section-header">
        <text class="section-label">{{ $t('relatedRecipes') }}</text>
      </view>
      <view class="recipe-tags">
        <text v-for="(r, idx) in recipes" :key="idx" class="recipe-tag">{{ r.title }}</text>
      </view>
    </view>

    <view class="section list-section">
      <view class="section-header">
        <view class="section-title-row">
          <image class="section-title-icon" src="/static/icons/icon_cart.svg" mode="aspectFit" />
          <text class="section-label">{{ $t('mergedList') }}</text>
        <text class="section-count">{{ editingList.length }} 项</text>
      </view>
      <text class="section-action" @tap="toggleAll">全选</text>
      <text v-if="hasPersistedShoppingItems" class="section-action" @tap="archiveList" style="margin-left:20rpx">归档</text>
      <text class="section-action" @tap="addItem" style="margin-left:20rpx">+ {{ $t('add') }}</text>
    </view>

      <view v-if="editingList.length === 0" class="le-empty">
        <text>{{ $t('noIngredient') }}</text>
      </view>

      <view v-for="(item, idx) in editingList" :key="idx" class="list-item" :class="{ checked: checkedItems[idx] }">
        <view class="check" @tap="toggleChecked(idx)">
          <text v-if="checkedItems[idx]">✓</text>
        </view>
        <view class="ingredient-icon">
          <image :src="ingredientIcon(item)" mode="aspectFit" />
          <text>{{ ingredientGlyph(item) }}</text>
        </view>
        <view class="item-info">
          <text class="item-name">{{ item.name || '-' }}</text>
          <text class="item-amount">{{ item.display || item.amount || '-' }}</text>
        </view>
        <view class="item-actions">
          <image class="action-icon" src="/static/icons/icon_edit.svg" @tap="editItem(idx)" mode="widthFix" />
          <image class="action-icon delete" src="/static/icons/icon_delete.svg" @tap="removeItem(idx)" mode="widthFix" />
        </view>
      </view>
    </view>

    <view class="bottom-actions">
      <button class="primary-action" @tap="copyToClipboard">
        <image class="btn-icon invert" src="/static/icons/icon_copy.svg" mode="widthFix" />
        {{ $t('copyToClipboard') }}
      </button>
      <button class="primary-action plan-action" @tap="planFromList">
        <image class="btn-icon invert" src="/static/icons/icon_calendar.svg" mode="widthFix" />
        加入{{ selectedMealSlotLabel }}计划
      </button>
      <view class="secondary-actions">
        <button @tap="chooseMealSlot"><image class="btn-icon" src="/static/icons/icon_plate.svg" mode="widthFix" />{{ selectedMealSlotLabel }}</button>
        <button @tap="exportMarkdown"><image class="btn-icon" src="/static/icons/icon_export.svg" mode="widthFix" />{{ $t('exportMarkdown') }}</button>
        <button @tap="shareToSocial"><image class="btn-icon" src="/static/icons/icon_share.svg" mode="widthFix" />{{ $t('shareToSocial') }}</button>
      </view>
    </view>
  </view>
  <view v-else class="loading-page"><text>加载中...</text></view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { ApiService } from '@/api/index'
import { t } from '@/utils/i18n'
import { summarizeIngredientNutrition, NUTRITION_TARGETS, ingredientName, normalizeIngredientItem } from '@/utils/food-analysis'

const $t = key => t(key)
const isLoading = ref(true)
const recipes = ref([])
const editingList = ref([])
const checkedItems = ref({})
const errorNotice = ref('')
const dailySummary = ref(null)
const intakeRecorded = ref(false)
const lastIntakeRecipe = ref(null)
const persistedShoppingMode = ref(false)
const selectedMealSlot = ref(currentMealSlot())
const mealSlotOptions = [
  { key: 'breakfast', label: '早餐' },
  { key: 'lunch', label: '午餐' },
  { key: 'dinner', label: '晚餐' },
  { key: 'snack', label: '加餐' },
  { key: 'late_night', label: '宵夜' },
  { key: 'custom', label: '自定义' }
]
const selectedMealSlotLabel = computed(() => mealSlotOptions.find(item => item.key === selectedMealSlot.value)?.label || selectedMealSlot.value || '本餐')
const recipeCount = computed(() => recipes.value.length)
const checkedCount = computed(() => Object.values(checkedItems.value).filter(Boolean).length)
const uniqueIngredientCount = computed(() => {
  const names = new Set()
  editingList.value.forEach(item => {
    const name = (item.name || '').trim().toLowerCase()
    if (name) names.add(name)
  })
  return names.size
})
const nutritionSummary = computed(() => summarizeIngredientNutrition(activeIntakeItems.value))
const activeTargets = computed(() => ({ ...NUTRITION_TARGETS, ...(dailySummary.value?.targets || {}) }))
const ingredientNutritionRows = computed(() => nutritionSummary.value.rows)
const batchNutritionTiles = computed(() => {
  const totals = nutritionSummary.value.totals
  return [
    { key: 'calories', label: '热量', value: Math.round(totals.calories || 0), unit: 'kcal', target: activeTargets.value.calories },
    { key: 'protein', label: '蛋白质', value: totals.protein || 0, unit: 'g', target: activeTargets.value.protein },
    { key: 'carbs', label: '碳水', value: totals.carbs || 0, unit: 'g', target: activeTargets.value.carbs },
    { key: 'fat', label: '脂肪', value: totals.fat || 0, unit: 'g', target: activeTargets.value.fat },
    { key: 'fiber', label: '膳食纤维', value: totals.fiber || 0, unit: 'g', target: activeTargets.value.fiber },
    { key: 'vitamin_c', label: '维生素C', value: totals.vitamin_c || 0, unit: 'mg', target: activeTargets.value.vitamin_c },
    { key: 'iron', label: '铁', value: totals.iron || 0, unit: 'mg', target: activeTargets.value.iron }
  ].map(item => ({ ...item, pct: Math.min(100, Math.round((Number(item.value) / item.target) * 100)) }))
})
const dailyGapRows = computed(() => {
  const current = dailySummary.value?.totals || {}
  return [
    { key: 'calories', label: '热量', unit: 'kcal', target: activeTargets.value.calories },
    { key: 'protein', label: '蛋白质', unit: 'g', target: activeTargets.value.protein },
    { key: 'carbs', label: '碳水', unit: 'g', target: activeTargets.value.carbs },
    { key: 'fat', label: '脂肪', unit: 'g', target: activeTargets.value.fat },
    { key: 'fiber', label: '膳食纤维', unit: 'g', target: activeTargets.value.fiber },
    { key: 'vitamin_c', label: '维生素C', unit: 'mg', target: activeTargets.value.vitamin_c },
    { key: 'iron', label: '铁', unit: 'mg', target: activeTargets.value.iron }
  ].map(item => {
    const value = Number(current[item.key] || 0)
    return { ...item, current: Number(value.toFixed(item.key === 'calories' ? 0 : 1)), need: Number(Math.max(0, item.target - value).toFixed(item.key === 'calories' ? 0 : 1)) }
  })
})
const activeIntakeItems = computed(() => {
  const checkedIndexes = Object.keys(checkedItems.value).filter(key => checkedItems.value[key]).map(Number)
  if (!checkedIndexes.length) return editingList.value
  return checkedIndexes.map(idx => editingList.value[idx]).filter(Boolean)
})
const hasPersistedShoppingItems = computed(() => editingList.value.some(item => itemIds(item).length))

function dedupeIngredients(list) {
  const map = new Map()
  list.forEach(item => {
    const normalized = normalizeIngredientItem(item)
    const key = ingredientName(normalized).toLowerCase()
    if (!key) return
    if (!map.has(key)) {
      map.set(key, normalized)
      return
    }
    const current = map.get(key)
    map.set(key, {
      ...current,
      ...normalized,
      name: current.name,
      confidence: Math.max(Number(current.confidence || 0), Number(normalized.confidence || 0)),
      source_count: Number(current.source_count || 1) + 1
    })
  })
  return Array.from(map.values())
}

onLoad(async (options) => {
  try {
    if (options && options.items) {
      const parsedItems = JSON.parse(decodeURIComponent(options.items))
      recipes.value = [{ title: decodeURIComponent(options.title || 'AI助手清单'), recipeId: 'agent_list' }]
      persistedShoppingMode.value = parsedItems.some(item => itemIds(item).length)
      editingList.value = dedupeIngredients(parsedItems.map(item => ({
        ...item,
        amount: item.display || item.amount || ''
      })))
    } else if (options && options.recipes) {
      const parsed = JSON.parse(decodeURIComponent(options.recipes))
      if (parsed.length > 0 && (parsed[0].recipeId || parsed[0].recipe_id)) {
        recipes.value = parsed
        const ids = parsed.map(r => r.recipeId || r.recipe_id)
        try {
          const merged = await ApiService.mergeShoppingList(ids)
          editingList.value = dedupeIngredients(merged)
        } catch (e) {
          errorNotice.value = '后端清单合并暂未连通，未使用本地演示清单。'
          editingList.value = []
        }
      } else if (parsed.length > 0 && parsed[0].name) {
        recipes.value = [{ title: 'AI推荐', recipeId: 'r_ai' }]
        editingList.value = dedupeIngredients(parsed)
      }
    }
  } catch (e) {
    errorNotice.value = '清单参数解析失败，未使用本地演示清单。'
    editingList.value = []
  }
  await loadDailySummary()
  isLoading.value = false
})

async function reloadPersistedShoppingList() {
  if (!persistedShoppingMode.value) return
  try {
    const data = await ApiService.getTodayShoppingList()
    editingList.value = dedupeIngredients((data.items || []).map(item => ({
      ...item,
      amount: item.display || item.amount || ''
    })))
    checkedItems.value = {}
  } catch (e) {
    errorNotice.value = e.message || '购物清单同步失败，请稍后重试。'
  }
}

async function loadDailySummary() {
  try {
    dailySummary.value = await ApiService.getNutritionSummary('day')
  } catch (e) {
    dailySummary.value = { totals: {} }
  }
}

function addItem() { editingList.value.push({ name: '', amount: '' }) }
function itemIds(item) {
  if (Array.isArray(item?.ids)) return item.ids.filter(Boolean)
  if (item?.id) return [item.id]
  return []
}
async function syncItemStatus(item, status) {
  const ids = itemIds(item)
  if (!ids.length) return false
  await Promise.all(ids.map(id => ApiService.updateShoppingItemStatus(id, status)))
  return true
}
async function toggleChecked(idx) {
  const item = editingList.value[idx]
  const nextChecked = !checkedItems.value[idx]
  checkedItems.value[idx] = nextChecked
  checkedItems.value = { ...checkedItems.value }
  try {
    const synced = await syncItemStatus(item, nextChecked ? 'purchased' : 'open')
    if (synced) await reloadPersistedShoppingList()
  } catch (e) {
    checkedItems.value[idx] = !nextChecked
    checkedItems.value = { ...checkedItems.value }
    uni.showToast({ title: e.message || '同步失败', icon: 'none' })
  }
}
function toggleAll() {
  const allChecked = editingList.value.length && editingList.value.every((_, i) => checkedItems.value[i])
  if (allChecked) { checkedItems.value = {} }
  else { const o = {}; editingList.value.forEach((_, i) => o[i] = true); checkedItems.value = o }
}
function editItem(idx) {
  const item = editingList.value[idx]
  uni.showModal({
    title: $t('editIngredient'),
    editable: true,
    placeholderText: `${item.name || '食材'} - ${item.display || item.amount || '100g'}`,
    success: (res) => {
      if (res.confirm && res.content) {
        const parts = res.content.split(/[-—]/).map(s => s.trim())
        const amount = parts[1] || item.amount || item.display || ''
        editingList.value[idx] = { ...item, name: parts[0] || item.name, amount, display: amount }
        editingList.value = dedupeIngredients(editingList.value)
      }
    }
  })
}
async function removeItem(idx) {
  const item = editingList.value[idx]
  const ids = itemIds(item)
  try {
    if (ids.length) {
      await Promise.all(ids.map(id => ApiService.deleteShoppingItem(id)))
      await reloadPersistedShoppingList()
      return
    }
    editingList.value.splice(idx, 1)
  } catch (e) {
    uni.showToast({ title: e.message || '删除失败', icon: 'none' })
  }
}
async function archiveList() {
  if (!hasPersistedShoppingItems.value) return
  uni.showModal({
    title: '归档今日清单',
    content: '归档后，今日补购清单会清空，已采纳的用餐计划不会被删除。',
    confirmText: '归档',
    success: async (res) => {
      if (!res.confirm) return
      try {
        const result = await ApiService.archiveTodayShoppingList()
        await reloadPersistedShoppingList()
        uni.showToast({ title: `已归档${result.archived_count || 0}项`, icon: 'success' })
      } catch (e) {
        uni.showToast({ title: e.message || '归档失败', icon: 'none' })
      }
    }
  })
}
function generateText() {
  let text = '=== ByteSavor 购物清单 ===\n\n'
  editingList.value.forEach(item => { text += `□ ${item.name} - ${item.amount}\n` })
  text += '\n由 ByteSavor AI 智能生成'
  return text
}
async function writeClipboard(text) {
  try {
    await new Promise((resolve, reject) => {
      uni.setClipboardData({
        data: text,
        success: resolve,
        fail: reject
      })
    })
    return true
  } catch (e) {
    if (typeof navigator !== 'undefined' && navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text)
      return true
    }
    throw e
  }
}
async function copyToClipboard() {
  try {
    await writeClipboard(generateText())
    uni.showToast({ title: $t('copied'), icon: 'success' })
  } catch (e) {
    uni.showToast({ title: '复制失败，请检查浏览器权限', icon: 'none' })
  }
}
function exportMarkdown() {
  let md = '# ByteSavor 购物清单\n\n## 关联食谱\n'
  recipes.value.forEach(r => { md += `- ${r.title} (匹配度 ${((r.matchScore || 0) * 100).toFixed(0)}%)\n` })
  md += '\n## 合并后的食材\n'
  editingList.value.forEach(item => { md += `- [ ] ${item.name} - ${item.amount}\n` })
  md += '\n---\n*由 ByteSavor 智能厨房助手生成*'
  uni.showModal({
    title: 'Markdown',
    content: md,
    confirmText: $t('copyToClipboard'),
    success: (res) => {
      if (res.confirm) {
        writeClipboard(md)
          .then(() => uni.showToast({ title: $t('copied'), icon: 'success' }))
          .catch(() => uni.showToast({ title: '复制失败，请检查浏览器权限', icon: 'none' }))
      }
    }
  })
}
async function planFromList() {
  if (!activeIntakeItems.value.length) {
    uni.showToast({ title: '暂无可加入计划的食材', icon: 'none' })
    return
  }
  const recipe = intakeRecipeSnapshot()
  try {
    const adopted = await ApiService.adoptMeal(selectedMealSlot.value, recipe)
    const count = (adopted.shopping_list || []).length
    uni.showToast({ title: count ? `已采纳，需补${count}项` : `已采纳到${selectedMealSlotLabel.value}`, icon: 'success' })
  } catch (e) {
    uni.showToast({ title: e.message || '采纳失败', icon: 'none' })
  }
}
function currentMealSlot() {
  const h = new Date().getHours()
  if (h < 10) return 'breakfast'
  if (h < 15) return 'lunch'
  return 'dinner'
}
function intakeRecipeSnapshot() {
  const totals = nutritionSummary.value.totals
  const rows = nutritionSummary.value.rows
  const names = rows.map(item => item.name).filter(Boolean)
  return {
    recipe_id: `scan_intake_${Date.now()}`,
    title: names.length ? `本次识别：${names.slice(0, 3).join('、')}` : '本次识别食材',
    calories: Math.round(totals.calories || 0),
    nutrition: {
      calories: Math.round(totals.calories || 0),
      protein: Math.round(totals.protein || 0),
      carbs: Math.round(totals.carbs || 0),
      fat: Math.round(totals.fat || 0),
      fiber: Math.round(totals.fiber || 0),
      vitamin_c: Math.round(totals.vitamin_c || 0),
      iron: Number(totals.iron || 0)
    },
    ingredients: rows.map(item => ({ name: item.name, amount: `${item.weight}g`, display: `${item.weight}g` }))
  }
}
function chooseMealSlot() {
  uni.showActionSheet({
    itemList: mealSlotOptions.map(item => item.label),
    success: (res) => {
      const option = mealSlotOptions[res.tapIndex]
      if (!option) return
      if (option.key !== 'custom') {
        selectedMealSlot.value = option.key
        return
      }
      uni.showModal({
        title: '自定义餐时',
        editable: true,
        placeholderText: '比如：训练后加餐、下午茶',
        confirmText: '保存',
        success: (modal) => {
          if (modal.confirm && modal.content?.trim()) selectedMealSlot.value = modal.content.trim()
        }
      })
    }
  })
}
function askMealFeedback(recipe) {
  uni.showActionSheet({
    itemList: ['很喜欢 5分', '还可以 4分', '一般 3分', '不喜欢 2分'],
    success: (res) => {
      const ratings = [5, 4, 3, 2]
      const rating = ratings[res.tapIndex] || 3
      askMealFeedbackReason(recipe, rating)
    },
    fail: () => {}
  })
}
function askMealFeedbackReason(recipe, rating) {
  uni.showModal({
    title: '这餐记忆一下',
    editable: true,
    placeholderText: '比如：喜欢清淡少油、牛肉口感好；或者太油腻、分量太大',
    cancelText: '跳过',
    confirmText: '提交',
    success: async (res) => {
      if (!res.confirm) return
      try {
        const comment = (res.content || '').trim() || `本次摄入评分 ${rating} 分`
        await ApiService.submitFeedback(recipe.recipe_id || lastIntakeRecipe.value?.recipe_id || '', rating, comment)
        uni.showToast({ title: '偏好已学习', icon: 'success' })
      } catch (e) {
        uni.showToast({ title: '摄入已记录，偏好学习失败', icon: 'none' })
      }
    }
  })
}
function ingredientIcon(item) {
  const name = `${item?.name || ''}${item?.nameEn || ''}`.toLowerCase()
  if (name.includes('牛') || name.includes('肉') || name.includes('鸡') || name.includes('beef') || name.includes('chicken')) return '/static/icons/icon_muscle.svg'
  if (name.includes('鱼') || name.includes('虾') || name.includes('fish') || name.includes('seafood')) return '/static/icons/icon_fish.svg'
  if (name.includes('油') || name.includes('oil') || name.includes('olive')) return '/static/icons/icon_olive.svg'
  return '/static/icons/icon_leaf.svg'
}
function ingredientGlyph(item) {
  const name = `${item?.name || ''}${item?.nameEn || ''}`.toLowerCase()
  if (name.includes('牛') || name.includes('肉') || name.includes('鸡') || name.includes('beef') || name.includes('chicken')) return '肉'
  if (name.includes('鱼') || name.includes('虾') || name.includes('fish') || name.includes('seafood')) return '鱼'
  if (name.includes('油') || name.includes('oil') || name.includes('olive')) return '油'
  return '菜'
}
function shareToSocial() {
  uni.showActionSheet({
    itemList: [$t('wechat'), $t('xiaohongshu')],
    success: () => { uni.showToast({ title: '分享功能待实现', icon: 'none' }) }
  })
}
function goBack() { uni.navigateBack() }
</script>

<style scoped>
.le-page { min-height: 100vh; background: var(--bg); padding: 28rpx; }
.loading-page { display: flex; align-items: center; justify-content: center; height: 100vh; }
.le-header { margin-bottom: 22rpx; }
.le-title { font-size: 42rpx; font-weight: 900; color: var(--text); display: block; }
.le-desc { font-size: 24rpx; color: var(--text-secondary); margin-top: 8rpx; display: block; line-height: 1.45; }
.summary-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12rpx; margin-bottom: 22rpx; }
.summary-card { background: #fff; border-radius: var(--radius); padding: 18rpx; box-shadow: var(--shadow-sm); }
.summary-num { display: block; font-size: 40rpx; font-weight: 900; color: var(--text); line-height: 1; }
.summary-label { display: block; margin-top: 8rpx; font-size: 21rpx; color: var(--text-muted); }
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
.automation-card {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10rpx;
  background: #fff;
  border-radius: var(--radius);
  padding: 14rpx;
  margin-bottom: 22rpx;
  box-shadow: var(--shadow-sm);
}
.auto-step {
  min-height: 128rpx;
  border-radius: 18rpx;
  background: var(--bg-elevated);
  padding: 14rpx;
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}
.auto-step.active { background: var(--teal-bg); }
.auto-step > text {
  width: 32rpx;
  height: 32rpx;
  border-radius: 12rpx;
  background: #fff;
  color: var(--accent);
  font-size: 20rpx;
  font-weight: 900;
  display: flex;
  align-items: center;
  justify-content: center;
}
.auto-title { display: block; font-size: 21rpx; font-weight: 900; color: var(--text); }
.auto-copy { display: block; margin-top: 4rpx; font-size: 18rpx; color: var(--text-secondary); line-height: 1.35; }
.section { margin-bottom: 22rpx; }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14rpx; }
.section-title-row { display: flex; align-items: center; min-width: 0; gap: 10rpx; }
.section-title-icon { width: 34rpx; height: 34rpx; flex-shrink: 0; }
.section-label { font-size: 30rpx; font-weight: 900; color: var(--text); }
.section-count { font-size: 22rpx; color: var(--text-muted); background: var(--bg-elevated); border-radius: var(--radius-full); padding: 5rpx 12rpx; flex-shrink: 0; }
.section-action { font-size: 25rpx; color: var(--teal); font-weight: 900; }
.recipe-tags { display: flex; flex-wrap: wrap; gap: 10rpx; }
.recipe-tag { background: #fff; color: var(--teal); font-size: 23rpx; padding: 9rpx 16rpx; border-radius: var(--radius-full); box-shadow: var(--shadow-sm); }
.nutrition-panel { background: #fff; border-radius: var(--radius); padding: 20rpx; margin-bottom: 22rpx; box-shadow: var(--shadow-sm); }
.nutrition-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12rpx; }
.nutrition-tile { background: var(--bg-elevated); border-radius: 18rpx; padding: 16rpx; min-width: 0; box-shadow: inset 0 0 0 1rpx rgba(19,35,29,.04); }
.nutrition-value { display: block; color: var(--text); font-size: 30rpx; line-height: 1; font-weight: 950; }
.nutrition-label { display: block; margin-top: 7rpx; color: var(--text-secondary); font-size: 21rpx; font-weight: 800; }
.nutrition-bar { height: 8rpx; margin-top: 12rpx; background: var(--border-light); border-radius: 999rpx; overflow: hidden; }
.nutrition-bar view { height: 100%; border-radius: 999rpx; background: linear-gradient(90deg, var(--teal), var(--amber)); }
.nutrition-foot { display: block; margin-top: 8rpx; color: var(--text-muted); font-size: 19rpx; }
.ingredient-nutrition-list { margin-top: 14rpx; display: flex; flex-direction: column; gap: 8rpx; }
.ingredient-nutrition-row { display: flex; justify-content: space-between; gap: 12rpx; background: #fff; border-radius: 14rpx; padding: 12rpx 14rpx; box-shadow: inset 0 0 0 1rpx rgba(19,35,29,.05); }
.ingredient-nutrition-row text:first-child { color: var(--text); font-size: 22rpx; font-weight: 900; }
.ingredient-nutrition-row text:last-child { color: var(--text-muted); font-size: 20rpx; text-align: right; }
.gap-panel { background: linear-gradient(180deg, #FFFFFF, #F8FCFA); }
.gap-list { display: flex; flex-direction: column; gap: 10rpx; }
.gap-item { display: flex; align-items: center; justify-content: space-between; gap: 12rpx; background: var(--bg-elevated); border-radius: 16rpx; padding: 14rpx; }
.gap-copy { min-width: 0; flex: 1; }
.gap-name { display: block; color: var(--text); font-size: 23rpx; font-weight: 950; }
.gap-meta { display: block; margin-top: 4rpx; color: var(--text-muted); font-size: 19rpx; }
.gap-need { color: var(--teal); font-size: 21rpx; font-weight: 900; flex-shrink: 0; }
.list-section { background: #fff; border-radius: var(--radius); padding: 20rpx; box-shadow: var(--shadow-sm); }
.le-empty { padding: 46rpx 0; text-align: center; color: var(--text-secondary); }
.list-item { display: flex; align-items: center; gap: 14rpx; padding: 18rpx 0; border-bottom: 1rpx solid var(--border-light); }
.list-item:last-child { border-bottom: none; }
.list-item.checked .item-name, .list-item.checked .item-amount { color: var(--text-muted); text-decoration: line-through; }
.check { width: 42rpx; height: 42rpx; border-radius: 50%; border: 2rpx solid var(--border); display: flex; align-items: center; justify-content: center; color: #fff; font-size: 22rpx; font-weight: 900; flex-shrink: 0; }
.list-item.checked .check { background: var(--teal); border-color: var(--teal); }
.ingredient-icon { width: 52rpx; height: 52rpx; border-radius: 16rpx; background: var(--teal-bg); display: flex; align-items: center; justify-content: center; flex-shrink: 0; position: relative; }
.ingredient-icon image { width: 30rpx; height: 30rpx; position: relative; z-index: 1; }
.ingredient-icon text { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; font-size: 18rpx; font-weight: 900; color: var(--teal); opacity: .22; }
.item-info { flex: 1; min-width: 0; }
.item-name { font-weight: 900; font-size: 28rpx; color: var(--text); display: block; }
.item-amount { font-size: 24rpx; color: var(--text-secondary); margin-top: 4rpx; display: block; }
.item-actions { display: flex; gap: 14rpx; align-items: center; }
.action-icon { width: 46rpx; height: 46rpx; }
.bottom-actions { margin-top: 24rpx; }
.primary-action { width: 100%; height: 90rpx; background: #23A978; color: #fff !important; border: none; border-radius: var(--radius); font-size: 29rpx; font-weight: 900; display: flex; align-items: center; justify-content: center; box-shadow: var(--shadow-md); line-height: 1; }
.primary-action::after { border: none; }
.plan-action { margin-top: 12rpx; background: linear-gradient(135deg, #173B2E, #23A978) !important; color: #fff !important; }
.intake-action { margin-top: 12rpx; background: linear-gradient(135deg, #8D7AE6, #A996FF) !important; color: #fff !important; }
.secondary-actions { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10rpx; margin-top: 12rpx; }
.secondary-actions button { height: 76rpx; background: #fff !important; color: #58645F !important; border: none; border-radius: var(--radius); font-size: 22rpx; font-weight: 800; display: flex; align-items: center; justify-content: center; gap: 4rpx; box-shadow: var(--shadow-sm); padding: 0 6rpx; line-height: 1; }
.secondary-actions button::after { border: none; }
.btn-icon { width: 34rpx; height: 34rpx; }
.btn-icon.invert { filter: brightness(0) invert(1); margin-right: 8rpx; }
.nutrition-empty { padding: 18rpx 0 6rpx; color: var(--text-muted); font-size: 23rpx; line-height: 1.4; }
</style>
