import { httpGet, httpPost, httpPut, httpDelete } from './request'
import type { LoginRequest, LoginResponse, User } from '../types/user'
import type {
  Site,
  SiteCreate,
  SiteUpdate,
  PaginatedResponse,
  ApiResponse
} from '../types/site'

/**
 * 用户认证API
 */
export const authApi = {
  /**
   * 用户登录
   */
  login(data: LoginRequest) {
    return httpPost<ApiResponse<LoginResponse>>('/auth/login', data)
  },

  /**
   * 用户登出
   */
  logout() {
    return httpPost<ApiResponse>('/auth/logout')
  }
}

/**
 * 站点管理API
 */
export const siteApi = {
  /**
   * 获取站点列表
   */
  getSites(params?: {
    page?: number
    page_size?: number
    name?: string
    region?: string
    is_active?: boolean
  }) {
    return httpGet<ApiResponse<PaginatedResponse<Site>>>('/sites', { params })
  },

  /**
   * 获取站点详情
   */
  getSiteDetail(id: number) {
    return httpGet<ApiResponse<Site>>(`/sites/${id}`)
  },

  /**
   * 创建站点
   */
  createSite(data: SiteCreate) {
    return httpPost<ApiResponse<Site>>('/sites', data)
  },

  /**
   * 更新站点
   */
  updateSite(id: number, data: SiteUpdate) {
    return httpPut<ApiResponse<Site>>(`/sites/${id}`, data)
  },

  /**
   * 删除站点
   */
  deleteSite(id: number) {
    return httpDelete<ApiResponse>(`/sites/${id}`)
  }
}

/**
 * 系统监控API
 */
export const systemApi = {
  /**
   * 获取系统状态
   */
  getStatus() {
    return httpGet<ApiResponse<any>>('/system/status')
  },

  /**
   * 健康检查
   */
  healthCheck() {
    return httpGet<ApiResponse<any>>('/system/health')
  }
}

/**
 * 下载管理API
 */
export const downloadApi = {
  /**
   * 获取下载状态
   */
  getDownloadStatus() {
    return httpGet<ApiResponse<any>>('/downloads/status')
  },

  /**
   * 获取下载历史
   */
  getDownloadHistory(params?: { page?: number; page_size?: number; status?: string }) {
    return httpGet<ApiResponse<PaginatedResponse<any>>>('/downloads/history', { params })
  },

  /**
   * 手动触发下载
   */
  triggerDownload(count: number = 1) {
    return httpPost<ApiResponse<any>>(`/downloads/trigger?count=${count}`)
  },

  /**
   * 重试失败任务
   */
  retryFailed(maxRetryCount: number = 3) {
    return httpPost<ApiResponse<any>>(`/downloads/retry?max_retry_count=${maxRetryCount}`)
  }
}

/**
 * 数据查询API
 */
export const dataApi = {
  /**
   * 查询站点雷达数据
   */
  queryData(params?: {
    page?: number
    page_size?: number
    site_id?: string
    start_time?: string
    end_time?: string
    data_source?: string
    dbz_min?: number
    dbz_max?: number
  }) {
    return httpGet<ApiResponse<PaginatedResponse<any>>>('/data/query', { params })
  },

  /**
   * 导出数据为CSV
   */
  exportData(params?: {
    site_id?: string
    start_time?: string
    end_time?: string
    data_source?: string
    dbz_min?: number
    dbz_max?: number
  }) {
    return httpGet<Blob>('/data/export', {
      params,
      responseType: 'blob'
    })
  },

  /**
   * 获取数据统计
   */
  getStatistics(params?: {
    site_id?: number
    start_time?: string
    end_time?: string
  }) {
    return httpGet<ApiResponse<any>>('/data/statistics', { params })
  }
}

/**
 * 预测管理API
 */
export const predictionApi = {
  /**
   * 获取可用的预测方法
   */
  getMethods() {
    return httpGet<ApiResponse<any>>('/predictions/methods')
  },

  /**
   * 获取站点最新预测
   */
  getLatestPrediction(siteId: number) {
    return httpGet<ApiResponse<any>>(`/predictions/site/${siteId}/latest`)
  },

  /**
   * 触发预测任务
   */
  createPrediction(siteId: number, data: { method: string; prediction_horizon_minutes: number }) {
    return httpPost<ApiResponse<any>>(`/predictions/site/${siteId}/predict`, data)
  },

  /**
   * 获取预测历史
   */
  getPredictionHistory(
    siteId: number,
    params?: {
      page?: number
      page_size?: number
      start_time?: string
      end_time?: string
      model_type?: string
    }
  ) {
    return httpGet<ApiResponse<PaginatedResponse<any>>>(`/predictions/site/${siteId}/history`, {
      params
    })
  }
}
