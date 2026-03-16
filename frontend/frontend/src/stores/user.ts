/**
 * 用户状态管理
 */
import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import type { User } from '@/api/modules'
import { authApi } from '@/api/modules'

export const useUserStore = defineStore('user', () => {
  // 状态
  const token = ref<string>(localStorage.getItem('access_token') || '')
  const userInfo = reactive<User>(
    JSON.parse(localStorage.getItem('user') || '{}')
  )
  const isLoggedIn = ref<boolean>(!!token.value)

  /**
   * 设置token
   */
  function setToken(newToken: string) {
    token.value = newToken
    isLoggedIn.value = true
    localStorage.setItem('access_token', newToken)
  }

  /**
   * 设置用户信息
   */
  function setUserInfo(user: User) {
    Object.assign(userInfo, user)
    localStorage.setItem('user', JSON.stringify(user))
  }

  /**
   * 登录
   */
  async function login(username: string, password: string) {
    try {
      const response = await authApi.login(username, password)
      const { access_token } = response.data.data

      setToken(access_token)
      setUserInfo({
        username,
        email: '',
        full_name: username,
        id: 0,
        is_active: true,
        is_superuser: false,
        created_at: new Date().toISOString()
      })

      return response
    } catch (error) {
      console.error('Login error:', error)
      throw error
    }
  }

  /**
   * 注册
   */
  async function register(userData: {
    username: string
    email: string
    password: string
    full_name: string
  }) {
    try {
      const response = await authApi.register(userData)
      return response
    } catch (error) {
      console.error('Register error:', error)
      throw error
    }
  }

  /**
   * 登出
   */
  async function logout() {
    try {
      await authApi.logout()
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      // 无论是否成功都清除本地状态
      token.value = ''
      isLoggedIn.value = false
      Object.assign(userInfo, {})
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
    }
  }

  return {
    token,
    userInfo,
    isLoggedIn,
    setToken,
    setUserInfo,
    login,
    register,
    logout
  }
})
