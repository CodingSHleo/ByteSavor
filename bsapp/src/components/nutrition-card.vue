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
          <text>🥩 {{ $t('protein') }}</text>
          <text class="nh-pct">{{ protein }}%</text>
        </view>
        <view class="nh-track"><view class="nh-fill p" :style="{ width: protein + '%' }"></view></view>
      </view>
      <view class="nh-bar">
        <view class="nh-bar-head">
          <text>🍚 {{ $t('carbs') }}</text>
          <text class="nh-pct">{{ carbs }}%</text>
        </view>
        <view class="nh-track"><view class="nh-fill c" :style="{ width: carbs + '%' }"></view></view>
      </view>
      <view class="nh-bar">
        <view class="nh-bar-head">
          <text>🥑 {{ $t('fat') }}</text>
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
  background: #fff;
  border-radius: 12rpx;
  padding: 20rpx 24rpx;
  margin-bottom: 20rpx;
  box-shadow: var(--shadow-sm);
}
.nh-row { display: flex; align-items: center; gap: 16rpx; margin-bottom: 16rpx; }
.nh-score-box {
  background: #F5F6FA;
  border-radius: 10rpx; padding: 10rpx 18rpx;
  display: flex; flex-direction: column; align-items: center;
}
.nh-score { color: var(--text); font-size: 44rpx; font-weight: 800; line-height: 1.1; }
.nh-unit { color: var(--text-muted); font-size: 18rpx; }
.nh-info { display: flex; flex-direction: column; }
.nh-title { color: var(--text); font-size: 26rpx; font-weight: 700; }
.nh-sub { color: var(--text-muted); font-size: 20rpx; }

.nh-bars { display: flex; flex-direction: column; gap: 8rpx; }
.nh-bar-head { display: flex; justify-content: space-between; margin-bottom: 3rpx; }
.nh-bar-head text { color: var(--text-secondary); font-size: 20rpx; }
.nh-pct { font-weight: 700; color: var(--text); }
.nh-track { height: 6rpx; background: var(--border); border-radius: 3rpx; overflow: hidden; }
.nh-fill { height: 100%; border-radius: 3rpx; }
.nh-fill.p { background: #4F6EF7; }
.nh-fill.c { background: #FF9500; }
.nh-fill.f { background: #34C759; }
</style>
