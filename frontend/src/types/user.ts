export interface User {
  id: number
  username: string
  email: string
  phone?: string
  avatar?: string
  is_active: boolean
  created_at: string
  updated_at?: string
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
}

export interface TokenData {
  sub?: string
  user_id?: number
  exp?: number
  type?: string
}