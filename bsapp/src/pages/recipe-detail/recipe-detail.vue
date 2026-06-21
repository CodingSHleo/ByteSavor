<template>
  <view class="rd-page" v-if="!isLoading">
    <view class="hero-card">
      <view class="hero-visual">
        <image v-if="detail?.imageUrl" :src="detail.imageUrl" class="hero-image" mode="aspectFill" />
        <view v-else class="hero-icon-shell">
          <image class="hero-icon" src="/static/icons/icon_plate.svg" mode="aspectFit" />
          <text class="hero-icon-fallback">食</text>
        </view>
      </view>
      <view class="hero-info">
        <text class="hero-title">{{ detail?.title || title }}</text>
        <text class="hero-sub">适合今日目标的智能推荐菜谱</text>
        <view class="hero-tags">
          <text>{{ detail?.cookTime || '-' }}{{ $t('minutes') }}</text>
          <text>{{ detail?.difficulty || '-' }}</text>
          <text>{{ detail?.calories || '-' }}{{ $t('kcal') }}</text>
        </view>
      </view>
    </view>

    <button class="shopping-btn" @tap="generateShoppingList">
      <image class="btn-small-icon" src="/static/icons/icon_cart.svg" mode="widthFix" />
      {{ $t('generateShoppingList') }}
    </button>
    <button class="check-btn" @tap="checkRecipe">清点当前库存缺什么</button>

    <view class="action-row">
      <view class="action-btn" :class="{ liked: isLiked }" @tap="toggleLike">
        <image :src="isLiked ? '/static/icons/icon_heart.svg' : '/static/icons/icon_heart_outline.svg'" class="action-icon" mode="aspectFit" />
        <text>{{ isLiked ? '已收藏' : $t('like') }}</text>
      </view>
      <view class="action-btn" @tap="showShare">
        <image class="action-icon" src="/static/icons/icon_share.svg" mode="aspectFit" />
        <text>{{ $t('share') }}</text>
      </view>
      <view class="action-btn" @tap="saveRecipe">
        <image class="action-icon" src="/static/icons/icon_bookmark.svg" mode="aspectFit" />
        <text>{{ $t('saveBookmark') }}</text>
      </view>
    </view>

    <view class="card" v-if="detail?.ingredients && detail.ingredients.length > 0">
      <view class="card-head"><text>{{ $t('ingredients') }}</text><text>{{ detail.ingredients.length }} 项</text></view>
      <view class="ing-list">
        <view v-for="(ing, idx) in detail.ingredients" :key="idx" class="ing-row">
          <view class="ing-icon">
            <image :src="ingredientIcon(ing)" mode="aspectFit" />
            <text>{{ ingredientGlyph(ing) }}</text>
          </view>
          <text class="ing-name">{{ ing.name }}</text>
          <text class="ing-amount">{{ ing.amount }}</text>
        </view>
      </view>
    </view>

    <view class="card">
      <view class="card-head"><text>{{ $t('cookingSteps') }}</text><text>{{ (detail?.steps || []).length }} 步</text></view>
      <view v-for="(step, idx) in detail?.steps || []" :key="idx" class="step-row">
        <view class="step-num">{{ idx + 1 }}</view>
        <text class="step-text">{{ step }}</text>
      </view>
    </view>

    <view class="card" v-if="detail?.nutrition">
      <view class="card-head"><text>{{ $t('nutritionPerServing') }}</text></view>
      <view class="nutri-grid">
        <view class="nutri-item protein"><text>{{ detail.nutrition.protein }}g</text><text>{{ $t('protein') }}</text></view>
        <view class="nutri-item fat"><text>{{ detail.nutrition.fat }}g</text><text>{{ $t('fat') }}</text></view>
        <view class="nutri-item carbs"><text>{{ detail.nutrition.carbs }}g</text><text>{{ $t('carbs') }}</text></view>
        <view class="nutri-item fiber"><text>{{ detail.nutrition.fiber }}g</text><text>{{ $t('fiber') }}</text></view>
      </view>
      <view class="nutri-extra">
        <text>维生素C {{ detail.nutrition.vitamin_c }}mg</text>
        <text>铁 {{ detail.nutrition.iron }}mg</text>
        <text>钙 {{ detail.nutrition.calcium }}mg</text>
      </view>
    </view>

    <view class="tip-card" v-if="detail?.tips">
      <image class="tip-icon" src="/static/icons/icon_ai.svg" mode="widthFix" />
      <text>{{ detail.tips }}</text>
    </view>

    <view class="card">
      <view class="card-head"><text>{{ $t('rating') }}</text></view>
      <view class="stars">
        <text v-for="n in 5" :key="n" class="star" :class="{ active: n <= rating }" @tap="setRating(n)">★</text>
      </view>
      <text class="rating-label">{{ rating > 0 ? $t('yourRating') + ': ' + rating + ' ' + $t('stars') : $t('clickToRate') }}</text>
    </view>

    <view class="card">
      <view class="card-head"><text>{{ $t('shareExperience') }}</text></view>
      <textarea class="feedback-textarea" v-model="feedback" :placeholder="$t('sharePlaceholder')" maxlength="500" />
      <view class="feedback-btns">
        <button class="btn-cancel" @tap="feedback = ''">{{ $t('cancel') }}</button>
        <button class="btn-submit" @tap="submitFeedback">{{ $t('submitFeedback') }}</button>
      </view>
    </view>
  </view>
  <view v-else class="loading-page"><text>加载中...</text></view>
