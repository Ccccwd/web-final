import request from '@/utils/request'
import type { Category } from '@/types/transaction'

/**
 * 获取分类列表
 */
export function getCategories() {
  return request.get<{ categories: Category[]; total: number }>('/categories')
}

/**
 * 创建分类
 */
export function createCategory(data: {
  name: string
  type: 'income' | 'expense'
  icon?: string
  color?: string
  parent_id?: number
}) {
  return request.post<{ data: Category }>('/categories', data)
}

/**
 * 更新分类
 */
export function updateCategory(categoryId: number, data: {
  name?: string
  icon?: string
  color?: string
}) {
  return request.put<{ data: Category }>(`/categories/${categoryId}`, data)
}

/**
 * 删除分类
 */
export function deleteCategory(categoryId: number) {
  return request.delete<{ message: string }>(`/categories/${categoryId}`)
}

/**
 * 获取分类详情
 */
export function getCategory(categoryId: number) {
  return request.get<{ data: Category }>(`/categories/${categoryId}`)
}