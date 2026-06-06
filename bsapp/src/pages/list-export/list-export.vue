<template>
  <view class="le-page" v-if="!isLoading">
    <!-- 头部 -->
    <view class="le-header">
      <text class="le-title">{{ $t('taskAutomation') }}</text>
      <text class="le-desc">{{ $t('mergeDesc') }}</text>
      <view class="le-success-banner">
        <text>✅ {{ $t('mergedTip', { n1: recipeCount, n2: uniqueIngredientCount }) }}</text>
      </view>
    </view>

    <!-- 关联食谱 -->
    <view class="section">
      <text class="section-label">{{ $t('relatedRecipes') }}</text>
      <view class="le-tags">
        <text
          v-for="(r, idx) in recipes"
          :key="idx"
          class="le-recipe-tag"
        >{{ r.title }}</text>
      </view>
    </view>

    <!-- 食材清单 -->
    <view class="section">
      <view class="section-header">
        <text class="section-label">{{ $t('mergedList') }}</text>
        <text class="section-action" @tap="addItem">+ {{ $t('add') }}</text>
      </view>

      <view v-if="editingList.length === 0" class="le-empty">
        <text>{{ $t('noIngredient') }}</text>
      </view>

      <view
        v-for="(item, idx) in editingList"
        :key="idx"
        class="le-item"
      >
        <view class="le-item-info">
          <text class="le-item-name">{{ item.name || '-' }}</text>
          <text class="le-item-amount">{{ item.amount || '-' }}</text>
        </view>
        <view class="le-item-actions">
          <image class="action-icon" src="/static/icons/icon_edit.svg" @tap="editItem(idx)" mode="widthFix" />
          <image class="action-icon delete" src="/static/icons/icon_delete.svg" @tap="removeItem(idx)" mode="widthFix" />
        </view>
      </view>
    </view>

    <!-- 操作按钮 -->
    <view class="le-buttons">
      <button class="le-btn-primary btn-gradient" @tap="copyToClipboard">
        <image class="btn-icon" src="/static/icons/icon_copy.svg" mode="widthFix" />
        {{ $t('copyToClipboard') }}
      </button>
      <button class="le-btn-secondary" @tap="exportMarkdown">
        <image class="btn-icon" src="/static/icons/icon_export.svg" mode="widthFix" />
        {{ $t('exportMarkdown') }}
      </button>
      <button class="le-btn-white" @tap="shareToSocial">
        <image class="btn-icon" src="/static/icons/icon_share.svg" mode="widthFix" />
        {{ $t('shareToSocial') }}
      </button>
      <button class="le-btn-white" @tap="goBack">
        <image class="btn-icon" src="/static/icons/icon_back.svg" mode="widthFix" />
        {{ $t('back') }}
      </button>
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
const recipeCount = computed(() => recipes.value.length)
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
      // 兼容两种数据格式：recipe对象数组 或 直接的购物清单数组
      if (parsed.length > 0 && (parsed[0].recipeId || parsed[0].recipe_id)) {
        recipes.value = parsed
        const ids = parsed.map(r => r.recipeId || r.recipe_id)
        const merged = await ApiService.mergeShoppingList(ids)
        editingList.value = dedupeIngredients(merged)
      } else if (parsed.length > 0 && parsed[0].name) {
        // 购物清单数据（从AI助手传来）
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

function addItem() {
  editingList.value.push({ name: '', amount: '' })
}

function editItem(idx) {
  const item = editingList.value[idx]
  uni.showModal({
    title: $t('editIngredient'),
    editable: true,
    placeholderText: item.name + ' - ' + item.amount,
    success: (res) => {
      if (res.confirm && res.content) {
        const parts = res.content.split('-').map(s => s.trim())
        editingList.value[idx] = {
          name: parts[0] || item.name,
          amount: parts[1] || item.amount
        }
        editingList.value = dedupeIngredients(editingList.value)
      }
    }
  })
}

function removeItem(idx) {
  editingList.value.splice(idx, 1)
}

function generateText() {
  let text = '=== ByteSavor 购物清单 ===\n\n'
  editingList.value.forEach(item => {
    text += `□ ${item.name} - ${item.amount}\n`
  })
  text += '\n由 ByteSavor AI 智能生成'
  return text
}

function copyToClipboard() {
  uni.setClipboardData({
    data: generateText(),
    success: () => uni.showToast({ title: $t('copied'), icon: 'success' })
  })
}

function exportMarkdown() {
  let md = '# ByteSavor 购物清单\n\n## 关联食谱\n'
  recipes.value.forEach(r => {
    md += `- ${r.title} (匹配度 ${((r.matchScore || 0) * 100).toFixed(0)}%)\n`
  })
  md += '\n## 合并后的食材\n'
  editingList.value.forEach(item => {
    md += `- [ ] ${item.name} - ${item.amount}\n`
  })
  md += '\n---\n*由 ByteSavor 智能厨房助手生成*'

  uni.showModal({
    title: 'Markdown',
    content: md,
    confirmText: $t('copyToClipboard'),
    success: (res) => {
      if (res.confirm) {
        uni.setClipboardData({
          data: md,
          success: () => uni.showToast({ title: $t('copied'), icon: 'success' })
        })
      }
    }
  })
}

function shareToSocial() {
  uni.showActionSheet({
    itemList: [$t('wechat'), $t('xiaohongshu')],
    success: () => {
      uni.showToast({ title: '分享功能待实现', icon: 'none' })
    }
  })
}

function goBack() {
  uni.navigateBack()
}
</script>

<style scoped>
.le-page { min-height: 100vh; background: var(--bg-color); padding: 24rpx; }
.loading-page { display: flex; align-items: center; justify-content: center; height: 100vh; }
.le-header { margin-bottom: 32rpx; }
.le-title { font-size: 44rpx; font-weight: bold; color: var(--accent); display: block; }
.le-desc { font-size: 26rpx; color: var(--text-secondary); margin-top: 8rpx; display: block; }
.le-success-banner {
  background: var(--success-bg);
  border: 1rpx solid #C8E6C9;
  border-radius: 12rpx;
  padding: 20rpx;
  margin-top: 16rpx;
  font-size: 24rpx;
  color: var(--success);
}
.section { margin-bottom: 28rpx; }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12rpx; }
.section-label { font-size: 30rpx; font-weight: bold; color: var(--text-color); }
.section-action { font-size: 26rpx; color: var(--accent); }
.le-tags { display: flex; flex-wrap: wrap; gap: 12rpx; }
.le-recipe-tag {
  background: var(--accent-bg);
  color: var(--accent);
  font-size: 24rpx;
  padding: 8rpx 20rpx;
  border-radius: 20rpx;
}
.le-empty { padding: 40rpx 0; text-align: center; color: var(--text-secondary); }
.le-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(180deg, rgba(255,255,255,0.9), rgba(250,250,255,0.85));
  border-radius: 16rpx;
  padding: 22rpx 24rpx;
  margin-bottom: 14rpx;
  box-shadow: 0 8rpx 20rpx rgba(12,15,40,0.05);
}
.le-item-name { font-weight: bold; font-size: 28rpx; display: block; }
.le-item-amount { font-size: 24rpx; color: var(--text-secondary); }
.le-item-actions { display: flex; gap: 18rpx; align-items: center; }
.action-icon { width: 56rpx; height: 56rpx; }
.action-icon.delete { opacity: 0.95 }
.le-buttons { display: flex; flex-direction: column; gap: 16rpx; }
.le-btn-primary {
  width: 100%; height: 84rpx;
  background: linear-gradient(135deg, #06B6D4, #7C3AED);
  color: #fff; border: none;
  border-radius: 16rpx; font-size: 28rpx; font-weight: 700;
  display: flex; align-items: center; gap: 16rpx; padding: 0 20rpx;
}
.le-btn-secondary {
  width: 100%; height: 84rpx;
  background: #fff; color: #06B6D4;
  border: 1.5px solid rgba(6,182,212,0.18);
  border-radius: 16rpx; font-size: 28rpx; font-weight: 600;
  display: flex; align-items: center; gap: 12rpx; padding: 0 20rpx;
}
.le-btn-white {
  width: 100%; height: 84rpx;
  background: #fff; color: var(--text-secondary);
  border: 1px solid rgba(16,24,40,0.06);
  border-radius: 16rpx; font-size: 28rpx; display: flex; align-items: center; gap: 12rpx; padding: 0 20rpx;
}

.btn-icon { width: 48rpx; height: 48rpx; }
</style>
