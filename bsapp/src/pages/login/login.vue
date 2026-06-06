<template>
  <view class="login-page">
    <view class="login-container">
      <!-- Logo -->
      <view class="logo-box">
        <text class="logo-emoji">🍳</text>
      </view>

      <!-- 标题 -->
      <text class="app-title">ByteSavor</text>
      <text class="app-subtitle">字节品鉴者 - 智能食谱推荐</text>

      <!-- 输入 -->
      <view class="input-group">
        <view class="input-row">
          <text class="input-icon">👤</text>
          <input
            class="input-field"
            v-model="username"
            :placeholder="$t('usernameOrEmail')"
            placeholder-class="ph"
          />
        </view>
        <view class="input-row">
          <text class="input-icon">🔒</text>
          <input
            class="input-field"
            v-model="password"
            type="password"
            :placeholder="$t('password')"
            placeholder-class="ph"
          />
        </view>
      </view>

      <!-- 错误提示 -->
      <view v-if="errorMessage" class="error-banner">
        <text>⚠️ {{ errorMessage }}</text>
      </view>

      <!-- 登录按钮 -->
      <button
        class="btn-login"
        :disabled="isLoading"
        @tap="handleLogin"
      >
        <text v-if="!isLoading">{{ $t('login') }}</text>
        <view v-else class="loading-spinner"></view>
      </button>

      <!-- 注册 -->
      <view class="link-row">
        <text class="link-label">{{ $t('noAccount') }}</text>
        <text class="link-action" @tap="goRegister">{{ $t('registerNow') }}</text>
      </view>

      <!-- 演示账号提示 -->
      <view class="demo-tip">
        <text>💡 {{ $t('demoAccount') }}: demo / 123456</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { ApiService } from '@/api/index'
import { useAuthStore } from '@/store/auth'
import { t } from '@/utils/i18n'

const $t = key => t(key)
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const isLoading = ref(false)
const errorMessage = ref('')

async function handleLogin() {
  if (!username.value || !password.value) {
    errorMessage.value = '请输入用户名和密码'
    return
  }

  isLoading.value = true
  errorMessage.value = ''

  try {
    const result = await ApiService.login(username.value, password.value)

    const token = result.token || ''
    const userData = result.user || {}

    if (token) {
      const user = {
        userId: userData.userId || 'u_001',
        username: userData.username || username.value,
        email: userData.email || '',
        token: token
      }

      await authStore.setAuthData(user, token)
      uni.switchTab({ url: '/pages/home/home' })
    } else {
      errorMessage.value = '登录失败，请检查用户名和密码'
    }
  } catch (e) {
    errorMessage.value = '登录出错: ' + (e.message || e)
  } finally {
    isLoading.value = false
  }
}

function goRegister() {
  uni.navigateTo({ url: '/pages/register/register' })
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  background: var(--bg-color);
  display: flex;
  align-items: center;
  justify-content: center;
}
.login-container {
  width: 100%;
  max-width: 600rpx;
  padding: 60rpx 48rpx;
}
.logo-box {
  width: 140rpx; height: 140rpx;
  background: var(--teal-bg);
  border-radius: 32rpx;
  display: flex; align-items: center; justify-content: center;
  align-self: center; margin: 0 auto 40rpx;
}
.logo-emoji { font-size: 72rpx; }
.app-title {
  font-size: 52rpx;
  font-weight: bold;
  color: var(--text-color);
  text-align: center;
  display: block;
}
.app-subtitle {
  font-size: 26rpx;
  color: var(--text-secondary);
  text-align: center;
  display: block;
  margin-top: 12rpx;
  margin-bottom: 48rpx;
}
.input-group {
  margin-bottom: 16rpx;
}
.input-row {
  display: flex;
  align-items: center;
  background: var(--card-bg);
  border-radius: 16rpx;
  padding: 0 24rpx;
  margin-bottom: 20rpx;
  border: 1rpx solid var(--border-color);
}
.input-icon {
  font-size: 36rpx;
  margin-right: 16rpx;
}
.input-field {
  flex: 1;
  height: 90rpx;
  font-size: 30rpx;
}
.ph {
  color: var(--text-muted);
}
.btn-login {
  width: 100%; height: 90rpx;
  background: var(--teal); color: #fff; border: none;
  border-radius: var(--radius); font-size: 30rpx; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  margin-top: 16rpx; letter-spacing: 0.03em;
  box-shadow: 0 2px 10px rgba(20,184,166,0.20);
}
.btn-login[disabled] { opacity: 0.6; }
.link-row {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: 28rpx;
}
.link-label {
  font-size: 26rpx;
  color: var(--text-secondary);
}
.link-action {
  font-size: 26rpx;
  color: var(--accent);
  font-weight: bold;
  margin-left: 8rpx;
}
.demo-tip {
  background: var(--info-bg);
  border: 1rpx solid var(--info-border);
  border-radius: 12rpx;
  padding: 20rpx;
  margin-top: 48rpx;
  text-align: center;
  font-size: 24rpx;
  color: var(--accent);
}
.loading-spinner {
  width: 36rpx;
  height: 36rpx;
  border: 4rpx solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
