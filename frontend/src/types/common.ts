export interface APIResponse<T = any> {
  code: number
  message: string
  data?: T
  success: boolean
}

export interface PaginationInfo {
  page: number
  pageSize: number
  total: number
  totalPages: number
}

export interface PaginatedResponse<T = any> extends APIResponse<T[]> {
  pagination: PaginationInfo
}

export interface ErrorResponse extends APIResponse {
  success: false
  error?: {
    field?: string
    message?: string
    type?: string
  }[]
}

export interface BaseEntity {
  id: number
  created_at: string
  updated_at?: string
}

export interface SelectOption {
  label: string
  value: string | number
  disabled?: boolean
  icon?: string
  color?: string
}

export interface DateRange {
  start: string
  end: string
}

export enum SortOrder {
  ASC = 'asc',
  DESC = 'desc'
}

export interface SortOption {
  field: string
  order: SortOrder
}

export interface FilterOptions {
  search?: string
  page?: number
  pageSize?: number
  sortBy?: SortOption
  filters?: Record<string, any>
}

export interface UploadFile {
  name: string
  url: string
  size: number
  type: string
}

export interface FormFieldError {
  field: string
  message: string
}

export interface ValidationResult {
  isValid: boolean
  errors: FormFieldError[]
}

// 图表相关配置
export interface ChartBaseConfig {
  width?: string | number
  height?: string | number
  responsive?: boolean
  maintainAspectRatio?: boolean
}

export interface PieChartConfig extends ChartBaseConfig {
  legend?: {
    show?: boolean
    position?: 'top' | 'bottom' | 'left' | 'right'
  }
}

export interface LineChartConfig extends ChartBaseConfig {
  smooth?: boolean
  showArea?: boolean
  showSymbol?: boolean
  xAxis?: {
    type?: 'category' | 'value' | 'time' | 'log'
    boundaryGap?: boolean | string | number
  }
  yAxis?: {
    type?: 'value' | 'category' | 'time' | 'log'
    splitLine?: {
      show?: boolean
    }
  }
}

export interface BarChartConfig extends ChartBaseConfig {
  horizontal?: boolean
  showDataLabel?: boolean
  xAxis?: {
    type?: 'category' | 'value' | 'time' | 'log'
    boundaryGap?: boolean | string | number
  }
  yAxis?: {
    type?: 'value' | 'category' | 'time' | 'log'
    splitLine?: {
      show?: boolean
    }
  }
}

// ECharts 配置类型
export type ECOption = any