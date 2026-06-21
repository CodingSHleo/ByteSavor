<template>
  <view class="tool-page">
    <view class="hero">
      <text class="kicker">TEXT INPUT</text>
      <text class="title">文本导入</text>
      <text class="desc">把测试文档、购物小票或手动记录里的食材导入当前库存。导入后只作为“现有食材”，不会计入今日摄入。</text>
    </view>

    <view class="input-card">
      <textarea
        class="textarea"
        v-model="rawText"
        maxlength="1200"
        placeholder="例如：猪肉 300g，青椒 3个，西瓜 1个&#10;也可以一行一个：牛肉 200g"
        placeholder-class="ph"
      />
      <view class="input-actions">
        <button class="ghost-btn" @tap="useExample">示例</button>
        <button class="primary-btn" @tap="previewItems">解析文本</button>
      </view>
    </view>

    <view v-if="errorMessage" class="error-card">
      <text>{{ errorMessage }}</text>
    </view>

    <view v-if="items.length" class="section">
      <view class="section-head">
        <text>解析结果</text>
        <text>{{ items.length }} 项</text>
      </view>
      <view v-for="(item, idx) in items" :key="`${item.name}-${idx}`" class="item-row">
        <view class="item-mark">{{ item.name.slice(0, 1) }}</view>
        <view class="item-main">
          <text class="item-name">{{ item.name }}</text>
          <text class="item-meta">{{ item.display || '数量待确认' }}</text>
        </view>
        <button class="delete-btn" @tap="removeItem(idx)">删</button>
      </view>
      <button class="confirm-btn" :disabled="loading" @tap="importItems">导入当前食材</button>
      <button class="home-btn" @tap="goHome">回首页生成推荐</button>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { ApiService } from '@/api/index'

const rawText = ref('')
const items = ref([])
const loading = ref(false)
const errorMessage = ref('')

function useExample() {
  rawText.value = '猪肉 300g，青椒 3个，西瓜 1个\n鸡胸肉 200g\n西兰花 150g'
  previewItems()
}

function previewItems() {
  errorMessage.value = ''
  const parsed = parseText(rawText.value)
  items.value = parsed
  if (!parsed.length) errorMessage.value = '没有解析到食材，请按“食材 数量单位”的格式输入。'
}

function parseText(text) {
  return String(text || '')
    .split(/[\n,，;；、]+/)
    .map(part => part.trim())
    .filter(Boolean)
    .map(part => {
      const match = part.match(/^(.+?)\s*[:：-]?\s*(\d+(?:\.\d+)?)\s*([a-zA-Z\u4e00-\u9fa5]*)$/)
      const name = (match?.[1] || part).trim()
      const value = match?.[2] ? Number(match[2]) : null
      const unit = match?.[3] || ''
      return {
        name: name || part,
        amount: value == null ? '' : `${value}${unit}`,
        unit,
        display: value == null ? '' : `${value}${unit}`,
        freshness: 'medium',
        confidence: 1,
        state: '文本导入',
        features: '用户文本确认'
      }
    })
    .filter(item => item.name)
}

function removeItem(idx) {
  items.value = items.value.filter((_, i) => i !== idx)
}

async function importItems() {
  if (!items.value.length) {
    previewItems()
    return
  }
  loading.value = true
  errorMessage.value = ''
  try {
    await ApiService.importInventory(items.value, 'text')
    uni.setStorageSync('last_ingredients', JSON.stringify(items.value))
    uni.showToast({ title: '已导入当前食材', icon: 'success' })
  } catch (e) {
    errorMessage.value = e.message || '导入失败'
  } finally {
    loading.value = false
  }
}

function goHome() {
  uni.switchTab({ url: '/pages/home/home' })
}
</script>

<style scoped>
.tool-page { min-height: 100vh; padding: 30rpx; background: linear-gradient(180deg, #FAFCFB 0%, var(--bg) 46%); box-sizing: border-box; }
.hero { padding: 28rpx; border-radius: var(--radius-xl); background: linear-gradient(145deg, #173B2E, #6E5A22); color: #fff; box-shadow: var(--shadow-lg); }
.kicker { display: block; font-size: 21rpx; opacity: .72; font-weight: 900; }
.title { display: block; margin-top: 8rpx; font-size: 44rpx; font-weight: 950; }
.desc { display: block; margin-top: 12rpx; font-size: 25rpx; line-height: 1.45; opacity: .84; }
.input-card { margin-top: 22rpx; padding: 18rpx; border-radius: var(--radius-lg); background: #fff; box-shadow: var(--shadow-md), var(--hairline); }
.textarea { width: 100%; min-height: 280rpx; padding: 20rpx; border-radius: var(--radius-md); background: var(--bg-elevated); color: var(--text); font-size: 27rpx; line-height: 1.55; box-sizing: border-box; }
.ph { color: var(--text-placeholder); }
.input-actions { display: flex; gap: 14rpx; margin-top: 16rpx; }
.ghost-btn, .primary-btn, .confirm-btn, .home-btn { height: 82rpx; margin: 0; border: none; border-radius: var(--radius-md); font-size: 27rpx; font-weight: 900; }
.ghost-btn { width: 150rpx; background: var(--amber-bg); color: #9A651B; }
.primary-btn { flex: 1; background: linear-gradient(135deg, var(--teal), var(--teal-light)); color: #fff; }
.error-card { margin-top: 18rpx; padding: 18rpx; border-radius: var(--radius-md); background: var(--red-bg); color: var(--red); font-size: 24rpx; }
.section-head { display: flex; justify-content: space-between; margin: 28rpx 2rpx 14rpx; color: var(--text-muted); font-size: 23rpx; }
.section-head text:first-child { color: var(--text); font-size: 32rpx; font-weight: 950; }
.item-row { display: flex; align-items: center; gap: 14rpx; padding: 18rpx; margin-bottom: 12rpx; border-radius: var(--radius-md); background: #fff; box-shadow: var(--shadow-sm), var(--hairline); }
.item-mark { width: 66rpx; height: 66rpx; border-radius: 21rpx; background: var(--green-bg); color: var(--teal); display: flex; align-items: center; justify-content: center; font-size: 29rpx; font-weight: 950; }
.item-main { flex: 1; min-width: 0; }
.item-name { display: block; color: var(--text); font-size: 28rpx; font-weight: 950; }
.item-meta { display: block; margin-top: 4rpx; color: var(--text-muted); font-size: 22rpx; }
.delete-btn { width: 62rpx; height: 54rpx; margin: 0; border: none; border-radius: 18rpx; background: var(--red-bg); color: var(--red); font-size: 21rpx; font-weight: 900; }
.confirm-btn { width: 100%; margin-top: 12rpx; background: linear-gradient(135deg, var(--teal), var(--teal-light)); color: #fff; }
.home-btn { width: 100%; margin-top: 12rpx; background: #fff; color: var(--teal); box-shadow: var(--shadow-sm), var(--hairline); }
</style>
