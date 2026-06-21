<template>
  <view class="register-page">
    <view class="top-card">
      <view class="brand-mark">
        <image src="/static/icons/icon_leaf.svg" mode="aspectFit" />
      </view>
      <text class="title">建立你的饮食档案</text>
      <text class="sub">{{ showOpenId ? '使用微信ID/OpenID 快速注册演示账号' : '设置用户名和密码创建正式账号' }}</text>
    </view>

    <view class="form-card">
      <!-- 昵称 -->
      <view class="field-block">
        <text class="label">昵称</text>
        <view class="input-shell">
          <image src="/static/icons/icon_avatar.svg" mode="aspectFit" />
          <input class="field" v-model="nickname" placeholder="怎么称呼你" placeholder-class="ph" />
        </view>
      </view>

      <!-- 密码注册（默认） -->
      <view v-if="!showOpenId">
        <view class="field-block">
          <text class="label">用户名</text>
          <view class="input-shell">
            <image src="/static/icons/icon_tag.svg" mode="aspectFit" />
            <input class="field" v-model="username" placeholder="3-32位字母数字下划线" placeholder-class="ph" />
          </view>
        </view>
        <view class="field-block">
          <text class="label">密码</text>
          <view class="input-shell">
            <image src="/static/icons/icon_tag.svg" mode="aspectFit" />
            <input class="field" v-model="password" type="password" placeholder="至少8位，含大小写+数字" placeholder-class="ph" />
          </view>
        </view>
        <view class="field-block">
          <text class="label">确认密码</text>
          <view class="input-shell">
            <image src="/static/icons/icon_tag.svg" mode="aspectFit" />
            <input class="field" v-model="confirmPassword" type="password" placeholder="再次输入密码" placeholder-class="ph" />
          </view>
        </view>
      </view>

      <!-- OpenID 演示注册（切换） -->
      <view v-else>
        <view class="field-block">
          <text class="label">微信ID</text>
          <view class="input-shell">
            <image src="/static/icons/icon_tag.svg" mode="aspectFit" />
            <input class="field" v-model="openid" placeholder="输入你的微信号/OpenID" placeholder-class="ph" />
          </view>
        </view>
      </view>

      <text v-if="error" class="error">{{ error }}</text>

      <button class="btn" :disabled="loading" @tap="doRegister">
        {{ loading ? '注册中...' : '注册' }}
      </button>

      <view class="switch-row">
        <text class="tip" @tap="showOpenId = !showOpenId">{{ showOpenId ? '切换为密码注册' : '切换为 OpenID 演示注册' }}</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { ApiService } from '@/api/index'
import { useAuthStore } from '@/store/auth'

const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const nickname = ref('')
const openid = ref('')
const showOpenId = ref(false)
const error = ref('')
const loading = ref(false)
const authStore = useAuthStore()

const PWD_RULE = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/

async function doRegister() {
  error.value = ''
  loading.value = true

  try {
    let res
    if (showOpenId.value) {
      if (!openid.value.trim()) { error.value = '请输入微信ID'; loading.value = false; return }
      res = await ApiService.register(openid.value.trim(), nickname.value.trim())
    } else {
      if (!username.value.trim()) { error.value = '请输入用户名'; loading.value = false; return }
      if (!PWD_RULE.test(password.value)) { error.value = '密码至少8位，含大小写字母和数字'; loading.value = false; return }
      if (password.value !== confirmPassword.value) { error.value = '两次密码不一致'; loading.value = false; return }
      res = await ApiService.register({
        username: username.value.trim(),
        password: password.value,
        name: nickname.value.trim(),
      })
    }

    await authStore.setAuthData({
      userId: res.user_id || res.userId || '',
      username: nickname.value || res.name || username.value || openid.value,
      email: ''
    }, res.token || '')
    uni.showToast({ title: res.is_new ? '欢迎加入！' : '欢迎回来', icon: 'success' })
    setTimeout(() => uni.switchTab({ url: '/pages/home/home' }), 600)
  } catch (e) {
    error.value = e.message || '网络异常，请重试'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-page { min-height: 100vh; background: var(--bg); padding: 42rpx 28rpx; }
.top-card { text-align: center; margin-bottom: 24rpx; }
.brand-mark { width: 88rpx; height: 88rpx; border-radius: 24rpx; background: var(--teal-bg); display: flex; align-items: center; justify-content: center; margin: 0 auto 22rpx; }
.brand-mark image { width: 44rpx; height: 44rpx; }
.title { display: block; font-size: 38rpx; font-weight: 800; color: var(--text); }
.sub { display: block; margin-top: 10rpx; font-size: 24rpx; color: var(--text-secondary); line-height: 1.5; max-width: 540rpx; margin-left: auto; margin-right: auto; }
.form-card { background: var(--bg-card); border-radius: var(--radius-xl); padding: 28rpx; box-shadow: var(--shadow-sm); }
.field-block { margin-bottom: 18rpx; }
.label { display: block; font-size: 24rpx; font-weight: 700; color: var(--text); margin-bottom: 10rpx; }
.input-shell { display: flex; align-items: center; height: 88rpx; background: var(--bg-elevated); border: 1rpx solid var(--border-light); border-radius: var(--radius); padding: 0 20rpx; }
.input-shell image { width: 34rpx; height: 34rpx; margin-right: 14rpx; }
.field { flex: 1; height: 88rpx; font-size: 26rpx; color: var(--text); border: none; background: transparent; }
.ph { color: var(--text-placeholder); }
.error { display: block; color: var(--danger); font-size: 24rpx; margin: 14rpx 0; text-align: center; }
.btn { width: 100%; height: 88rpx; margin-top: 14rpx; background: var(--teal); color: #fff; border: none; border-radius: var(--radius); font-size: 30rpx; font-weight: 800; display: flex; align-items: center; justify-content: center; box-shadow: 0 16rpx 32rpx rgba(35,169,120,0.22); }
.btn[disabled] { opacity: 0.65; }
.switch-row { text-align: center; margin-top: 20rpx; }
.tip { font-size: 23rpx; color: var(--accent); }
</style>
