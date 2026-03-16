/**
 * 数据查询相关类型定义
 */

export interface SiteRadarData {
  id: number
  site_id: number
  observation_time: string
  dbz_value: number
  dbz_category: string
  cloud_impact_factor: number
  rgb_value: string | null
  data_quality: 'excellent' | 'good' | 'fair' | 'poor'
  data_source: 'actual' | 'predicted'
  created_at: string
  updated_at: string
}

export interface DataQueryParams {
  page?: number
  page_size?: number
  site_id?: string
  start_time?: string
  end_time?: string
  data_source?: string
  dbz_min?: number
  dbz_max?: number
}

export interface DataStatistics {
  total_records: number
  average_dbz: number
  max_dbz: number
  min_dbz: number
  data_sources: {
    actual: number
    predicted: number
  }
  quality_distribution: {
    excellent: number
    good: number
    fair: number
    poor: number
  }
}

export interface PredictionResult {
  id: number
  site_id: number
  prediction_time: string
  predicted_dbz: number
  confidence_lower?: number
  confidence_upper?: number
  model_type: 'optical_flow' | 'prophet' | 'ensemble'
  model_version: string
  prediction_horizon: number
  prediction_accuracy?: number
  created_at: string
}

export interface PredictionMethod {
  name: string
  display_name: string
  description: string
  min_data_requirement: string
  prediction_range: string
  accuracy: string
}
