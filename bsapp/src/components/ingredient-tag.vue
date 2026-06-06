<template>
  <view class="ingredient-tag">
    <text class="it-emoji">🥘</text>
    <text class="it-name">{{ ingredient.name }}</text>
    <text v-if="ingredient.freshness" class="it-freshness">{{ freshnessLabel }}</text>
  </view>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  ingredient: { type: Object, required: true }
})

const freshnessLabel = computed(() => {
  const map = { high: '新鲜', normal: '普通', low: '一般' }
  return map[props.ingredient.freshness] || props.ingredient.freshness
})
</script>

<style scoped>
.ingredient-tag {
  background: var(--card-bg);
  border: 1rpx solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 16rpx 24rpx;
  margin-right: 16rpx;
  min-width: 130rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6rpx;
  box-shadow: var(--card-shadow);
  transition: all var(--transition-fast);
}
.ingredient-tag:active {
  transform: scale(0.96);
}
.it-emoji {
  font-size: 28rpx;
}
.it-name {
  font-weight: 600;
  font-size: 26rpx;
  color: var(--text-color);
}
.it-freshness {
  font-size: 20rpx;
  color: var(--accent);
  background: var(--accent-bg);
  padding: 2rpx 12rpx;
  border-radius: 8rpx;
}
</style>
