import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  Account,
  AccountType,
  Transaction,
  AccountSummary
} from '@/types'
import { http } from '@/utils'
import { formatAmount } from '@/utils/format'
import { ElMessage } from 'element-plus'

export const useAccountStore = defineStore('account', () => {
  // 状态
  const accounts = ref<Account[]>([])
  const accountSummaries = ref<AccountSummary[]>([])
  const accountTransactions = ref<Transaction[]>([])
  const isLoading = ref(false)
  const isSubmitting = ref(false)
  const selectedAccountId = ref<number | null>(null)

  // 计算属性
  const enabledAccounts = computed(() => {
    return accounts.value.filter(a => a.is_enabled)
  })

  const totalAssets = computed(() => {
    return enabledAccounts.value.reduce((sum, account) => sum + account.balance, 0)
  })

  const defaultAccount = computed(() => {
    return accounts.value.find(a => a.is_default) || enabledAccounts.value[0]
  })

  const selectedAccount = computed(() => {
    if (!selectedAccountId.value) return null
    return accounts.value.find(a => a.id === selectedAccountId.value) || null
  })

  const accountsByType = computed(() => {
    const grouped: Record<AccountType, Account[]> = {
      cash: [],
      bank: [],
      wechat: [],
      alipay: [],
      meal_card: [],
      credit_card: [],
      other: []
    }

    enabledAccounts.value.forEach(account => {
      grouped[account.type].push(account)
    })

    return grouped
  })

  const totalAssetsByType = computed(() => {
    const totals: Record<string, number> = {}

    Object.entries(accountsByType.value).forEach(([type, accounts]) => {
      totals[type] = accounts.reduce((sum, account) => sum + account.balance, 0)
    })

    return totals
  })

  const accountOptions = computed(() => {
    return enabledAccounts.value.map(account => ({
      label: `${account.name} (${formatAmount(account.balance)})`,
      value: account.id,
      icon: account.icon,
      color: account.color
    }))
  })

  // 获取账户列表
  const fetchAccounts = async (): Promise<void> => {
    try {
      isLoading.value = true

      const response = await http.get<Account[]>('/accounts')

      if (response.success && response.data) {
        accounts.value = response.data
      }
    } catch (error: any) {
      console.error('Fetch accounts error:', error)
      ElMessage.error(error.message || '获取账户列表失败')
    } finally {
      isLoading.value = false
    }
  }

  // 获取单条账户
  const fetchAccount = async (id: number): Promise<Account | null> => {
    try {
      const response = await http.get<Account>(`/accounts/${id}`)

      if (response.success && response.data) {
        return response.data
      }
      return null
    } catch (error: any) {
      console.error('Fetch account error:', error)
      ElMessage.error(error.message || '获取账户失败')
      return null
    }
  }

  // 创建账户
  const createAccount = async (accountData: Omit<Account, 'id' | 'user_id' | 'created_at'>): Promise<boolean> => {
    try {
      isSubmitting.value = true

      const response = await http.post<Account>('/accounts', accountData)

      if (response.success && response.data) {
        accounts.value.push(response.data)
        ElMessage.success('账户创建成功')

        // 如果新账户设为默认，更新其他账户的默认状态
        if (accountData.is_default) {
          accounts.value.forEach(account => {
            if (account.id !== response.data!.id) {
              account.is_default = false
            }
          })
        }

        return true
      } else {
        throw new Error(response.message || '创建失败')
      }
    } catch (error: any) {
      console.error('Create account error:', error)
      ElMessage.error(error.message || '创建失败')
      return false
    } finally {
      isSubmitting.value = false
    }
  }

  // 更新账户
  const updateAccount = async (id: number, updateData: Partial<Account>): Promise<boolean> => {
    try {
      isSubmitting.value = true

      const response = await http.put<Account>(`/accounts/${id}`, updateData)

      if (response.success && response.data) {
        const index = accounts.value.findIndex(a => a.id === id)
        if (index !== -1) {
          accounts.value[index] = response.data
        }
        ElMessage.success('更新成功')

        // 如果更新了默认账户，更新其他账户
        if (updateData.is_default) {
          accounts.value.forEach(account => {
            if (account.id !== id) {
              account.is_default = false
            }
          })
        }

        return true
      } else {
        throw new Error(response.message || '更新失败')
      }
    } catch (error: any) {
      console.error('Update account error:', error)
      ElMessage.error(error.message || '更新失败')
      return false
    } finally {
      isSubmitting.value = false
    }
  }

  // 删除账户
  const deleteAccount = async (id: number): Promise<boolean> => {
    try {
      isSubmitting.value = true

      const response = await http.delete(`/accounts/${id}`)

      if (response.success) {
        const index = accounts.value.findIndex(a => a.id === id)
        if (index !== -1) {
          accounts.value.splice(index, 1)
        }
        ElMessage.success('删除成功')

        // 如果删除的是选中的账户，清除选择
        if (selectedAccountId.value === id) {
          selectedAccountId.value = null
        }

        return true
      } else {
        throw new Error(response.message || '删除失败')
      }
    } catch (error: any) {
      console.error('Delete account error:', error)
      ElMessage.error(error.message || '删除失败')
      return false
    } finally {
      isSubmitting.value = false
    }
  }

  // 切换账户状态
  const toggleAccountStatus = async (id: number): Promise<boolean> => {
    try {
      const account = accounts.value.find(a => a.id === id)
      if (!account) return false

      const response = await http.put<Account>(`/accounts/${id}`, {
        is_enabled: !account.is_enabled
      })

      if (response.success && response.data) {
        const index = accounts.value.findIndex(a => a.id === id)
        if (index !== -1) {
          accounts.value[index] = response.data
        }

        const status = account.is_enabled ? '禁用' : '启用'
        ElMessage.success(`账户${status}成功`)

        // 如果禁用的是选中的账户，清除选择
        if (!response.data.is_enabled && selectedAccountId.value === id) {
          selectedAccountId.value = null
        }

        return true
      } else {
        throw new Error(response.message || '操作失败')
      }
    } catch (error: any) {
      console.error('Toggle account status error:', error)
      ElMessage.error(error.message || '操作失败')
      return false
    }
  }

  // 设置默认账户
  const setDefaultAccount = async (id: number): Promise<boolean> => {
    try {
      const response = await http.put<Account>(`/accounts/${id}`, {
        is_default: true
      })

      if (response.success && response.data) {
        // 更新所有账户的默认状态
        accounts.value.forEach(account => {
          account.is_default = account.id === id
        })

        ElMessage.success('默认账户设置成功')
        return true
      } else {
        throw new Error(response.message || '设置失败')
      }
    } catch (error: any) {
      console.error('Set default account error:', error)
      ElMessage.error(error.message || '设置失败')
      return false
    }
  }

  // 账户转账
  const transfer = async (fromAccountId: number, toAccountId: number, amount: number, remark?: string): Promise<boolean> => {
    try {
      isSubmitting.value = true

      const response = await http.post('/accounts/transfer', {
        from_account_id: fromAccountId,
        to_account_id: toAccountId,
        amount,
        remark
      })

      if (response.success) {
        // 更新账户余额
        const fromAccount = accounts.value.find(a => a.id === fromAccountId)
        const toAccount = accounts.value.find(a => a.id === toAccountId)

        if (fromAccount) {
          fromAccount.balance -= amount
        }
        if (toAccount) {
          toAccount.balance += amount
        }

        ElMessage.success('转账成功')
        return true
      } else {
        throw new Error(response.message || '转账失败')
      }
    } catch (error: any) {
      console.error('Transfer error:', error)
      ElMessage.error(error.message || '转账失败')
      return false
    } finally {
      isSubmitting.value = false
    }
  }

  // 获取账户汇总信息
  const fetchAccountSummaries = async (params?: { start_date?: string; end_date?: string }): Promise<void> => {
    try {
      const queryParams = params || {}

      const response = await http.get<AccountSummary[]>('/accounts/summaries', {
        params: queryParams
      })

      if (response.success && response.data) {
        accountSummaries.value = response.data
      }
    } catch (error: any) {
      console.error('Fetch account summaries error:', error)
    }
  }

  // 获取账户交易记录
  const fetchAccountTransactions = async (accountId: number, params?: any): Promise<void> => {
    try {
      isLoading.value = true

      const queryParams = {
        account_ids: [accountId],
        ...params
      }

      const response = await http.get<Transaction[]>('/transactions', {
        params: queryParams
      })

      if (response.success && response.data) {
        accountTransactions.value = response.data
      }
    } catch (error: any) {
      console.error('Fetch account transactions error:', error)
      ElMessage.error(error.message || '获取账户交易记录失败')
    } finally {
      isLoading.value = false
    }
  }

  // 调整账户余额
  const adjustBalance = async (accountId: number, newBalance: number, remark?: string): Promise<boolean> => {
    try {
      isSubmitting.value = true

      const account = accounts.value.find(a => a.id === accountId)
      if (!account) return false

      const adjustmentAmount = newBalance - account.balance

      const response = await http.post(`/accounts/${accountId}/adjust-balance`, {
        new_balance: newBalance,
        adjustment_amount: adjustmentAmount,
        remark
      })

      if (response.success) {
        account.balance = newBalance
        ElMessage.success('余额调整成功')
        return true
      } else {
        throw new Error(response.message || '调整失败')
      }
    } catch (error: any) {
      console.error('Adjust balance error:', error)
      ElMessage.error(error.message || '调整失败')
      return false
    } finally {
      isSubmitting.value = false
    }
  }

  // 选择账户
  const selectAccount = (accountId: number | null): void => {
    selectedAccountId.value = accountId
  }

  // 刷新数据
  const refresh = async (): Promise<void> => {
    await fetchAccounts()
    await fetchAccountSummaries()
  }

  // 清空数据
  const clear = (): void => {
    accounts.value = []
    accountSummaries.value = []
    accountTransactions.value = []
    selectedAccountId.value = null
  }

  return {
    // 状态
    accounts,
    accountSummaries,
    accountTransactions,
    isLoading,
    isSubmitting,
    selectedAccountId,

    // 计算属性
    enabledAccounts,
    totalAssets,
    defaultAccount,
    selectedAccount,
    accountsByType,
    totalAssetsByType,
    accountOptions,

    // 方法
    fetchAccounts,
    fetchAccount,
    createAccount,
    updateAccount,
    deleteAccount,
    toggleAccountStatus,
    setDefaultAccount,
    transfer,
    fetchAccountSummaries,
    fetchAccountTransactions,
    adjustBalance,
    selectAccount,
    refresh,
    clear
  }
})