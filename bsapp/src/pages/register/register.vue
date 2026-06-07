<template>
  <view class="register-page">
    <view class="top-card">
      <view class="brand-mark">
        <image src="/static/icons/icon_leaf.svg" mode="aspectFit" />
      </view>
      <text class="title">建立你的饮食档案</text>
      <text class="sub">昵称用于本地展示，微信ID/OpenID 用来创建或登录账号。</text>
    </view>

    <view class="form-card">
      <view class="field-block">
        <text class="label">昵称</text>
        <view class="input-shell">
          <image src="/static/icons/icon_avatar.svg" mode="aspectFit" />
          <input class="field" v-model="nickname" placeholder="怎么称呼你" placeholder-class="ph" />
        </view>
      </view>

      <view class="field-block">
        <text class="label">微信ID</text>
        <view class="input-shell">
          <image src="/static/icons/icon_tag.svg" mode="aspectFit" />
          <input class="field" v-model="openid" placeholder="输入你的微信号/OpenID" placeholder-class="ph" />
        </view>
      </view>

      <view class="setup-list">
        <view class="setup-item">
          <image src="/static/icons/icon_scan.svg" mode="aspectFit" />
          <text>食材识别</text>
        </view>
        <view class="setup-item">
          <image src="/static/icons/icon_chart.svg" mode="aspectFit" />
          <text>营养看板</text>
        </view>
        <view class="setup-item">
          <image src="/static/icons/icon_cart.svg" mode="aspectFit" />
          <text>清单导出</text>
        </view>
      </view>

      <text v-if="error" class="error">{{ error }}</text>

      <button class="btn" :disabled="loading" @tap="doRegister">
        {{ loading ? '注册中...' : '开始使用' }}
      </button>
      <text class="tip">已有账号会自动登录并进入首页</text>
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
.register-page {
  min-height: 100vh;
  background: var(--bg);
  padding: 44rpx 28rpx;
}
.top-card {
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  padding: 34rpx;
  box-shadow: var(--shadow-md);
}
.brand-mark {
  width: 78rpx;
  height: 78rpx;
  border-radius: 24rpx;
  background: var(--teal-bg);
  display: flex;
  align-items: center;
  justify-content: center;
}
.brand-mark image { width: 42rpx; height: 42rpx; }
.title {
  display: block;
  margin-top: 28rpx;
  font-size: 44rpx;
  line-height: 1.18;
  font-weight: 800;
  color: var(--ink-green);
}
.sub {
  display: block;
  margin-top: 14rpx;
  color: var(--text-secondary);
  font-size: 25rpx;
  line-height: 1.55;
}
.form-card {
  margin-top: 22rpx;
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  padding: 28rpx;
  box-shadow: var(--shadow-sm);
}
.field-block { margin-bottom: 22rpx; }
.label {
  display: block;
  font-size: 24rpx;
  color: var(--text-secondary);
  font-weight: 700;
  margin-bottom: 10rpx;
}
.input-shell {
  height: 92rpx;
  display: flex;
  align-items: center;
  gap: 14rpx;
  background: var(--bg-elevated);
  border: 1rpx solid var(--border-light);
  border-radius: var(--radius);
  padding: 0 20rpx;
}
.input-shell image { width: 34rpx; height: 34rpx; flex-shrink: 0; }
.field { flex: 1; height: 92rpx; border: none; background: transparent; font-size: 28rpx; color: var(--text); padding: 0; }
.ph { color: var(--text-placeholder); }
.setup-list {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12rpx;
  margin: 8rpx 0 22rpx;
}
.setup-item {
  min-height: 94rpx;
  border-radius: 22rpx;
  background: var(--bg-elevated);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
}
.setup-item image { width: 30rpx; height: 30rpx; }
.setup-item text { font-size: 20rpx; color: var(--text-secondary); }
.error { display: block; color: var(--danger); background: var(--red-bg); border-radius: 16rpx; padding: 14rpx 16rpx; font-size: 24rpx; margin-bottom: 18rpx; }
.btn {
  width: 100%;
  height: 92rpx;
  background: var(--teal);
  color: #fff;
  font-size: 30rpx;
  font-weight: 800;
  border-radius: var(--radius);
  border: none;
  box-shadow: 0 16rpx 32rpx rgba(35, 169, 120, 0.22);
}
.btn[disabled] { opacity: 0.65; }
.tip { display: block; text-align: center; margin-top: 24rpx; font-size: 23rpx; color: var(--text-muted); }
</style>
