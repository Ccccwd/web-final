export interface Budget {
  id: number
  category?: {
    id: number
    name: string
    icon: string
    color: string
  }
  amount: number
  actual_spending: number
  remaining: number
  percentage: number
  status: 'normal' | 'warning' | 'exceeded'
  period_type: 'monthly' | 'yearly'
  year: number
  month?: number
  alert_threshold: number
  is_enabled: boolean
  created_at?: string
}

export interface BudgetSummary {
  year: number
  month?: number
  summary: {
    total_budget: number
    total_spending: number
    total_remaining: number
    total_percentage: number
    overall_status: 'normal' | 'warning' | 'exceeded'
    budget_count: number
    over_budget_count: number
    warning_count: number
  }
  details: Array<{
    category_name: string
    budget_amount: number
    actual_spending: number
    percentage: number
    status: 'normal' | 'warning' | 'exceeded'
  }>
}

export interface BudgetAlert {
  id: number
  category_name: string
  budget_amount: number
  actual_spending: number
  percentage: number
  status: 'warning' | 'exceeded'
  remaining: number
  alert_threshold: number
  period_type: 'monthly' | 'yearly'
}

export interface BudgetAlerts {
  alerts: BudgetAlert[]
  total_count: number
  warning_count: number
  exceeded_count: number
}

export interface CreateBudgetData {
  category_id?: number
  amount: number
  period_type: 'monthly' | 'yearly'
  year: number
  month?: number
  alert_threshold?: number
  is_enabled?: boolean
}

export interface UpdateBudgetData {
  amount?: number
  alert_threshold?: number
  is_enabled?: boolean
}

// 添加缺失的类型
export interface BudgetCreate {
  category_id: number
  amount: number
  period_type: 'monthly' | 'yearly'
  year: number
  month?: number
  alert_threshold?: number
  is_enabled?: boolean
}

export interface BudgetUpdate {
  amount?: number
  alert_threshold?: number
  is_enabled?: boolean
}

export interface BudgetUsage {
  category_id: number
  category_name: string
  budget_amount: number
  actual_spending: number
  percentage: number
  status: 'normal' | 'warning' | 'exceeded'
  remaining: number
  alert_threshold: number
  period_type: 'monthly' | 'yearly'
}

export type PeriodType = 'monthly' | 'yearly'