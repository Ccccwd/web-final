import request from '@/utils/request'
import type { Transaction, TransactionType } from '@/types/transaction'

/**
 * 获取交易列表
 */
export function getTransactions(params?: {
  type?: string
  category_id?: number
  account_id?: number
  start_date?: string
  end_date?: string
  keyword?: string
  page?: number
  page_size?: number
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}) {
  return request.get<{
    data: Transaction[]
    pagination: {
      page: number
      page_size: number
      total: number
      total_pages: number
    }
  }>('/transactions', { params })
}

/**
 * 创建交易记录
 */
export function createTransaction(data: {
  type: TransactionType
  amount: number
  category_id: number
  account_id: number
  description?: string
  transaction_date?: string
  tags?: string[]
}) {
  return request.post<{ data: Transaction }>('/transactions', data)
}

/**
 * 更新交易记录
 */
export function updateTransaction(transactionId: number, data: {
  type?: TransactionType
  amount?: number
  category_id?: number
  account_id?: number
  description?: string
  transaction_date?: string
  tags?: string[]
}) {
  return request.put<{ data: Transaction }>(`/transactions/${transactionId}`, data)
}

/**
 * 删除交易记录
 */
export function deleteTransaction(transactionId: number) {
  return request.delete<{ message: string }>(`/transactions/${transactionId}`)
}

/**
 * 获取交易详情
 */
export function getTransaction(transactionId: number) {
  return request.get<{ data: Transaction }>(`/transactions/${transactionId}`)
}

/**
 * 批量导入交易记录
 */
export function importTransactions(data: {
  transactions: any[]
  source?: string
}) {
  return request.post<{ message: string; data: any }>('/transactions/import', data)
}

/**
 * 获取交易统计数据
 */
export function getStatistics(params?: {
  start_date?: string
  end_date?: string
  type?: string
}) {
  return request.get<{
    data: {
      total_income: number
      total_expense: number
      net_income: number
      transaction_count: number
    }
  }>('/transactions/statistics', { params })
}