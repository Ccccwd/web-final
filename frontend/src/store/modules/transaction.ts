import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  Transaction,
  TransactionCreate,
  TransactionUpdate,
  TransactionFilter,
  TransactionSummary,
  Category,
  Account
} from '@/types'
import { http } from '@/utils'
import { formatDate } from '@/utils/format'
import { ElMessage } from 'element-plus'

export const useTransactionStore = defineStore('transaction', () => {
  // 状态
  const transactions = ref<Transaction[]>([])
  const categories = ref<Category[]>([])
  const accounts = ref<Account[]>([])
  const summary = ref<TransactionSummary | null>(null)
  const isLoading = ref(false)
  const isSubmitting = ref(false)
  const currentPage = ref(1)
  const pageSize = ref(20)
  const total = ref(0)
  const filter = ref<TransactionFilter>({})

  // 计算属性
  const todayTransactions = computed(() => {
    const today = formatDate(new Date())
    return transactions.value.filter(t => formatDate(t.transaction_date) === today)
  })

  const recentTransactions = computed(() => {
    return transactions.value
      .sort((a, b) => new Date(b.transaction_date).getTime() - new Date(a.transaction_date).getTime())
      .slice(0, 10)
  })

  const incomeCategories = computed(() => {
    return categories.value.filter(c => c.type === 'income')
  })

  const expenseCategories = computed(() => {
    return categories.value.filter(c => c.type === 'expense')
  })

  const enabledAccounts = computed(() => {
    return accounts.value.filter(a => a.is_enabled)
  })

  const defaultAccount = computed(() => {
    return accounts.value.find(a => a.is_default) || enabledAccounts.value[0]
  })

  // 获取交易记录列表
  const fetchTransactions = async (params?: TransactionFilter): Promise<void> => {
    try {
      isLoading.value = true

      const queryParams = {
        page: params?.page || currentPage.value,
        pageSize: params?.page_size || pageSize.value,
        ...filter.value,
        ...params
      }

      const response = await http.get<Transaction[]>('/transactions', {
        params: queryParams
      })

      if (response.success && response.data) {
        transactions.value = response.data
        // 如果API返回分页信息，这里需要相应更新
        // currentPage.value = response.pagination.page
        // total.value = response.pagination.total
      }
    } catch (error: any) {
      console.error('Fetch transactions error:', error)
      ElMessage.error(error.message || '获取交易记录失败')
    } finally {
      isLoading.value = false
    }
  }

  // 获取单条交易记录
  const fetchTransaction = async (id: number): Promise<Transaction | null> => {
    try {
      const response = await http.get<Transaction>(`/transactions/${id}`)

      if (response.success && response.data) {
        return response.data
      }
      return null
    } catch (error: any) {
      console.error('Fetch transaction error:', error)
      ElMessage.error(error.message || '获取交易记录失败')
      return null
    }
  }

  // 创建交易记录
  const createTransaction = async (transactionData: TransactionCreate): Promise<boolean> => {
    try {
      isSubmitting.value = true

      const response = await http.post<Transaction>('/transactions', transactionData)

      if (response.success && response.data) {
        transactions.value.unshift(response.data)
        ElMessage.success('添加成功')

        // 刷新汇总数据
        await fetchSummary()

        return true
      } else {
        throw new Error(response.message || '添加失败')
      }
    } catch (error: any) {
      console.error('Create transaction error:', error)
      ElMessage.error(error.message || '添加失败')
      return false
    } finally {
      isSubmitting.value = false
    }
  }

  // 更新交易记录
  const updateTransaction = async (id: number, updateData: TransactionUpdate): Promise<boolean> => {
    try {
      isSubmitting.value = true

      const response = await http.put<Transaction>(`/transactions/${id}`, updateData)

      if (response.success && response.data) {
        const index = transactions.value.findIndex(t => t.id === id)
        if (index !== -1) {
          transactions.value[index] = response.data
        }
        ElMessage.success('更新成功')

        // 刷新汇总数据
        await fetchSummary()

        return true
      } else {
        throw new Error(response.message || '更新失败')
      }
    } catch (error: any) {
      console.error('Update transaction error:', error)
      ElMessage.error(error.message || '更新失败')
      return false
    } finally {
      isSubmitting.value = false
    }
  }

  // 删除交易记录
  const deleteTransaction = async (id: number): Promise<boolean> => {
    try {
      isSubmitting.value = true

      const response = await http.delete(`/transactions/${id}`)

      if (response.success) {
        const index = transactions.value.findIndex(t => t.id === id)
        if (index !== -1) {
          transactions.value.splice(index, 1)
        }
        ElMessage.success('删除成功')

        // 刷新汇总数据
        await fetchSummary()

        return true
      } else {
        throw new Error(response.message || '删除失败')
      }
    } catch (error: any) {
      console.error('Delete transaction error:', error)
      ElMessage.error(error.message || '删除失败')
      return false
    } finally {
      isSubmitting.value = false
    }
  }

  // 批量删除交易记录
  const deleteTransactions = async (ids: number[]): Promise<boolean> => {
    try {
      isSubmitting.value = true

      const response = await http.post('/transactions/batch-delete', { ids })

      if (response.success) {
        transactions.value = transactions.value.filter(t => !ids.includes(t.id))
        ElMessage.success(`成功删除 ${ids.length} 条记录`)

        // 刷新汇总数据
        await fetchSummary()

        return true
      } else {
        throw new Error(response.message || '批量删除失败')
      }
    } catch (error: any) {
      console.error('Batch delete transactions error:', error)
      ElMessage.error(error.message || '批量删除失败')
      return false
    } finally {
      isSubmitting.value = false
    }
  }

  // 获取汇总数据
  const fetchSummary = async (params?: { start_date?: string; end_date?: string }): Promise<void> => {
    try {
      const queryParams = params || {}

      const response = await http.get<TransactionSummary>('/transactions/summary', {
        params: queryParams
      })

      if (response.success && response.data) {
        summary.value = response.data
      }
    } catch (error: any) {
      console.error('Fetch summary error:', error)
      // 汇总数据获取失败不显示错误消息，避免干扰用户体验
    }
  }

  // 获取分类列表
  const fetchCategories = async (): Promise<void> => {
    try {
      const response = await http.get<Category[]>('/categories')

      if (response.success && response.data) {
        categories.value = response.data
      }
    } catch (error: any) {
      console.error('Fetch categories error:', error)
      ElMessage.error(error.message || '获取分类列表失败')
    }
  }

  // 获取账户列表
  const fetchAccounts = async (): Promise<void> => {
    try {
      const response = await http.get<Account[]>('/accounts')

      if (response.success && response.data) {
        accounts.value = response.data
      }
    } catch (error: any) {
      console.error('Fetch accounts error:', error)
      ElMessage.error(error.message || '获取账户列表失败')
    }
  }

  // 设置筛选条件
  const setFilter = (newFilter: Partial<TransactionFilter>): void => {
    filter.value = { ...filter.value, ...newFilter }
  }

  // 重置筛选条件
  const resetFilter = (): void => {
    filter.value = {}
    currentPage.value = 1
  }

  // 设置分页
  const setPagination = (page: number, size?: number): void => {
    currentPage.value = page
    if (size) {
      pageSize.value = size
    }
  }

  // 刷新数据
  const refresh = async (): Promise<void> => {
    await fetchTransactions()
    await fetchCategories()
    await fetchAccounts()
    await fetchSummary()
  }

  // 清空数据
  const clear = (): void => {
    transactions.value = []
    categories.value = []
    accounts.value = []
    summary.value = null
    currentPage.value = 1
    total.value = 0
    filter.value = {}
  }

  return {
    // 状态
    transactions,
    categories,
    accounts,
    summary,
    isLoading,
    isSubmitting,
    currentPage,
    pageSize,
    total,
    filter,

    // 计算属性
    todayTransactions,
    recentTransactions,
    incomeCategories,
    expenseCategories,
    enabledAccounts,
    defaultAccount,

    // 方法
    fetchTransactions,
    fetchTransaction,
    createTransaction,
    updateTransaction,
    deleteTransaction,
    deleteTransactions,
    fetchSummary,
    fetchCategories,
    fetchAccounts,
    setFilter,
    resetFilter,
    setPagination,
    refresh,
    clear
  }
})