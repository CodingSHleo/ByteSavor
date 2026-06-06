<template>
  <view class="ir-page">
    <!-- 标题 -->
    <view class="ir-header">
      <text class="ir-title">{{ $t('smartIngredientRecognition') }}</text>
      <text class="ir-desc">拍照或从相册选择食材图片，AI将自动识别食材并分析新鲜度</text>
    </view>

    <!-- 图片区域 -->
    <view class="ir-image-box" @tap="showImageOptions">
      <image v-if="selectedImage" :src="selectedImage" class="ir-image" mode="aspectFill" />
      <view v-else class="ir-placeholder">
        <image class="ir-placeholder-icon" src="/static/icons/icon_camera.svg" mode="widthFix" />
        <text class="ir-placeholder-text">{{ $t('noImage') }}</text>
      </view>
    </view>

    <!-- 操作按钮 -->
    <view class="ir-actions">
      <button class="ir-btn ir-btn-outline" @tap="pickFromGallery">
        <image class="btn-small-icon" src="/static/icons/icon_export.svg" mode="widthFix" />
        <text>{{ $t('selectFromGallery') }}</text>
      </button>
      <button class="ir-btn ir-btn-primary" @tap="takePhoto">
        <image class="btn-small-icon" src="/static/icons/icon_camera.svg" mode="widthFix" />
        <text>{{ $t('takePhoto') }}</text>
      </button>
    </view>


    <!-- 状态 -->
    <view v-if="recognitionStatus" class="ir-status">
      <text>{{ recognitionStatus }}</text>
      <view v-if="isLoading" class="loading-dots">
        <view class="dot"></view><view class="dot"></view><view class="dot"></view>
      </view>
    </view>

    <!-- 错误 -->
    <view v-if="errorMessage" class="error-banner">
      <text>⚠️ {{ errorMessage }}</text>
    </view>

    <!-- 识别结果 -->
    <view v-if="recognizedIngredients.length > 0" class="ir-results">
      <text class="section-title">{{ $t('recognitionResults') }}</text>
      <view
        v-for="(item, idx) in recognizedIngredients"
        :key="idx"
        class="ir-ingredient-card"
      >
        <view class="ir-ing-avatar">
          <text class="ir-ing-letter">{{ item.name.charAt(0).toUpperCase() }}</text>
        </view>
        <view class="ir-ing-info">
          <text class="ir-ing-name">{{ item.name }}</text>
          <text class="ir-ing-detail">{{ $t('confidence') }}: {{ (item.confidence * 100).toFixed(1) }}%</text>
          <text class="ir-ing-detail">{{ $t('freshness') }}: {{ item.freshness }} ({{ item.state }})</text>
          <text v-if="item.features" class="ir-ing-features">{{ $t('features') }}: {{ item.features }}</text>
        </view>
        <image class="ir-ing-edit" @tap="editIngredient(item, idx)" src="/static/icons/icon_edit.svg" mode="widthFix" />
      </view>

      <!-- 确认按钮 -->
      <button class="btn-confirm" @tap="confirmAndNavigate">
        {{ $t('confirmAndGoToDashboard') }}
      </button>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { ApiService } from '@/api/index'
import { useHistoryStore } from '@/store/history'
import { t } from '@/utils/i18n'

const $t = key => t(key)
const historyStore = useHistoryStore()

const selectedImage = ref('')
const recognizedIngredients = ref([])
const isLoading = ref(false)
const errorMessage = ref('')
const recognitionStatus = ref('')

function showImageOptions() {
  uni.showActionSheet({
    itemList: [$t('takePhoto'), $t('selectFromGallery')],
    success: (res) => {
      if (res.tapIndex === 0) takePhoto()
      else pickFromGallery()
    }
  })
}

function triggerFileInput(capture) {
  // 动态创建 file input（避免 #ifdef 编译问题）
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'image/*'
  if (capture) input.setAttribute('capture', 'environment')
  input.onchange = handleNativeFile
  input.click()
}

