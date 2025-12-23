/**
 * 验证邮箱格式
 */
export function validateEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

/**
 * 验证手机号格式（中国大陆）
 */
export function validatePhone(phone: string): boolean {
  const phoneRegex = /^1[3-9]\d{9}$/
  return phoneRegex.test(phone)
}

/**
 * 验证密码强度
 * 至少8位，包含字母和数字
 */
export function validatePassword(password: string): {
  isValid: boolean
  message?: string
} {
  if (password.length < 8) {
    return {
      isValid: false,
      message: '密码长度至少8位'
    }
  }

  if (!/[a-zA-Z]/.test(password)) {
    return {
      isValid: false,
      message: '密码必须包含字母'
    }
  }

  if (!/\d/.test(password)) {
    return {
      isValid: false,
      message: '密码必须包含数字'
    }
  }

  return { isValid: true }
}

/**
 * 验证金额格式
 */
export function validateAmount(amount: string): {
  isValid: boolean
  amount?: number
  message?: string
} {
  // 检查是否为数字
  if (!/^\d*\.?\d+$/.test(amount)) {
    return {
      isValid: false,
      message: '请输入有效的金额'
    }
  }

  const numAmount = parseFloat(amount)

  // 检查金额是否为0
  if (numAmount === 0) {
    return {
      isValid: false,
      message: '金额不能为0'
    }
  }

  // 检查金额是否过大（超过1亿）
  if (numAmount > 100000000) {
    return {
      isValid: false,
      message: '金额不能超过1亿元'
    }
  }

  // 检查小数位数（最多2位）
  if (amount.includes('.') && amount.split('.')[1].length > 2) {
    return {
      isValid: false,
      message: '金额最多2位小数'
    }
  }

  return {
    isValid: true,
    amount: numAmount
  }
}

/**
 * 验证用户名格式
 * 4-20位，只能包含字母、数字、下划线
 */
export function validateUsername(username: string): {
  isValid: boolean
  message?: string
} {
  if (username.length < 4 || username.length > 20) {
    return {
      isValid: false,
      message: '用户名长度为4-20位'
    }
  }

  if (!/^[a-zA-Z0-9_]+$/.test(username)) {
    return {
      isValid: false,
      message: '用户名只能包含字母、数字、下划线'
    }
  }

  if (!/^[a-zA-Z]/.test(username)) {
    return {
      isValid: false,
      message: '用户名必须以字母开头'
    }
  }

  return { isValid: true }
}

/**
 * 验证日期格式
 */
export function validateDate(date: string): {
  isValid: boolean
  message?: string
} {
  const dateObj = new Date(date)

  if (isNaN(dateObj.getTime())) {
    return {
      isValid: false,
      message: '日期格式无效'
    }
  }

  // 检查日期是否在合理范围内（1900-2100年）
  const year = dateObj.getFullYear()
  if (year < 1900 || year > 2100) {
    return {
      isValid: false,
      message: '日期超出合理范围'
    }
  }

  // 检查日期是否是未来的日期（交易日期不能是未来）
  const now = new Date()
  if (dateObj > now) {
    return {
      isValid: false,
      message: '交易日期不能是未来日期'
    }
  }

  return { isValid: true }
}

/**
 * 验证时间格式
 */
export function validateTime(time: string): {
  isValid: boolean
  message?: string
} {
  const timeRegex = /^([01]?[0-9]|2[0-3]):[0-5][0-9]$/

  if (!timeRegex.test(time)) {
    return {
      isValid: false,
      message: '时间格式无效，请使用HH:MM格式'
    }
  }

  return { isValid: true }
}

/**
 * 验证URL格式
 */
export function validateUrl(url: string): boolean {
  try {
    new URL(url)
    return true
  } catch {
    return false
  }
}

/**
 * 验证IDCard格式（中国大陆）
 */
export function validateIDCard(idCard: string): {
  isValid: boolean
  message?: string
} {
  // 18位身份证正则
  const idCardRegex = /^[1-9]\d{5}(18|19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]$/

  if (!idCardRegex.test(idCard)) {
    return {
      isValid: false,
      message: '身份证格式无效'
    }
  }

  // 简单的校验码验证（这里可以添加更复杂的校验算法）
  const weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
  const codes = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']

  let sum = 0
  for (let i = 0; i < 17; i++) {
    sum += parseInt(idCard[i]) * weights[i]
  }

  const checkCode = codes[sum % 11]
  if (idCard[17].toUpperCase() !== checkCode) {
    return {
      isValid: false,
      message: '身份证校验码错误'
    }
  }

  return { isValid: true }
}

/**
 * 通用表单验证器
 */
export class FormValidator {
  private errors: Array<{ field: string; message: string }> = []

  addError(field: string, message: string): void {
    this.errors.push({ field, message })
  }

  validateField(value: any, rules: Array<(value: any) => { isValid: boolean; message?: string }>): this {
    for (const rule of rules) {
      const result = rule(value)
      if (!result.isValid && result.message) {
        // 从错误消息中提取字段名或使用默认值
        this.addError('field', result.message)
        break
      }
    }
    return this
  }

  validateEmail(email: string, field = 'email'): this {
    if (!email) {
      this.addError(field, '请输入邮箱地址')
    } else if (!validateEmail(email)) {
      this.addError(field, '邮箱格式不正确')
    }
    return this
  }

  validatePhone(phone: string, field = 'phone'): this {
    if (phone && !validatePhone(phone)) {
      this.addError(field, '手机号格式不正确')
    }
    return this
  }

  validatePassword(password: string, field = 'password'): this {
    if (!password) {
      this.addError(field, '请输入密码')
    } else {
      const result = validatePassword(password)
      if (!result.isValid && result.message) {
        this.addError(field, result.message)
      }
    }
    return this
  }

  validateUsername(username: string, field = 'username'): this {
    if (!username) {
      this.addError(field, '请输入用户名')
    } else {
      const result = validateUsername(username)
      if (!result.isValid && result.message) {
        this.addError(field, result.message)
      }
    }
    return this
  }

  validateAmount(amount: string, field = 'amount'): this {
    if (!amount) {
      this.addError(field, '请输入金额')
    } else {
      const result = validateAmount(amount)
      if (!result.isValid && result.message) {
        this.addError(field, result.message)
      }
    }
    return this
  }

  getErrors(): Array<{ field: string; message: string }> {
    return this.errors
  }

  hasErrors(): boolean {
    return this.errors.length > 0
  }

  clear(): void {
    this.errors = []
  }
}