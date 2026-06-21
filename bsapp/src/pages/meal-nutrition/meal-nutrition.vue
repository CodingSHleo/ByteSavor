<template>
  <view class="tool-page">
    <view class="hero">
      <text class="kicker">SCENE 04</text>
      <text class="title">一餐营养分析</text>
      <text class="desc">拍一顿饭，独立计算热量、蛋白质、碳水和脂肪。这里只做分析，不自动写入今日摄入。</text>
    </view>

    <view class="photo-card" @tap="showImageOptions">
      <image v-if="selectedImage" :src="selectedImage" class="photo" mode="aspectFill" />
      <view v-else class="empty-photo">
        <view class="mark">营</view>
        <text>添加一张餐盘照片</text>
        <text>适合米饭、肉类、蔬菜组合餐</text>
      </view>
    </view>

    <view class="goal-row">
      <view v-for="g in goals" :key="g.key" class="goal-chip" :class="{ active: goal === g.key }" @tap="goal = g.key">
        <text>{{ g.label }}</text>
      </view>
    </view>

    <view class="actions">
      <button class="btn secondary" @tap="pickFromGallery">选择图片</button>
      <button class="btn primary" :disabled="loading" @tap="takePhoto">拍照分析</button>
    </view>

    <view v-if="statusText" class="status-card">
      <text>{{ statusText }}</text>
    </view>
    <view v-if="errorMessage" class="error-card">
      <text>{{ errorMessage }}</text>
    </view>

    <view v-if="result?.total" class="summary-card">
      <text class="summary-kicker">本餐估算</text>
      <view class="calorie-line">
        <text>{{ result.total.calories || 0 }}</text>
        <text>kcal</text>
      </view>
      <view class="macro-row">
        <view class="macro">
          <text>{{ result.total.protein || 0 }}g</text>
          <text>蛋白质</text>
        </view>
        <view class="macro">
          <text>{{ result.total.carbs || 0 }}g</text>
          <text>碳水</text>
        </view>
        <view class="macro">
          <text>{{ result.total.fat || 0 }}g</text>
          <text>脂肪</text>
        </view>
      </view>
      <button class="eat-btn" :disabled="recording" @tap="confirmEaten">确认已吃并计入今日</button>
      <text class="eat-note">只有点击确认后才写入长期营养记录；写错后可在健康看板删除。</text>
    </view>

    <view v-if="result?.items?.length" class="section">
      <view class="section-head">
        <text>识别食物</text>
        <text>{{ result.items.length }} 项</text>
      </view>
      <view v-for="item in result.items" :key="item.name" class="food-row">
        <view class="food-mark">{{ item.name?.slice(0, 1) || '食' }}</view>
        <view class="food-main">
          <text class="food-name">{{ item.name }}</text>
          <text class="food-meta">{{ item.weight || 0 }}g · {{ item.calories || 0 }}kcal · {{ item.portion_ref }}</text>
        </view>
      </view>
    </view>

    <view v-if="gapItems.length" class="section">
      <view class="section-head">
        <text>目标差距</text>
        <text>{{ goalLabel }}</text>
      </view>
      <view v-for="gap in gapItems" :key="gap.key" class="gap-row">
        <view>
          <text class="gap-name">{{ gap.label }}</text>
          <text class="gap-advice">{{ gap.value.advice }}</text>
        </view>
        <view class="gap-bar">
          <view class="gap-fill" :style="{ width: Math.min(100, gap.value.pct || 0) + '%' }"></view>
        </view>
        <text class="gap-pct">{{ gap.value.pct || 0 }}%</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ApiService } from '@/api/index'

