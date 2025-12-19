import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getOverview, getTrend, getCategoryStatistics } from '@/api/statistics'
import type {
  OverviewData,
  TrendData,
  CategoryStatistics,
  OverviewResponse,
  CategoryStatisticsResponse
} from '@/types/statistics'

export const useStatisticsStore = defineStore('statistics', () => {
  // 状态
  const overview = ref<OverviewData | null>(null)
  const trendData = ref<TrendData[]>([])
  const categoryStats = ref<CategoryStatistics | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 计算属性
  const monthlyIncome = computed(() => overview.value?.monthly_summary.income || 0)
  const monthlyExpense = computed(() => overview.value?.monthly_summary.expense || 0)
  const monthlyBalance = computed(() => overview.value?.monthly_summary.balance || 0)
  const totalBalance = computed(() => overview.value?.total_balance || 0)

  // 获取首页概览数据
  const fetchOverview = async (params?: {
    current_year?: number
    current_month?: number
  }) => {
    try {
      loading.value = true
      error.value = null
      const response = await getOverview(params)
      overview.value = response.data
      return response.data
    } catch (err: any) {
      error.value = err.message || '获取概览数据失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // 获取趋势数据
  const fetchTrend = async (params: {
    period?: 'daily' | 'weekly' | 'monthly' | 'yearly'
    start_date?: string
    end_date?: string
  }) => {
    try {
      loading.value = true
      error.value = null
      const response = await getTrend(params)
      trendData.value = response.data.data
      return response.data.data
    } catch (err: any) {
      error.value = err.message || '获取趋势数据失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // 获取分类统计
  const fetchCategoryStatistics = async (params: {
    transaction_type: 'income' | 'expense'
    period: 'monthly' | 'yearly'
    year: number
    month?: number
  }) => {
    try {
      loading.value = true
      error.value = null
      const response = await getCategoryStatistics(params)
      categoryStats.value = response.data
      return response.data
    } catch (err: any) {
      error.value = err.message || '获取分类统计失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // 清除数据
  const clearData = () => {
    overview.value = null
    trendData.value = []
    categoryStats.value = null
    error.value = null
  }

  return {
    // 状态
    overview,
    trendData,
    categoryStats,
    loading,
    error,

    // 计算属性
    monthlyIncome,
    monthlyExpense,
    monthlyBalance,
    totalBalance,

    // 方法
    fetchOverview,
    fetchTrend,
    fetchCategoryStatistics,
    clearData
  }
})