<template>
  <view class="explore-page">
    <!-- 搜索 -->
    <view class="search-bar">
      <image class="search-icon" src="/static/icons/icon_search.svg" />
      <input class="search-input" v-model="searchText" :placeholder="$t('searchPlaceholder')" placeholder-class="ph" />
    </view>

    <!-- 分类标签 -->
    <scroll-view scroll-x class="cat-scroll" :show-scrollbar="false">
      <view v-for="c in categories" :key="c.key" class="cat-tag" :class="{ active: activeCategory === c.key }" @tap="activeCategory = c.key">
        <image class="cat-icon" :src="`/static/icons/${c.icon}.svg`" />
        <text>{{ c.label }}</text>
      </view>
    </scroll-view>

    <!-- 单列菜谱 Feed -->
    <view class="feed-list">
      <view v-for="item in filteredRecipes" :key="item.recipeId" class="feed-card" @tap="goDetail(item)">
        <view class="feed-emoji">
          <image class="feed-emoji-img" :src="item.imageUrl || '/static/icons/icon_plate.svg'" />
        </view>
        <view class="feed-body">
          <view class="feed-top">
            <text class="feed-title">{{ item.title }}</text>
            <text class="feed-cat" :style="{ background: tagBg(item.category), color: tagFg(item.category) }">{{ catLabel(item.category) }}</text>
          </view>
          <view class="feed-meta">
            <view class="meta-item"><image class="meta-icon" src="/static/icons/icon_calendar.svg" /><text>{{ item.cookTime }}{{ $t('minutes') }}</text></view>
            <view class="meta-item"><image class="meta-icon" src="/static/icons/icon_fire.svg" /><text>{{ item.calories }}{{ $t('kcal') }}</text></view>
            <view class="meta-item"><image class="meta-icon" src="/static/icons/icon_chart.svg" /><text>{{ item.difficulty }}</text></view>
          </view>
        </view>
        <text class="feed-arrow">›</text>
      </view>
    </view>

    <view v-if="filteredRecipes.length === 0" class="empty">
      <image class="empty-icon" src="/static/icons/icon_plate.svg" />
      <text>{{ $t('noRecipesFound') }}</text>
    </view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { getExploreRecipes } from '@/api/index'
import { t } from '@/utils/i18n'

const $t = key => t(key)
const searchText = ref('')
const activeCategory = ref('all')

const categories = [
  { key: 'all', label: $t('allCategories'), icon: 'icon_tag' },
  { key: 'quick', label: $t('quickMeals'), icon: 'icon_flash' },
  { key: 'high_protein', label: $t('highProtein'), icon: 'icon_muscle' },
  { key: 'low_fat', label: $t('lowFat'), icon: 'icon_leaf' },
  { key: 'vegetarian', label: $t('vegetarian'), icon: 'icon_leaf' },
  { key: 'seafood', label: $t('seafood'), icon: 'icon_fish' },
  { key: 'comfort', label: $t('comfortFood'), icon: 'icon_plate' }
]

const filteredRecipes = computed(() => {
  let list = getExploreRecipes()
  if (activeCategory.value !== 'all') list = list.filter(r => r.category === activeCategory.value)
  if (searchText.value.trim()) {
    const kw = searchText.value.trim().toLowerCase()
    list = list.filter(r => r.title.toLowerCase().includes(kw))
  }
  return list
})

function tagBg(cat) { const m = { high_protein: '#EEF1FE', low_fat: '#E9F9EE', quick: '#FFF5E6', vegetarian: '#E9F9EE', seafood: '#EDF9FE', comfort: '#F6EEFC' }; return m[cat] || '#F2F3F7' }
function tagFg(cat) { const m = { high_protein: '#4F6EF7', low_fat: '#34C759', quick: '#4F6EF7', vegetarian: '#34C759', seafood: '#5AC8FA', comfort: '#6C5CE7' }; return m[cat] || '#6A6E7B' }
function catLabel(cat) { const m = { high_protein: $t('highProtein'), low_fat: $t('lowFat'), quick: $t('quickMeals'), vegetarian: $t('vegetarian'), seafood: $t('seafood'), comfort: $t('comfortFood') }; return m[cat] || cat }
function goDetail(item) { uni.navigateTo({ url: `/pages/recipe-detail/recipe-detail?recipeId=${item.recipeId}&title=${encodeURIComponent(item.title)}` }) }
</script>

<style scoped>
.explore-page { min-height: 100vh; background: var(--bg); padding: 16rpx 24rpx; overflow-x: hidden; }

/* 搜索 */
.search-bar {
  display: flex; align-items: center; background: #fff; border-radius: var(--radius-full);
  padding: 0 18rpx; height: 68rpx; margin-bottom: 14rpx; box-shadow: var(--shadow-sm);
}
 .search-icon { width: 36rpx; height: 36rpx; margin-right: 8rpx; }
.search-input { flex: 1; font-size: 26rpx; color: var(--text); height: 100%; }
.ph { color: var(--text-placeholder); }

/* 分类 */
.cat-scroll { white-space: nowrap; margin-bottom: 16rpx; }
.cat-tag {
  display: inline-flex; align-items: center; gap: 6rpx;
  padding: 12rpx 22rpx; border-radius: var(--radius-full);
  font-size: 24rpx; font-weight: 500; margin-right: 10rpx;
  background: #fff; color: var(--text-secondary);
  box-shadow: var(--shadow-sm);
  transition: all var(--fast) ease;
}
.cat-icon { font-size: 24rpx; transition: transform var(--fast) ease; }
.cat-tag.active {
  background: var(--blue); color: #fff; font-weight: 600;
  box-shadow: 0 2px 12px rgba(79,110,247,0.25);
  transform: scale(1.05);
}
.cat-tag.active .cat-icon { transform: scale(1.15); }

/* 单列 Feed */
.feed-list { display: flex; flex-direction: column; gap: 12rpx; }
.feed-card {
  display: flex; align-items: center; background: #fff; border-radius: var(--radius);
  padding: 20rpx 24rpx; box-shadow: var(--shadow-sm);
}
.feed-emoji {
  width: 80rpx; height: 80rpx; background: var(--bg); border-radius: var(--radius);
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
 .feed-emoji-img { width: 64rpx; height: 64rpx; border-radius: 10rpx; object-fit: cover; }
 .cat-icon { width: 28rpx; height: 28rpx; margin-right: 6rpx; }
 .meta-item { display: flex; align-items: center; gap: 6rpx; color: var(--text-muted); font-size: 22rpx; }
 .meta-icon { width: 22rpx; height: 22rpx; }
 .empty-icon { width: 72rpx; height: 72rpx; margin-bottom: 16rpx; }
.feed-body { flex: 1; margin-left: 18rpx; display: flex; flex-direction: column; gap: 10rpx; }
.feed-top { display: flex; align-items: center; gap: 10rpx; }
.feed-title { font-size: 28rpx; font-weight: 700; color: var(--text); flex: 1; }
.feed-cat { font-size: 18rpx; padding: 3rpx 12rpx; border-radius: var(--radius-full); font-weight: 500; white-space: nowrap; }
.feed-meta { display: flex; gap: 16rpx; font-size: 22rpx; color: var(--text-muted); }
.feed-arrow { font-size: 32rpx; color: var(--text-muted); margin-left: 4rpx; }

.empty { display: flex; flex-direction: column; align-items: center; padding-top: 100rpx; color: var(--text-muted); }
.empty-icon { font-size: 72rpx; margin-bottom: 16rpx; }
</style>
