// Vue.js前端配置文件

export default {
  // 应用配置
  appName: '气象雷达数据管理与预测平台',
  appVersion: '1.0.0',
  appDescription: '雷达数据自动化采集、处理、管理和预测平台',

  // API配置
  apiBaseUrl: process.env.VUE_APP_API_BASE_URL || 'http://localhost:8000/api/v1',
  apiTimeout: 30000,

  // WebSocket配置
  wsBaseUrl: process.env.VUE_APP_WS_BASE_URL || 'ws://localhost:8000/api/v1/ws',
  wsReconnectInterval: 5000,
  wsMaxReconnectAttempts: 10,

  // 认证配置
  tokenKey: 'access_token',
  refreshTokenKey: 'refresh_token',
  tokenRefreshThreshold: 300, // 提前5分钟刷新token

  // 路由配置
  routes: {
    home: '/',
    login: '/login',
    sites: '/sites',
    siteDetail: '/sites/:id',
    data: '/data',
    prediction: '/prediction',
    system: '/system',
    notFound: '/404'
  },

  // 分页配置
  pagination: {
    defaultPageSize: 20,
    pageSizes: [10, 20, 50, 100],
    showSizeChanger: true,
    showQuickJumper: true
  },

  // 图表配置
  charts: {
    theme: 'default',
    animation: true,
    colors: [
      '#5470c6', '#91cc75', '#fac858', '#ee6666',
      '#73c0de', '#3ba272', '#fc8452', '#9a60b4'
    ]
  },

  // 数据查询配置
  dataQuery: {
    maxDateRange: 90, // 最大查询天数
    defaultDateRange: 7, // 默认查询天数
    maxRecords: 10000 // 单次最大查询记录数
  },

  // 文件上传配置
  upload: {
    maxSize: 10 * 1024 * 1024, // 10MB
    allowedTypes: ['.csv', '.xlsx', '.xls'],
    allowedMimeTypes: [
      'text/csv',
      'application/vnd.ms-excel',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    ]
  },

  // 缓存配置
  cache: {
    enabled: true,
    ttl: 300, // 5分钟
    maxSize: 100 // 最大缓存条目数
  },

  // UI配置
  ui: {
    layout: 'side', // 'side' or 'top'
    theme: 'light', // 'light' or 'dark'
    locale: 'zh-CN',
    pageSize: 20,
    tableBorder: false,
    tableStripe: true
  },

  // 性能配置
  performance: {
    enableVirtualScroll: true,
    virtualScrollItemSize: 50,
    enableDebounce: true,
    debounceDelay: 300,
    enableThrottle: true,
    throttleDelay: 100
  },

  // 监控配置
  monitoring: {
    enabled: true,
    errorTracking: true,
    performanceTracking: true,
    logging: true
  },

  // 导出配置
  export: {
    dateFormat: 'YYYY-MM-DD HH:mm:ss',
    csvDelimiter: ',',
    csvEncoding: 'UTF-8',
    includeBOM: true
  },

  // 日期格式配置
  dateFormat: {
    date: 'YYYY-MM-DD',
    datetime: 'YYYY-MM-DD HH:mm:ss',
    time: 'HH:mm:ss',
    month: 'YYYY-MM',
    year: 'YYYY'
  },

  // 时区配置
  timezone: 'Asia/Shanghai',

  // 数字格式配置
  numberFormat: {
    decimal: 2,
    thousands: ','
  },

  // 错误处理配置
  errorHandling: {
    showAlert: true,
    autoRetry: false,
    maxRetries: 3,
    retryDelay: 1000
  },

  // 开发模式配置
  development: {
    enableMockData: false,
    enableDebugTools: true,
    logLevel: 'debug'
  }
}
