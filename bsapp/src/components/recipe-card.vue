<template>
  <view class="recipe-card" @tap="handleTap">
    <view class="rc-image">
      <text class="rc-emoji">{{ recipe.imageEmoji || '食' }}</text>
    </view>
    <view class="rc-info">
      <text class="rc-title">{{ recipe.title }}</text>
      <view class="rc-meta">
        <view v-if="recipe.cookTime" class="rc-meta-item"><image src="/static/icons/icon_calendar.svg" mode="aspectFit" /><text>{{ recipe.cookTime }}'</text></view>
        <view v-if="recipe.calories" class="rc-meta-item"><image src="/static/icons/icon_fire.svg" mode="aspectFit" /><text>{{ recipe.calories }}kcal</text></view>
        <view class="rc-match">
          <image src="/static/icons/icon_leaf.svg" mode="aspectFit" />
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
  border-radius: var(--radius);
  padding: 18rpx;
  margin-bottom: 14rpx;
  box-shadow: var(--shadow-sm);
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
  border-radius: 26rpx;
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
  font-weight: 800;
  color: var(--text-color);
  letter-spacing: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.rc-meta {
  display: flex;
  align-items: center;
  gap: 14rpx;
}
.rc-meta-item {
  display: flex;
  align-items: center;
  gap: 4rpx;
  font-size: 20rpx;
  color: var(--text-secondary);
}
.rc-meta-item image {
  width: 22rpx;
  height: 22rpx;
}
.rc-match {
  display: flex;
  align-items: center;
  gap: 4rpx;
  margin-left: auto;
  background: var(--green-bg);
  padding: 4rpx 10rpx;
  border-radius: var(--radius-full);
}
.rc-match image {
  width: 20rpx;
  height: 20rpx;
}
.rc-score {
  font-size: 20rpx;
  color: var(--accent);
  font-weight: 800;
}
.rc-arrow {
  font-size: 32rpx;
  color: var(--text-muted);
  margin-left: 8rpx;
}
</style>
