import request from '@/utils/request'

export interface Reminder {
  id: number
  user_id: number
  type: 'daily' | 'budget' | 'recurring' | 'report'
  title?: string
  content?: string
  remind_time?: string
  remind_day?: number
  category_id?: number
  amount?: number
  is_enabled: boolean
  last_reminded_at?: string
  created_at: string
  updated_at: string
  category_name?: string
}

/**
 * 获取提醒列表
 */
export function getReminders(params?: {
  type?: string
  is_enabled?: boolean
}) {
  return request.get<{ data: { reminders: Reminder[]; total: number } }>('/reminders', { params })
}

/**
 * 获取提醒详情
 */
export function getReminder(reminderId: number) {
  return request.get<{ data: Reminder }>(`/reminders/${reminderId}`)
}

/**
 * 创建提醒
 */
export function createReminder(data: {
  type: 'daily' | 'budget' | 'recurring' | 'report'
  title?: string
  content?: string
  remind_time?: string
  remind_day?: number
  category_id?: number
  amount?: number
  is_enabled?: boolean
}) {
  return request.post<{ data: Reminder }>('/reminders', data)
}

/**
 * 更新提醒
 */
export function updateReminder(reminderId: number, data: {
  title?: string
  content?: string
  remind_time?: string
  remind_day?: number
  category_id?: number
  amount?: number
  is_enabled?: boolean
}) {
  return request.put<{ data: Reminder }>(`/reminders/${reminderId}`, data)
}

/**
 * 删除提醒
 */
export function deleteReminder(reminderId: number) {
  return request.delete<{ message: string }>(`/reminders/${reminderId}`)
}

/**
 * 获取提醒统计
 */
export function getReminderStatistics() {
  return request.get<{ data: any }>('/reminders/statistics/summary')
}

/**
 * 检查每日提醒
 */
export function checkDailyReminder() {
  return request.post<{ data: any }>('/reminders/check-daily-reminder')
}

/**
 * 处理到期提醒（系统接口）
 */
export function processDueReminders() {
  return request.post<{ data: any }>('/reminders/system/process-due-reminders')
}

/**
 * 获取提醒模板
 */
export function getTemplate(templateType: 'daily' | 'budget' | 'monthly-report') {
  const endpoint = templateType === 'monthly-report' ? '/reminders/templates/monthly-report' : `/reminders/templates/${templateType}-reminder`
  return request.get<{ data: any }>(endpoint)
}

// 导出为reminderApi（与组件中使用的名称一致）
export const reminderApi = {
  getReminders,
  getReminder,
  createReminder,
  updateReminder,
  deleteReminder,
  getReminderStatistics,
  checkDailyReminder,
  processDueReminders,
  getTemplate
}