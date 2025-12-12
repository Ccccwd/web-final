export enum TransactionType {
  INCOME = 'income',
  EXPENSE = 'expense',
  TRANSFER = 'transfer'
}

export interface Category {
  id: number
  name: string
  type: TransactionType
  icon?: string
  color?: string
  parent_id?: number
  sort_order: number
  is_system: boolean
  created_at: string
  children?: Category[]
}

export enum AccountType {
  CASH = 'cash',
  BANK = 'bank',
  WECHAT = 'wechat',
  ALIPAY = 'alipay',
  MEAL_CARD = 'meal_card',
  CREDIT_CARD = 'credit_card',
  OTHER = 'other'
}

export interface Account {
  id: number
  user_id: number
  name: string
  type: AccountType
  balance: number
  initial_balance: number
  icon?: string
  color?: string
  is_default: boolean
  is_enabled: boolean
  description?: string
  created_at: string
}

export interface Transaction {
  id: number
  user_id: number
  type: TransactionType
  amount: number
  category_id: number
  account_id: number
  to_account_id?: number
  transaction_date: string
  remark?: string
  images?: string[]
  tags?: string
  location?: string
  created_at: string
  updated_at?: string

  // 关联数据
  category?: Category
  account?: Account
  to_account?: Account
}

export interface TransactionCreate {
  type: TransactionType
  amount: number
  category_id: number
  account_id: number
  to_account_id?: number
  transaction_date: string
  remark?: string
  images?: string[]
  tags?: string
  location?: string
}

export interface TransactionUpdate {
  type?: TransactionType
  amount?: number
  category_id?: number
  account_id?: number
  to_account_id?: number
  transaction_date?: string
  remark?: string
  images?: string[]
  tags?: string
  location?: string
}

export interface TransactionFilter {
  start_date?: string
  end_date?: string
  type?: TransactionType
  category_ids?: number[]
  account_ids?: number[]
  min_amount?: number
  max_amount?: number
  keyword?: string
  page?: number
  page_size?: number
}

export interface TransactionSummary {
  income: number
  expense: number
  balance: number
  income_count: number
  expense_count: number
}