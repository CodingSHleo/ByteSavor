<template>
  <view class="tool-page quality">
    <view class="hero">
      <text class="kicker">SCENE 03</text>
      <text class="title">品质鉴定</text>
      <text class="desc">拍水果或食材照片，独立调用品质评估接口，输出新鲜度、等级、依据和购买建议。</text>
    </view>

    <view class="photo-card" @tap="showImageOptions">
      <image v-if="selectedImage" :src="selectedImage" class="photo" mode="aspectFill" />
      <view v-else class="empty-photo">
        <view class="mark">质</view>
        <text>添加一张待鉴定图片</text>
        <text>适合西瓜、番茄、榴莲、蔬菜等</text>
      </view>
    </view>

    <view class="actions">
      <button class="btn secondary" @tap="pickFromGallery">选择图片</button>
      <button class="btn primary" :disabled="loading" @tap="takePhoto">拍照鉴定</button>
    </view>

    <view v-if="statusText" class="status-card">
      <text>{{ statusText }}</text>
    </view>
    <view v-if="errorMessage" class="error-card">
      <text>{{ errorMessage }}</text>
    </view>

    <view v-if="result?.items?.length" class="section">
      <view class="section-head">
        <text>鉴定结果</text>
        <text>{{ result.items.length }} 项</text>
      </view>
      <view v-for="item in result.items" :key="item.name" class="result-card">
        <view class="grade" :class="gradeClass(item.grade)">
          <text>{{ item.grade || '待' }}</text>
        </view>
        <view class="result-main">
          <view class="result-title-row">
            <text class="result-title">{{ item.name }}</text>
            <text class="pill">{{ freshnessLabel(item.freshness) }}</text>
          </view>
          <text class="grade-text">{{ item.grade_text || '等待人工确认' }}</text>
          <text v-if="item.features" class="body-text">{{ item.features }}</text>
          <view class="info-block">
            <text class="info-label">判断依据</text>
            <text>{{ item.standard || item.tip || '暂无标准' }}</text>
          </view>
          <view v-if="item.tip" class="info-block muted">
            <text class="info-label">挑选建议</text>
            <text>{{ item.tip }}</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { ApiService } from '@/api/index'

const selectedImage = ref('')
const result = ref(null)
const loading = ref(false)
const statusText = ref('')
const errorMessage = ref('')

function showImageOptions() {
  uni.showActionSheet({
    itemList: ['拍照', '从相册选择'],
    success: res => res.tapIndex === 0 ? takePhoto() : pickFromGallery()
  })
}

function triggerFileInput(capture) {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'image/*'
  if (capture) input.setAttribute('capture', 'environment')
  input.onchange = handleNativeFile
  input.style.display = 'none'
  document.body.appendChild(input)
  input.click()
  setTimeout(() => { if (input.parentNode) input.parentNode.removeChild(input) }, 60000)
}

function takePhoto() {
  // #ifdef H5
  triggerFileInput(true)
  // #endif
  // #ifndef H5
  chooseNative(['camera'])
  // #endif
}

function pickFromGallery() {
  // #ifdef H5
  triggerFileInput(false)
  // #endif
  // #ifndef H5
  chooseNative(['album'])
  // #endif
}

function chooseNative(sourceType) {
  uni.chooseMedia({
    count: 1,
    mediaType: ['image'],
    sourceType,
    success: res => {
      selectedImage.value = res.tempFiles[0].tempFilePath
      assess()
    },
    fail: () => { errorMessage.value = '图片选择失败' }
  })
}

