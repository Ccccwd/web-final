import { TransactionType, Category } from './transaction'

export interface OverviewData {
  period: string
  income: {
    amount: number
    count: number
    change: number // 环比增长%
  }
  expense: {
    amount: number
    count: number
    change: number // 环比增长%
  }
  balance: number
  top_categories: CategorySummary[]
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

export interface LineChartData extends ChartData {
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