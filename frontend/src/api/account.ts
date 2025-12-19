import request from '@/utils/request'
import type { Account } from '@/types/transaction'

/**
 * 获取账户列表
 */
export function getAccounts(params?: {
  type?: string
  is_enabled?: boolean
}) {
  return request.get<{ data: { accounts: Account[]; total: number } }>('/accounts', { params })
}

/**
 * 创建账户
 */
export function createAccount(data: {
  name: string
  type: string
  initial_balance?: number
  icon?: string
  color?: string
  is_default?: boolean
  description?: string
}) {
  return request.post<{ data: Account }>('/accounts', data)
}

/**
 * 更新账户
 */
export function updateAccount(accountId: number, data: {
  name?: string
  initial_balance?: number
  icon?: string
  color?: string
  is_enabled?: boolean
  is_default?: boolean
  description?: string
}) {
  return request.put<{ data: Account }>(`/accounts/${accountId}`, data)
}

/**
 * 删除账户
 */
export function deleteAccount(accountId: number) {
  return request.delete<{ message: string }>(`/accounts/${accountId}`)
}

/**
 * 获取账户详情
 */
export function getAccount(accountId: number) {
  return request.get<{ data: Account }>(`/accounts/${accountId}`)
}

/**
 * 获取账户统计摘要
 */
export function getAccountSummary() {
  return request.get<{ data: any }>('/accounts/summary')
}

/**
 * 获取默认账户
 */
export function getDefaultAccount() {
  return request.get<{ data: Account }>('/accounts/default')
}

/**
 * 设置默认账户
 */
export function setDefaultAccount(accountId: number) {
  return request.post<{ data: Account }>(`/accounts/${accountId}/set-default`)
}

/**
 * 账户转账
 */
export function transfer(data: {
  from_account_id: number
  to_account_id: number
  amount: number
  transaction_date?: string
  remark?: string
}) {
  return request.post<{ message: string; data: any }>('/accounts/transfer', data)
}

/**
 * 获取账户余额历史
 */
export function getBalanceHistory(accountId: number, params?: {
  limit?: number
  offset?: number
  change_type?: string
}) {
  return request.get<{ data: any[] }>(`/accounts/${accountId}/balance-history`, { params })
}

/**
 * 获取账户余额统计
 */
export function getBalanceStatistics(accountId: number, params?: {
  days?: number
}) {
  return request.get<{ data: any }>(`/accounts/${accountId}/balance-statistics`, { params })
}

// 导出为accountApi（与组件中使用的名称一致）
export const accountApi = {
  getAccounts,
  createAccount,
  updateAccount,
  deleteAccount,
  getAccount,
  getAccountSummary,
  getDefaultAccount,
  setDefaultAccount,
  transfer,
  getBalanceHistory,
  getBalanceStatistics
}