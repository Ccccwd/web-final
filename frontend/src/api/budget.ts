import request from '@/utils/request'
import type {
  Budget,
  BudgetSummary,
  BudgetAlerts,
  CreateBudgetData,
  UpdateBudgetData
} from '@/types/budget'

/**
 * 获取预算列表
 */
export function getBudgets(params: {
  year: number
  month?: number
  period_type?: string
}) {
  return request.get<{
    year: number
    month?: number
    period_type?: string
    budgets: Budget[]
  }>('/budgets', { params })
}

/**
 * 创建预算
 */
export function createBudget(data: CreateBudgetData) {
  return request.post<{ id: number; message: string }>('/budgets', data)
}

/**
 * 更新预算
 */
export function updateBudget(budgetId: number, data: UpdateBudgetData) {
  return request.put<{ message: string }>(`/budgets/${budgetId}`, data)
}

/**
 * 删除预算
 */
export function deleteBudget(budgetId: number) {
  return request.delete<{ message: string }>(`/budgets/${budgetId}`)
}

/**
 * 获取预算汇总
 */
export function getBudgetSummary(params: {
  year: number
  month?: number
}) {
  return request.get<BudgetSummary>('/budgets/summary', { params })
}

/**
 * 获取预算预警
 */
export function getBudgetAlerts() {
  return request.get<BudgetAlerts>('/budgets/alerts')
}