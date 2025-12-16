import request from '@/utils/request'
import type {
  OverviewResponse,
  TrendData,
  CategoryStatisticsResponse,
  ExportParams,
  ExportResponse
} from '@/types/statistics'

/**
 * 获取首页概览数据
 */
export function getOverview(params?: {
  current_year?: number
  current_month?: number
}) {
  return request.get<OverviewResponse>('/statistics/overview', { params })
}

/**
 * 获取趋势数据
 */
export function getTrend(params: {
  period?: 'daily' | 'weekly' | 'monthly' | 'yearly'
  start_date?: string
  end_date?: string
}) {
  return request.get<{ data: TrendData[] }>('/statistics/trend', { params })
}

/**
 * 获取分类统计
 */
export function getCategoryStatistics(params: {
  transaction_type: 'income' | 'expense'
  period: 'monthly' | 'yearly'
  year: number
  month?: number
}) {
  return request.get<CategoryStatisticsResponse>('/statistics/category', { params })
}

/**
 * 导出Excel
 */
export function exportExcel(params: ExportParams) {
  return request.get<ExportResponse>('/statistics/export/excel', { params })
}

/**
 * 导出PDF
 */
export function exportPdf(params: ExportParams) {
  return request.get<ExportResponse>('/statistics/export/pdf', { params })
}