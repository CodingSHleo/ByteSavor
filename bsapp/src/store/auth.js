import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  const token = ref('')
  const currentUser = ref(null)
  const isLoggedIn = computed(() => token.value !== '')

  // 初始化：从本地存储恢复登录状态
  async function init() {
    try {
      const savedToken = uni.getStorageSync('auth_token') || ''
      if (savedToken) {
        token.value = savedToken
        currentUser.value = {
          userId: uni.getStorageSync('user_id') || '',
          username: uni.getStorageSync('username') || '',
          email: uni.getStorageSync('email') || ''
        }
      }
    } catch (e) {
      console.error('Auth init error:', e)
    }
  }

  // 保存登录数据
  async function setAuthData(user, newToken) {
    currentUser.value = user
    token.value = newToken

    uni.setStorageSync('auth_token', newToken)
    uni.setStorageSync('user_id', user.userId)
    uni.setStorageSync('username', user.username)
    uni.setStorageSync('email', user.email || '')
  }

  async function setUsername(username) {
    if (!currentUser.value) return
    currentUser.value = { ...currentUser.value, username }
    uni.setStorageSync('username', username)
  }

  // 清除认证数据
  async function clear() {
    currentUser.value = null
    token.value = ''

    uni.removeStorageSync('auth_token')
    uni.removeStorageSync('user_id')
    uni.removeStorageSync('username')
    uni.removeStorageSync('email')
  }

  // 退出登录
  async function logout() {
    await clear()
  }

  return { token, currentUser, isLoggedIn, init, setAuthData, setUsername, clear, logout }
})