</template>

<script setup>
import { ref, watch } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { ApiService } from '@/api/index'
import { t, currentLang } from '@/utils/i18n'

const $t = key => t(key)
const isLoading = ref(true)
const recipeId = ref('')
const title = ref('')
const detail = ref(null)
const rating = ref(0)
const isLiked = ref(false)
const feedback = ref('')

async function loadDetail() {
  isLoading.value = true
  try {
    detail.value = await ApiService.getRecipeDetail(recipeId.value)
    try { isLiked.value = await ApiService.getFavoriteStatus('system_recipe', recipeId.value) } catch (e) {}
    uni.setNavigationBarTitle({ title: detail.value?.title || title.value })
  } catch (e) {
    detail.value = null
    uni.showToast({ title: e.message || '菜谱详情加载失败', icon: 'none' })
  } finally {
    isLoading.value = false
  }
}
onLoad(async (options) => {
  recipeId.value = options.recipeId || 'r_101'
  title.value = options.title ? decodeURIComponent(options.title) : ''
  await loadDetail()
})
watch(currentLang, () => { loadDetail() })
function setRating(n) { rating.value = n }
async function submitFeedback() {
  if (rating.value > 0) {
    try {
      const result = await ApiService.submitFeedback(recipeId.value, rating.value)
      const points = result?.reward_points || 1
      uni.showToast({ title: $t('thanksFeedback') + '+' + points + $t('rewardPoints'), icon: 'success' })
      rating.value = 0
      feedback.value = ''
    } catch (e) {
      uni.showToast({ title: e.message || '反馈提交失败', icon: 'none' })
    }
  } else {
    uni.showToast({ title: $t('clickToRate'), icon: 'none' })
  }
}
async function toggleLike() {
  try {
    if (isLiked.value) {
      await ApiService.removeFavorite('system_recipe', recipeId.value)
      isLiked.value = false
      uni.showToast({ title: $t('unlikedRecipe'), icon: 'none' })
    } else {
      await ApiService.addFavorite('system_recipe', recipeId.value, detail.value || { title: title.value })
      isLiked.value = true
      uni.showToast({ title: $t('likedRecipe'), icon: 'success' })
    }
  } catch (e) {
    uni.showToast({ title: e.message || '收藏失败', icon: 'none' })
  }
}
async function saveRecipe() {
  await ApiService.addFavorite('system_recipe', recipeId.value, detail.value || { title: title.value })
  isLiked.value = true
  uni.showToast({ title: $t('savedToMyRecipes'), icon: 'success' })
}
function checkRecipe() {
  uni.navigateTo({ url: `/pages/recipe-checker/recipe-checker?targetType=system_recipe&targetId=${recipeId.value}` })
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
async function generateShoppingList() {
  try {
    await ApiService.mergeShoppingList([recipeId.value])
    const recipes = [{ recipeId: recipeId.value, title: detail.value?.title || '', matchScore: 1.0 }]
    const data = encodeURIComponent(JSON.stringify(recipes))
    uni.navigateTo({ url: `/pages/list-export/list-export?recipes=${data}` })
  } catch (e) {
    uni.showToast({ title: e.message || '购物清单生成失败', icon: 'none' })
  }
}
function showShare() {
  uni.showActionSheet({
    itemList: [$t('wechat'), $t('xiaohongshu')],
    success: (res) => {
      const platform = res.tapIndex === 0 ? $t('wechat') : $t('xiaohongshu')
      uni.showToast({ title: $t('sharedTo') + ' ' + title.value + ' 到' + platform, icon: 'success' })
    }
  })
}
</script>

<style scoped>
.rd-page { min-height: 100vh; background: var(--bg); padding: 28rpx; }
.loading-page { display: flex; align-items: center; justify-content: center; height: 100vh; }
.hero-card { background: #fff; border-radius: var(--radius-lg); padding: 22rpx; box-shadow: var(--shadow-md); display: flex; gap: 20rpx; margin-bottom: 18rpx; }
.hero-visual { width: 150rpx; height: 150rpx; border-radius: 34rpx; background: var(--teal-bg); display: flex; align-items: center; justify-content: center; flex-shrink: 0; overflow: hidden; }
.hero-image { width: 100%; height: 100%; }
.hero-icon-shell { width: 92rpx; height: 92rpx; position: relative; display: flex; align-items: center; justify-content: center; }
.hero-icon { width: 78rpx; height: 78rpx; position: relative; z-index: 1; }
.hero-icon-fallback { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; color: var(--teal); font-size: 38rpx; font-weight: 900; opacity: .18; }
.hero-info { flex: 1; min-width: 0; }
.hero-title { display: block; font-size: 36rpx; font-weight: 900; color: var(--text); line-height: 1.25; }
.hero-sub { display: block; margin-top: 8rpx; font-size: 24rpx; color: var(--text-secondary); }
.hero-tags { display: flex; flex-wrap: wrap; gap: 8rpx; margin-top: 16rpx; }
.hero-tags text { background: var(--bg); color: var(--text-secondary); border-radius: var(--radius-full); padding: 6rpx 12rpx; font-size: 21rpx; font-weight: 700; }
.shopping-btn { width: 100%; height: 90rpx; background: var(--teal); color: #fff; border: none; border-radius: var(--radius); font-size: 30rpx; font-weight: 900; display: flex; align-items: center; justify-content: center; margin-bottom: 14rpx; box-shadow: var(--shadow-sm); }
.check-btn { width: 100%; height: 82rpx; background: #173B2E; color: #fff; border: none; border-radius: var(--radius); font-size: 28rpx; font-weight: 900; display: flex; align-items: center; justify-content: center; margin-bottom: 14rpx; box-shadow: var(--shadow-sm); }
.btn-small-icon { width: 40rpx; height: 40rpx; margin-right: 10rpx; filter: brightness(0) invert(1); }
.action-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12rpx; margin-bottom: 20rpx; }
.action-btn { background: #fff; border-radius: var(--radius); padding: 16rpx 10rpx; display: flex; flex-direction: column; align-items: center; gap: 8rpx; color: var(--text-secondary); font-size: 22rpx; box-shadow: var(--shadow-sm); }
.action-btn.liked { background: var(--red-bg); color: var(--danger); font-weight: 900; }
.action-icon { width: 42rpx; height: 42rpx; }
.card { background: #fff; border-radius: var(--radius); padding: 24rpx; margin-bottom: 20rpx; box-shadow: var(--shadow-sm); }
.card-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 18rpx; }
.card-head text:first-child { font-size: 31rpx; font-weight: 900; color: var(--text); }
.card-head text:last-child { font-size: 22rpx; color: var(--text-muted); font-weight: 700; }
.ing-row { display: flex; align-items: center; padding: 13rpx 0; border-bottom: 1rpx solid var(--border-light); }
.ing-row:last-child { border-bottom: none; }
.ing-icon { width: 48rpx; height: 48rpx; border-radius: 15rpx; background: var(--teal-bg); margin-right: 12rpx; display: flex; align-items: center; justify-content: center; flex-shrink: 0; position: relative; }
.ing-icon image { width: 28rpx; height: 28rpx; position: relative; z-index: 1; }
.ing-icon text { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; font-size: 18rpx; font-weight: 900; color: var(--teal); opacity: .22; }
.ing-name { flex: 1; font-size: 27rpx; color: var(--text); font-weight: 800; }
.ing-amount { font-size: 25rpx; color: var(--text-secondary); }
.step-row { display: flex; align-items: flex-start; gap: 14rpx; margin-bottom: 18rpx; }
.step-row:last-child { margin-bottom: 0; }
.step-num { width: 42rpx; height: 42rpx; background: var(--teal-bg); color: var(--teal); border-radius: 50%; font-size: 22rpx; font-weight: 900; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.step-text { font-size: 27rpx; color: var(--text); flex: 1; line-height: 1.65; }
.nutri-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10rpx; margin-bottom: 14rpx; }
.nutri-item { border-radius: 18rpx; padding: 14rpx 8rpx; text-align: center; }
.nutri-item.protein { background: var(--green-bg); }
.nutri-item.fat { background: var(--purple-bg); }
.nutri-item.carbs { background: var(--amber-bg); }
.nutri-item.fiber { background: var(--blue-bg); }
.nutri-item text:first-child { display: block; color: var(--text); font-size: 27rpx; font-weight: 900; }
.nutri-item text:last-child { display: block; color: var(--text-muted); font-size: 20rpx; margin-top: 4rpx; }
.nutri-extra { display: flex; gap: 10rpx; flex-wrap: wrap; }
.nutri-extra text { font-size: 21rpx; color: var(--text-secondary); background: var(--bg); padding: 6rpx 12rpx; border-radius: var(--radius-full); }
.tip-card { background: var(--purple-bg); border-radius: var(--radius); padding: 18rpx; display: flex; gap: 12rpx; align-items: flex-start; color: var(--text-secondary); font-size: 24rpx; line-height: 1.55; margin-bottom: 20rpx; }
.tip-icon { width: 38rpx; height: 38rpx; flex-shrink: 0; }
.stars { display: flex; justify-content: center; gap: 10rpx; margin-bottom: 12rpx; }
.star { font-size: 52rpx; color: var(--border); }
.star.active { color: var(--amber); }
.rating-label { display: block; text-align: center; font-size: 24rpx; color: var(--text-muted); }
.feedback-textarea { width: 100%; min-height: 150rpx; background: var(--bg); border-radius: var(--radius); padding: 18rpx; font-size: 27rpx; box-sizing: border-box; margin-bottom: 16rpx; }
.feedback-btns { display: flex; gap: 14rpx; }
.btn-cancel, .btn-submit { flex: 1; height: 76rpx; border-radius: var(--radius); font-size: 27rpx; font-weight: 800; }
.btn-cancel { background: #fff; color: var(--text-secondary); border: 1rpx solid var(--border); }
.btn-submit { background: var(--teal); color: #fff; border: none; }
</style>
