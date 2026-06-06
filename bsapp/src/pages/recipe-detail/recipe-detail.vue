<template>
  <view class="rd-page" v-if="!isLoading">
    <!-- 头部图 -->
    <view class="rd-image">
      <image v-if="detail?.imageUrl" :src="detail.imageUrl" class="rd-emoji" mode="aspectFill" />
      <image v-else class="rd-emoji" src="/static/icons/icon_plate.svg" mode="widthFix" />
    </view>

    <!-- 菜谱元数据 -->
    <view class="rd-meta-bar">
      <view class="rd-meta-item">
        <image class="rd-meta-icon-img" src="/static/icons/icon_clock.svg" mode="widthFix" />
        <text class="rd-meta-text">{{ detail?.cookTime || '-' }}{{ $t('minutes') }}</text>
      </view>
      <view class="rd-meta-item">
        <image class="rd-meta-icon-img" src="/static/icons/icon_chart.svg" mode="widthFix" />
        <text class="rd-meta-text">{{ detail?.difficulty || '-' }}</text>
      </view>
      <view class="rd-meta-item">
        <image class="rd-meta-icon-img" src="/static/icons/icon_fire.svg" mode="widthFix" />
        <text class="rd-meta-text">{{ detail?.calories || '-' }}{{ $t('kcal') }}</text>
      </view>
      <view class="rd-meta-item">
        <image class="rd-meta-icon-img" src="/static/icons/icon_plate.svg" mode="widthFix" />
        <text class="rd-meta-text">{{ detail?.servingSize || '2人份' }}</text>
      </view>
    </view>

    <!-- 食材清单 -->
    <view class="card" v-if="detail?.ingredients && detail.ingredients.length > 0">
      <text class="card-title">{{ $t('ingredients') }}</text>
      <view class="rd-ing-list">
        <view v-for="(ing, idx) in detail.ingredients" :key="idx" class="rd-ing-row">
          <text class="rd-ing-bullet">•</text>
          <text class="rd-ing-name">{{ ing.name }}</text>
          <text class="rd-ing-amount">{{ ing.amount }}</text>
        </view>
      </view>
    </view>

    <!-- 制作步骤 -->
    <view class="card">
      <text class="card-title">{{ $t('cookingSteps') }}</text>
      <view
        v-for="(step, idx) in detail?.steps || []"
        :key="idx"
        class="rd-step"
      >
        <view class="rd-step-num">{{ idx + 1 }}</view>
        <text class="rd-step-text">{{ step }}</text>
      </view>
    </view>

    <!-- 营养信息 -->
    <view class="card" v-if="detail?.nutrition">
      <text class="card-title">{{ $t('nutritionPerServing') }}</text>
      <view class="rd-nutri-grid">
        <view class="rd-nutri-item">
          <text class="rd-nutri-val">{{ detail.nutrition.protein }}g</text>
          <text class="rd-nutri-label">{{ $t('protein') }}</text>
        </view>
        <view class="rd-nutri-item">
          <text class="rd-nutri-val">{{ detail.nutrition.fat }}g</text>
          <text class="rd-nutri-label">{{ $t('fat') }}</text>
        </view>
        <view class="rd-nutri-item">
          <text class="rd-nutri-val">{{ detail.nutrition.carbs }}g</text>
          <text class="rd-nutri-label">{{ $t('carbs') }}</text>
        </view>
        <view class="rd-nutri-item">
          <text class="rd-nutri-val">{{ detail.nutrition.fiber }}g</text>
          <text class="rd-nutri-label">{{ $t('fiber') }}</text>
        </view>
      </view>
      <view class="rd-nutri-extra">
        <text class="rd-nutri-mini">维生素C {{ detail.nutrition.vitamin_c }}mg</text>
        <text class="rd-nutri-mini">铁 {{ detail.nutrition.iron }}mg</text>
        <text class="rd-nutri-mini">钙 {{ detail.nutrition.calcium }}mg</text>
      </view>
    </view>

    <!-- 烹饪技巧 -->
    <view class="ai-tip" v-if="detail?.tips">
      <image class="ai-tip-icon" src="/static/icons/icon_export.svg" mode="widthFix" />
      <text>{{ detail.tips }}</text>
    </view>

    <!-- 互动按钮 -->
    <view class="rd-interactions">
      <view class="rd-int-btn" @tap="toggleLike">
        <image :src="isLiked ? '/static/icons/icon_heart.svg' : '/static/icons/icon_heart_outline.svg'" class="rd-int-icon" mode="widthFix" />
        <text :style="{ color: isLiked ? 'var(--danger)' : '#999' }">{{ $t('like') }}</text>
      </view>
      <view class="rd-int-btn" @tap="showShare">
        <image class="rd-int-icon" src="/static/icons/icon_share.svg" mode="widthFix" />
        <text style="color: var(--accent);">{{ $t('share') }}</text>
      </view>
      <view class="rd-int-btn" @tap="saveRecipe">
        <image class="rd-int-icon" src="/static/icons/icon_bookmark.svg" mode="widthFix" />
        <text style="color: var(--accent);">{{ $t('saveBookmark') }}</text>
      </view>
    </view>

    <!-- 生成购物清单 -->
    <button class="rd-shopping-btn" @tap="generateShoppingList">
      <image class="btn-small-icon" src="/static/icons/icon_cart.svg" mode="widthFix" />
      {{ $t('generateShoppingList') }}
    </button>

    <!-- 评分 -->
    <view class="card">
      <text class="card-title">{{ $t('rating') }}</text>
      <view class="rd-stars">
        <text
          v-for="n in 5"
          :key="n"
          class="rd-star"
          @tap="setRating(n)"
        >{{ n <= rating ? '⭐' : '☆' }}</text>
      </view>
      <text class="rd-rating-label">
        {{ rating > 0 ? $t('yourRating') + ': ' + rating + ' ' + $t('stars') : $t('clickToRate') }}
      </text>
    </view>

    <!-- 反馈 -->
    <view class="card">
      <text class="card-title">{{ $t('shareExperience') }}</text>
      <textarea
        class="rd-textarea"
        v-model="feedback"
        :placeholder="$t('sharePlaceholder')"
        maxlength="500"
      />
      <view class="rd-feedback-btns">
        <button class="rd-btn-cancel" @tap="feedback = ''">{{ $t('cancel') }}</button>
        <button class="rd-btn-submit" @tap="submitFeedback">{{ $t('submitFeedback') }}</button>
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
  detail.value = await ApiService.getRecipeDetail(recipeId.value)
  uni.setNavigationBarTitle({ title: detail.value?.title || title.value })
  isLoading.value = false
}

