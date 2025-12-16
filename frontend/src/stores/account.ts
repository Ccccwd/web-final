import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getAccounts } from '@/api/account'
import type { Account } from '@/types/transaction'

export const useAccountStore = defineStore('account', () => {
  // 状态
  const accounts = ref<Account[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 计算属性
  const totalBalance = computed(() => {
    return accounts.value.reduce((sum, account) => sum + account.balance, 0)
  })

  const activeAccounts = computed(() => {
    return accounts.value.filter(account => account.is_active)
  })

  // 获取账户列表
  const fetchAccounts = async () => {
    try {
      loading.value = true
      error.value = null
      const response = await getAccounts()
      accounts.value = response.data
      return response.data
    } catch (err: any) {
      error.value = err.message || '获取账户失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // 根据ID查找账户
  const getAccountById = (accountId: number) => {
    return accounts.value.find(a => a.id === accountId)
  }

  // 清除状态
  const clearAccounts = () => {
    accounts.value = []
    error.value = null
  }

  return {
    // 状态
    accounts,
    loading,
    error,

    // 计算属性
    totalBalance,
    activeAccounts,

    // 方法
    fetchAccounts,
    getAccountById,
    clearAccounts
  }
})