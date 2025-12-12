export enum ReminderType {
  DAILY = 'daily',
  BUDGET = 'budget',
  RECURRING = 'recurring',
  REPORT = 'report'
}

export interface Reminder {
  id: number
  user_id: number
  type: ReminderType
  title?: string
  content?: string
  remind_time?: string
  remind_day?: number
  category_id?: number
  amount?: number
  is_enabled: boolean
  last_reminded_at?: string
  created_at: string
  updated_at?: string

  // 关联数据
  category?: {
    id: number
    name: string
    icon?: string
  }
}

export interface ReminderCreate {
  type: ReminderType
  title?: string
  content?: string
  remind_time?: string
  remind_day?: number
  category_id?: number
  amount?: number
  is_enabled?: boolean
}

export interface ReminderUpdate {
  type?: ReminderType
  title?: string
  content?: string
  remind_time?: string
  remind_day?: number
  category_id?: number
  amount?: number
  is_enabled?: boolean
}

export interface ReminderNotification {
  id: number
  type: ReminderType
  title: string
  content: string
  created_at: string
  is_read: boolean
}

export interface BudgetAlert {
  reminder_id: number
  category_name?: string
  budget_amount: number
  used_amount: number
  percentage: number
  alert_level: 'warning' | 'danger' | 'exceeded'
  message: string
}