onLoad(async (options) => {
  recipeId.value = options.recipeId || 'r_101'
  title.value = options.title ? decodeURIComponent(options.title) : ''
  await loadDetail()
})

watch(currentLang, () => { loadDetail() })

function setRating(n) {
  rating.value = n
}

async function submitFeedback() {
  if (rating.value > 0) {
    const result = await ApiService.submitFeedback(recipeId.value, rating.value)
    const points = result?.reward_points || 1
    uni.showToast({ title: $t('thanksFeedback') + '+' + points + $t('rewardPoints'), icon: 'success' })
    rating.value = 0
    feedback.value = ''
  } else {
    uni.showToast({ title: $t('clickToRate'), icon: 'none' })
  }
}

function toggleLike() {
  isLiked.value = !isLiked.value
  uni.showToast({ title: isLiked.value ? $t('likedRecipe') : $t('unlikedRecipe'), icon: 'none' })
}

function saveRecipe() {
  uni.showToast({ title: $t('savedToMyRecipes'), icon: 'success' })
}

async function generateShoppingList() {
  const list = await ApiService.mergeShoppingList([recipeId.value])
  const recipes = [{ recipeId: recipeId.value, title: detail.value?.title || '', matchScore: 1.0 }]
  const data = encodeURIComponent(JSON.stringify(recipes))
  uni.navigateTo({ url: `/pages/list-export/list-export?recipes=${data}` })
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
.rd-page { min-height: 100vh; background: var(--bg-color); padding: 24rpx; }
.loading-page { display: flex; align-items: center; justify-content: center; height: 100vh; }
.rd-image {
  width: 100%;
  height: 360rpx;
  background: var(--accent-bg);
  border-radius: 16rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 24rpx;
}
.rd-emoji { width: 100%; height: 100%; object-fit: cover; border-radius: 12rpx; }
.card { background: var(--card-bg); border-radius: 16rpx; padding: 24rpx; margin-bottom: 20rpx; }
.card-title { font-size: 32rpx; font-weight: bold; color: var(--text-color); display: block; margin-bottom: 16rpx; }
/* 元数据 */
.rd-meta-bar {
  display: flex;
  justify-content: space-around;
  background: var(--card-bg);
  border-radius: 16rpx;
  padding: 20rpx;
  margin-bottom: 20rpx;
}
.rd-meta-item { display: flex; flex-direction: column; align-items: center; gap: 4rpx; }
.rd-meta-icon-img { width: 40rpx; height: 40rpx; }
.ai-tip-icon { width: 36rpx; height: 36rpx; margin-right: 8rpx; }
.rd-meta-text { font-size: 22rpx; color: var(--text-secondary); }
/* 食材清单 */
.rd-ing-list { }
.rd-ing-row {
  display: flex;
  align-items: center;
  padding: 12rpx 0;
  border-bottom: 1rpx solid var(--border-light);
}
.rd-ing-row:last-child { border-bottom: none; }
.rd-ing-bullet { color: var(--accent); font-size: 28rpx; margin-right: 12rpx; }
.rd-ing-name { flex: 1; font-size: 28rpx; color: var(--text-color); }
.rd-ing-amount { font-size: 26rpx; color: var(--text-secondary); }
/* 营养 */
.rd-nutri-grid {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16rpx;
}
.rd-nutri-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12rpx 8rpx;
}
.rd-nutri-val { font-size: 30rpx; font-weight: bold; color: var(--accent); }
.rd-nutri-label { font-size: 22rpx; color: var(--text-secondary); margin-top: 4rpx; }
.rd-nutri-extra { display: flex; gap: 16rpx; flex-wrap: wrap; }
.rd-nutri-mini {
  font-size: 22rpx;
  color: var(--text-secondary);
  background: var(--border-light);
  padding: 4rpx 14rpx;
  border-radius: 10rpx;
}
/* 购物清单按钮 */
.rd-shopping-btn {
  width: 100%;
  height: 80rpx;
  background: var(--success);
  color: #fff;
  border: none;
  border-radius: 16rpx;
  font-size: 28rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20rpx;
}
/* 步骤（更新为编号样式） */
.rd-step { display: flex; margin-bottom: 16rpx; align-items: flex-start; }
.rd-step-num {
  width: 40rpx;
  height: 40rpx;
  background: var(--accent);
  color: #fff;
  border-radius: 50%;
  font-size: 22rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12rpx;
  flex-shrink: 0;
}
.rd-step-text { font-size: 28rpx; color: var(--text-color); flex: 1; line-height: 1.6; }
.rd-interactions { display: flex; justify-content: space-around; margin-bottom: 20rpx; }
.rd-int-btn { display: flex; flex-direction: column; align-items: center; gap: 8rpx; padding: 16rpx; }
.rd-int-icon { width: 48rpx; height: 48rpx; }
.btn-small-icon { width: 40rpx; height: 40rpx; margin-right: 8rpx; }
.rd-stars { display: flex; justify-content: center; gap: 12rpx; margin-bottom: 16rpx; }
.rd-star { font-size: 56rpx; }
.rd-rating-label { text-align: center; font-size: 26rpx; color: var(--text-secondary); display: block; }
.rd-textarea {
  width: 100%;
  min-height: 160rpx;
  background: var(--bg-color);
  border-radius: 12rpx;
  padding: 20rpx;
  font-size: 28rpx;
  box-sizing: border-box;
  margin-bottom: 20rpx;
}
.rd-feedback-btns { display: flex; gap: 16rpx; }
.rd-btn-cancel {
  flex: 1;
  height: 74rpx;
  background: var(--card-bg);
  border: 1rpx solid var(--border-color);
  border-radius: 12rpx;
  font-size: 28rpx;
}
.rd-btn-submit {
  flex: 1;
  height: 74rpx;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: 12rpx;
  font-size: 28rpx;
}
</style>
