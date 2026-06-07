<template>
  <view class="nutri-hero">
    <view class="nh-row">
      <view class="nh-score-box">
        <text class="nh-score">{{ score }}</text>
        <text class="nh-unit">{{ $t('points') }}</text>
      </view>
      <view class="nh-info">
        <text class="nh-title">{{ $t('healthIndex') }}</text>
        <text class="nh-sub">{{ $t('todayScore') }}</text>
      </view>
    </view>
    <view class="nh-bars">
      <view class="nh-bar">
        <view class="nh-bar-head">
          <view class="nh-label"><image src="/static/icons/icon_muscle.svg" mode="aspectFit" /><text>{{ $t('protein') }}</text></view>
          <text class="nh-pct">{{ protein }}%</text>
        </view>
        <view class="nh-track"><view class="nh-fill p" :style="{ width: protein + '%' }"></view></view>
      </view>
      <view class="nh-bar">
        <view class="nh-bar-head">
          <view class="nh-label"><image src="/static/icons/icon_flash.svg" mode="aspectFit" /><text>{{ $t('carbs') }}</text></view>
          <text class="nh-pct">{{ carbs }}%</text>
        </view>
        <view class="nh-track"><view class="nh-fill c" :style="{ width: carbs + '%' }"></view></view>
      </view>
      <view class="nh-bar">
        <view class="nh-bar-head">
          <view class="nh-label"><image src="/static/icons/icon_olive.svg" mode="aspectFit" /><text>{{ $t('fat') }}</text></view>
          <text class="nh-pct">{{ fat }}%</text>
        </view>
        <view class="nh-track"><view class="nh-fill f" :style="{ width: fat + '%' }"></view></view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed } from 'vue'
import { t } from '@/utils/i18n'

const props = defineProps({ score: { type: Number, default: 65 } })
const $t = key => t(key)

const protein = computed(() => Math.min(100, Math.round(props.score * 1.15)))
const carbs = computed(() => Math.min(100, Math.round(props.score * 0.9)))
const fat = computed(() => Math.min(100, Math.round(props.score * 0.7)))
</script>

<style scoped>
.nutri-hero {
  background: var(--bg-card);
  border-radius: var(--radius);
  padding: 22rpx 24rpx;
  margin-bottom: 20rpx;
  box-shadow: var(--shadow-sm);
}
.nh-row { display: flex; align-items: center; gap: 16rpx; margin-bottom: 16rpx; }
.nh-score-box {
  background: var(--teal-bg);
  border-radius: 20rpx; padding: 12rpx 20rpx;
  display: flex; flex-direction: column; align-items: center;
}
.nh-score { color: var(--accent); font-size: 44rpx; font-weight: 800; line-height: 1.1; }
.nh-unit { color: var(--text-secondary); font-size: 18rpx; }
.nh-info { display: flex; flex-direction: column; }
.nh-title { color: var(--text); font-size: 26rpx; font-weight: 700; }
.nh-sub { color: var(--text-muted); font-size: 20rpx; }

.nh-bars { display: flex; flex-direction: column; gap: 8rpx; }
.nh-bar-head { display: flex; justify-content: space-between; margin-bottom: 3rpx; }
.nh-label { display: flex; align-items: center; gap: 6rpx; }
.nh-label image { width: 22rpx; height: 22rpx; }
.nh-label text { color: var(--text-secondary); font-size: 20rpx; }
.nh-pct { font-weight: 700; color: var(--text); }
.nh-track { height: 7rpx; background: var(--border-light); border-radius: 999rpx; overflow: hidden; }
.nh-fill { height: 100%; border-radius: 3rpx; }
.nh-fill.p { background: var(--tomato); }
.nh-fill.c { background: var(--cheese); }
.nh-fill.f { background: var(--avocado); }
</style>
