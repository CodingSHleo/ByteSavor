<template>
  <view class="hist-page">
    <view class="hist-header">
      <view>
        <text class="hist-title-main">{{ $t('history') }}</text>
        <text class="hist-sub">识别、推荐与清单导出的近期动作</text>
      </view>
      <view class="hist-count">
        <text class="count-num">{{ items.length }}</text>
        <text class="count-label">records</text>
      </view>
    </view>

    <view class="hist-empty" v-if="items.length === 0">
      <view class="empty-icon">
        <image src="/static/icons/icon_copy.svg" mode="aspectFit" />
      </view>
      <text class="hist-empty-text">{{ $t('noHistory') }}</text>
      <text class="hist-empty-hint">完成一次食材识别或清单导出后，这里会形成你的饮食时间线。</text>
    </view>

    <view v-else class="timeline">
      <view v-for="(item, idx) in items" :key="idx" class="hist-card">
        <view class="hist-avatar">
          <image :src="iconFor(item.type)" mode="aspectFit" />
        </view>
        <view class="hist-info">
          <view class="hist-row">
            <text class="hist-title">{{ item.title }}</text>
            <view class="hist-type-tag">
              <text>{{ item.type }}</text>
            </view>
          </view>
          <text class="hist-detail">{{ item.detail }}</text>
          <text class="hist-time">{{ formatTime(item.createdAt) }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { useHistoryStore } from '@/store/history'
import { t } from '@/utils/i18n'

const $t = key => t(key)
const historyStore = useHistoryStore()
const items = ref([])

onShow(async () => {
  await historyStore.loadHistory()
  items.value = historyStore.items
})

function formatTime(dateStr) {
  return historyStore.formatTime(dateStr)
}

function iconFor(type) {
  const text = String(type || '')
  if (text.includes('识别') || text.toLowerCase().includes('scan')) return '/static/icons/icon_scan.svg'
  if (text.includes('清单') || text.toLowerCase().includes('list')) return '/static/icons/icon_cart.svg'
  if (text.includes('食谱') || text.toLowerCase().includes('recipe')) return '/static/icons/icon_plate.svg'
  return '/static/icons/icon_copy.svg'
}
</script>

<style scoped>
.hist-page { min-height: 100vh; background: var(--bg); padding: 28rpx; }
.hist-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18rpx;
  margin-bottom: 22rpx;
}
.hist-title-main { display: block; font-size: 42rpx; font-weight: 800; color: var(--text); line-height: 1.1; }
.hist-sub { display: block; margin-top: 10rpx; font-size: 24rpx; color: var(--text-secondary); }
.hist-count {
  min-width: 116rpx;
  border-radius: 26rpx;
  background: var(--bg-card);
  box-shadow: var(--shadow-sm);
  padding: 16rpx;
  text-align: center;
}
.count-num { display: block; font-size: 34rpx; font-weight: 800; color: var(--accent); line-height: 1; }
.count-label { display: block; margin-top: 6rpx; font-size: 18rpx; color: var(--text-muted); }
.hist-empty {
  margin-top: 80rpx;
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  padding: 70rpx 44rpx;
  box-shadow: var(--shadow-sm);
  display: flex;
  flex-direction: column;
  align-items: center;
}
.empty-icon {
  width: 112rpx;
  height: 112rpx;
  border-radius: 34rpx;
  background: var(--blue-bg);
  display: flex;
  align-items: center;
  justify-content: center;
}
.empty-icon image { width: 58rpx; height: 58rpx; }
.hist-empty-text { font-size: 30rpx; color: var(--text); font-weight: 800; margin-top: 24rpx; }
.hist-empty-hint { margin-top: 10rpx; color: var(--text-secondary); font-size: 24rpx; line-height: 1.5; text-align: center; }
.timeline { display: flex; flex-direction: column; gap: 16rpx; }
.hist-card {
  display: flex;
  align-items: flex-start;
  gap: 18rpx;
  background: var(--bg-card);
  border-radius: var(--radius);
  padding: 22rpx;
  box-shadow: var(--shadow-sm);
}
.hist-avatar {
  width: 70rpx;
  height: 70rpx;
  background: var(--teal-bg);
  border-radius: 22rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.hist-avatar image { width: 38rpx; height: 38rpx; }
.hist-info { flex: 1; min-width: 0; }
.hist-row { display: flex; align-items: center; gap: 10rpx; }
.hist-title { flex: 1; font-size: 28rpx; font-weight: 800; color: var(--text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.hist-detail { font-size: 24rpx; color: var(--text-secondary); display: block; margin-top: 8rpx; line-height: 1.45; }
.hist-time { font-size: 21rpx; color: var(--text-muted); display: block; margin-top: 10rpx; }
.hist-type-tag {
  background: var(--bg-elevated);
  padding: 6rpx 14rpx;
  border-radius: var(--radius-full);
  font-size: 20rpx;
  color: var(--accent);
  flex-shrink: 0;
}
</style>
