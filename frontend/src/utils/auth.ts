import { Token } from '@/types'

const TOKEN_KEY = 'finance_token'
const REFRESH_TOKEN_KEY = 'finance_refresh_token'
const USER_KEY = 'finance_user'

export class TokenManager {
  /**
   * 保存token到localStorage
   */
  static setToken(token: Token): void {
    localStorage.setItem(TOKEN_KEY, token.access_token)
    localStorage.setItem(REFRESH_TOKEN_KEY, token.refresh_token)
  }

  /**
   * 获取访问token
   */
  static getAccessToken(): string | null {
    return localStorage.getItem(TOKEN_KEY)
  }

  /**
   * 获取刷新token
   */
  static getRefreshToken(): string | null {
    return localStorage.getItem(REFRESH_TOKEN_KEY)
  }

  /**
   * 清除所有token
   */
  static clearTokens(): void {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  }

  /**
   * 检查是否已登录
   */
  static isLoggedIn(): boolean {
    return !!this.getAccessToken()
  }

  /**
   * 解析JWT token获取用户信息
   */
  static parseToken(token: string): any {
    try {
      const base64Url = token.split('.')[1]
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map(function (c) {
            return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)
          })
          .join('')
      )
      return JSON.parse(jsonPayload)
    } catch (error) {
      console.error('Token解析失败:', error)
      return null
    }
  }

  /**
   * 检查token是否过期
   */
  static isTokenExpired(token: string): boolean {
    const payload = this.parseToken(token)
    if (!payload || !payload.exp) {
      return true
    }
    const currentTime = Math.floor(Date.now() / 1000)
    return payload.exp < currentTime
  }

  /**
   * 检查当前访问token是否即将过期（5分钟内）
   */
  static isTokenExpiringSoon(): boolean {
    const token = this.getAccessToken()
    if (!token) return true

    const payload = this.parseToken(token)
    if (!payload || !payload.exp) return true

    const currentTime = Math.floor(Date.now() / 1000)
    const fiveMinutes = 5 * 60
    return payload.exp - currentTime < fiveMinutes
  }

  /**
   * 保存用户信息
   */
  static setUser(user: any): void {
    localStorage.setItem(USER_KEY, JSON.stringify(user))
  }

  /**
   * 获取用户信息
   */
  static getUser(): any | null {
    const userStr = localStorage.getItem(USER_KEY)
    try {
      return userStr ? JSON.parse(userStr) : null
    } catch (error) {
      console.error('用户信息解析失败:', error)
      return null
    }
  }

  /**
   * 从token中获取用户ID
   */
  static getUserId(): number | null {
    const token = this.getAccessToken()
    if (!token) return null

    const payload = this.parseToken(token)
    return payload?.user_id || null
  }

  /**
   * 从token中获取用户名
   */
  static getUsername(): string | null {
    const token = this.getAccessToken()
    if (!token) return null

    const payload = this.parseToken(token)
    return payload?.sub || null
  }
}

export default TokenManager