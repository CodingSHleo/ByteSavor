<template>
  <view class="login-page">
    <view class="hero-card">
      <view class="brand-row">
        <view class="brand-mark">
          <image src="/static/icons/icon_leaf.svg" mode="aspectFit" />
        </view>
        <view>
          <text class="brand-title">ByteSavor</text>
          <text class="brand-sub">智能饮食管理</text>
        </view>
      </view>

      <text class="headline">把今天的食材变成清晰计划</text>
      <text class="subline">识别食材、生成食谱、同步营养缺口与采购清单。</text>

      <view class="preview-grid">
        <view class="preview-card">
          <image src="/static/icons/icon_scan.svg" mode="aspectFit" />
          <text class="preview-num">3</text>
          <text class="preview-label">食材识别</text>
        </view>
        <view class="preview-card amber">
          <image src="/static/icons/icon_chart.svg" mode="aspectFit" />
          <text class="preview-num">82</text>
          <text class="preview-label">健康指数</text>
        </view>
        <view class="preview-card blue">
          <image src="/static/icons/icon_cart.svg" mode="aspectFit" />
          <text class="preview-num">7</text>
          <text class="preview-label">待采购</text>
        </view>
      </view>
    </view>

    <view class="login-panel">
      <view class="input-row">
        <image class="input-icon" src="/static/icons/icon_avatar.svg" mode="aspectFit" />
        <input
          class="input-field"
          v-model="openid"
          placeholder="输入已注册的微信号/OpenID"
          placeholder-class="ph"
        />
      </view>

      <view v-if="errorMessage" class="error-banner">
        <text>{{ errorMessage }}</text>
      </view>

      <button class="btn-login" :disabled="isLoading" @tap="handleLogin">
        <text v-if="!isLoading">{{ $t('login') }}</text>
        <view v-else class="loading-spinner"></view>
      </button>

      <view class="link-row">
        <text class="link-label">{{ $t('noAccount') }}</text>
        <text class="link-action" @tap="goRegister">{{ $t('registerNow') }}</text>
      </view>

      <view class="demo-tip">
        <image src="/static/icons/icon_flash.svg" mode="aspectFit" />
        <text>首次使用请先注册，已有账号可直接登录</text>
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

const openid = ref('demo')
const isLoading = ref(false)
const errorMessage = ref('')

async function handleLogin() {
  if (!openid.value.trim()) {
    errorMessage.value = '请输入 OpenID'
    return
  }

  isLoading.value = true
  errorMessage.value = ''

  try {
    const result = await ApiService.login(openid.value.trim())

    const token = result.token || ''
    const userId = result.user_id || result.userId || 'u_001'
    const username = result.name || openid.value

    if (token) {
      const user = { userId, username, email: '' }

      await authStore.setAuthData(user, token)
      uni.switchTab({ url: '/pages/home/home' })
    } else {
      errorMessage.value = '登录失败，请检查 OpenID'
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
  background: var(--bg);
  padding: 42rpx 28rpx 34rpx;
}
.hero-card {
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  padding: 34rpx;
  box-shadow: var(--shadow-md);
}
.brand-row { display: flex; align-items: center; gap: 18rpx; }
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
.brand-title { display: block; font-size: 34rpx; font-weight: 800; color: var(--text); line-height: 1.1; }
.brand-sub { display: block; margin-top: 6rpx; font-size: 22rpx; color: var(--text-secondary); }
.headline {
  display: block;
  margin-top: 34rpx;
  max-width: 560rpx;
  font-size: 46rpx;
  line-height: 1.16;
  font-weight: 800;
  color: var(--ink-green);
}
.subline {
  display: block;
  margin-top: 14rpx;
  font-size: 25rpx;
  line-height: 1.55;
  color: var(--text-secondary);
}
.preview-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14rpx; margin-top: 30rpx; }
.preview-card {
  min-height: 132rpx;
  border-radius: 24rpx;
  background: var(--green-bg);
  padding: 16rpx;
}
.preview-card.amber { background: var(--amber-bg); }
.preview-card.blue { background: var(--blue-bg); }
.preview-card image { width: 30rpx; height: 30rpx; }
.preview-num { display: block; margin-top: 12rpx; font-size: 34rpx; line-height: 1; font-weight: 800; color: var(--text); }
.preview-label { display: block; margin-top: 8rpx; font-size: 20rpx; color: var(--text-secondary); }
.login-panel {
  margin-top: 22rpx;
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  padding: 28rpx;
  box-shadow: var(--shadow-sm);
}
.input-row {
  display: flex;
  align-items: center;
  height: 92rpx;
  background: var(--bg-elevated);
  border: 1rpx solid var(--border-light);
  border-radius: var(--radius);
  padding: 0 22rpx;
}
.input-icon { width: 38rpx; height: 38rpx; margin-right: 16rpx; }
.input-field { flex: 1; height: 92rpx; border: none; background: transparent; font-size: 28rpx; color: var(--text); }
.ph { color: var(--text-placeholder); }
.error-banner {
  margin-top: 16rpx;
  padding: 16rpx 18rpx;
  border-radius: 18rpx;
  background: var(--red-bg);
  color: var(--danger);
  font-size: 24rpx;
}
.btn-login {
  width: 100%;
  height: 92rpx;
  margin-top: 18rpx;
  background: var(--teal);
  color: #fff;
  border: none;
  border-radius: var(--radius);
  font-size: 30rpx;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 16rpx 32rpx rgba(35, 169, 120, 0.22);
}
.btn-login[disabled] { opacity: 0.65; }
.link-row { display: flex; justify-content: center; align-items: center; margin-top: 24rpx; }
.link-label { font-size: 24rpx; color: var(--text-secondary); }
.link-action { font-size: 24rpx; color: var(--accent); font-weight: 800; margin-left: 8rpx; }
.demo-tip {
  margin-top: 24rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10rpx;
  background: var(--amber-bg);
  border-radius: 18rpx;
  padding: 16rpx;
  color: #9B6A20;
  font-size: 23rpx;
}
.demo-tip image { width: 28rpx; height: 28rpx; }
.loading-spinner {
  width: 36rpx;
  height: 36rpx;
  border: 4rpx solid rgba(255,255,255,0.35);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
