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
    </view>

    <view class="login-panel">
      <!-- 用户名密码登录（默认） -->
      <view v-if="!showOpenId">
        <view class="input-row">
          <image class="input-icon" src="/static/icons/icon_avatar.svg" mode="aspectFit" />
          <input class="input-field" v-model="username" placeholder="用户名" placeholder-class="ph" />
        </view>
        <view class="input-row" style="margin-top:14rpx">
          <image class="input-icon" src="/static/icons/icon_tag.svg" mode="aspectFit" />
          <input class="input-field" v-model="password" type="password" placeholder="密码" placeholder-class="ph" />
        </view>
      </view>

      <!-- OpenID 演示登录（切换） -->
      <view v-else>
        <view class="input-row">
          <image class="input-icon" src="/static/icons/icon_tag.svg" mode="aspectFit" />
          <input class="input-field" v-model="openid" placeholder="输入微信ID/OpenID" placeholder-class="ph" />
        </view>
      </view>

      <view v-if="errorMessage" class="error-banner">
        <text>{{ errorMessage }}</text>
      </view>

      <button class="btn-login" :disabled="isLoading" @tap="handleLogin">
        <text v-if="!isLoading">{{ loginLabel }}</text>
        <view v-else class="loading-spinner"></view>
      </button>

      <view class="link-row">
        <text class="link-label">{{ showOpenId ? '密码登录' : '演示 OpenID 登录' }}</text>
        <text class="link-action" @tap="showOpenId = !showOpenId">{{ showOpenId ? '切换' : '切换' }}</text>
      </view>

      <view class="link-row">
        <text class="link-label">没有账号？</text>
        <text class="link-action" @tap="goRegister">立即注册</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ApiService } from '@/api/index'
import { useAuthStore } from '@/store/auth'

const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const openid = ref('demo')
const showOpenId = ref(false)
const isLoading = ref(false)
const errorMessage = ref('')

const loginLabel = computed(() => showOpenId.value ? 'OpenID 登录' : '登录')

async function handleLogin() {
  errorMessage.value = ''
  isLoading.value = true

  try {
    let result
    if (showOpenId.value) {
      if (!openid.value.trim()) { errorMessage.value = '请输入 OpenID'; isLoading.value = false; return }
      result = await ApiService.login(openid.value.trim())
    } else {
      if (!username.value.trim() || !password.value) { errorMessage.value = '请输入用户名和密码'; isLoading.value = false; return }
      result = await ApiService.login({ username: username.value.trim(), password: password.value })
    }

    const token = result.token || ''
    const userId = result.user_id || result.userId || ''
    const name = result.name || username.value || openid.value

    if (token) {
      await authStore.setAuthData({ userId, username: name, email: '' }, token)
      uni.switchTab({ url: '/pages/home/home' })
    } else {
      errorMessage.value = '登录失败'
    }
  } catch (e) {
    errorMessage.value = e.message || '登录出错'
  } finally {
    isLoading.value = false
  }
}

function goRegister() {
  uni.navigateTo({ url: '/pages/register/register' })
}
</script>

<style scoped>
.login-page { min-height: 100vh; background: var(--bg); padding: 42rpx 28rpx 34rpx; }
.hero-card { background: var(--bg-card); border-radius: var(--radius-xl); padding: 34rpx; box-shadow: var(--shadow-md); }
.brand-row { display: flex; align-items: center; gap: 18rpx; }
.brand-mark { width: 78rpx; height: 78rpx; border-radius: 24rpx; background: var(--teal-bg); display: flex; align-items: center; justify-content: center; }
.brand-mark image { width: 42rpx; height: 42rpx; }
.brand-title { display: block; font-size: 34rpx; font-weight: 800; color: var(--text); line-height: 1.1; }
.brand-sub { display: block; margin-top: 6rpx; font-size: 22rpx; color: var(--text-secondary); }
.headline { display: block; margin-top: 34rpx; max-width: 560rpx; font-size: 46rpx; line-height: 1.16; font-weight: 800; color: var(--ink-green); }
.subline { display: block; margin-top: 14rpx; font-size: 25rpx; line-height: 1.55; color: var(--text-secondary); }
.login-panel { margin-top: 22rpx; background: var(--bg-card); border-radius: var(--radius-xl); padding: 28rpx; box-shadow: var(--shadow-sm); }
.input-row { display: flex; align-items: center; height: 92rpx; background: var(--bg-elevated); border: 1rpx solid var(--border-light); border-radius: var(--radius); padding: 0 22rpx; }
.input-icon { width: 38rpx; height: 38rpx; margin-right: 16rpx; }
.input-field { flex: 1; height: 92rpx; border: none; background: transparent; font-size: 28rpx; color: var(--text); }
.ph { color: var(--text-placeholder); }
.error-banner { margin-top: 16rpx; padding: 16rpx 18rpx; border-radius: 18rpx; background: var(--red-bg); color: var(--danger); font-size: 24rpx; }
.btn-login { width: 100%; height: 92rpx; margin-top: 18rpx; background: var(--teal); color: #fff; border: none; border-radius: var(--radius); font-size: 30rpx; font-weight: 800; display: flex; align-items: center; justify-content: center; box-shadow: 0 16rpx 32rpx rgba(35,169,120,0.22); }
.btn-login[disabled] { opacity: 0.65; }
.link-row { display: flex; justify-content: center; align-items: center; margin-top: 20rpx; }
.link-label { font-size: 24rpx; color: var(--text-secondary); }
.link-action { font-size: 24rpx; color: var(--accent); font-weight: 800; margin-left: 8rpx; }
.loading-spinner { width: 36rpx; height: 36rpx; border: 4rpx solid rgba(255,255,255,0.35); border-top-color: #fff; border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
