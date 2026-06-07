<template>
  <view class="explore-page">
    <view class="page-head">
      <text class="page-title">探索菜谱</text>
      <text class="page-sub">按目标、时间和营养偏好找到下一餐</text>
    </view>

    <view class="search-bar">
      <image class="search-icon" src="/static/icons/icon_search.svg" />
      <input class="search-input" v-model="searchText" :placeholder="$t('searchPlaceholder')" placeholder-class="ph" />
    </view>

    <view class="recipe-stats">
      <view><text>{{ recipes.length }}</text><text>真实菜谱</text></view>
      <view><text>{{ highProteinCount }}</text><text>高蛋白</text></view>
      <view><text>{{ microRichCount }}</text><text>微量亮点</text></view>
    </view>

    <view v-if="errorNotice" class="notice-card">
      <image src="/static/icons/icon_flash.svg" mode="aspectFit" />
      <text>{{ errorNotice }}</text>
    </view>

    <scroll-view scroll-x class="cat-scroll" :show-scrollbar="false">
      <view v-for="c in categories" :key="c.key" class="cat-tag" :class="{ active: activeCategory === c.key }" @tap="activeCategory = c.key">
        <image class="cat-icon" :src="`/static/icons/${c.icon}.svg`" />
        <text>{{ c.label }}</text>
      </view>
    </scroll-view>

    <view class="feed-list">
      <view v-for="item in filteredRecipes" :key="item.recipeId" class="feed-card" @tap="goDetail(item)">
        <view class="feed-visual" :class="item.category">
          <text>{{ item.imageEmoji || '食' }}</text>
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
          <view class="micro-row">
            <text v-for="micro in (item.micro_highlights || []).slice(0, 3)" :key="micro">{{ micro }}</text>
          </view>
        </view>
        <text class="feed-arrow">›</text>
      </view>
    </view>

    <view v-if="isLoading" class="empty">
      <image class="empty-icon" src="/static/icons/icon_plate.svg" />
      <text>正在从后端加载菜谱...</text>
    </view>

    <view v-else-if="filteredRecipes.length === 0" class="empty">
      <image class="empty-icon" src="/static/icons/icon_plate.svg" />
      <text>{{ $t('noRecipesFound') }}</text>
    </view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { ApiService } from '@/api/index'
import { t } from '@/utils/i18n'

const $t = key => t(key)
const searchText = ref('')
const activeCategory = ref('all')
const recipes = ref([])
const isLoading = ref(true)
const errorNotice = ref('')

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
  let list = recipes.value
  if (activeCategory.value !== 'all') list = list.filter(r => r.category === activeCategory.value)
  if (searchText.value.trim()) {
    const kw = searchText.value.trim().toLowerCase()
    list = list.filter(r => r.title.toLowerCase().includes(kw))
  }
  return list
})
const highProteinCount = computed(() => recipes.value.filter(r => r.category === 'high_protein' || (r.tags || []).includes('high_protein')).length)
const microRichCount = computed(() => recipes.value.filter(r => (r.micro_highlights || []).length > 0).length)

onLoad(async () => {
  try {
    recipes.value = await ApiService.getRecipes()
  } catch (e) {
    errorNotice.value = '后端菜谱接口暂不可用，未使用本地 mock 数据。'
    recipes.value = []
  } finally {
    isLoading.value = false
  }
})

function tagBg(cat) { const m = { high_protein: 'var(--red-bg)', low_fat: 'var(--green-bg)', quick: 'var(--amber-bg)', vegetarian: 'var(--green-bg)', seafood: 'var(--blue-bg)', comfort: 'var(--purple-bg)' }; return m[cat] || 'var(--border-light)' }
function tagFg(cat) { const m = { high_protein: 'var(--tomato)', low_fat: 'var(--teal)', quick: '#9A651B', vegetarian: 'var(--teal)', seafood: 'var(--blue)', comfort: 'var(--berry)' }; return m[cat] || 'var(--text-secondary)' }
function catLabel(cat) { const m = { high_protein: $t('highProtein'), low_fat: $t('lowFat'), quick: $t('quickMeals'), vegetarian: $t('vegetarian'), seafood: $t('seafood'), comfort: $t('comfortFood'), balanced: '均衡' }; return m[cat] || cat }
function goDetail(item) { uni.navigateTo({ url: `/pages/recipe-detail/recipe-detail?recipeId=${item.recipeId}&title=${encodeURIComponent(item.title)}` }) }
</script>

