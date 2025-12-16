import request from '@/utils/request'
import type { User, LoginData, RegisterData } from '@/types/user'

/**
 * 用户登录
 */
export function login(data: LoginData) {
  return request.post<{
    token: string
    user: User
  }>('/auth/login', data)
}

/**
 * 用户注册
 */
export function register(data: RegisterData) {
  return request.post<{
    token: string
    user: User
  }>('/auth/register', data)
}

/**
 * 用户登出
 */
export function logout() {
  return request.post<{ message: string }>('/auth/logout')
}

/**
 * 获取用户信息
 */
export function getUserInfo() {
  return request.get<{ data: User }>('/auth/me')
}

/**
 * 刷新token
 */
export function refreshToken() {
  return request.post<{
    token: string
  }>('/auth/refresh')
}

/**
 * 修改密码
 */
export function changePassword(data: {
  old_password: string
  new_password: string
}) {
  return request.post<{ message: string }>('/auth/change-password', data)
}

/**
 * 忘记密码
 */
export function forgotPassword(data: {
  email: string
}) {
  return request.post<{ message: string }>('/auth/forgot-password', data)
}

/**
 * 重置密码
 */
export function resetPassword(data: {
  token: string
  new_password: string
}) {
  return request.post<{ message: string }>('/auth/reset-password', data)
}