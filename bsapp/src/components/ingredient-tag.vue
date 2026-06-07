<template>
  <view class="ingredient-tag">
    <view class="it-icon">
      <image src="/static/icons/icon_leaf.svg" mode="aspectFit" />
    </view>
    <view class="it-copy">
      <text class="it-name">{{ ingredient.name }}</text>
      <text v-if="ingredient.freshness" class="it-freshness">{{ freshnessLabel }}</text>
    </view>
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
  border-radius: var(--radius);
  padding: 16rpx 18rpx;
  margin-right: 16rpx;
  min-width: 190rpx;
  display: flex;
  align-items: center;
  gap: 14rpx;
  box-shadow: var(--shadow-sm);
  transition: all var(--transition-fast);
}
.ingredient-tag:active {
  transform: scale(0.96);
}
.it-icon {
  width: 54rpx;
  height: 54rpx;
  border-radius: 18rpx;
  background: var(--teal-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.it-icon image {
  width: 30rpx;
  height: 30rpx;
}
.it-copy {
  flex: 1;
  min-width: 0;
}
.it-name {
  display: block;
  font-weight: 600;
  font-size: 26rpx;
  color: var(--text-color);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.it-freshness {
  display: inline-flex;
  margin-top: 6rpx;
  font-size: 20rpx;
  color: var(--accent);
  background: var(--accent-bg);
  padding: 3rpx 12rpx;
  border-radius: var(--radius-full);
}
</style>