<style scoped>
.explore-page {
  min-height: 100vh;
  background:
    radial-gradient(circle at 85% 0%, rgba(75,167,200,.12), transparent 30%),
    linear-gradient(180deg, #F9FCFA 0%, var(--bg) 44%);
  padding: 28rpx;
  overflow-x: hidden;
}
.page-head { margin-bottom: 22rpx; }
.page-title { display: block; font-size: 44rpx; line-height: 1.12; font-weight: 950; color: var(--text); }
.page-sub { display: block; margin-top: 8rpx; font-size: 24rpx; color: var(--text-secondary); }
.search-bar { display: flex; align-items: center; background: rgba(255,255,255,.94); border-radius: var(--radius-full); padding: 0 20rpx; height: 78rpx; margin-bottom: 16rpx; box-shadow: var(--shadow-sm), var(--hairline); backdrop-filter: blur(10rpx); }
.search-icon { width: 36rpx; height: 36rpx; margin-right: 10rpx; }
.search-input { flex: 1; font-size: 26rpx; color: var(--text); height: 100%; }
.ph { color: var(--text-placeholder); }
.recipe-stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12rpx; margin-bottom: 16rpx; }
.recipe-stats view { background: rgba(255,255,255,.94); border-radius: var(--radius); padding: 17rpx; box-shadow: var(--shadow-sm), var(--hairline); }
.recipe-stats text:first-child { display: block; color: var(--text); font-size: 32rpx; font-weight: 900; line-height: 1; }
.recipe-stats text:last-child { display: block; margin-top: 8rpx; color: var(--text-muted); font-size: 20rpx; }
.notice-card { display: flex; align-items: center; gap: 12rpx; background: var(--amber-bg); color: #9A651B; border-radius: var(--radius); padding: 16rpx 18rpx; margin-bottom: 18rpx; font-size: 23rpx; line-height: 1.45; box-shadow: var(--shadow-sm); }
.notice-card image { width: 30rpx; height: 30rpx; flex-shrink: 0; }
.cat-scroll { white-space: nowrap; margin-bottom: 20rpx; }
.cat-tag { display: inline-flex; align-items: center; gap: 8rpx; padding: 13rpx 22rpx; border-radius: var(--radius-full); font-size: 24rpx; font-weight: 850; margin-right: 12rpx; background: rgba(255,255,255,.92); color: var(--text-secondary); box-shadow: var(--shadow-xs), var(--hairline); transition: all var(--fast) ease; }
.cat-tag.active { background: linear-gradient(135deg, var(--ink-green), #245445); color: #fff; transform: translateY(-2rpx); box-shadow: 0 14rpx 28rpx rgba(23,59,46,.16); }
.cat-icon { width: 28rpx; height: 28rpx; }
.cat-tag.active .cat-icon { filter: brightness(0) invert(1); }
.feed-list { display: flex; flex-direction: column; gap: 15rpx; }
.feed-card { display: flex; align-items: center; background: linear-gradient(145deg, #FFFFFF, #F9FCFA); border-radius: var(--radius-md); padding: 18rpx; box-shadow: var(--shadow-sm), var(--hairline); animation: soft-pop .28s var(--ease) both; }
.feed-card:active { transform: translateY(-2rpx); box-shadow: var(--shadow-md), var(--hairline); }
.feed-visual { width: 92rpx; height: 92rpx; border-radius: 27rpx; display: flex; align-items: center; justify-content: center; flex-shrink: 0; font-size: 38rpx; background: var(--green-bg); box-shadow: inset 0 0 0 1rpx rgba(255,255,255,.6); }
.feed-visual.high_protein { background: var(--red-bg); }
.feed-visual.low_fat, .feed-visual.vegetarian { background: var(--green-bg); }
.feed-visual.quick { background: var(--amber-bg); }
.feed-visual.seafood { background: var(--blue-bg); }
.feed-visual.comfort { background: var(--purple-bg); }
.feed-body { flex: 1; margin-left: 18rpx; display: flex; flex-direction: column; gap: 10rpx; min-width: 0; }
.feed-top { display: flex; align-items: center; gap: 10rpx; }
.feed-title { font-size: 29rpx; font-weight: 950; color: var(--text); flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.feed-cat { font-size: 19rpx; padding: 5rpx 12rpx; border-radius: var(--radius-full); font-weight: 800; white-space: nowrap; }
.feed-meta { display: flex; gap: 14rpx; flex-wrap: wrap; }
.meta-item { display: flex; align-items: center; gap: 5rpx; color: var(--text-muted); font-size: 21rpx; }
.meta-icon { width: 22rpx; height: 22rpx; }
.micro-row { display: flex; flex-wrap: wrap; gap: 8rpx; }
.micro-row text { background: var(--blue-bg); color: var(--blue); border-radius: var(--radius-full); padding: 5rpx 11rpx; font-size: 19rpx; font-weight: 850; box-shadow: inset 0 0 0 1rpx rgba(75,167,200,.08); }
.feed-arrow { font-size: 34rpx; color: var(--text-muted); margin-left: 6rpx; }
.empty { display: flex; flex-direction: column; align-items: center; padding-top: 120rpx; color: var(--text-muted); font-size: 26rpx; }
.empty-icon { width: 78rpx; height: 78rpx; margin-bottom: 16rpx; }
</style>
