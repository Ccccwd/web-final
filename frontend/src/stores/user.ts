import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login, logout, getUserInfo } from '@/api/auth'
import type { User, LoginData, UserResponse } from '@/types/user'
import { ElMessage } from 'element-plus'

export const useUserStore = defineStore('user', () => {
  // 状态
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('token'))
  const loading = ref(false)

  // 计算属性
  const isLoggedIn = computed(() => !!token.value)
  const userName = computed(() => user.value?.username || '')
  const userRole = computed(() => user.value?.role || 'user')

  // 登录
  const loginAction = async (loginData: LoginData) => {
    try {
      loading.value = true
      const response = await login(loginData)

      token.value = response.data.token
      user.value = response.data.user

      // 保存token到localStorage
      localStorage.setItem('token', response.data.token)

      ElMessage.success('登录成功')
      return response.data
    } catch (error) {
      ElMessage.error('登录失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  // 登出
  const logoutAction = async () => {
    try {
      await logout()
    } catch (error) {
      console.error('登出请求失败:', error)
    } finally {
      // 无论请求是否成功，都清除本地状态
      token.value = null
      user.value = null
      localStorage.removeItem('token')
      ElMessage.success('已登出')
    }
  }

  // 获取用户信息
  const fetchUserInfo = async () => {
    try {
      const response = await getUserInfo()
      user.value = response.data.data
      return response.data.data
    } catch (error) {
      console.error('获取用户信息失败:', error)
      throw error
    }
  }

  // 清除用户状态
  const clearUserState = () => {
    user.value = null
    token.value = null
    localStorage.removeItem('token')
  }

  return {
    // 状态
    user,
    token,
    loading,

    // 计算属性
    isLoggedIn,
    userName,
    userRole,

    // 方法
    loginAction,
    logoutAction,
    fetchUserInfo,
    clearUserState
  }
})