import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  getBudgets,
  createBudget,
  updateBudget,
  deleteBudget,
  getBudgetSummary,
  getBudgetAlerts
} from '@/api/budget'
import type {
  Budget,
  BudgetSummary,
  BudgetAlerts,
  CreateBudgetData,
  UpdateBudgetData
} from '@/types/budget'

export const useBudgetStore = defineStore('budget', () => {
  // 状态
  const budgets = ref<Budget[]>([])
  const budgetSummary = ref<BudgetSummary | null>(null)
  const budgetAlerts = ref<BudgetAlerts | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 计算属性
  const totalBudget = computed(() => {
    return budgets.value.reduce((sum, budget) => sum + budget.amount, 0)
  })

  const totalSpending = computed(() => {
    return budgets.value.reduce((sum, budget) => sum + budget.actual_spending, 0)
  })

  const overBudgetCount = computed(() => {
    return budgets.value.filter(budget => budget.status === 'exceeded').length
  })

  const warningCount = computed(() => {
    return budgets.value.filter(budget => budget.status === 'warning').length
  })

  // 获取预算列表
  const fetchBudgets = async (params: {
    year: number
    month?: number
    period_type?: string
  }) => {
    try {
      loading.value = true
      error.value = null
      const response = await getBudgets(params)
      budgets.value = response.data.budgets
      return response.data
    } catch (err: any) {
      error.value = err.message || '获取预算列表失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // 创建预算
  const createBudgetItem = async (data: CreateBudgetData) => {
    try {
      loading.value = true
      error.value = null
      const response = await createBudget(data)
      return response.data
    } catch (err: any) {
      error.value = err.message || '创建预算失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // 更新预算
  const updateBudgetItem = async (budgetId: number, data: UpdateBudgetData) => {
    try {
      loading.value = true
      error.value = null
      const response = await updateBudget(budgetId, data)

      // 更新本地状态
      const budgetIndex = budgets.value.findIndex(b => b.id === budgetId)
      if (budgetIndex !== -1) {
        budgets.value[budgetIndex] = {
          ...budgets.value[budgetIndex],
          ...data
        }
      }

      return response.data
    } catch (err: any) {
      error.value = err.message || '更新预算失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // 删除预算
  const deleteBudgetItem = async (budgetId: number) => {
    try {
      loading.value = true
      error.value = null
      const response = await deleteBudget(budgetId)

      // 从本地状态中移除
      budgets.value = budgets.value.filter(b => b.id !== budgetId)

      return response.data
    } catch (err: any) {
      error.value = err.message || '删除预算失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // 获取预算汇总
  const fetchBudgetSummary = async (params: {
    year: number
    month?: number
  }) => {
    try {
      loading.value = true
      error.value = null
      const response = await getBudgetSummary(params)
      budgetSummary.value = response.data
      return response.data
    } catch (err: any) {
      error.value = err.message || '获取预算汇总失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // 获取预算预警
  const fetchBudgetAlerts = async () => {
    try {
      loading.value = true
      error.value = null
      const response = await getBudgetAlerts()
      budgetAlerts.value = response.data
      return response.data
    } catch (err: any) {
      error.value = err.message || '获取预算预警失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // 清除数据
  const clearData = () => {
    budgets.value = []
    budgetSummary.value = null
    budgetAlerts.value = null
    error.value = null
  }

  // 根据ID查找预算
  const getBudgetById = (budgetId: number) => {
    return budgets.value.find(b => b.id === budgetId)
  }

  // 获取预算状态统计
  const getBudgetStatusStats = () => {
    const normal = budgets.value.filter(b => b.status === 'normal').length
    const warning = budgets.value.filter(b => b.status === 'warning').length
    const exceeded = budgets.value.filter(b => b.status === 'exceeded').length

    return {
      normal,
      warning,
      exceeded,
      total: budgets.value.length
    }
  }

  return {
    // 状态
    budgets,
    budgetSummary,
    budgetAlerts,
    loading,
    error,

    // 计算属性
    totalBudget,
    totalSpending,
    overBudgetCount,
    warningCount,

    // 方法
    fetchBudgets,
    createBudgetItem,
    updateBudgetItem,
    deleteBudgetItem,
    fetchBudgetSummary,
    fetchBudgetAlerts,
    clearData,
    getBudgetById,
    getBudgetStatusStats
  }
})