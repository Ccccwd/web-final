import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { User, UserLogin, UserCreate, Token } from '@/types'
import { http } from '@/utils'
import { TokenManager } from '@/utils/auth'
import { ElMessage } from 'element-plus'

export const useUserStore = defineStore('user', () => {
  // 状态
  const user = ref<User | null>(null)
  const token = ref<string | null>(TokenManager.getAccessToken())
  const refreshToken = ref<string | null>(TokenManager.getRefreshToken())
  const isLoading = ref(false)
  const loginAttempts = ref(0)

  // 计算属性
  const isLoggedIn = computed(() => !!token.value && !!user.value)
  const userInfo = computed(() => user.value)
  const username = computed(() => user.value?.username || '')
  const userId = computed(() => user.value?.id || null)
  const avatar = computed(() => user.value?.avatar || '')

  // 登录
  const login = async (loginData: UserLogin): Promise<boolean> => {
    try {
      isLoading.value = true

      const response = await http.post<Token>('/auth/login', loginData)

      if (response.success && response.data) {
        // 保存token
        token.value = response.data.access_token
        refreshToken.value = response.data.refresh_token
        TokenManager.setToken(response.data)

        // 获取用户信息
        await fetchUserInfo()

        // 重置登录尝试次数
        loginAttempts.value = 0

        ElMessage.success('登录成功')
        return true
      } else {
        throw new Error(response.message || '登录失败')
      }
    } catch (error: any) {
      loginAttempts.value++
      const errorMessage = error.message || '登录失败，请检查用户名和密码'
      ElMessage.error(errorMessage)
      return false
    } finally {
      isLoading.value = false
    }
  }

  // 注册
  const register = async (registerData: UserCreate): Promise<boolean> => {
    try {
      isLoading.value = true

      const response = await http.post<User>('/auth/register', registerData)

      if (response.success && response.data) {
        ElMessage.success('注册成功，请登录')
        return true
      } else {
        throw new Error(response.message || '注册失败')
      }
    } catch (error: any) {
      const errorMessage = error.message || '注册失败'
      ElMessage.error(errorMessage)
      return false
    } finally {
      isLoading.value = false
    }
  }

  // 登出
  const logout = async (): Promise<void> => {
    try {
      // 调用后端登出接口（可选）
      await http.post('/auth/logout')
    } catch (error) {
      // 忽略登出接口错误
      console.error('Logout API error:', error)
    } finally {
      // 清除本地数据
      clearUser()
      ElMessage.success('已退出登录')
    }
  }

  // 刷新token
  const refreshAccessToken = async (): Promise<boolean> => {
    try {
      const currentRefreshToken = refreshToken.value
      if (!currentRefreshToken) {
        throw new Error('没有刷新token')
      }

      const response = await http.post<Token>('/auth/refresh', {
        refresh_token: currentRefreshToken
      })

      if (response.success && response.data) {
        token.value = response.data.access_token
        refreshToken.value = response.data.refresh_token
        TokenManager.setToken(response.data)
        return true
      } else {
        throw new Error(response.message || '刷新token失败')
      }
    } catch (error) {
      console.error('Refresh token error:', error)
      // 刷新失败，清除用户信息
      clearUser()
      return false
    }
  }

  // 获取用户信息
  const fetchUserInfo = async (): Promise<User | null> => {
    try {
      const response = await http.get<User>('/auth/me')

      if (response.success && response.data) {
        user.value = response.data
        TokenManager.setUser(response.data)
        return response.data
      } else {
        throw new Error(response.message || '获取用户信息失败')
      }
    } catch (error) {
      console.error('Fetch user info error:', error)
      return null
    }
  }

  // 更新用户信息
  const updateUserInfo = async (userData: Partial<User>): Promise<boolean> => {
    try {
      isLoading.value = true

      const response = await http.put<User>('/auth/profile', userData)

      if (response.success && response.data) {
        user.value = response.data
        TokenManager.setUser(response.data)
        ElMessage.success('更新成功')
        return true
      } else {
        throw new Error(response.message || '更新失败')
      }
    } catch (error: any) {
      const errorMessage = error.message || '更新失败'
      ElMessage.error(errorMessage)
      return false
    } finally {
      isLoading.value = false
    }
  }

  // 修改密码
  const changePassword = async (oldPassword: string, newPassword: string): Promise<boolean> => {
    try {
      isLoading.value = true

      const response = await http.post('/auth/change-password', {
        old_password: oldPassword,
        new_password: newPassword
      })

      if (response.success) {
        ElMessage.success('密码修改成功')
        return true
      } else {
        throw new Error(response.message || '密码修改失败')
      }
    } catch (error: any) {
      const errorMessage = error.message || '密码修改失败'
      ElMessage.error(errorMessage)
      return false
    } finally {
      isLoading.value = false
    }
  }

  // 重置密码
  const resetPassword = async (email: string): Promise<boolean> => {
    try {
      isLoading.value = true

      const response = await http.post('/auth/reset-password', { email })

      if (response.success) {
        ElMessage.success('重置密码邮件已发送')
        return true
      } else {
        throw new Error(response.message || '重置密码失败')
      }
    } catch (error: any) {
      const errorMessage = error.message || '重置密码失败'
      ElMessage.error(errorMessage)
      return false
    } finally {
      isLoading.value = false
    }
  }

  // 清除用户信息
  const clearUser = (): void => {
    user.value = null
    token.value = null
    refreshToken.value = null
    loginAttempts.value = 0
    TokenManager.clearTokens()
  }

  // 检查登录状态
  const checkAuthStatus = async (): Promise<boolean> => {
    const currentToken = TokenManager.getAccessToken()

    if (!currentToken) {
      clearUser()
      return false
    }

    // 检查token是否过期
    if (TokenManager.isTokenExpired(currentToken)) {
      // 尝试刷新token
      const refreshSuccess = await refreshAccessToken()
      if (!refreshSuccess) {
        clearUser()
        return false
      }
    }

    // 获取用户信息
    const userInfo = await fetchUserInfo()
    if (!userInfo) {
      clearUser()
      return false
    }

    return true
  }

  // 初始化用户状态（应用启动时调用）
  const initializeAuth = async (): Promise<boolean> => {
    return await checkAuthStatus()
  }

  return {
    // 状态
    user,
    token,
    refreshToken,
    isLoading,
    loginAttempts,

    // 计算属性
    isLoggedIn,
    userInfo,
    username,
    userId,
    avatar,

    // 方法
    login,
    register,
    logout,
    refreshAccessToken,
    fetchUserInfo,
    updateUserInfo,
    changePassword,
    resetPassword,
    clearUser,
    checkAuthStatus,
    initializeAuth
  }
})