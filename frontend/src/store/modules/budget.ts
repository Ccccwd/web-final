import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  Budget,
  BudgetCreate,
  BudgetUpdate,
  BudgetUsage,
  BudgetAlert,
  PeriodType
} from '@/types'
import { http } from '@/utils'
import { ElMessage } from 'element-plus'

export const useBudgetStore = defineStore('budget', () => {
  // 状态
  const budgets = ref<Budget[]>([])
  const budgetUsages = ref<BudgetUsage[]>([])
  const budgetAlerts = ref<BudgetAlert[]>([])
  const isLoading = ref(false)
  const isSubmitting = ref(false)

  // 计算属性
  const activeBudgets = computed(() => {
    return budgets.value.filter(b => b.is_enabled)
  })

  const monthlyBudgets = computed(() => {
    return activeBudgets.value.filter(b => b.period_type === PeriodType.MONTHLY)
  })

  const yearlyBudgets = computed(() => {
    return activeBudgets.value.filter(b => b.period_type === PeriodType.YEARLY)
  })

  const totalBudgetAmount = computed(() => {
    return monthlyBudgets.value
      .filter(b => !b.category_id) // 总预算
      .reduce((sum, b) => sum + b.amount, 0)
  })

  const categoryBudgets = computed(() => {
    return activeBudgets.value.filter(b => b.category_id)
  })

  const overBudgetAlerts = computed(() => {
    return budgetAlerts.value.filter(alert =>
      alert.alert_level === 'exceeded' || alert.alert_level === 'danger'
    )
  })

  // 获取预算列表
  const fetchBudgets = async (params?: { year?: number; month?: number }): Promise<void> => {
    try {
      isLoading.value = true

      const queryParams = params || {}

      const response = await http.get<Budget[]>('/budgets', {
        params: queryParams
      })

      if (response.success && response.data) {
        budgets.value = response.data
      }
    } catch (error: any) {
      console.error('Fetch budgets error:', error)
      ElMessage.error(error.message || '获取预算列表失败')
    } finally {
      isLoading.value = false
    }
  }

  // 获取单条预算
  const fetchBudget = async (id: number): Promise<Budget | null> => {
    try {
      const response = await http.get<Budget>(`/budgets/${id}`)

      if (response.success && response.data) {
        return response.data
      }
      return null
    } catch (error: any) {
      console.error('Fetch budget error:', error)
      ElMessage.error(error.message || '获取预算失败')
      return null
    }
  }

  // 创建预算
  const createBudget = async (budgetData: BudgetCreate): Promise<boolean> => {
    try {
      isSubmitting.value = true

      const response = await http.post<Budget>('/budgets', budgetData)

      if (response.success && response.data) {
        budgets.value.push(response.data)
        ElMessage.success('预算创建成功')

        // 刷新使用情况
        await fetchBudgetUsages()

        return true
      } else {
        throw new Error(response.message || '创建失败')
      }
    } catch (error: any) {
      console.error('Create budget error:', error)
      ElMessage.error(error.message || '创建失败')
      return false
    } finally {
      isSubmitting.value = false
    }
  }

  // 更新预算
  const updateBudget = async (id: number, updateData: BudgetUpdate): Promise<boolean> => {
    try {
      isSubmitting.value = true

      const response = await http.put<Budget>(`/budgets/${id}`, updateData)

      if (response.success && response.data) {
        const index = budgets.value.findIndex(b => b.id === id)
        if (index !== -1) {
          budgets.value[index] = response.data
        }
        ElMessage.success('更新成功')

        // 刷新使用情况
        await fetchBudgetUsages()

        return true
      } else {
        throw new Error(response.message || '更新失败')
      }
    } catch (error: any) {
      console.error('Update budget error:', error)
      ElMessage.error(error.message || '更新失败')
      return false
    } finally {
      isSubmitting.value = false
    }
  }

  // 删除预算
  const deleteBudget = async (id: number): Promise<boolean> => {
    try {
      isSubmitting.value = true

      const response = await http.delete(`/budgets/${id}`)

      if (response.success) {
        const index = budgets.value.findIndex(b => b.id === id)
        if (index !== -1) {
          budgets.value.splice(index, 1)
        }
        ElMessage.success('删除成功')

        // 刷新使用情况
        await fetchBudgetUsages()

        return true
      } else {
        throw new Error(response.message || '删除失败')
      }
    } catch (error: any) {
      console.error('Delete budget error:', error)
      ElMessage.error(error.message || '删除失败')
      return false
    } finally {
      isSubmitting.value = false
    }
  }

  // 切换预算状态
  const toggleBudgetStatus = async (id: number): Promise<boolean> => {
    try {
      const budget = budgets.value.find(b => b.id === id)
      if (!budget) return false

      const response = await http.put<Budget>(`/budgets/${id}`, {
        is_enabled: !budget.is_enabled
      })

      if (response.success && response.data) {
        const index = budgets.value.findIndex(b => b.id === id)
        if (index !== -1) {
          budgets.value[index] = response.data
        }

        const status = budget.is_enabled ? '禁用' : '启用'
        ElMessage.success(`预算${status}成功`)

        // 刷新使用情况
        await fetchBudgetUsages()

        return true
      } else {
        throw new Error(response.message || '操作失败')
      }
    } catch (error: any) {
      console.error('Toggle budget status error:', error)
      ElMessage.error(error.message || '操作失败')
      return false
    }
  }

  // 获取预算使用情况
  const fetchBudgetUsages = async (params?: { year?: number; month?: number }): Promise<void> => {
    try {
      const queryParams = params || {}

      const response = await http.get<BudgetUsage[]>('/budgets/usages', {
        params: queryParams
      })

      if (response.success && response.data) {
        budgetUsages.value = response.data
      }
    } catch (error: any) {
      console.error('Fetch budget usages error:', error)
      // 使用情况获取失败不显示错误消息
    }
  }

  // 获取预算预警
  const fetchBudgetAlerts = async (): Promise<void> => {
    try {
      const response = await http.get<BudgetAlert[]>('/budgets/alerts')

      if (response.success && response.data) {
        budgetAlerts.value = response.data
      }
    } catch (error: any) {
      console.error('Fetch budget alerts error:', error)
      // 预警获取失败不显示错误消息
    }
  }

  // 批量创建预算（基于模板）
  const createBudgetsFromTemplate = async (year: number, templateData: any[]): Promise<boolean> => {
    try {
      isSubmitting.value = true

      const response = await http.post<Budget[]>('/budgets/batch-create', {
        year,
        budgets: templateData
      })

      if (response.success && response.data) {
        budgets.value.push(...response.data)
        ElMessage.success(`成功创建 ${templateData.length} 个预算`)

        // 刷新使用情况
        await fetchBudgetUsages()

        return true
      } else {
        throw new Error(response.message || '批量创建失败')
      }
    } catch (error: any) {
      console.error('Create budgets from template error:', error)
      ElMessage.error(error.message || '批量创建失败')
      return false
    } finally {
      isSubmitting.value = false
    }
  }

  // 复制预算到下月/下年
  const copyBudgets = async (fromPeriod: { year: number; month?: number }, toPeriod: { year: number; month?: number }): Promise<boolean> => {
    try {
      isSubmitting.value = true

      const response = await http.post<Budget[]>('/budgets/copy', {
        from_period: fromPeriod,
        to_period: toPeriod
      })

      if (response.success && response.data) {
        budgets.value.push(...response.data)
        ElMessage.success('预算复制成功')

        // 刷新使用情况
        await fetchBudgetUsages()

        return true
      } else {
        throw new Error(response.message || '复制失败')
      }
    } catch (error: any) {
      console.error('Copy budgets error:', error)
      ElMessage.error(error.message || '复制失败')
      return false
    } finally {
      isSubmitting.value = false
    }
  }

  // 获取预算模板
  const fetchBudgetTemplates = async (): Promise<any[]> => {
    try {
      const response = await http.get<any[]>('/budgets/templates')

      if (response.success && response.data) {
        return response.data
      }
      return []
    } catch (error: any) {
      console.error('Fetch budget templates error:', error)
      return []
    }
  }

  // 检查预算冲突
  const checkBudgetConflict = async (budgetData: BudgetCreate, excludeId?: number): Promise<boolean> => {
    try {
      const queryParams = { ...budgetData, exclude_id }

      const response = await http.get<boolean>('/budgets/check-conflict', {
        params: queryParams
      })

      if (response.success) {
        return response.data || false
      }
      return false
    } catch (error) {
      console.error('Check budget conflict error:', error)
      return true // 有错误时假设有冲突，更安全
    }
  }

  // 刷新数据
  const refresh = async (params?: { year?: number; month?: number }): Promise<void> => {
    await fetchBudgets(params)
    await fetchBudgetUsages(params)
    await fetchBudgetAlerts()
  }

  // 清空数据
  const clear = (): void => {
    budgets.value = []
    budgetUsages.value = []
    budgetAlerts.value = []
  }

  return {
    // 状态
    budgets,
    budgetUsages,
    budgetAlerts,
    isLoading,
    isSubmitting,

    // 计算属性
    activeBudgets,
    monthlyBudgets,
    yearlyBudgets,
    totalBudgetAmount,
    categoryBudgets,
    overBudgetAlerts,

    // 方法
    fetchBudgets,
    fetchBudget,
    createBudget,
    updateBudget,
    deleteBudget,
    toggleBudgetStatus,
    fetchBudgetUsages,
    fetchBudgetAlerts,
    createBudgetsFromTemplate,
    copyBudgets,
    fetchBudgetTemplates,
    checkBudgetConflict,
    refresh,
    clear
  }
})