import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User } from '../types/user'

export const useUserStore = defineStore('user', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(null)

  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.is_superuser || false)

  // 从localStorage加载用户信息
  function loadUserFromStorage() {
    const storedToken = localStorage.getItem('access_token')
    const storedUser = localStorage.getItem('user')

    if (storedToken && storedUser) {
      token.value = storedToken
      user.value = JSON.parse(storedUser)
    }
  }

  // 设置用户信息
  function setUser(userinfo: User, accessToken: string) {
    user.value = userinfo
    token.value = accessToken

    // 保存到localStorage
    localStorage.setItem('access_token', accessToken)
    localStorage.setItem('user', JSON.stringify(userinfo))
  }

  // 清除用户信息
  function clearUser() {
    user.value = null
    token.value = null

    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
  }

  return {
    user,
    token,
    isAuthenticated,
    isAdmin,
    setUser,
    clearUser,
    loadUserFromStorage
  }
})
