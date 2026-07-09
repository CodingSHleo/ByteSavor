<template>
  <view class="ir-page">
    <view class="ir-header">
      <text class="ir-title">{{ $t('smartIngredientRecognition') }}</text>
      <text class="ir-desc">拍照或选择食材图片，AI 将识别食材、新鲜度与可用特征。</text>
    </view>

    <view class="scan-panel" @tap="showImageOptions">
      <image v-if="selectedImage" :src="selectedImage" class="scan-image" mode="aspectFill" />
      <view v-else class="scan-empty">
        <view class="scan-icon-wrap">
          <image class="scan-icon" src="/static/icons/icon_scan.svg" mode="aspectFit" />
          <text>扫</text>
        </view>
        <text class="scan-title">添加一张食材照片</text>
        <text class="scan-sub">支持冰箱、菜板、餐盘等场景</text>
      </view>
      <view class="scan-grid"></view>
      <view class="scan-corners">
        <view></view><view></view><view></view><view></view>
      </view>
    </view>

    <view class="ir-actions">
      <button class="ir-btn secondary" @tap="pickFromGallery">
        <view class="btn-icon-shell">
          <image class="btn-small-icon" src="/static/icons/icon_export.svg" mode="aspectFit" />
          <text>相</text>
        </view>
        <text>{{ $t('selectFromGallery') }}</text>
      </button>
      <button class="ir-btn primary" @tap="takePhoto">
        <view class="btn-icon-shell">
          <image class="btn-small-icon" src="/static/icons/icon_camera.svg" mode="aspectFit" />
          <text>拍</text>
        </view>
        <text>{{ $t('takePhoto') }}</text>
      </button>
    </view>

    <view class="stage-card">
      <view v-for="(stage, idx) in stages" :key="stage.label" class="stage-item" :class="{ active: stageIndex >= idx }">
        <view class="stage-dot">{{ idx + 1 }}</view>
        <text>{{ stage.label }}</text>
      </view>
    </view>

    <view v-if="recognitionStatus" class="ir-status">
      <view class="status-copy">
        <text>{{ recognitionStatus }}</text>
        <text v-if="recognitionMetaText" class="status-meta">{{ recognitionMetaText }}</text>
      </view>
      <view v-if="isLoading" class="loading-dots">
        <view class="dot"></view><view class="dot"></view><view class="dot"></view>
      </view>
    </view>

    <view v-if="errorMessage" class="error-banner">
      <text>{{ errorMessage }}</text>
    </view>

    <view v-if="recognizedIngredients.length > 0" class="ir-results">
      <view class="section-head">
        <text>{{ $t('recognitionResults') }}</text>
        <text class="section-sub">{{ recognizedIngredients.length }} 种已确认食材</text>
      </view>
      <view v-for="(item, idx) in recognizedIngredients" :key="idx" class="ingredient-card">
        <view class="ing-symbol" :class="freshnessClass(item.freshness)">
          <text>{{ item.name.charAt(0).toUpperCase() }}</text>
        </view>
        <view class="ing-info">
          <view class="ing-title-row">
            <text class="ing-name">{{ item.name }}</text>
            <text class="freshness-pill" :class="freshnessClass(item.freshness)">{{ freshnessLabel(item.freshness) }}</text>
          </view>
          <view class="confidence-row">
            <view class="confidence-track">
              <view class="confidence-fill" :style="{ width: Math.round((item.confidence || 0) * 100) + '%' }"></view>
            </view>
            <text>{{ ((item.confidence || 0) * 100).toFixed(0) }}%</text>
          </view>
          <text v-if="item.features" class="ing-features">{{ item.features }}</text>
          <text v-else class="ing-features">{{ item.state || '等待确认' }}</text>
          <text v-if="item.source_count > 1" class="merge-note">已将 {{ item.source_count }} 个相同候选合并为 1 项</text>
        </view>
        <view class="card-actions">
          <button class="icon-action" @tap.stop="editIngredient(item, idx)">
            <image src="/static/icons/icon_edit.svg" mode="aspectFit" />
          </button>
          <button class="icon-action danger" @tap.stop="deleteIngredient(idx)">
            <image src="/static/icons/icon_delete.svg" mode="aspectFit" />
          </button>
        </view>
      </view>

      <button class="btn-add" @tap="addIngredient">手动添加食材</button>
      <button class="btn-confirm" @tap="confirmAndNavigate">
        确认并生成清单
      </button>
    </view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ApiService } from '@/api/index'
import { useHistoryStore } from '@/store/history'
import { t } from '@/utils/i18n'
import { mergeRecognizedIngredients, removeIngredientAt, updateIngredientAt } from '@/utils/ingredient-confirmation'

