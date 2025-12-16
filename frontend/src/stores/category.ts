import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Category } from '@/types/transaction'
import { getCategories } from '@/api/category'

export const useCategoryStore = defineStore('category', () => {
  // 状态
  const categories = ref<Category[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 获取分类列表
  const fetchCategories = async () => {
    try {
      loading.value = true
      error.value = null
      const response = await getCategories()
      categories.value = response.data.data
      return response.data.data
    } catch (err: any) {
      error.value = err.message || '获取分类失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // 根据ID查找分类
  const getCategoryById = (categoryId: number) => {
    return categories.value.find(c => c.id === categoryId)
  }

  // 获取支出分类
  const getExpenseCategories = () => {
    return categories.value.filter(c => c.type === 'expense')
  }

  // 获取收入分类
  const getIncomeCategories = () => {
    return categories.value.filter(c => c.type === 'income')
  }

  // 清除状态
  const clearCategories = () => {
    categories.value = []
    error.value = null
  }

  return {
    // 状态
    categories,
    loading,
    error,

    // 方法
    fetchCategories,
    getCategoryById,
    getExpenseCategories,
    getIncomeCategories,
    clearCategories
  }
})