const selectedImage = ref('')
const result = ref(null)
const loading = ref(false)
const recording = ref(false)
const statusText = ref('')
const errorMessage = ref('')
const goal = ref('balanced')
const goals = [
  { key: 'balanced', label: '均衡' },
  { key: 'fat_loss', label: '减脂' },
  { key: 'muscle_gain', label: '增肌' }
]
const goalLabel = computed(() => goals.find(g => g.key === goal.value)?.label || '均衡')
const gapItems = computed(() => {
  const labels = { calories: '热量', protein: '蛋白质', carbs: '碳水', fat: '脂肪' }
  return Object.entries(result.value?.gaps || {}).map(([key, value]) => ({ key, label: labels[key] || key, value }))
})

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
      analyze()
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
    analyze()
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
async function analyze() {
  if (!selectedImage.value || loading.value) return
  loading.value = true
  result.value = null
  errorMessage.value = ''
  statusText.value = '正在进行一餐营养分析...'
  try {
    result.value = await ApiService.analyzeMealNutrition(await imagePayload(), goal.value)
    statusText.value = result.value?.status === 'ok' ? '分析完成。本页不写入长期记录，完成用餐请回首页三餐计划确认。' : '未识别到可分析食物'
  } catch (e) {
    errorMessage.value = e.message || '营养分析失败'
    statusText.value = ''
  } finally {
    loading.value = false
  }
}

function currentMealSlot() {
  const h = new Date().getHours()
  if (h < 10) return 'breakfast'
  if (h < 15) return 'lunch'
  return 'dinner'
}

function recipeFromResult() {
  const total = result.value?.total || {}
  const names = (result.value?.items || []).map(i => i.name).filter(Boolean)
  return {
    recipe_id: `nutrition_${Date.now()}`,
    title: names.length ? `已吃：${names.slice(0, 3).join('、')}` : '已吃餐食',
    calories: total.calories || 0,
    protein: total.protein || 0,
    carbs: total.carbs || 0,
    fat: total.fat || 0,
    nutrition: {
      calories: total.calories || 0,
      protein: total.protein || 0,
      carbs: total.carbs || 0,
      fat: total.fat || 0,
      fiber: 0,
      vitamin_c: 0,
      iron: 0
    },
    ingredients: (result.value?.items || []).map(item => ({
      name: item.name,
      amount: item.weight ? `${item.weight}g` : ''
    }))
  }
}

async function confirmEaten() {
  if (!result.value?.total || recording.value) return
  uni.showModal({
    title: '确认已吃',
    content: '确认已经吃完这一餐？确认后会写入今日营养记录，后续可在健康看板删除。',
    cancelText: '取消',
    confirmText: '计入',
    success: async res => {
      if (!res.confirm) return
      recording.value = true
      try {
        const recipe = recipeFromResult()
        const meal = await ApiService.planMeal(currentMealSlot(), recipe, recipe.ingredients, [])
        await ApiService.completeMeal(meal.id)
        uni.showToast({ title: '已计入今日营养', icon: 'success' })
      } catch (e) {
        errorMessage.value = e.message || '计入失败'
      } finally {
        recording.value = false
      }
    }
  })
}
</script>

