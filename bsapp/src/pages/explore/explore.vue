<template>
  <view class="explore-page">
    <view class="page-head">
      <text class="page-title">菜谱库</text>
      <text class="page-sub">搜索全部菜谱，按当前库存清点缺少食材</text>
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

    <view v-if="featuredRecipe" class="featured-recipe" @tap="goDetail(featuredRecipe)">
      <view class="featured-copy">
        <text class="featured-label">今日精选</text>
        <text class="featured-title">{{ featuredRecipe.title }}</text>
        <text class="featured-meta">{{ featuredRecipe.cookTime }}分钟 · {{ featuredRecipe.calories }}千卡 · {{ catLabel(featuredRecipe.category) }}</text>
        <view class="featured-micro">
          <text v-for="micro in (featuredRecipe.micro_highlights || []).slice(0, 3)" :key="micro">{{ micro }}</text>
        </view>
      </view>
      <view class="featured-visual" :class="featuredRecipe.category">
        <text>{{ featuredRecipe.imageEmoji || '食' }}</text>
      </view>
    </view>

    <scroll-view scroll-x class="cat-scroll" :show-scrollbar="false">
      <view v-for="c in categories" :key="c.key" class="cat-tag" :class="{ active: activeCategory === c.key }" @tap="activeCategory = c.key">
        <image class="cat-icon" :src="`/static/icons/${c.icon}.svg`" />
        <text>{{ c.label }}</text>
      </view>
    </scroll-view>

    <view class="feed-list">
      <view v-for="item in visibleRecipes" :key="item.recipeId" class="feed-card" @tap="goDetail(item)">
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
          <view v-if="recipeExplainChips(item).length" class="explain-row">
            <text v-for="chip in recipeExplainChips(item)" :key="chip">{{ chip }}</text>
          </view>
        </view>
        <view class="feed-actions">
          <button class="icon-action" :class="{ active: item.favorited_by_me }" @tap.stop="favoriteRecipe(item)">
            <image :src="item.favorited_by_me ? '/static/icons/icon_heart.svg' : '/static/icons/icon_heart_outline.svg'" mode="aspectFit" />
            <text>{{ item.favorited_by_me ? '已藏' : '收藏' }}</text>
          </button>
          <button class="dark" @tap.stop="checkRecipe(item)">清点</button>
          <button class="accent" @tap.stop="planRecipeFromExplore(item)">计划</button>
        </view>
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

    <button v-if="visibleRecipes.length < filteredRecipes.length" class="load-more" @tap="visibleLimit += 40">
      显示更多 {{ filteredRecipes.length - visibleRecipes.length }} 道
    </button>
  </view>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { ApiService } from '@/api/index'
import { t } from '@/utils/i18n'
import { searchRecipes } from '@/utils/recipe-search'

const $t = key => t(key)
const searchText = ref('')
const activeCategory = ref('all')
const recipes = ref([])
const favoriteIds = ref(new Set())
const userPreferences = ref([])
const isLoading = ref(true)
const errorNotice = ref('')
const visibleLimit = ref(60)

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
    list = searchRecipes(list, searchText.value.trim(), { preferences: userPreferences.value })
  }
  return list
})

const visibleRecipes = computed(() => filteredRecipes.value.slice(0, visibleLimit.value))
const highProteinCount = computed(() => recipes.value.filter(r => r.category === 'high_protein' || (r.tags || []).includes('high_protein')).length)
const microRichCount = computed(() => recipes.value.filter(r => (r.micro_highlights || []).length > 0).length)
const featuredRecipe = computed(() => filteredRecipes.value[0] || recipes.value[0] || null)

watch([searchText, activeCategory], () => {
  visibleLimit.value = 60
})

onLoad(async () => {
  try {
    const [recipeList] = await Promise.all([
      ApiService.getRecipes(),
      loadFavoriteIds(),
      loadUserPreferences()
    ])
    recipes.value = recipeList.map(markFavorite)
  } catch (e) {
    errorNotice.value = '后端菜谱接口暂不可用，未使用本地 mock 数据。'
    recipes.value = []
  } finally {
    isLoading.value = false
  }
})

async function loadFavoriteIds() {
  try {
    const favorites = await ApiService.getFavorites()
    favoriteIds.value = new Set(
      favorites
        .filter(f => f.target_type === 'system_recipe')
        .map(f => String(f.target_id))
    )
  } catch (e) {
    favoriteIds.value = new Set()
  }
}