function takePhoto() {
  // #ifdef H5
  triggerFileInput(true)
  // #endif
  // #ifndef H5
  uni.chooseMedia({
    count: 1,
    mediaType: ['image'],
    sourceType: ['camera'],
    success: (res) => {
      const tempFile = res.tempFiles[0]
      selectedImage.value = tempFile.tempFilePath
      recognizedIngredients.value = []
      recognitionStatus.value = '正在上传图片...'
      analyzeImage()
    },
    fail: () => { errorMessage.value = $t('photoFailed') }
  })
  // #endif
}

function pickFromGallery() {
  // #ifdef H5
  triggerFileInput(false)
  // #endif
  // #ifndef H5
  uni.chooseMedia({
    count: 1,
    mediaType: ['image'],
    sourceType: ['album'],
    success: (res) => {
      const tempFile = res.tempFiles[0]
      selectedImage.value = tempFile.tempFilePath
      recognizedIngredients.value = []
      recognitionStatus.value = '正在上传图片...'
      analyzeImage()
    },
    fail: () => { errorMessage.value = $t('selectImageFailed') }
  })
  // #endif
}

function handleNativeFile(e) {
  const file = e.target?.files?.[0] || e.detail?.files?.[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = (ev) => {
    selectedImage.value = ev.target.result
    recognizedIngredients.value = []
    recognitionStatus.value = '正在识别食材...'
    analyzeImage()
  }
  reader.readAsDataURL(file)
}

async function analyzeImage() {
  if (!selectedImage.value) return
  isLoading.value = true
  recognitionStatus.value = 'VLM多模态模型推理中...'

  try {
    let imageData = selectedImage.value
    // 如果是本地文件路径（小程序），读文件转 base64
    if (!imageData.startsWith('data:')) {
      const fs = uni.getFileSystemManager()
      const base64 = await new Promise((resolve, reject) => {
        fs.readFile({
          filePath: imageData,
          encoding: 'base64',
          success: (r) => resolve(r.data),
          fail: reject
        })
      })
      imageData = `data:image/jpeg;base64,${base64}`
    }
    const ingredients = await ApiService.analyzeIngredient(imageData)
    recognizedIngredients.value = ingredients
    recognitionStatus.value = `识别完成！检测到${ingredients.length}种食材`
    isLoading.value = false

    if (ingredients.length > 0) {
      showVisionVerify(ingredients[0])
    }
  } catch (e) {
    errorMessage.value = $t('aiRecognitionFailed') + ': ' + (e.message || e)
    recognitionStatus.value = ''
    isLoading.value = false
  }
}

function showVisionVerify(ingredient) {
  uni.showModal({
    title: $t('visualVerification'),
    content: t('confirmEditTitle', { name: ingredient.name, freshness: ingredient.freshness }),
    cancelText: $t('needCorrection'),
    confirmText: $t('correctRecognition'),
    success: (res) => {
      if (res.cancel) {
        showManualCorrection(ingredient)
      }
    }
  })
}

function showManualCorrection(ingredient) {
  // 简化版本：逐个修正
  uni.showModal({
    title: $t('manualCorrection'),
    content: `${$t('ingredientName')}: ${ingredient.name}\n${$t('freshness')}: ${ingredient.freshness}`,
    editable: true,
    placeholderText: ingredient.name,
    success: (res) => {
      if (res.confirm && res.content) {
        const idx = recognizedIngredients.value.indexOf(ingredient)
        if (idx >= 0) {
          recognizedIngredients.value[idx] = {
            ...ingredient,
            name: res.content
          }
        }
      }
    }
  })
}

function editIngredient(ingredient, idx) {
  uni.showModal({
    title: $t('manualCorrection'),
    content: `${$t('ingredientName')}: ${ingredient.name}`,
    editable: true,
    placeholderText: ingredient.name,
    success: (res) => {
      if (res.confirm && res.content) {
        recognizedIngredients.value[idx] = {
          ...ingredient,
          name: res.content
        }
      }
    }
  })
}

function confirmAndNavigate() {
  if (recognizedIngredients.value.length === 0) {
    uni.showToast({ title: $t('pleaseRecognizeIngredients'), icon: 'none' })
    return
  }
  historyStore.addEntry({
    type: 'scan',
    title: $t('scanCompleteTitle'),
    detail: t('scanCompleteDetail', { n: recognizedIngredients.value.length })
  })
  // 保存到本地，首页可直接读取
  uni.setStorageSync('last_ingredients', JSON.stringify(recognizedIngredients.value))
  const data = encodeURIComponent(JSON.stringify(recognizedIngredients.value))
  uni.navigateTo({ url: `/pages/health-dashboard/health-dashboard?ingredients=${data}` })
}
</script>

<style scoped>
.ir-page { min-height: 100vh; background: var(--bg-color); padding: 24rpx; }
.ir-header { margin-bottom: 32rpx; }
.ir-title { font-size: 40rpx; font-weight: bold; color: var(--text-color); display: block; }
.ir-desc { font-size: 26rpx; color: var(--text-secondary); margin-top: 12rpx; display: block; }
.ir-image-box {
  width: 100%;
  height: 500rpx;
  background: var(--card-bg);
  border: 2rpx dashed var(--border-color);
  border-radius: 16rpx;
  overflow: hidden;
  margin-bottom: 24rpx;
}
.ir-image { width: 100%; height: 100%; }
.ir-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
}
.ir-placeholder-icon { width: 88rpx; height: 88rpx; margin-bottom: 12rpx; }
.ir-placeholder-text { color: var(--text-secondary); font-size: 28rpx; margin-top: 16rpx; }
.ir-actions { display: flex; gap: 16rpx; margin-bottom: 24rpx; }
.ir-btn {
  flex: 1;
  height: 88rpx;
  border: none;
  border-radius: 16rpx;
  font-size: 28rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}
