<template>
  <view class="page">
    <view class="header">
      <text class="eyebrow">社区发布</text>
      <text class="title">分享今天的餐桌</text>
    </view>
    <view class="tabs">
      <view v-for="tab in tabs" :key="tab.key" class="tab" :class="{active: form.category === tab.key}" @tap="form.category = tab.key">{{ tab.label }}</view>
    </view>
    <input v-model="form.title" placeholder="标题" placeholder-class="ph" />
    <textarea v-model="form.content" placeholder="写下做法、经验或问题" placeholder-class="ph" />

    <view v-if="form.category === 'recipe'" class="recipe-box">
      <text class="section">结构化食材</text>
      <view v-for="(ing, idx) in ingredients" :key="idx" class="ing-row">
        <input v-model="ing.name" placeholder="食材" />
        <input v-model="ing.amount" placeholder="用量" />
      </view>
      <button class="ghost" @tap="ingredients.push({ name:'', amount:'' })">添加食材</button>
    </view>

    <!-- 图片选择 -->
    <view class="image-section">
      <text class="section">图片（可选，最多9张）</text>
      <view class="image-grid">
        <view v-for="(img, idx) in form.images" :key="idx" class="image-item" @tap="previewImage(idx)">
          <image :src="img" mode="aspectFill" class="image-thumb" />
          <view class="image-delete" @tap.stop="removeImage(idx)">×</view>
        </view>
        <view v-if="form.images.length < 9" class="image-add" @tap="chooseImage">
          <text class="add-icon">+</text>
          <text class="add-label">添加图片</text>
        </view>
      </view>
    </view>

    <button class="submit" :disabled="submitting" @tap="submit">{{ submitting ? '发布中...' : '发布' }}</button>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { ApiService } from '@/api/index'

const tabs = [
  { key: 'recipe', label: '菜谱' },
  { key: 'health', label: '健康咨询' },
  { key: 'checkin', label: '打卡' }
]
const form = ref({ title: '', content: '', category: 'recipe', images: [] })
const ingredients = ref([{ name: '', amount: '' }, { name: '', amount: '' }])
const submitting = ref(false)

function chooseImage() {
  uni.chooseImage({
    count: 9 - form.value.images.length,
    sizeType: ['compressed'],
    success: async (res) => {
      const paths = res.tempFilePaths || []
      const files = res.tempFiles || []
      const images = []
      for (let i = 0; i < paths.length; i++) {
        images.push(await imageToDataUrl(paths[i], files[i]))
      }
      form.value.images = [...form.value.images, ...images].slice(0, 9)
    }
  })
}

function imageToDataUrl(path, fileInfo) {
  const file = fileInfo?.file || fileInfo
  if (path && String(path).startsWith('data:')) return Promise.resolve(path)
  if (typeof FileReader !== 'undefined' && file instanceof Blob) {
    return new Promise(resolve => {
      const reader = new FileReader()
      reader.onload = () => resolve(reader.result)
      reader.onerror = () => resolve(path)
      reader.readAsDataURL(file)
    })
  }
  return Promise.resolve(path)
}
function removeImage(idx) {
  form.value.images.splice(idx, 1)
}
function previewImage(idx) {
  uni.previewImage({ current: idx, urls: form.value.images })
}

function validateForm() {
  if (!form.value.title.trim()) return '请输入标题'
  if (!form.value.content.trim()) return form.value.category === 'recipe' ? '请输入做法或步骤说明' : '请输入内容'
  if (form.value.category === 'recipe') {
    const validIngredients = ingredients.value.filter(i => i.name.trim())
    if (!validIngredients.length) return '菜谱至少需要 1 个食材'
  }
  return ''
}

async function submit() {
  if (submitting.value) return
  const message = validateForm()
  if (message) {
    uni.showToast({ title: message, icon: 'none' })
    return
  }
  submitting.value = true
  const payload = { ...form.value, recipe_payload: {} }
  if (payload.category === 'recipe') {
    payload.recipe_payload = {
      title: payload.title,
      ingredients: ingredients.value.filter(i => i.name.trim()).map(i => ({ name: i.name.trim(), amount: (i.amount || '').trim() })),
      steps: payload.content ? payload.content.split(/[。.\n]/).filter(Boolean) : [],
      calories: 0,
      macros: {}
    }
  }
  try {
    await ApiService.createCommunityPost(payload)
    uni.showToast({ title: '已发布', icon: 'success' })
    setTimeout(() => uni.navigateBack(), 500)
  } catch (e) {
    uni.showToast({ title: e.message || '发布失败', icon: 'none' })
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.page { min-height:100vh; padding:28rpx 24rpx 130rpx; background:#F7F7F8; }
.header { margin-bottom:18rpx; }
.eyebrow { display:block; color:#7a828e; font-size:21rpx; font-weight:700; }
.title { display:block; margin-top:6rpx; font-size:36rpx; font-weight:850; color:#15171a; letter-spacing:0; }
.tabs { display:flex; gap:12rpx; margin-bottom:18rpx; }
.tab { padding:13rpx 24rpx; border-radius:999rpx; background:#fff; color:#69717D; font-size:24rpx; font-weight:750; box-shadow:0 1rpx 2rpx rgba(17,24,39,.04); }
.tab.active { background:#15171a; color:#fff; }
input,textarea,.recipe-box { background:#fff; border-radius:20rpx; box-shadow:0 8rpx 24rpx rgba(17,24,39,.055); }
input { height:74rpx; padding:0 18rpx; margin-bottom:14rpx; font-size:26rpx; }
textarea { width:100%; min-height:190rpx; padding:20rpx; box-sizing:border-box; font-size:26rpx; line-height:1.55; margin-bottom:14rpx; }
.recipe-box { padding:18rpx; margin-bottom:18rpx; }
.section { display:block; font-size:27rpx; font-weight:800; color:#15171a; margin-bottom:12rpx; }
.ing-row { display:grid; grid-template-columns: 1fr 1fr; gap:10rpx; }
button { height:72rpx; border-radius:999rpx; border:none; font-size:26rpx; font-weight:800; }
button::after { border:none; }
.ghost { width:100%; background:#E8F7EF; color:#23A978; }
.submit { width:100%; background:#23A978; color:#fff; }
.submit[disabled] { opacity:.65; }
.image-section { margin-bottom: 18rpx; }
.image-grid { display: flex; flex-wrap: wrap; gap: 12rpx; }
.image-item { width: 160rpx; height: 160rpx; border-radius: 16rpx; overflow: hidden; position: relative; }
.image-thumb { width: 100%; height: 100%; }
.image-delete { position: absolute; top: 4rpx; right: 8rpx; width: 36rpx; height: 36rpx; border-radius: 50%; background: rgba(0,0,0,.5); color: #fff; display: flex; align-items: center; justify-content: center; font-size: 24rpx; }
.image-add { width: 160rpx; height: 160rpx; border-radius: 16rpx; border: 2rpx dashed #D7DCE2; display: flex; flex-direction: column; align-items: center; justify-content: center; background: #fff; }
.add-icon { font-size: 44rpx; color: #8F959E; }
.add-label { font-size: 20rpx; color: #8F959E; margin-top: 4rpx; }
.ph { color:#A5B0AA; }
</style>