<style scoped>
.tool-page { min-height: 100vh; padding: 30rpx; background: linear-gradient(180deg, #FAFCFB 0%, var(--bg) 46%); box-sizing: border-box; }
.hero { padding: 28rpx; border-radius: var(--radius-xl); background: linear-gradient(145deg, #24324A, #356A60); color: #fff; box-shadow: var(--shadow-lg); }
.kicker { display: block; font-size: 21rpx; opacity: .72; font-weight: 900; }
.title { display: block; margin-top: 8rpx; font-size: 44rpx; font-weight: 950; }
.desc { display: block; margin-top: 12rpx; font-size: 25rpx; line-height: 1.45; opacity: .84; }
.photo-card { height: 420rpx; margin-top: 22rpx; border-radius: var(--radius-xl); overflow: hidden; background: linear-gradient(135deg, var(--blue-bg), #fff); box-shadow: var(--shadow-md), var(--hairline); }
.photo { width: 100%; height: 100%; }
.empty-photo { height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 12rpx; color: var(--text-muted); font-size: 24rpx; }
.mark { width: 104rpx; height: 104rpx; border-radius: 32rpx; display: flex; align-items: center; justify-content: center; background: #fff; color: var(--blue); font-size: 42rpx; font-weight: 950; box-shadow: var(--shadow-sm); }
.goal-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12rpx; margin-top: 18rpx; }
.goal-chip { height: 66rpx; border-radius: var(--radius-full); display: flex; align-items: center; justify-content: center; background: #fff; color: var(--text-muted); font-size: 24rpx; font-weight: 900; box-shadow: var(--shadow-xs), var(--hairline); }
.goal-chip.active { background: var(--green-bg); color: var(--teal); }
.actions { display: flex; gap: 16rpx; margin-top: 18rpx; }
.btn { flex: 1; height: 86rpx; margin: 0; border: none; border-radius: var(--radius-md); font-size: 27rpx; font-weight: 900; }
.primary { background: linear-gradient(135deg, var(--teal), var(--teal-light)); color: #fff; }
.secondary { background: #fff; color: var(--teal); box-shadow: var(--shadow-sm), var(--hairline); }
.status-card, .error-card, .summary-card { margin-top: 18rpx; padding: 20rpx; border-radius: var(--radius-md); box-shadow: var(--shadow-sm), var(--hairline); }
.status-card { background: var(--blue-bg); color: var(--text-secondary); font-size: 24rpx; line-height: 1.45; }
.error-card { background: var(--red-bg); color: var(--red); font-size: 24rpx; }
.summary-card { background: #fff; }
.summary-kicker { display: block; color: var(--text-muted); font-size: 22rpx; font-weight: 900; }
.calorie-line { display: flex; align-items: flex-end; gap: 8rpx; margin-top: 6rpx; color: var(--text); }
.calorie-line text:first-child { font-size: 62rpx; line-height: 1; font-weight: 950; }
.calorie-line text:last-child { font-size: 25rpx; margin-bottom: 8rpx; color: var(--text-muted); }
.macro-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12rpx; margin-top: 18rpx; }
.macro { border-radius: 20rpx; padding: 16rpx; background: var(--bg-elevated); }
.macro text:first-child { display: block; font-size: 30rpx; color: var(--text); font-weight: 950; }
.macro text:last-child { display: block; margin-top: 4rpx; font-size: 21rpx; color: var(--text-muted); }
.eat-btn { width: 100%; height: 84rpx; margin: 18rpx 0 0; border: none; border-radius: var(--radius-md); background: linear-gradient(135deg, var(--teal), var(--teal-light)); color: #fff; font-size: 27rpx; font-weight: 950; }
.eat-note { display: block; margin-top: 10rpx; color: var(--text-muted); font-size: 21rpx; line-height: 1.45; }
.section-head { display: flex; justify-content: space-between; margin: 28rpx 2rpx 14rpx; color: var(--text-muted); font-size: 23rpx; }
.section-head text:first-child { color: var(--text); font-size: 32rpx; font-weight: 950; }
.food-row, .gap-row { display: flex; align-items: center; gap: 14rpx; padding: 18rpx; margin-bottom: 12rpx; border-radius: var(--radius-md); background: #fff; box-shadow: var(--shadow-sm), var(--hairline); }
.food-mark { width: 68rpx; height: 68rpx; border-radius: 22rpx; display: flex; align-items: center; justify-content: center; flex-shrink: 0; background: var(--amber-bg); color: #9A651B; font-size: 30rpx; font-weight: 950; }
.food-main { flex: 1; min-width: 0; }
.food-name { display: block; color: var(--text); font-size: 28rpx; font-weight: 950; }
.food-meta { display: block; margin-top: 6rpx; color: var(--text-muted); font-size: 22rpx; line-height: 1.35; }
.gap-row { align-items: center; }
.gap-row > view:first-child { width: 118rpx; flex-shrink: 0; }
.gap-name { display: block; color: var(--text); font-size: 24rpx; font-weight: 950; }
.gap-advice { display: block; margin-top: 4rpx; color: var(--text-muted); font-size: 20rpx; }
.gap-bar { flex: 1; height: 12rpx; border-radius: 999rpx; background: var(--border-light); overflow: hidden; }
.gap-fill { height: 100%; border-radius: 999rpx; background: linear-gradient(90deg, var(--teal), var(--amber)); }
.gap-pct { width: 58rpx; text-align: right; color: var(--text-muted); font-size: 22rpx; font-weight: 900; }
</style>