.btn-small-icon { width: 36rpx; height: 36rpx; margin-right: 10rpx; }
.ir-btn-primary { background: var(--accent); color: #fff; }
.ir-btn-outline { background: var(--info-bg); color: var(--accent); }
.ir-status {
  background: var(--info-bg);
  border: 1rpx solid var(--info-border);
  border-radius: 12rpx;
  padding: 20rpx;
  margin-bottom: 24rpx;
  display: flex;
  align-items: center;
  gap: 12rpx;
  font-size: 26rpx;
  color: var(--accent);
}
.loading-dots { display: flex; gap: 8rpx; }
.dot {
  width: 12rpx; height: 12rpx;
  background: var(--accent); border-radius: 50%;
  animation: blink 1.4s infinite ease-in-out both;
}
.dot:nth-child(2) { animation-delay: 0.16s; }
.dot:nth-child(3) { animation-delay: 0.32s; }
@keyframes blink {
  0%, 80%, 100% { opacity: 0; }
  40% { opacity: 1; }
}
.section-title {
  font-size: 34rpx;
  font-weight: bold;
  color: var(--text-color);
  margin-bottom: 20rpx;
  display: block;
}
.ir-ingredient-card {
  display: flex;
  align-items: center;
  background: var(--card-bg);
  border-radius: 16rpx;
  padding: 24rpx;
  margin-bottom: 16rpx;
}
.ir-ing-avatar {
  width: 100rpx;
  height: 100rpx;
  background: var(--accent-bg);
  border-radius: 16rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}
.ir-ing-letter { font-size: 48rpx; font-weight: bold; color: var(--accent); }
.ir-ing-info { flex: 1; margin-left: 20rpx; }
.ir-ing-name { font-size: 30rpx; font-weight: bold; color: var(--text-color); display: block; }
.ir-ing-detail { font-size: 24rpx; color: var(--text-secondary); display: block; }
.ir-ing-features { font-size: 22rpx; color: var(--text-secondary); }
.ir-ing-edit { width: 44rpx; height: 44rpx; }
.btn-confirm {
  width: 100%;
  height: 90rpx;
  background: var(--success);
  color: #fff;
  border: none;
  border-radius: 16rpx;
  font-size: 32rpx;
  font-weight: bold;
  margin-top: 16rpx;
}
</style>
