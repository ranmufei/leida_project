/**
 * 用户类型定义
 */
export interface User {
  id: number
  username: string
  email: string
  full_name: string | null
  is_active: boolean
  is_superuser: boolean
  created_at: string
  last_login: string | null
}

/**
 * 登录请求
 */
export interface LoginRequest {
  username: string
  password: string
}

/**
 * 登录响应
 */
export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

/**
 * Token数据
 */
export interface TokenData {
  sub?: string
  user_id?: number
  exp?: number
}
