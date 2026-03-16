/**
 * API服务模块
 * 包含所有后端API的调用方法
 */
import api, { type ApiResponse } from './index'

// ==================== 类型定义 ====================

export interface User {
  id: number
  username: string
  email: string
  full_name: string
  is_active: boolean
  is_superuser: boolean
  created_at: string
  last_login?: string
}

export interface Token {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface Site {
  id: number
  station_id: string
  station_name: string
  longitude: number
  latitude: number
  address?: string
  region?: string
  station_type?: string
  retry_count?: number
  max_retries?: number
  status?: 'active' | 'disabled' | 'error'
  last_sync_time?: string
  last_sync_status?: 'success' | 'failed' | 'pending'
  last_error_message?: string
  created_at: string
  updated_at: string
  remark?: string
}

export interface RadarData {
  id: number
  site_id: number
  observation_time: string
  dbz_value: number
  dbz_category: string
  rgb_value: string
  cloud_impact_factor: number
  pixel_x?: number
  pixel_y?: number
  longitude?: number
  latitude?: number
  created_at: string
}

export interface Prediction {
  id: number
  site_id: number
  model_type: string
  prediction_time: string
  predicted_dbz: number
  confidence_lower: number
  confidence_upper: number
  model_version: string
  prediction_horizon: number
  prediction_accuracy: number
  created_at: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

// ==================== 认证API ====================

export const authApi = {
  /**
   * 用户登录
   */
  login: (username: string, password: string) => {
    return api.post<ApiResponse<Token>>('/auth/login', null, {
      params: {
        username,
        password
      }
    })
  },

  /**
   * 用户注册
   */
  register: (data: {
    username: string
    email: string
    password: string
    full_name: string
  }) => {
    return api.post<ApiResponse<User>>('/auth/register', data)
  },

  /**
   * 用户登出
   */
  logout: () => {
    return api.post<ApiResponse>('/auth/logout')
  }
}

// ==================== 站点管理API ====================

export const siteApi = {
  /**
   * 获取站点列表
   */
  getList: (params?: { page?: number; page_size?: number; station_name?: string; region?: string; status?: string }) => {
    return api.get<ApiResponse<PaginatedResponse<Site>>>('/weather-stations/', { params })
  },

  /**
   * 获取站点详情
   */
  getDetail: (id: number) => {
    return api.get<ApiResponse<Site>>(`/weather-stations/${id}`)
  },

  /**
   * 创建站点
   */
  create: (data: Partial<Site>) => {
    return api.post<ApiResponse<Site>>('/weather-stations/', data)
  },

  /**
   * 更新站点
   */
  update: (id: number, data: Partial<Site>) => {
    return api.put<ApiResponse<Site>>(`/weather-stations/${id}`, data)
  },

  /**
   * 删除站点
   */
  delete: (id: number) => {
    return api.delete<ApiResponse>(`/weather-stations/${id}`)
  }
}

// ==================== 数据查询API ====================

export const dataApi = {
  /**
   * 查询雷达数据
   */
  query: (params: {
    site_id?: number
    start_time?: string
    end_time?: string
    min_dbz?: number
    max_dbz?: number
    page?: number
    page_size?: number
  }) => {
    return api.get<ApiResponse<PaginatedResponse<RadarData>>>('/data/query', { params })
  },

  /**
   * 获取统计信息
   */
  getStatistics: (params: { site_id?: number; days?: number }) => {
    return api.get<ApiResponse>('/data/statistics', { params })
  }
}

// ==================== 预测管理API ====================

export const predictionApi = {
  /**
   * 获取预测方法列表
   */
  getMethods: () => {
    return api.get<ApiResponse<{ methods: any[]; total: number }>>('/predictions/methods')
  },

  /**
   * 创建预测任务
   */
  create: (params: { site_id: number; model_type?: string; hours?: number }) => {
    return api.post<ApiResponse<Prediction>>('/predictions/predict', null, { params })
  },

  /**
   * 获取最新预测
   */
  getLatest: (siteId: number, modelType?: string) => {
    return api.get<ApiResponse<Prediction>>(`/predictions/site/${siteId}/latest`, {
      params: modelType ? { model_type: modelType } : undefined
    })
  }
}

// ==================== 下载管理API ====================

export const downloadApi = {
  /**
   * 获取下载状态
   */
  getStatus: () => {
    return api.get<ApiResponse<any>>('/downloads/status')
  },

  /**
   * 手动触发下载
   */
  trigger: () => {
    return api.post<ApiResponse<any>>('/downloads/trigger')
  }
}

// ==================== 系统监控API ====================

export const systemApi = {
  /**
   * 健康检查
   */
  health: () => {
    return api.get<ApiResponse<{ status: string }>>('/system/health')
  },

  /**
   * 获取系统信息
   */
  getInfo: () => {
    return api.get<ApiResponse<any>>('/system/info')
  },

  /**
   * 获取系统状态
   */
  getStatus: () => {
    return api.get<ApiResponse<any>>('/system/status')
  }
}

// ==================== 图片管理API ====================

export interface RadarImage {
  id: number
  filename: string
  original_filename: string | null
  original_time_str: string | null
  file_path: string
  download_url: string | null
  file_size: number | null
  observation_time: string
  download_time: string | null
  download_status: string
  retry_count: number
  md5_hash: string | null
  error_message: string | null
  is_processed: boolean
  created_at: string
}

export const imageApi = {
  /**
   * 获取图片列表
   */
  getList: (params: {
    page?: number
    page_size?: number
    sort_by?: string
    sort_order?: string
    status?: string
  }) => {
    return api.get<ApiResponse<{
      items: RadarImage[]
      total: number
      page: number
      page_size: number
      total_pages: number
    }>>('/images/list', { params })
  },

  /**
   * 获取图片详情
   */
  getDetail: (id: number) => {
    return api.get<ApiResponse<RadarImage>>(`/images/${id}`)
  },

  /**
   * 获取图片预览URL
   */
  getPreviewUrl: (id: number) => {
    return `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'}/images/${id}/preview`
  },

  /**
   * 获取统计信息
   */
  getStatistics: () => {
    return api.get<ApiResponse<{
      total_images: number
      success_count: number
      failed_count: number
      pending_count: number
      success_rate: number
      total_size_bytes: number
      total_size_mb: number
      latest_observation_time: string | null
      earliest_observation_time: string | null
    }>>('/images/stats/summary')
  },

  /**
   * 删除图片
   */
  delete: (id: number) => {
    return api.delete<ApiResponse<{ deleted_id: number }>>(`/images/${id}`)
  }
}

// ==================== 坐标校准API ====================

export interface ControlPointData {
  id: number
  pixel_x: number
  pixel_y: number
  longitude: number
  latitude: number
  name: string
  created_at: string
}

export const calibrationApi = {
  /**
   * 添加控制点
   */
  addControlPoint: (data: {
    pixel_x: number
    pixel_y: number
    longitude: number
    latitude: number
    name?: string
  }) => {
    return api.post<ApiResponse<ControlPointData>>('/calibration/control-points', data)
  },

  /**
   * 获取所有控制点
   */
  getControlPoints: () => {
    return api.get<ApiResponse<{ items: ControlPointData[]; total: number }>>('/calibration/control-points')
  },

  /**
   * 删除控制点
   */
  deleteControlPoint: (id: number) => {
    return api.delete<ApiResponse>(`/calibration/control-points/${id}`)
  },

  /**
   * 执行校准
   */
  calibrate: (controlPointIds?: number[]) => {
    return api.post<ApiResponse<{
      success: boolean
      affine_lon: number[]
      affine_lat: number[]
      errors: Array<{ id: number; name: string; error_lon: number; error_lat: number }>
      control_points_used: number
    }>>('/calibration/calibrate', { control_point_ids: controlPointIds })
  },

  /**
   * 获取当前激活的校准参数
   */
  getActiveCalibration: () => {
    return api.get<ApiResponse<{
      id: number
      affine_lon: number[]
      affine_lat: number[]
      is_active: boolean
      created_at: string
    } | null>>('/calibration/calibration/active')
  },

  /**
   * 停用校准参数
   */
  deactivateCalibration: () => {
    return api.delete<ApiResponse>('/calibration/calibration/active')
  }
}
