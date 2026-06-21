<template>
  <view class="tool-page">
    <view class="hero">
      <text class="kicker">SCENE 05</text>
      <text class="title">探店向导</text>
      <text class="desc">拍经典菜品，独立调用菜品讲解接口，返回菜系、历史故事、口味特点和最佳吃法。</text>
    </view>

    <view class="photo-card" @tap="showImageOptions">
      <image v-if="selectedImage" :src="selectedImage" class="photo" mode="aspectFill" />
      <view v-else class="empty-photo">
        <view class="mark">游</view>
        <text>添加一道菜品照片</text>
        <text>适合白切鸡、东坡肉、麻婆豆腐等</text>
      </view>
    </view>

    <view class="actions">
      <button class="btn secondary" @tap="pickFromGallery">选择图片</button>
      <button class="btn primary" :disabled="loading" @tap="takePhoto">拍照讲解</button>
    </view>

    <view v-if="statusText" class="status-card">
      <text>{{ statusText }}</text>
    </view>
    <view v-if="errorMessage" class="error-card">
      <text>{{ errorMessage }}</text>
    </view>

    <view v-if="result?.status === 'ok'" class="guide-card">
      <view class="guide-top">
        <view>
          <text class="dish">{{ result.dish_name || '未知菜品' }}</text>
          <text class="meta">{{ result.cuisine || '其他菜系' }} · {{ result.category || '菜品' }} · {{ result.difficulty || '难度待定' }}</text>
        </view>
        <text v-if="result.from_knowledge_base" class="kb">知识库</text>
      </view>
      <view class="stat-row">
        <view>
          <text>{{ result.estimated_calories || 0 }}</text>
          <text>kcal</text>
        </view>
        <view>
          <text>{{ result.ingredients?.length || 0 }}</text>
          <text>主料</text>
        </view>
      </view>
      <view class="story-block">
        <text class="block-title">历史故事</text>
        <text>{{ result.history || '暂无历史说明' }}</text>
      </view>
      <view class="story-block">
        <text class="block-title">口味技法</text>
        <text>{{ result.features || '暂无口味说明' }}</text>
      </view>
      <view class="story-block">
        <text class="block-title">最佳吃法</text>
        <text>{{ result.best_eat || '暂无搭配建议' }}</text>
      </view>
      <view v-if="result.ingredients?.length" class="ingredient-line">
        <text v-for="item in result.ingredients" :key="item.name" class="chip">{{ item.name }} {{ item.amount || '' }}</text>
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
  uni.showActionSheet({ itemList: ['拍照', '从相册选择'], success: res => res.tapIndex === 0 ? takePhoto() : pickFromGallery() })
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
      explore()
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
    explore()
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
async function explore() {
  if (!selectedImage.value || loading.value) return
  loading.value = true
  result.value = null
  errorMessage.value = ''
  statusText.value = '正在识别菜品并匹配美食知识库...'
  try {
    result.value = await ApiService.exploreFoodGuide(await imagePayload())
    statusText.value = result.value?.status === 'ok' ? '讲解完成，适合探店演示。' : (result.value?.message || '未识别到菜品')
  } catch (e) {
    errorMessage.value = e.message || '探店向导失败'
    statusText.value = ''
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.tool-page { min-height: 100vh; padding: 30rpx; background: linear-gradient(180deg, #FAFCFB 0%, var(--bg) 46%); box-sizing: border-box; }
.hero { padding: 28rpx; border-radius: var(--radius-xl); background: linear-gradient(145deg, #4D3558, #23634D); color: #fff; box-shadow: var(--shadow-lg); }
.kicker { display: block; font-size: 21rpx; opacity: .72; font-weight: 900; }
.title { display: block; margin-top: 8rpx; font-size: 44rpx; font-weight: 950; }
.desc { display: block; margin-top: 12rpx; font-size: 25rpx; line-height: 1.45; opacity: .84; }
.photo-card { height: 420rpx; margin-top: 22rpx; border-radius: var(--radius-xl); overflow: hidden; background: linear-gradient(135deg, var(--purple-bg), #fff); box-shadow: var(--shadow-md), var(--hairline); }
.photo { width: 100%; height: 100%; }
.empty-photo { height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 12rpx; color: var(--text-muted); font-size: 24rpx; }
.mark { width: 104rpx; height: 104rpx; border-radius: 32rpx; display: flex; align-items: center; justify-content: center; background: #fff; color: var(--berry); font-size: 42rpx; font-weight: 950; box-shadow: var(--shadow-sm); }
.actions { display: flex; gap: 16rpx; margin-top: 18rpx; }
.btn { flex: 1; height: 86rpx; margin: 0; border: none; border-radius: var(--radius-md); font-size: 27rpx; font-weight: 900; }
.primary { background: linear-gradient(135deg, var(--teal), var(--teal-light)); color: #fff; }
.secondary { background: #fff; color: var(--teal); box-shadow: var(--shadow-sm), var(--hairline); }
.status-card, .error-card, .guide-card { margin-top: 18rpx; padding: 20rpx; border-radius: var(--radius-md); box-shadow: var(--shadow-sm), var(--hairline); }
.status-card { background: var(--blue-bg); color: var(--text-secondary); font-size: 24rpx; line-height: 1.45; }
.error-card { background: var(--red-bg); color: var(--red); font-size: 24rpx; }
.guide-card { background: #fff; }
.guide-top { display: flex; justify-content: space-between; align-items: flex-start; gap: 16rpx; }
.dish { display: block; color: var(--text); font-size: 38rpx; font-weight: 950; }
.meta { display: block; margin-top: 8rpx; color: var(--text-muted); font-size: 23rpx; }
.kb { padding: 6rpx 13rpx; border-radius: var(--radius-full); background: var(--green-bg); color: var(--teal); font-size: 21rpx; font-weight: 900; flex-shrink: 0; }
.stat-row { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12rpx; margin-top: 18rpx; }
.stat-row view { padding: 16rpx; border-radius: 20rpx; background: var(--bg-elevated); }
.stat-row text:first-child { display: block; color: var(--text); font-size: 32rpx; font-weight: 950; }
.stat-row text:last-child { display: block; margin-top: 4rpx; color: var(--text-muted); font-size: 21rpx; }
.story-block { margin-top: 16rpx; padding: 16rpx; border-radius: 20rpx; background: var(--bg-elevated); }
.story-block text:last-child { display: block; margin-top: 7rpx; color: var(--text-secondary); font-size: 24rpx; line-height: 1.55; }
.block-title { display: block; color: var(--text); font-size: 23rpx; font-weight: 950; }
.ingredient-line { display: flex; flex-wrap: wrap; gap: 10rpx; margin-top: 16rpx; }
.chip { padding: 8rpx 13rpx; border-radius: var(--radius-full); background: var(--amber-bg); color: #9A651B; font-size: 22rpx; font-weight: 800; }
</style>
