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
        <text class="section-action" @tap="addItem">+ {{ $t('add') }}</text>
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
        </view>
        <view class="item-info">
          <text class="item-name">{{ item.name || '-' }}</text>
          <text class="item-amount">{{ item.amount || '-' }}</text>
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
      <view class="secondary-actions">
        <button @tap="exportMarkdown"><image class="btn-icon" src="/static/icons/icon_export.svg" mode="widthFix" />{{ $t('exportMarkdown') }}</button>
        <button @tap="shareToSocial"><image class="btn-icon" src="/static/icons/icon_share.svg" mode="widthFix" />{{ $t('shareToSocial') }}</button>
        <button @tap="goBack"><image class="btn-icon" src="/static/icons/icon_back.svg" mode="widthFix" />{{ $t('back') }}</button>
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

const $t = key => t(key)
const isLoading = ref(true)
const recipes = ref([])
const editingList = ref([])
const checkedItems = ref({})
const errorNotice = ref('')
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

function dedupeIngredients(list) {
  const map = new Map()
  list.forEach(item => {
    const key = (item.name || '').trim().toLowerCase()
    if (!key) return
    if (!map.has(key)) {
      map.set(key, { ...item, name: item.name.trim(), amount: item.amount || '' })
    }
  })
  return Array.from(map.values())
}

onLoad(async (options) => {
  try {
    if (options && options.recipes) {
      const parsed = JSON.parse(decodeURIComponent(options.recipes))
      if (parsed.length > 0 && (parsed[0].recipeId || parsed[0].recipe_id)) {
        recipes.value = parsed
        const ids = parsed.map(r => r.recipeId || r.recipe_id)
        try {
          const merged = await ApiService.mergeShoppingList(ids)
          editingList.value = dedupeIngredients(merged)
        } catch (e) {
          errorNotice.value = '后端清单合并暂未连通，已根据食谱生成本地演示清单。'
          editingList.value = dedupeIngredients([
            { name: '牛肉', amount: '300g', nameEn: 'Beef' },
            { name: '西兰花', amount: '200g', nameEn: 'Broccoli' },
            { name: '蒜蓉', amount: '10g', nameEn: 'Minced Garlic' }
          ])
        }
      } else if (parsed.length > 0 && parsed[0].name) {
        recipes.value = [{ title: 'AI推荐', recipeId: 'r_ai' }]
        editingList.value = dedupeIngredients(parsed)
      }
    }
  } catch (e) {
    editingList.value = dedupeIngredients([
      { name: '牛肉', amount: '300g', nameEn: 'Beef' },
      { name: '蒜蓉', amount: '10g', nameEn: 'Minced Garlic' }
    ])
  }
  if (recipes.value.length === 0) recipes.value = [{ title: '示例菜谱', recipeId: 'r_101' }]
  isLoading.value = false
})

function addItem() { editingList.value.push({ name: '', amount: '' }) }
function toggleChecked(idx) { checkedItems.value[idx] = !checkedItems.value[idx]; checkedItems.value = { ...checkedItems.value } }
function editItem(idx) {
  const item = editingList.value[idx]
  uni.showModal({
    title: $t('editIngredient'),
    editable: true,
    placeholderText: item.name + ' - ' + item.amount,
    success: (res) => {
      if (res.confirm && res.content) {
        const parts = res.content.split('-').map(s => s.trim())
        editingList.value[idx] = { name: parts[0] || item.name, amount: parts[1] || item.amount }
        editingList.value = dedupeIngredients(editingList.value)
      }
    }
  })
}
function removeItem(idx) { editingList.value.splice(idx, 1) }
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
function ingredientIcon(item) {
  const name = `${item?.name || ''}${item?.nameEn || ''}`.toLowerCase()
  if (name.includes('牛') || name.includes('肉') || name.includes('beef') || name.includes('chicken')) return '/static/icons/icon_muscle.svg'
  if (name.includes('鱼') || name.includes('虾') || name.includes('fish') || name.includes('seafood')) return '/static/icons/icon_fish.svg'
  if (name.includes('油') || name.includes('oil') || name.includes('olive')) return '/static/icons/icon_olive.svg'
  return '/static/icons/icon_leaf.svg'
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
.list-section { background: #fff; border-radius: var(--radius); padding: 20rpx; box-shadow: var(--shadow-sm); }
.le-empty { padding: 46rpx 0; text-align: center; color: var(--text-secondary); }
.list-item { display: flex; align-items: center; gap: 14rpx; padding: 18rpx 0; border-bottom: 1rpx solid var(--border-light); }
.list-item:last-child { border-bottom: none; }
.list-item.checked .item-name, .list-item.checked .item-amount { color: var(--text-muted); text-decoration: line-through; }
.check { width: 42rpx; height: 42rpx; border-radius: 50%; border: 2rpx solid var(--border); display: flex; align-items: center; justify-content: center; color: #fff; font-size: 22rpx; font-weight: 900; flex-shrink: 0; }
.list-item.checked .check { background: var(--teal); border-color: var(--teal); }
.ingredient-icon { width: 52rpx; height: 52rpx; border-radius: 16rpx; background: var(--teal-bg); display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.ingredient-icon image { width: 30rpx; height: 30rpx; }
.item-info { flex: 1; min-width: 0; }
.item-name { font-weight: 900; font-size: 28rpx; color: var(--text); display: block; }
.item-amount { font-size: 24rpx; color: var(--text-secondary); margin-top: 4rpx; display: block; }
.item-actions { display: flex; gap: 14rpx; align-items: center; }
.action-icon { width: 46rpx; height: 46rpx; }
.bottom-actions { margin-top: 24rpx; }
.primary-action { width: 100%; height: 90rpx; background: var(--teal); color: #fff; border: none; border-radius: var(--radius); font-size: 29rpx; font-weight: 900; display: flex; align-items: center; justify-content: center; box-shadow: var(--shadow-md); }
.secondary-actions { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10rpx; margin-top: 12rpx; }
.secondary-actions button { height: 76rpx; background: #fff; color: var(--text-secondary); border: none; border-radius: var(--radius); font-size: 22rpx; font-weight: 800; display: flex; align-items: center; justify-content: center; gap: 4rpx; box-shadow: var(--shadow-sm); padding: 0 6rpx; }
.btn-icon { width: 34rpx; height: 34rpx; }
.btn-icon.invert { filter: brightness(0) invert(1); margin-right: 8rpx; }
</style>