async function loadUserPreferences() {
  try {
    const profile = await ApiService.getUserProfile()
    userPreferences.value = profile.preferences || []
  } catch (e) {
    userPreferences.value = []
  }
}

function recipeKey(item) {
  return String(item.recipeId || item.recipe_id || '')
}

function markFavorite(item) {
  return { ...item, favorited_by_me: favoriteIds.value.has(recipeKey(item)) }
}

function tagBg(cat) { const m = { high_protein: 'var(--red-bg)', low_fat: 'var(--green-bg)', quick: 'var(--amber-bg)', vegetarian: 'var(--green-bg)', seafood: 'var(--blue-bg)', comfort: 'var(--purple-bg)' }; return m[cat] || 'var(--border-light)' }
function tagFg(cat) { const m = { high_protein: 'var(--tomato)', low_fat: 'var(--teal)', quick: '#9A651B', vegetarian: 'var(--teal)', seafood: 'var(--blue)', comfort: 'var(--berry)' }; return m[cat] || 'var(--text-secondary)' }
function catLabel(cat) { const m = { high_protein: $t('highProtein'), low_fat: $t('lowFat'), quick: $t('quickMeals'), vegetarian: $t('vegetarian'), seafood: $t('seafood'), comfort: $t('comfortFood'), balanced: '均衡' }; return m[cat] || cat }
function goDetail(item) { uni.navigateTo({ url: `/pages/recipe-detail/recipe-detail?recipeId=${item.recipeId}&title=${encodeURIComponent(item.title)}` }) }
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
function recipeExplainChips(item) {
  const meta = item?._meta || {}
  const chips = []
  const matched = listFromMeta(meta.matched_ingredients || item?.matched_ingredients).slice(0, 2)
  const missing = listFromMeta(meta.missing_ingredients || item?.missing_ingredients).slice(0, 2)
  const purchase = listFromMeta(meta.purchase_suggestions || item?.purchase_suggestions).slice(0, 2)
  const prefs = listFromMeta(meta.preference_matches || item?.preference_matches || item?.matched_preferences).slice(0, 2)
  if (matched.length) chips.push(`已用 ${matched.join('、')}`)
  if (missing.length) chips.push(`缺 ${missing.join('、')}`)
  if (purchase.length) chips.push(`补买 ${purchase.join('、')}`)
  if (prefs.length) chips.push(`偏好 ${prefs.join('、')}`)
  if (item?.llm_reranked) chips.push('AI重排')
  return chips.slice(0, 5)
}
async function favoriteRecipe(item) {
  try {
    const id = recipeKey(item)
    if (!id) return
    if (item.favorited_by_me) {
      await ApiService.removeFavorite('system_recipe', id)
      favoriteIds.value.delete(id)
      item.favorited_by_me = false
      uni.showToast({ title: '已取消收藏', icon: 'none' })
    } else {
      await ApiService.addFavorite('system_recipe', id, item)
      favoriteIds.value.add(id)
      item.favorited_by_me = true
      uni.showToast({ title: '已收藏', icon: 'success' })
    }
  } catch (e) {
    uni.showToast({ title: e.message || '收藏失败', icon: 'none' })
  }
}
function checkRecipe(item) {
  uni.navigateTo({ url: `/pages/recipe-checker/recipe-checker?targetType=system_recipe&targetId=${item.recipeId || item.recipe_id}` })
}
async function planRecipeFromExplore(item) {
  const recipe = item.recipe || item
  const slotLabels = ['早餐', '午餐', '晚餐', '加餐']
  const slotKeys = ['breakfast', 'lunch', 'dinner', 'snack']
  uni.showActionSheet({
    itemList: slotLabels,
    success: async (res) => {
      const slot = slotKeys[res.tapIndex] || 'lunch'
      try {
        await ApiService.planMeal(slot, recipe, (recipe.ingredients || []), [])
        uni.showToast({ title: `已加入${slotLabels[res.tapIndex]}计划`, icon: 'success' })
      } catch (e) {
        uni.showToast({ title: e.message || '加入失败', icon: 'none' })
      }
    }
  })
}
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
.featured-recipe {
  min-height: 238rpx;
  margin-bottom: 18rpx;
  padding: 26rpx;
  border-radius: 38rpx;
  color: #fff;
  background:
    radial-gradient(circle at 88% 18%, rgba(255,255,255,.22), transparent 32%),
    linear-gradient(145deg, #173B2E, #245445);
  box-shadow: 0 24rpx 58rpx rgba(23,59,46,.20);
  display: flex;
  align-items: center;
  gap: 18rpx;
  overflow: hidden;
  position: relative;
  animation: soft-pop .34s var(--ease) both;
}
.featured-recipe::after {
  content: "";
  position: absolute;
  inset: auto -58rpx -78rpx auto;
  width: 220rpx;
  height: 220rpx;
  border-radius: 50%;
  background: rgba(255,255,255,.08);
}
.featured-copy { flex: 1; min-width: 0; position: relative; z-index: 1; }
.featured-label { display: block; font-size: 22rpx; font-weight: 850; color: rgba(255,255,255,.68); }
.featured-title { display: block; margin-top: 10rpx; font-size: 36rpx; line-height: 1.2; font-weight: 950; color: #fff; }
.featured-meta { display: block; margin-top: 10rpx; font-size: 22rpx; color: rgba(255,255,255,.74); }
.featured-micro { display: flex; flex-wrap: wrap; gap: 8rpx; margin-top: 16rpx; }
.featured-micro text { padding: 6rpx 12rpx; border-radius: var(--radius-full); background: rgba(255,255,255,.14); color: #fff; font-size: 20rpx; font-weight: 850; }
.featured-visual { width: 118rpx; height: 118rpx; border-radius: 34rpx; flex-shrink: 0; display: flex; align-items: center; justify-content: center; font-size: 52rpx; background: rgba(255,255,255,.16); box-shadow: inset 0 0 0 1rpx rgba(255,255,255,.22); position: relative; z-index: 1; }
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
.feed-body { flex: 1; margin-left: 18rpx; display: flex; flex-direction: column; gap: 10rpx; min-width: 0; padding-right: 4rpx; }
.feed-top { display: flex; align-items: center; gap: 10rpx; }
.feed-title { font-size: 29rpx; font-weight: 950; color: var(--text); flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.feed-cat { font-size: 19rpx; padding: 5rpx 12rpx; border-radius: var(--radius-full); font-weight: 800; white-space: nowrap; }
.feed-meta { display: flex; gap: 14rpx; flex-wrap: wrap; }
.meta-item { display: flex; align-items: center; gap: 5rpx; color: var(--text-muted); font-size: 21rpx; }
.meta-icon { width: 22rpx; height: 22rpx; }
.micro-row { display: flex; flex-wrap: wrap; gap: 8rpx; }
.micro-row text { background: var(--blue-bg); color: var(--blue); border-radius: var(--radius-full); padding: 5rpx 11rpx; font-size: 19rpx; font-weight: 850; box-shadow: inset 0 0 0 1rpx rgba(75,167,200,.08); }
.explain-row { display: flex; flex-wrap: wrap; gap: 7rpx; }
.explain-row text { max-width: 220rpx; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; background: var(--green-bg); color: var(--teal); border-radius: var(--radius-full); padding: 5rpx 10rpx; font-size: 19rpx; font-weight: 850; box-sizing: border-box; }
.feed-actions { display: flex; flex-direction: column; gap: 8rpx; flex-shrink: 0; }
.feed-actions button { width: 82rpx; height: 46rpx; margin: 0; padding: 0; border-radius: var(--radius-full); border: none; background: var(--green-bg); color: var(--teal); font-size: 20rpx; font-weight: 900; line-height: 1; display: flex; align-items: center; justify-content: center; }
.feed-actions .icon-action { gap: 4rpx; transition: transform .18s ease, background-color .18s ease; }
.feed-actions .icon-action image { width: 18rpx; height: 18rpx; flex-shrink: 0; }
.feed-actions .icon-action.active { background: #FFE9EA; color: #D94F4F; transform: scale(1.03); }
.feed-actions button.dark { background: #173B2E; color: #fff; }
.feed-actions button.accent { background: var(--amber-bg); color: #9A651B; }
.feed-actions button::after { border: none; }
.empty { display: flex; flex-direction: column; align-items: center; padding-top: 120rpx; color: var(--text-muted); font-size: 26rpx; }
.empty-icon { width: 78rpx; height: 78rpx; margin-bottom: 16rpx; }
.load-more { height: 76rpx; margin: 24rpx 0 10rpx; border-radius: var(--radius-full); background: #fff; color: var(--accent); font-size: 25rpx; font-weight: 900; border: 1rpx solid var(--border-light); box-shadow: var(--shadow-sm); display: flex; align-items: center; justify-content: center; }
</style>
