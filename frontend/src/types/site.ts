/**
 * 站点类型定义
 */
export interface Site {
  id: number
  name: string
  code: string
  longitude: number
  latitude: number
  altitude: number | null
  region: string | null
  description: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

/**
 * 创建站点请求
 */
export interface SiteCreate {
  name: string
  code: string
  longitude: number
  latitude: number
  altitude?: number
  region?: string
  description?: string
}

/**
 * 更新站点请求
 */
export interface SiteUpdate {
  name?: string
  longitude?: number
  latitude?: number
  altitude?: number
  region?: string
  description?: string
  is_active?: boolean
}

/**
 * 分页响应
 */
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

/**
 * API响应
 */
export interface ApiResponse<T> {
  code: number
  message: string
  data: T
  timestamp: string
}
