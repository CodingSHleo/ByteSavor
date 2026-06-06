<template>
  <view class="hist-page">
    <view v-if="items.length === 0" class="hist-empty">
      <image class="hist-empty-icon" src="/static/icons/icon_copy.svg" mode="widthFix" />
      <text class="hist-empty-text">{{ $t('noHistory') }}</text>
    </view>

    <view
      v-for="(item, idx) in items"
      :key="idx"
      class="hist-card"
    >
      <view class="hist-avatar">
        <image src="/static/icons/icon_copy.svg" mode="widthFix" />
      </view>
      <view class="hist-info">
        <text class="hist-title">{{ item.title }}</text>
        <text class="hist-detail">{{ item.detail }}</text>
        <text class="hist-time">{{ formatTime(item.createdAt) }}</text>
      </view>
      <view class="hist-type-tag">
        <text>{{ item.type }}</text>
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
</script>

<style scoped>
.hist-page { min-height: 100vh; background: var(--bg-color); padding: 20rpx; }
.hist-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding-top: 200rpx;
}
.hist-empty-icon { width: 120rpx; height: 120rpx; }
.hist-empty-text { font-size: 28rpx; color: var(--text-secondary); margin-top: 20rpx; }
.hist-card {
  display: flex;
  align-items: flex-start;
  background: var(--card-bg);
  border-radius: 16rpx;
  padding: 24rpx;
  margin-bottom: 16rpx;
}
.hist-avatar {
  width: 80rpx;
  height: 80rpx;
  background: var(--accent-bg);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}
.hist-info { flex: 1; margin-left: 16rpx; }
.hist-title { font-size: 28rpx; font-weight: bold; color: var(--text-color); display: block; }
.hist-detail { font-size: 24rpx; color: var(--text-secondary); display: block; margin-top: 4rpx; }
.hist-time { font-size: 22rpx; color: var(--text-muted); display: block; margin-top: 6rpx; }
.hist-type-tag {
  background: var(--accent-bg);
  padding: 8rpx 16rpx;
  border-radius: 12rpx;
  font-size: 22rpx;
  color: var(--accent);
}
</style>
