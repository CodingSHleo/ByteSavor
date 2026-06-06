<template>
  <view class="recipe-card" @tap="handleTap">
    <view class="rc-image">
      <text class="rc-emoji">{{ recipe.imageEmoji || '🍽️' }}</text>
    </view>
    <view class="rc-info">
      <text class="rc-title">{{ recipe.title }}</text>
      <view class="rc-meta">
        <text v-if="recipe.cookTime" class="rc-meta-item">⏱ {{ recipe.cookTime }}'</text>
        <text v-if="recipe.calories" class="rc-meta-item">🔥 {{ recipe.calories }}kcal</text>
        <view class="rc-match">
          <text class="rc-star">★</text>
          <text class="rc-score">{{ matchPercent }}%</text>
        </view>
      </view>
    </view>
    <text class="rc-arrow">›</text>
  </view>
</template>

<script setup>
import { computed } from 'vue'
import { t } from '@/utils/i18n'

const props = defineProps({
  recipe: { type: Object, required: true }
})

const emit = defineEmits(['tap'])
const $t = key => t(key)

const matchPercent = computed(() => {
  return ((props.recipe.matchScore || 0) * 100).toFixed(0)
})

function handleTap() {
  emit('tap', props.recipe)
}
</script>

<style scoped>
.recipe-card {
  display: flex;
  align-items: center;
  background: var(--card-bg);
  border-radius: var(--radius-md);
  padding: 22rpx 24rpx;
  margin-bottom: 14rpx;
  box-shadow: var(--card-shadow);
  transition: all var(--transition-fast);
}
.recipe-card:active {
  transform: scale(0.985);
  box-shadow: var(--card-hover-shadow);
}
.rc-image {
  width: 90rpx;
  height: 90rpx;
  background: var(--accent-bg);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.rc-emoji { font-size: 42rpx; }
.rc-info {
  flex: 1;
  margin-left: 20rpx;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}
.rc-title {
  font-size: 28rpx;
  font-weight: 700;
  color: var(--text-color);
  font-family: var(--font-serif);
  letter-spacing: 0.02em;
}
.rc-meta {
  display: flex;
  align-items: center;
  gap: 14rpx;
}
.rc-meta-item {
  font-size: 20rpx;
  color: var(--text-secondary);
}
.rc-match {
  display: flex;
  align-items: center;
  gap: 4rpx;
  margin-left: auto;
}
.rc-star {
  font-size: 22rpx;
  color: var(--accent);
}
.rc-score {
  font-size: 22rpx;
  color: var(--accent);
  font-weight: 700;
}
.rc-arrow {
  font-size: 32rpx;
  color: var(--text-muted);
  margin-left: 8rpx;
}
</style>
