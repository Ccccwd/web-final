export enum PeriodType {
  MONTHLY = 'monthly',
  YEARLY = 'yearly'
}

export interface Budget {
  id: number
  user_id: number
  category_id?: number
  amount: number
  period_type: PeriodType
  year: number
  month?: number
  alert_threshold: number
  is_enabled: boolean
  created_at: string
  updated_at?: string

  // 关联数据
  category?: {
    id: number
    name: string
    icon?: string
    color?: string
  }
}

export interface BudgetCreate {
  category_id?: number
  amount: number
  period_type: PeriodType
  year: number
  month?: number
  alert_threshold?: number
}

export interface BudgetUpdate {
  category_id?: number
  amount?: number
  period_type?: PeriodType
  year?: number
  month?: number
  alert_threshold?: number
  is_enabled?: boolean
}

export interface BudgetUsage {
  budget_id: number
  category_name?: string
  budget_amount: number
  used_amount: number
  remaining_amount: number
  usage_percentage: number
  is_over_budget: boolean
  days_remaining?: number
  daily_budget?: number
}

export interface BudgetAlert {
  budget_id: number
  category_name?: string
  alert_type: 'warning' | 'danger' | 'exceeded'
  message: string
  usage_percentage: number
  used_amount: number
  budget_amount: number
}