function handleNativeFile(e) {
  const file = e.target?.files?.[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = ev => compressImage(ev.target.result, dataUrl => {
    selectedImage.value = dataUrl
    assess()
  })
  reader.readAsDataURL(file)
}

function compressImage(dataUrl, callback) {
  const img = new Image()
  img.onload = () => {
    const maxW = 800
    let w = img.width
    let h = img.height
    if (w > maxW) { h = h * maxW / w; w = maxW }
    const canvas = document.createElement('canvas')
    canvas.width = w
    canvas.height = h
    canvas.getContext('2d').drawImage(img, 0, 0, w, h)
    callback(canvas.toDataURL('image/jpeg', 0.72))
  }
  img.src = dataUrl
}

async function imagePayload() {
  if (selectedImage.value.startsWith('data:')) return selectedImage.value
  const fs = uni.getFileSystemManager()
  const base64 = await new Promise((resolve, reject) => {
    fs.readFile({ filePath: selectedImage.value, encoding: 'base64', success: r => resolve(r.data), fail: reject })
  })
  return `data:image/jpeg;base64,${base64}`
}

async function assess() {
  if (!selectedImage.value || loading.value) return
  loading.value = true
  result.value = null
  errorMessage.value = ''
  statusText.value = '正在调用品质鉴定模型...'
  try {
    result.value = await ApiService.assessQuality(await imagePayload())
    statusText.value = result.value?.status === 'ok' ? '鉴定完成，结果来自后端品质接口。' : (result.value?.message || '未识别到可鉴定食材')
  } catch (e) {
    errorMessage.value = e.message || '品质鉴定失败'
    statusText.value = ''
  } finally {
    loading.value = false
  }
}

function freshnessLabel(f) { return ({ high: '新鲜', normal: '冷藏', medium: '普通', low: '风险' })[f] || f || '待确认' }
function gradeClass(g) { return g === '优' ? 'good' : g === '差' ? 'bad' : 'mid' }
</script>

<style scoped>
.tool-page { min-height: 100vh; padding: 30rpx; background: linear-gradient(180deg, #FAFCFB 0%, var(--bg) 46%); box-sizing: border-box; }
.hero { padding: 28rpx; border-radius: var(--radius-xl); background: linear-gradient(145deg, #173B2E, #23634D); color: #fff; box-shadow: var(--shadow-lg); }
.kicker { display: block; font-size: 21rpx; opacity: .72; font-weight: 900; }
.title { display: block; margin-top: 8rpx; font-size: 44rpx; font-weight: 950; }
.desc { display: block; margin-top: 12rpx; font-size: 25rpx; line-height: 1.45; opacity: .82; }
.photo-card { height: 430rpx; margin-top: 22rpx; border-radius: var(--radius-xl); overflow: hidden; background: linear-gradient(135deg, var(--teal-bg), #fff); box-shadow: var(--shadow-md), var(--hairline); }
.photo { width: 100%; height: 100%; }
.empty-photo { height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 12rpx; color: var(--text-muted); font-size: 24rpx; }
.mark { width: 104rpx; height: 104rpx; border-radius: 32rpx; display: flex; align-items: center; justify-content: center; background: #fff; color: var(--teal); font-size: 42rpx; font-weight: 950; box-shadow: var(--shadow-sm); }
.actions { display: flex; gap: 16rpx; margin-top: 18rpx; }
.btn { flex: 1; height: 86rpx; margin: 0; border: none; border-radius: var(--radius-md); font-size: 27rpx; font-weight: 900; }
.primary { background: linear-gradient(135deg, var(--teal), var(--teal-light)); color: #fff; }
.secondary { background: #fff; color: var(--teal); box-shadow: var(--shadow-sm), var(--hairline); }
.status-card, .error-card { margin-top: 18rpx; padding: 18rpx 20rpx; border-radius: var(--radius-md); font-size: 24rpx; line-height: 1.45; box-shadow: var(--shadow-sm), var(--hairline); }
.status-card { background: var(--blue-bg); color: var(--text-secondary); }
.error-card { background: var(--red-bg); color: var(--red); }
.section-head { display: flex; justify-content: space-between; margin: 28rpx 2rpx 14rpx; color: var(--text-muted); font-size: 23rpx; }
.section-head text:first-child { color: var(--text); font-size: 32rpx; font-weight: 950; }
.result-card { display: flex; gap: 16rpx; padding: 20rpx; margin-bottom: 14rpx; border-radius: var(--radius-md); background: #fff; box-shadow: var(--shadow-sm), var(--hairline); }
.grade { width: 82rpx; height: 82rpx; border-radius: 25rpx; display: flex; align-items: center; justify-content: center; flex-shrink: 0; font-size: 34rpx; font-weight: 950; }
.grade.good { background: var(--green-bg); color: var(--teal); }
.grade.mid { background: var(--amber-bg); color: #9A651B; }
.grade.bad { background: var(--red-bg); color: var(--red); }
.result-main { flex: 1; min-width: 0; }
.result-title-row { display: flex; justify-content: space-between; gap: 12rpx; align-items: center; }
.result-title { font-size: 31rpx; font-weight: 950; color: var(--text); }
.pill { padding: 5rpx 12rpx; border-radius: var(--radius-full); background: var(--bg); color: var(--text-muted); font-size: 20rpx; font-weight: 800; }
.grade-text { display: block; margin-top: 8rpx; color: var(--teal); font-size: 24rpx; font-weight: 900; }
.body-text, .info-block text:last-child { display: block; margin-top: 8rpx; color: var(--text-secondary); font-size: 23rpx; line-height: 1.45; }
.info-block { margin-top: 14rpx; padding: 14rpx; border-radius: 18rpx; background: var(--bg-elevated); }
.info-block.muted { background: var(--amber-bg); }
.info-label { display: block; color: var(--text); font-size: 21rpx; font-weight: 900; }
</style>
