import request from '@/utils/request'

/**
 * 微信账单导入API
 */
const wechatImportApi = {
  /**
   * 上传微信账单文件
   */
  upload: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)

    return request.post('/v1/wechat/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  /**
   * 预览微信账单数据
   */
  preview: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)

    return request.post('/v1/wechat/preview', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  /**
   * 获取导入记录详情
   */
  getImportLog: (importId: number) => {
    return request.get(`/v1/wechat/import/${importId}`)
  },

  /**
   * 获取导入记录列表
   */
  getImportLogs: (params?: { skip?: number; limit?: number }) => {
    return request.get('/v1/wechat/imports', { params })
  },

  /**
   * 获取导入错误详情
   */
  getImportErrors: (importId: number) => {
    return request.get(`/v1/wechat/imports/${importId}/errors`)
  },

  /**
   * 重试导入错误记录
   */
  retryImport: (importId: number, data: any) => {
    return request.post(`/v1/wechat/imports/${importId}/retry`, data)
  },

  /**
   * 验证导入后的账户余额
   */
  verifyBalance: (importId: number, tolerance?: number) => {
    return request.get(`/v1/wechat/imports/${importId}/verify-balance`, {
      params: { tolerance }
    })
  },

  /**
   * 获取导入统计信息
   */
  getStatistics: (days?: number) => {
    return request.get('/v1/wechat/statistics', { params: { days } })
  }
}

// 使用具名导出
export default wechatImportApi
