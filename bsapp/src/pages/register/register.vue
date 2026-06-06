<template>
  <view class="page">
    <view class="card">
      <text class="title">ByteSavor</text>
      <text class="sub">你的AI饮食助手</text>

      <view class="input-row">
        <text class="label">昵称</text>
        <input class="field" v-model="nickname" placeholder="怎么称呼你" />
      </view>
      <view class="input-row">
        <text class="label">微信ID</text>
        <input class="field" v-model="openid" placeholder="输入你的微信号/OpenID" />
      </view>

      <text v-if="error" class="error">{{ error }}</text>

      <button class="btn" :disabled="loading" @tap="doRegister">
        {{ loading ? '注册中...' : '开始使用' }}
      </button>
      <text class="tip">已有账号？自动登录</text>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { ApiService } from '@/api/index'

const openid = ref('')
const nickname = ref('')
const error = ref('')
const loading = ref(false)

async function doRegister() {
  error.value = ''
  if (!openid.value.trim()) { error.value = '请输入微信ID'; return }
  loading.value = true
  try {
    const res = await ApiService.register(openid.value.trim())
    uni.setStorageSync('auth_token', res.token)
    uni.setStorageSync('user', { user_id: res.user_id, name: nickname.value || res.name || '食客' })
    uni.showToast({ title: res.is_new ? '欢迎加入！' : '欢迎回来', icon: 'success' })
    setTimeout(() => uni.switchTab({ url: '/pages/home/home' }), 600)
  } catch (e) {
    error.value = '网络异常，请重试'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.page { min-height:100vh; display:flex; align-items:center; justify-content:center; background:linear-gradient(135deg, #ecfdf5 0%, #d1fae5 50%, #a7f3d0 100%); padding:30rpx; }
.card { width:100%; max-width:600rpx; background:#fff; border-radius:24rpx; padding:60rpx 40rpx; box-shadow:0 8px 30px rgba(0,0,0,0.06); }
.title { display:block; text-align:center; font-size:48rpx; font-weight:700; color:#059669; }
.sub { display:block; text-align:center; font-size:28rpx; color:#6b7280; margin:8rpx 0 50rpx; }
.input-row { margin-bottom:30rpx; }
.label { display:block; font-size:26rpx; color:#374151; margin-bottom:10rpx; }
.field { width:100%; height:88rpx; background:#f9fafb; border:2rpx solid #e5e7eb; border-radius:16rpx; padding:0 24rpx; font-size:30rpx; box-sizing:border-box; }
.field:focus { border-color:#059669; }
.error { display:block; color:#ef4444; font-size:24rpx; margin-bottom:20rpx; }
.btn { width:100%; height:96rpx; background:linear-gradient(135deg,#059669,#10b981); color:#fff; font-size:32rpx; font-weight:600; border-radius:16rpx; border:none; margin-top:10rpx; }
.btn[disabled] { opacity:0.6; }
.tip { display:block; text-align:center; margin-top:30rpx; font-size:24rpx; color:#9ca3af; }
</style>
