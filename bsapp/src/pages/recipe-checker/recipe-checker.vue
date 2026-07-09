<template>
  <view class="page">
    <view class="head">
      <text class="title">{{ result?.target?.title || '菜谱清点器' }}</text>
      <text class="sub">根据当前库存判断能不能做，缺少项可导入购物清单</text>
    </view>

    <view v-if="result" class="score-card">
      <text class="score">{{ Math.round((result.fit_ratio || 0) * 100) }}%</text>
      <text class="score-label">{{ result.can_cook ? '库存充足，可以做' : '还需要补充食材' }}</text>
    </view>

    <view class="section">
      <text class="section-title">已有食材</text>
      <view v-for="item in result?.owned || []" :key="item.name" class="item ok">
        <text>{{ item.name }}</text><text>{{ item.available || '已拥有' }}</text>
      </view>
      <view v-if="!(result?.owned || []).length" class="empty">当前库存暂无匹配食材。</view>
    </view>

    <view class="section">
      <text class="section-title">缺少食材</text>
      <view v-for="item in result?.missing || []" :key="item.name" class="item miss">
        <text>{{ item.name }}</text><text>{{ item.shortage || item.required }}</text>
      </view>
      <view v-if="!(result?.missing || []).length" class="empty">没有缺少项。</view>
    </view>

    <button class="primary" @tap="goList">缺少项导入购物清单</button>
    <button class="secondary" @tap="addPlan">加入今日计划</button>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { ApiService } from '@/api/index'

const targetType = ref('system_recipe')
const targetId = ref('')
const result = ref(null)

onLoad(async (options) => {
  targetType.value = options.targetType || 'system_recipe'
  targetId.value = options.targetId || ''
  await load()
})

async function load() {
  try {
    result.value = await ApiService.checkRecipe(targetType.value, targetId.value)
  } catch (e) {
    uni.showToast({ title: e.message || '清点失败', icon: 'none' })
  }
}

function goList() {
  const items = result.value?.shopping_list || []
  uni.navigateTo({ url: `/pages/list-export/list-export?items=${encodeURIComponent(JSON.stringify(items))}&title=${encodeURIComponent('缺少食材清单')}` })
}

async function addPlan() {
  const recipe = result.value?.target?.recipe
  if (!recipe) return
  try {
    const adopted = await ApiService.adoptMeal('lunch', recipe)
    const count = (adopted.shopping_list || []).length
    uni.showToast({ title: count ? `已采纳，需补${count}项` : '已采纳到午餐', icon: 'success' })
  } catch (e) {
    uni.showToast({ title: e.message || '采纳失败', icon: 'none' })
  }
}
</script>

<style scoped>
.page { min-height:100vh; padding:30rpx; background:#F4FAF6; }
.title { display:block; font-size:42rpx; font-weight:950; color:#173B2E; }
.sub { display:block; margin-top:8rpx; color:#66756D; font-size:24rpx; }
.score-card,.section { background:#fff; border-radius:26rpx; padding:24rpx; margin-top:18rpx; box-shadow:0 12rpx 34rpx rgba(23,59,46,.08); }
.score { display:block; font-size:58rpx; font-weight:950; color:#23A978; }
.score-label { color:#66756D; font-size:24rpx; }
.section-title { display:block; font-size:30rpx; font-weight:950; color:#173B2E; margin-bottom:12rpx; }
.item { display:flex; justify-content:space-between; padding:14rpx 0; border-bottom:1rpx solid #EDF2EF; font-size:25rpx; }
.item.ok text:last-child { color:#23A978; font-weight:800; }
.item.miss text:last-child { color:#E85D4F; font-weight:800; }
.empty { color:#8A9690; font-size:23rpx; padding:10rpx 0; }
button { height:78rpx; border-radius:999rpx; margin-top:18rpx; font-size:27rpx; font-weight:900; border:none; }
button::after { border:none; }
.primary { background:#173B2E; color:#fff; }
.secondary { background:#23A978; color:#fff; }
</style>
