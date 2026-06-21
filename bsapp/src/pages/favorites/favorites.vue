<template>
  <view class="page">
    <view class="head">
      <text class="title">我的收藏</text>
      <text class="sub">收藏的系统菜谱和社区菜谱都可以进入清点器</text>
    </view>
    <view v-for="fav in favorites" :key="fav.id" class="card">
      <view class="main">
        <text class="name">{{ fav.snapshot?.title || fav.snapshot?.recipe_payload?.title || fav.target_id }}</text>
        <text class="meta">{{ fav.target_type === 'community_post' ? '社区菜谱' : '系统菜谱' }}</text>
      </view>
      <button @tap="check(fav)">清点</button>
      <button class="ghost" @tap="remove(fav)">取消</button>
    </view>
    <view v-if="!favorites.length && !loading" class="empty">还没有收藏。可以在菜谱库、详情页或社区里点收藏。</view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { ApiService } from '@/api/index'

const favorites = ref([])
const loading = ref(false)
onShow(load)
async function load() {
  loading.value = true
  try { favorites.value = await ApiService.getFavorites() } finally { loading.value = false }
}
function check(fav) {
  uni.navigateTo({ url: `/pages/recipe-checker/recipe-checker?targetType=${fav.target_type}&targetId=${fav.target_id}` })
}
async function remove(fav) {
  await ApiService.removeFavorite(fav.target_type, fav.target_id)
  await load()
}
</script>

<style scoped>
.page { min-height:100vh; padding:30rpx; background:#F4FAF6; }
.title { display:block; font-size:42rpx; font-weight:950; color:#173B2E; }
.sub { display:block; margin-top:8rpx; color:#66756D; font-size:24rpx; }
.card,.empty { margin-top:16rpx; background:#fff; border-radius:24rpx; padding:20rpx; box-shadow:0 10rpx 30rpx rgba(23,59,46,.08); }
.card { display:flex; align-items:center; gap:12rpx; }
.main { flex:1; min-width:0; }
.name { display:block; font-size:28rpx; font-weight:900; color:#173B2E; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.meta { display:block; margin-top:5rpx; font-size:22rpx; color:#7A8982; }
button { width:86rpx; height:52rpx; padding:0; border-radius:999rpx; background:#23A978; color:#fff; font-size:22rpx; font-weight:900; }
button.ghost { background:#F0F5F2; color:#66756D; }
button::after { border:none; }
.empty { color:#7A8982; font-size:24rpx; }
</style>

