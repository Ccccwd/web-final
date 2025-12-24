import { TransactionType, Category } from './transaction'

// API响应类型
export interface OverviewResponse {
  data: OverviewData
}

export interface CategoryStatisticsResponse {
  data: CategoryStatistics
}

export interface OverviewData {
  monthly_summary: {
    income: number
    expense: number
    balance: number
    income_growth: number
    expense_growth: number
  }
  total_balance: number
  category_distribution: Array<{
    name: string
    icon: string
    color: string
    amount: number
    percentage: number
  }>
  trend_data: Array<{
    date: string
    amount: number
  }>
  period: string
}

export interface OverviewResponse {
  data: OverviewData
}

export interface CategorySummary {
  category_id: number
  category_name: string
  icon?: string
  color?: string
  total_amount: number
  count: number
  percentage: number
  change?: number // 同比变化
}

export interface CategoryStatistics {
  transaction_type: string
  period: string
  year: number
  month?: number
  total_amount: number
  categories: Array<{
    id: number
    name: string
    icon: string
    color: string
    amount: number
    count: number
    percentage: number
  }>
}

export interface CategoryStatisticsResponse {
  data: CategoryStatistics
}

export interface TrendData {
  date: string
  income: number
  expense: number
  balance: number
}

export interface AccountSummary {
  account_id: number
  account_name: string
  balance: number
  total_income: number
  total_expense: number
  transaction_count: number
  type: string
}

export interface MonthlyReport {
  year: number
  month: number
  overview: OverviewData
  daily_trends: TrendData[]
  category_analysis: CategorySummary[]
  account_analysis: AccountSummary[]
}

export interface StatisticsFilter {
  period_type: 'daily' | 'weekly' | 'monthly' | 'yearly' | 'custom'
  start_date?: string
  end_date?: string
  category_ids?: number[]
  account_ids?: number[]
  compare_with_previous?: boolean
}

export interface ChartData {
  labels: string[]
  datasets: {
    label: string
    data: number[]
    backgroundColor?: string[]
    borderColor?: string[]
    borderWidth?: number
  }[]
}

export interface PieChartData extends ChartData {
  datasets: {
    label: string
    data: number[]
    backgroundColor: string[]
    borderColor?: string[]
    borderWidth?: number
  }[]
}

export interface LineChartData {
  labels: string[]
  datasets: {
    label: string
    data: number[]
    borderColor: string
    backgroundColor?: string
    borderWidth?: number
    fill?: boolean
    tension?: number
  }[]
}

export interface BarChartData extends ChartData {
  datasets: {
    label: string
    data: number[]
    backgroundColor: string[]
    borderColor?: string[]
    borderWidth?: number
  }[]
}

export interface ExportParams {
  transaction_type: 'income' | 'expense' | 'all'
  start_date: string
  end_date: string
}

export interface ExportResponse {
  message: string
  file_path: string
  filename: string
}