<template>
  <view v-if="!unlocked" class="lock-screen">
    <view class="lock-card">
      <text class="lock-icon">🔒</text>
      <text class="lock-title">ByteSavor Demo</text>
      <input class="lock-input" type="password" v-model="pwd" placeholder="输入演示密码" @confirm="tryUnlock" />
      <button class="lock-btn" @tap="tryUnlock">进入演示</button>
      <text v-if="pwdError" class="lock-error">密码错误</text>
    </view>
  </view>
  <slot v-else />
</template>

<script setup>
import { ref } from 'vue'
import { onLaunch } from '@dcloudio/uni-app'
import { useAuthStore } from '@/store/auth'
import { useSettingsStore } from '@/store/settings'

const unlocked = ref(false)
const pwd = ref('')
const pwdError = ref(false)

function tryUnlock() {
  if (pwd.value === '123456') {
    unlocked.value = true
    pwdError.value = false
  } else {
    pwdError.value = true
    pwd.value = ''
  }
}

onLaunch(async () => {
  const authStore = useAuthStore()
  await authStore.init()
  const settingsStore = useSettingsStore()
  await settingsStore.init()
})
</script>

<style lang="scss">
.lock-screen {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 50%, #a7f3d0 100%);
  display: flex; align-items: center; justify-content: center; z-index: 9999;
}
.lock-card {
  background: #fff; border-radius: 24rpx; padding: 60rpx 40rpx;
  width: 80%; max-width: 500rpx; text-align: center;
  box-shadow: 0 8px 30px rgba(0,0,0,0.08);
}
.lock-icon { font-size: 80rpx; display: block; }
.lock-title { display: block; font-size: 36rpx; font-weight: 700; color: #059669; margin: 20rpx 0 40rpx; }
.lock-input { width: 100%; height: 88rpx; background: #f9fafb; border: 2rpx solid #e5e7eb; border-radius: 16rpx; padding: 0 24rpx; font-size: 30rpx; text-align: center; box-sizing: border-box; }
.lock-btn { width: 100%; height: 88rpx; background: #059669; color: #fff; font-size: 30rpx; font-weight: 600; border-radius: 16rpx; border: none; margin-top: 24rpx; }
.lock-error { display: block; color: #ef4444; font-size: 24rpx; margin-top: 16rpx; }
</style>
