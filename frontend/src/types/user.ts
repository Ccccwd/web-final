export interface User {
  id: number
  username: string
  email: string
  phone?: string
  avatar?: string
  is_active: boolean
  role?: string
  created_at: string
  updated_at?: string
}

// API响应类型
export interface UserResponse {
  data: User
}

export interface UserCreate {
  username: string
  email: string
  password: string
  phone?: string
}

export interface UserLogin {
  username: string
  password: string
}

export interface LoginData {
  username: string
  password: string
}

export interface RegisterData {
  username: string
  email: string
  password: string
  confirm_password?: string
  phone?: string
}

export interface UserUpdate {
  username?: string
  email?: string
  phone?: string
  avatar?: string
}

export interface Token {
  access_token: string
  refresh_token: string
  token_type: string
  token?: string  // 别名，与 access_token 相同
  user?: User     // 登录/注册时返回的用户信息
}

export interface TokenData {
  sub?: string
  user_id?: number
  exp?: number
  type?: string
}