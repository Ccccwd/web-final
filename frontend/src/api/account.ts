import request from '@/utils/request'
import type { Account } from '@/types/transaction'

/**
 * 获取账户列表
 */
export function getAccounts() {
  return request.get<{ data: Account[] }>('/accounts')
}

/**
 * 创建账户
 */
export function createAccount(data: {
  name: string
  type: string
  balance?: number
  icon?: string
  color?: string
  description?: string
}) {
  return request.post<{ data: Account }>('/accounts', data)
}

/**
 * 更新账户
 */
export function updateAccount(accountId: number, data: {
  name?: string
  balance?: number
  icon?: string
  color?: string
  description?: string
  is_active?: boolean
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
 * 账户转账
 */
export function transferBetweenAccounts(data: {
  from_account_id: number
  to_account_id: number
  amount: number
  description?: string
}) {
  return request.post<{ message: string; data: any }>('/accounts/transfer', data)
}