import dayjs from 'dayjs'

/**
 * 格式化金额显示
 */
export function formatAmount(amount: number | string, currency = '¥'): string {
  const num = typeof amount === 'string' ? parseFloat(amount) : amount
  if (isNaN(num)) return `${currency}0.00`
  return `${currency}${num.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',')}`
}

/**
 * 格式化日期时间
 */
export function formatDateTime(
  datetime: string | Date,
  format = 'YYYY-MM-DD HH:mm:ss'
): string {
  return dayjs(datetime).format(format)
}

/**
 * 格式化日期
 */
export function formatDate(date: string | Date, format = 'YYYY-MM-DD'): string {
  return dayjs(date).format(format)
}

/**
 * 格式化时间
 */
export function formatTime(time: string | Date, format = 'HH:mm:ss'): string {
  return dayjs(time).format(format)
}

/**
 * 相对时间显示
 */
export function formatRelativeTime(datetime: string | Date): string {
  const now = dayjs()
  const date = dayjs(datetime)
  const diffMinutes = now.diff(date, 'minute')
  const diffHours = now.diff(date, 'hour')
  const diffDays = now.diff(date, 'day')

  if (diffMinutes < 1) {
    return '刚刚'
  } else if (diffMinutes < 60) {
    return `${diffMinutes}分钟前`
  } else if (diffHours < 24) {
    return `${diffHours}小时前`
  } else if (diffDays < 7) {
    return `${diffDays}天前`
  } else {
    return date.format('MM-DD')
  }
}

/**
 * 格式化百分比
 */
export function formatPercentage(value: number, decimals = 1): string {
  return `${value.toFixed(decimals)}%`
}

/**
 * 格式化文件大小
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'

  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

/**
 * 格式化手机号码
 */
export function formatPhoneNumber(phone: string): string {
  if (!phone) return ''
  const cleaned = phone.replace(/\D/g, '')
  if (cleaned.length !== 11) return phone

  return `${cleaned.slice(0, 3)} ${cleaned.slice(3, 7)} ${cleaned.slice(7)}`
}

/**
 * 格式化银行卡号（隐藏中间部分）
 */
export function formatBankCard(cardNumber: string): string {
  if (!cardNumber) return ''
  const cleaned = cardNumber.replace(/\D/g, '')
  if (cleaned.length < 8) return cardNumber

  return `${cleaned.slice(0, 4)} **** **** ${cleaned.slice(-4)}`
}

/**
 * 格式化数字，添加千分位分隔符
 */
export function formatNumber(num: number | string, decimals = 0): string {
  const value = typeof num === 'string' ? parseFloat(num) : num
  if (isNaN(value)) return '0'

  return value.toLocaleString('zh-CN', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  })
}

/**
 * 截断文本并添加省略号
 */
export function truncateText(text: string, maxLength: number): string {
  if (!text) return ''
  if (text.length <= maxLength) return text

  return text.slice(0, maxLength) + '...'
}

/**
 * 首字母大写
 */
export function capitalize(text: string): string {
  if (!text) return ''
  return text.charAt(0).toUpperCase() + text.slice(1).toLowerCase()
}

/**
 * 获取相对时间描述
 */
export function getTimeRangeDescription(startDate: string, endDate: string): string {
  const start = dayjs(startDate)
  const end = dayjs(endDate)
  const now = dayjs()

  if (start.isSame(now, 'day')) {
    return '今天'
  } else if (start.isSame(now.subtract(1, 'day'), 'day')) {
    return '昨天'
  } else if (start.isSame(now.add(1, 'day'), 'day')) {
    return '明天'
  } else if (start.isSame(now, 'week')) {
    return '本周'
  } else if (start.isSame(now, 'month')) {
    return '本月'
  } else if (start.isSame(now, 'year')) {
    return '本年'
  } else {
    return start.format('YYYY年MM月DD日')
  }
}

/**
 * 获取交易类型的显示文本
 */
export function getTransactionTypeText(type: string): string {
  const typeMap: Record<string, string> = {
    income: '收入',
    expense: '支出',
    transfer: '转账'
  }
  return typeMap[type] || type
}

/**
 * 获取账户类型的显示文本
 */
export function getAccountTypeText(type: string): string {
  const typeMap: Record<string, string> = {
    cash: '现金',
    bank: '银行卡',
    wechat: '微信',
    alipay: '支付宝',
    meal_card: '饭卡',
    credit_card: '信用卡',
    other: '其他'
  }
  return typeMap[type] || type
}

/**
 * 获取预算周期类型的显示文本
 */
export function getPeriodTypeText(type: string): string {
  const typeMap: Record<string, string> = {
    monthly: '月度',
    yearly: '年度'
  }
  return typeMap[type] || type
}