const $t = key => t(key)
const historyStore = useHistoryStore()

const selectedImage = ref('')
const recognizedIngredients = ref([])
const isLoading = ref(false)
const errorMessage = ref('')
const recognitionStatus = ref('')
const recognitionMeta = ref(null)
const recognitionMetaText = computed(() => {
  const meta = recognitionMeta.value
  if (!meta || typeof meta.latency_ms !== 'number') return ''
  const cacheText = meta.cache_hit ? '缓存命中' : '实时推理'
  return `${cacheText} · ${meta.latency_ms}ms`
})
const stages = [{ label: '上传图片' }, { label: 'AI 识别' }, { label: '人工校正' }]
const stageIndex = computed(() => {
  if (recognizedIngredients.value.length > 0) return 2
  if (isLoading.value) return 1
  if (selectedImage.value) return 0
  return -1
})

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
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'image/*'
  if (capture) input.setAttribute('capture', 'environment')
  input.onchange = handleNativeFile
  input.style.display = 'none'
  document.body.appendChild(input)  // 挂到DOM防移动端回收
  input.click()
  setTimeout(() => { if (input.parentNode) input.parentNode.removeChild(input) }, 60000)
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
      recognitionMeta.value = null
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
      recognitionMeta.value = null
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
  recognitionStatus.value = '正在压缩图片...'
  recognitionMeta.value = null
  recognizedIngredients.value = []
  const reader = new FileReader()
  reader.onload = (ev) => {
    compressImage(ev.target.result, (compressed) => {
      selectedImage.value = compressed
      recognitionStatus.value = '图片已压缩，准备调用视觉模型...'
      analyzeImage()
    })
  }
  reader.readAsDataURL(file)
}

function compressImage(dataUrl, callback) {
  const img = new Image()
  img.onload = () => {
    const maxW = 512
    let w = img.width, h = img.height
    if (w > maxW) { h = h * maxW / w; w = maxW }
    const canvas = document.createElement('canvas')
    canvas.width = w; canvas.height = h
    canvas.getContext('2d').drawImage(img, 0, 0, w, h)
    callback(canvas.toDataURL('image/jpeg', 0.58))
  }
  img.src = dataUrl
}

