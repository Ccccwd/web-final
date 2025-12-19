import axios, { AxiosInstance, InternalAxiosRequestConfig, AxiosResponse, AxiosError } from 'axios'
import { ElMessage, ElLoading } from 'element-plus'
import { APIResponse } from '@/types'
import { useUserStore } from '@/stores/user'

// 声明接口用于扩展axios配置
interface CustomAxiosRequestConfig extends InternalAxiosRequestConfig {
  showLoading?: boolean
  showError?: boolean
  skipAuth?: boolean
  headers?: any
}

let loadingInstance: any = null
let loadingCount = 0

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
  (config: CustomAxiosRequestConfig) => {
    // 显示加载动画
    if (config.showLoading !== false) {
      showLoading()
    }

    // 添加认证token
    const userStore = useUserStore()
    if (!config.skipAuth && userStore.token) {
      config.headers = config.headers || {}
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
  (response: AxiosResponse<APIResponse>) => {
    // 隐藏加载动画
    const config = response.config as CustomAxiosRequestConfig
    if (config.showLoading !== false) {
      hideLoading()
    }

    const { data } = response

    // 检查业务状态码
    if (data.code === 200) {
      return data
    } else {
      // 业务错误
      const errorMessage = data.message || '请求失败'
      if (config.showError !== false) {
        ElMessage.error(errorMessage)
      }
      return Promise.reject(new Error(errorMessage))
    }
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
          const userStore = useUserStore()
          userStore.logout()
          ElMessage.error('登录已过期，请重新登录')
          // 可以在这里使用路由跳转到登录页
          // router.push('/login')
          break

        case 403:
          ElMessage.error('没有权限访问')
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