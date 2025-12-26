import axios, { AxiosInstance, InternalAxiosRequestConfig, AxiosResponse, AxiosError } from 'axios'
import { ElMessage, ElLoading } from 'element-plus'
import { APIResponse } from '@/types'
import { useUserStore } from '@/stores/user'
import router from '@/router'

// 声明接口用于扩展axios配置
interface CustomAxiosRequestConfig extends InternalAxiosRequestConfig {
  showLoading?: boolean
  showError?: boolean
  skipAuth?: boolean
}

let loadingInstance: any = null
let loadingCount = 0
let isRefreshing = false // 防止多个401请求同时触发跳转

// 显示加载动画
function showLoading() {
  if (loadingCount === 0) {
    loadingInstance = ElLoading.service({
      lock: true,
      text: '加载中...',
      background: 'rgba(0, 0, 0, 0.7)',
      spinner: 'el-icon-loading'
    })
  }
  loadingCount++
}

// 隐藏加载动画
function hideLoading() {
  loadingCount--
  if (loadingCount === 0 && loadingInstance) {
    loadingInstance.close()
    loadingInstance = null
  }
}

// 创建axios实例
const request: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
request.interceptors.request.use(
  (config: InternalAxiosRequestConfig): InternalAxiosRequestConfig => {
    const customConfig = config as CustomAxiosRequestConfig
    
    // 显示加载动画
    if (customConfig.showLoading !== false) {
      showLoading()
    }

    // 添加认证token
    const userStore = useUserStore()
    if (!customConfig.skipAuth && userStore.token) {
      config.headers = config.headers || {} as any
      config.headers.Authorization = `Bearer ${userStore.token}`
    }

    return config
  },
  (error: AxiosError) => {
    hideLoading()
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response: AxiosResponse<APIResponse>): any => {
    // 隐藏加载动画
    const config = response.config as CustomAxiosRequestConfig
    if (config.showLoading !== false) {
      hideLoading()
    }

    const { data } = response

    // 检查响应格式
    // 后端有些API返回标准格式 {code, message, data, success}
    // 有些API直接返回数据 {transactions: [...], total: ...}
    if (data && typeof data === 'object') {
      // 如果有 code 字段，说明是标准API响应
      if ('code' in data) {
        if (data.code === 200 || data.success) {
          // 成功响应，返回完整数据
          return Promise.resolve(data)
        } else {
          // 业务错误
          const errorMessage = data.message || '请求失败'
          if (config.showError !== false) {
            ElMessage.error(errorMessage)
          }
          return Promise.reject(new Error(errorMessage))
        }
      } else {
        // 没有 code 字段，说明是直接数据响应
        // 包装成标准格式
        return Promise.resolve({
          code: 200,
          message: 'success',
          data: data,
          success: true
        })
      }
    }

    // 其他情况，直接返回数据
    return Promise.resolve({
      code: 200,
      message: 'success',
      data: data,
      success: true
    })
  },
  (error: AxiosError) => {
    // 隐藏加载动画
    const config = error.config as CustomAxiosRequestConfig
    if (config?.showLoading !== false) {
      hideLoading()
    }

    // 处理HTTP错误状态码
    if (error.response) {
      const { status, data } = error.response

      switch (status) {
        case 401:
          // 未授权，跳转到登录页
          if (!isRefreshing) {
            isRefreshing = true
            const userStore = useUserStore()
            userStore.logoutAction()

            // 延迟一点，确保所有401请求都被处理
            setTimeout(() => {
              isRefreshing = false
              if (router.currentRoute.value.path !== '/auth/login') {
                ElMessage.error('登录已过期，请重新登录')
                router.push({
                  path: '/auth/login',
                  query: { redirect: router.currentRoute.value.fullPath }
                })
              }
            }, 100)
          }
          break

        case 403:
          // 可能是token过期或未认证
          const errorMessage403 = (data as any)?.message || '没有权限访问'
          if (errorMessage403.includes('Not authenticated') || errorMessage403.includes('未认证')) {
            if (!isRefreshing) {
              isRefreshing = true
              const userStore = useUserStore()
              userStore.logoutAction()

              setTimeout(() => {
                isRefreshing = false
                if (router.currentRoute.value.path !== '/auth/login') {
                  ElMessage.error('请先登录')
                  router.push({
                    path: '/auth/login',
                    query: { redirect: router.currentRoute.value.fullPath }
                  })
                }
              }, 100)
            }
          } else {
            ElMessage.error(errorMessage403)
          }
          break

        case 404:
          ElMessage.error('请求的资源不存在')
          break

        case 422:
          // 表单验证错误
          const errorData = data as any
          if (errorData.data && Array.isArray(errorData.data)) {
            const errorMessage = errorData.data.map((err: any) => err.message).join(', ')
            ElMessage.error(errorMessage)
          } else {
            ElMessage.error('请求参数错误')
          }
          break

        case 500:
          ElMessage.error('服务器内部错误')
          break

        default:
          const errorMessage = (data as any)?.message || '网络错误'
          if (config?.showError !== false) {
            ElMessage.error(errorMessage)
          }
      }
    } else if (error.request) {
      // 请求已发送但没有收到响应
      ElMessage.error('网络连接失败，请检查网络设置')
    } else {
      // 请求配置错误
      ElMessage.error('请求配置错误')
    }

    return Promise.reject(error)
  }
)

// 封装常用请求方法
export const http = {
  get<T = any>(url: string, config?: CustomAxiosRequestConfig): Promise<APIResponse<T>> {
    return request.get(url, config)
  },

  post<T = any>(url: string, data?: any, config?: CustomAxiosRequestConfig): Promise<APIResponse<T>> {
    return request.post(url, data, config)
  },

  put<T = any>(url: string, data?: any, config?: CustomAxiosRequestConfig): Promise<APIResponse<T>> {
    return request.put(url, data, config)
  },

  delete<T = any>(url: string, config?: CustomAxiosRequestConfig): Promise<APIResponse<T>> {
    return request.delete(url, config)
  },

  patch<T = any>(url: string, data?: any, config?: CustomAxiosRequestConfig): Promise<APIResponse<T>> {
    return request.patch(url, data, config)
  },

  // 文件上传
  upload<T = any>(url: string, formData: FormData, config?: CustomAxiosRequestConfig): Promise<APIResponse<T>> {
    return request.post(url, formData, {
      ...config,
      headers: {
        'Content-Type': 'multipart/form-data',
        ...config?.headers
      }
    })
  },

  // 文件下载
  download(url: string, filename?: string, config?: CustomAxiosRequestConfig): Promise<void> {
    return request.get(url, {
      ...config,
      responseType: 'blob'
    }).then((response: any) => {
      // 创建下载链接
      const blob = new Blob([response])
      const downloadUrl = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = filename || 'download'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(downloadUrl)
    })
  }
}

// 导出实例
export default request