async function analyzeImage() {
  if (!selectedImage.value) return
  isLoading.value = true
  recognitionStatus.value = 'VLM 多模态模型推理中...'

  try {
    let imageData = selectedImage.value
    if (!imageData.startsWith('data:')) {
      recognitionStatus.value = '正在读取图片...'
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
      recognitionStatus.value = '图片已准备，准备调用视觉模型...'
    }
    if (imageData.length > 5 * 1024 * 1024) {
      recognitionStatus.value = '图片较大，已进入服务端大小校验，建议下次使用压缩图以提升速度...'
    }
    recognitionStatus.value = 'VLM 多模态模型推理中...'
    const analysis = await ApiService.analyzeIngredientDetail(imageData)
    recognitionMeta.value = {
      cache_hit: !!analysis.cache_hit,
      latency_ms: analysis.latency_ms,
      model: analysis.model,
      prompt_version: analysis.prompt_version,
      cache_key: analysis.cache_key
    }
    if (analysis.cache_hit) {
      recognitionStatus.value = '命中缓存，已快速识别'
    }
    const ingredients = mergeRecognizedIngredients(analysis.ingredients || [])
    recognizedIngredients.value = ingredients
    const latencyText = Number.isFinite(Number(analysis.latency_ms))
      ? ` · ${analysis.latency_ms}ms`
      : ''
    recognitionStatus.value = analysis.cache_hit
      ? `命中缓存，已快速识别${latencyText}。识别完成，请确认 ${ingredients.length} 种食材`
      : `识别完成${latencyText}，请确认 ${ingredients.length} 种食材`
    isLoading.value = false

    if (ingredients.length > 0) {
      showVisionVerify(ingredients[0])
    }
  } catch (e) {
    const rawMessage = e.message || e
    const timeoutHint = String(rawMessage).includes('timeout') || String(rawMessage).includes('超时')
      ? '视觉模型响应超时，请换一张更清晰/更小的图片重试。'
      : rawMessage
    errorMessage.value = $t('aiRecognitionFailed') + ': ' + timeoutHint
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
  uni.showModal({
    title: $t('manualCorrection'),
    content: `${$t('ingredientName')}: ${ingredient.name}\n${$t('freshness')}: ${ingredient.freshness}`,
    editable: true,
    placeholderText: ingredient.name,
    success: (res) => {
      if (res.confirm && res.content) {
        const idx = recognizedIngredients.value.indexOf(ingredient)
        if (idx >= 0) {
          recognizedIngredients.value = updateIngredientAt(recognizedIngredients.value, idx, { name: res.content, source_count: 1 })
        }
      }
    }
  })
}

function editIngredient(ingredient, idx) {
  const oldName = ingredient.name
  uni.showModal({
    title: $t('manualCorrection'),
    content: `${$t('ingredientName')}: ${ingredient.name}`,
    editable: true,
    placeholderText: ingredient.name,
    success: (res) => {
      if (res.confirm && res.content) {
        recognizedIngredients.value = updateIngredientAt(recognizedIngredients.value, idx, { name: res.content, source_count: 1 })
        // P1-9: 写入纠错日志
        ApiService.recordCorrection({
          action: 'rename',
          source: 'sense',
          original_name: oldName,
          corrected_name: res.content,
          confidence: ingredient.confidence || 0,
          meta: { page: 'ingredient-recognition' }
        }).catch((e) => {
  console.warn('[correction] recordCorrection failed:', e)
})
      }
    }
  })
}

function deleteIngredient(idx) {
  const item = recognizedIngredients.value[idx]
  uni.showModal({
    title: '删除食材',
    content: `确定删除「${item?.name || '该食材'}」吗？`,
    cancelText: $t('cancel'),
    confirmText: '删除',
    success: (res) => {
      if (res.confirm) {
        recognizedIngredients.value = removeIngredientAt(recognizedIngredients.value, idx)
        // P1-9: 写入纠错日志
        ApiService.recordCorrection({
          action: 'delete',
          source: 'sense',
          original_name: item?.name || '',
          confidence: item?.confidence || 0,
          meta: { page: 'ingredient-recognition' }
        }).catch((e) => {
  console.warn('[correction] recordCorrection failed:', e)
})
        recognitionStatus.value = recognizedIngredients.value.length
          ? `已确认 ${recognizedIngredients.value.length} 种食材`
          : '识别结果已清空，请重新添加或拍照'
      }
    }
  })
}

function addIngredient() {
  uni.showModal({
    title: '添加食材',
    editable: true,
    placeholderText: '例如：西瓜',
    cancelText: $t('cancel'),
    confirmText: $t('add'),
    success: (res) => {
      const name = String(res.content || '').trim()
      if (res.confirm && name) {
        recognizedIngredients.value = mergeRecognizedIngredients([
          ...recognizedIngredients.value,
          { name, confidence: 1, freshness: 'medium', state: '手动确认', features: '用户手动添加' }
        ])
        recognitionStatus.value = `已确认 ${recognizedIngredients.value.length} 种食材`
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
  uni.setStorageSync('last_ingredients', JSON.stringify(recognizedIngredients.value))
  ApiService.importInventory(recognizedIngredients.value, 'scan')
    .catch(() => {})
    .finally(() => {
      const data = encodeURIComponent(JSON.stringify(recognizedIngredients.value))
      uni.navigateTo({ url: `/pages/list-export/list-export?items=${data}&title=${encodeURIComponent('本次识别食材')}&source=scan` })
    })
}

function freshnessLabel(f) { return ({ high: '新鲜', normal: '冷藏', medium: '普通', low: '待确认' })[f] || f || '待确认' }
function freshnessClass(f) { return f === 'high' ? 'fresh-high' : f === 'low' ? 'fresh-low' : 'fresh-normal' }
</script>

<style scoped>
.ir-page {
  min-height: 100vh;
  background:
    radial-gradient(circle at 50% 0%, rgba(35,169,120,.13), transparent 34%),
    linear-gradient(180deg, #FAFCFB 0%, var(--bg) 46%);
  padding: 28rpx;
}
.ir-header { margin-bottom: 24rpx; }
.ir-title { font-size: 44rpx; line-height: 1.15; font-weight: 950; color: var(--text); display: block; }
.ir-desc { font-size: 25rpx; color: var(--text-secondary); margin-top: 10rpx; display: block; line-height: 1.45; }
.scan-panel {
  height: 520rpx;
  background:
    radial-gradient(circle at 50% 38%, rgba(35,169,120,.10), transparent 34%),
    linear-gradient(135deg, #E8F8F0, #FFFFFF);
  border-radius: var(--radius-xl);
  overflow: hidden;
  position: relative;
  margin-bottom: 18rpx;
  box-shadow: var(--shadow-lg), var(--hairline);
}
.scan-panel::after {
  content: "";
  position: absolute;
  left: 36rpx;
  right: 36rpx;
  top: 90rpx;
  height: 3rpx;
  border-radius: 999rpx;
  background: linear-gradient(90deg, transparent, rgba(35,169,120,.72), transparent);
  box-shadow: 0 0 22rpx rgba(35,169,120,.24);
  animation: scan-line 2.8s ease-in-out infinite;
}
.scan-grid {
  position: absolute;
  inset: 34rpx;
  border-radius: 34rpx;
  opacity: .22;
  pointer-events: none;
  background-image:
    linear-gradient(rgba(35,169,120,.20) 1rpx, transparent 1rpx),
    linear-gradient(90deg, rgba(35,169,120,.20) 1rpx, transparent 1rpx);
  background-size: 54rpx 54rpx;
  mask-image: radial-gradient(circle at center, #000 0%, rgba(0,0,0,.55) 52%, transparent 78%);
}
@keyframes scan-line {
  0%, 100% { transform: translateY(0); opacity: .15; }
  45% { opacity: .8; }
  50% { transform: translateY(330rpx); opacity: .65; }
}
.scan-image { width: 100%; height: 100%; }
.scan-empty { height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.scan-icon-wrap { width: 118rpx; height: 118rpx; border-radius: 34rpx; background: rgba(255,255,255,.94); display: flex; align-items: center; justify-content: center; box-shadow: var(--shadow-md), var(--hairline); position: relative; animation: float-breathe 3.6s ease-in-out infinite; }
.scan-icon-wrap text { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; color: var(--teal); font-size: 34rpx; font-weight: 900; opacity: .24; }
.scan-icon { width: 66rpx; height: 66rpx; position: relative; z-index: 1; }
.scan-title { margin-top: 26rpx; font-size: 32rpx; font-weight: 950; color: var(--text); }
.scan-sub { margin-top: 8rpx; font-size: 24rpx; color: var(--text-muted); }
.scan-corners view { position: absolute; width: 46rpx; height: 46rpx; border-color: rgba(35,169,120,.55); }
.scan-corners view:nth-child(1) { left: 28rpx; top: 28rpx; border-left: 4rpx solid; border-top: 4rpx solid; border-radius: 12rpx 0 0 0; }
.scan-corners view:nth-child(2) { right: 28rpx; top: 28rpx; border-right: 4rpx solid; border-top: 4rpx solid; border-radius: 0 12rpx 0 0; }
.scan-corners view:nth-child(3) { left: 28rpx; bottom: 28rpx; border-left: 4rpx solid; border-bottom: 4rpx solid; border-radius: 0 0 0 12rpx; }
.scan-corners view:nth-child(4) { right: 28rpx; bottom: 28rpx; border-right: 4rpx solid; border-bottom: 4rpx solid; border-radius: 0 0 12rpx 0; }
.ir-actions { display: flex; gap: 16rpx; margin-bottom: 18rpx; }
.ir-btn { flex: 1; height: 90rpx; margin: 0; padding: 0 18rpx; border: none; border-radius: var(--radius-md); font-size: 27rpx; font-weight: 900; line-height: 1; display: flex; align-items: center; justify-content: center; box-sizing: border-box; }
.ir-btn.primary { background: linear-gradient(135deg, var(--teal), var(--teal-light)); color: #fff; box-shadow: 0 16rpx 32rpx rgba(35,169,120,.18); }
.ir-btn.secondary { background: rgba(255,255,255,.94); color: var(--teal); box-shadow: var(--shadow-sm), var(--hairline); }
.btn-icon-shell { width: 40rpx; height: 40rpx; margin-right: 10rpx; position: relative; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.btn-small-icon { width: 36rpx; height: 36rpx; position: relative; z-index: 1; }
.btn-icon-shell text { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; font-size: 18rpx; font-weight: 900; opacity: .22; }
.stage-card { background: rgba(255,255,255,.94); border-radius: var(--radius-md); padding: 18rpx; display: grid; grid-template-columns: repeat(3, 1fr); gap: 8rpx; box-shadow: var(--shadow-sm), var(--hairline); margin-bottom: 18rpx; }
.stage-item { display: flex; align-items: center; justify-content: center; gap: 8rpx; color: var(--text-muted); font-size: 22rpx; }
.stage-dot { width: 34rpx; height: 34rpx; border-radius: 50%; background: var(--border-light); display: flex; align-items: center; justify-content: center; font-size: 18rpx; font-weight: 900; }
.stage-item.active { color: var(--teal); font-weight: 800; }
.stage-item.active .stage-dot { background: var(--teal-bg); box-shadow: inset 0 0 0 1rpx rgba(35,169,120,.12); }
.ir-status { background: linear-gradient(135deg, var(--blue-bg), #FFFFFF); border-radius: var(--radius-md); padding: 18rpx 20rpx; margin-bottom: 18rpx; display: flex; align-items: center; justify-content: space-between; gap: 12rpx; font-size: 25rpx; color: var(--text-secondary); box-shadow: var(--shadow-sm), var(--hairline); }
.status-copy { min-width: 0; display: flex; flex-direction: column; gap: 6rpx; }
.status-meta { font-size: 21rpx; color: var(--text-muted); }
.loading-dots { display: flex; gap: 8rpx; }
.dot { width: 12rpx; height: 12rpx; background: var(--teal); border-radius: 50%; animation: blink 1.4s infinite ease-in-out both; }
.dot:nth-child(2) { animation-delay: .16s; }
.dot:nth-child(3) { animation-delay: .32s; }
@keyframes blink { 0%, 80%, 100% { opacity: .25; } 40% { opacity: 1; } }
.section-head { display: flex; justify-content: space-between; align-items: baseline; margin: 24rpx 2rpx 14rpx; }
.section-head text:first-child { font-size: 32rpx; font-weight: 900; color: var(--text); }
.section-sub { font-size: 23rpx; color: var(--text-muted); }
.ingredient-card { display: flex; align-items: flex-start; gap: 16rpx; background: linear-gradient(145deg, #FFFFFF, #F9FCFA); border-radius: var(--radius-md); padding: 20rpx; margin-bottom: 14rpx; box-shadow: var(--shadow-sm), var(--hairline); animation: soft-pop .28s var(--ease) both; }
.ing-symbol { width: 84rpx; height: 84rpx; border-radius: 25rpx; display: flex; align-items: center; justify-content: center; flex-shrink: 0; box-shadow: inset 0 0 0 1rpx rgba(255,255,255,.6); }
.ing-symbol text { font-size: 32rpx; font-weight: 900; }
.fresh-high { background: var(--green-bg); color: var(--teal); }
.fresh-normal { background: var(--amber-bg); color: #9A651B; }
.fresh-low { background: var(--red-bg); color: var(--red); }
.ing-info { flex: 1; min-width: 0; }
.ing-title-row { display: flex; align-items: center; justify-content: space-between; gap: 10rpx; }
.ing-name { font-size: 30rpx; font-weight: 900; color: var(--text); }
.freshness-pill { border-radius: var(--radius-full); padding: 5rpx 12rpx; font-size: 20rpx; font-weight: 800; white-space: nowrap; }
.confidence-row { display: flex; align-items: center; gap: 10rpx; margin-top: 12rpx; color: var(--text-muted); font-size: 22rpx; }
.confidence-track { flex: 1; height: 8rpx; border-radius: 8rpx; background: var(--border-light); overflow: hidden; }
.confidence-fill { height: 100%; border-radius: 8rpx; background: linear-gradient(90deg, var(--teal), var(--teal-light)); transform-origin: left center; animation: bar-grow .5s var(--ease) both; }
.ing-features { display: block; margin-top: 10rpx; font-size: 23rpx; color: var(--text-secondary); line-height: 1.45; }
.merge-note { display: inline-flex; align-self: flex-start; margin-top: 10rpx; padding: 6rpx 12rpx; border-radius: var(--radius-full); background: var(--blue-bg); color: var(--blue); font-size: 20rpx; font-weight: 800; }
.card-actions { display: flex; flex-direction: column; gap: 10rpx; flex-shrink: 0; }
.icon-action { width: 56rpx; height: 56rpx; padding: 0; margin: 0; border-radius: 18rpx; border: none; background: var(--green-bg); display: flex; align-items: center; justify-content: center; box-shadow: inset 0 0 0 1rpx rgba(35,169,120,.08); }
.icon-action image { width: 30rpx; height: 30rpx; }
.icon-action.danger { background: var(--red-bg); }
.btn-add { width: 100%; height: 82rpx; background: rgba(255,255,255,.94); color: var(--teal); border: 1rpx solid var(--border-light); border-radius: var(--radius-md); font-size: 27rpx; font-weight: 900; margin-top: 10rpx; box-shadow: var(--shadow-sm); }
.btn-confirm { width: 100%; height: 94rpx; background: linear-gradient(135deg, var(--teal), var(--teal-light)); color: #fff; border: none; border-radius: var(--radius-md); font-size: 30rpx; font-weight: 950; margin-top: 16rpx; box-shadow: 0 18rpx 36rpx rgba(35,169,120,.20); }
</style>
