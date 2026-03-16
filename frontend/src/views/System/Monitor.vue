<template>
  <div class="system-monitor-page">
    <div class="page-header">
      <h2>系统监控</h2>
      <el-button @click="loadSystemStatus" :loading="loading">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
    </div>

    <!-- 系统状态概览 -->
    <el-row :gutter="20" class="status-row">
      <el-col :span="6">
        <el-card class="status-card">
          <div class="status-item">
            <div class="status-icon success">
              <el-icon><CircleCheck /></el-icon>
            </div>
            <div class="status-content">
              <div class="status-label">系统状态</div>
              <div class="status-value">{{ systemStatus.status || '正常' }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="status-card">
          <div class="status-item">
            <div class="status-icon primary">
              <el-icon><Clock /></el-icon>
            </div>
            <div class="status-content">
              <div class="status-label">运行时间</div>
              <div class="status-value">{{ uptime }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="status-card">
          <div class="status-item">
            <div class="status-icon warning">
              <el-icon><Cpu /></el-icon>
            </div>
            <div class="status-content">
              <div class="status-label">CPU使用率</div>
              <div class="status-value">{{ systemStatus.cpu_usage || 0 }}%</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="status-card">
          <div class="status-item">
            <div class="status-icon info">
              <el-icon><Memo /></el-icon>
            </div>
            <div class="status-content">
              <div class="status-label">内存使用率</div>
              <div class="status-value">{{ systemStatus.memory_usage || 0 }}%</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 详细监控信息 -->
    <el-row :gutter="20">
      <!-- Celery任务队列 -->
      <el-col :span="12">
        <el-card class="monitor-card">
          <template #header>
            <div class="card-header">
              <span>Celery任务队列</span>
              <el-tag type="success">运行中</el-tag>
            </div>
          </template>

          <div class="metric-list">
            <div class="metric-item">
              <span class="metric-label">活跃任务</span>
              <span class="metric-value">{{ celeryStatus.active_tasks || 0 }}</span>
            </div>
            <div class="metric-item">
              <span class="metric-label">等待任务</span>
              <span class="metric-value">{{ celeryStatus.pending_tasks || 0 }}</span>
            </div>
            <div class="metric-item">
              <span class="metric-label">已完成任务</span>
              <span class="metric-value">{{ celeryStatus.completed_tasks || 0 }}</span>
            </div>
            <div class="metric-item">
              <span class="metric-label">失败任务</span>
              <span class="metric-value error">{{ celeryStatus.failed_tasks || 0 }}</span>
            </div>
            <div class="metric-item">
              <span class="metric-label">Worker数量</span>
              <span class="metric-value">{{ celeryStatus.worker_count || 4 }}</span>
            </div>
          </div>

          <el-divider />

          <div class="chart-container">
            <div ref="celeryChartRef" class="chart"></div>
          </div>
        </el-card>
      </el-col>

      <!-- 数据库连接池 -->
      <el-col :span="12">
        <el-card class="monitor-card">
          <template #header>
            <div class="card-header">
              <span>数据库连接池</span>
              <el-tag type="success">正常</el-tag>
            </div>
          </template>

          <div class="metric-list">
            <div class="metric-item">
              <span class="metric-label">活跃连接</span>
              <span class="metric-value">{{ dbStatus.active_connections || 0 }}</span>
            </div>
            <div class="metric-item">
              <span class="metric-label">空闲连接</span>
              <span class="metric-value">{{ dbStatus.idle_connections || 0 }}</span>
            </div>
            <div class="metric-item">
              <span class="metric-label">Pool Size</span>
              <span class="metric-value">{{ dbStatus.pool_size || 20 }}</span>
            </div>
            <div class="metric-item">
              <span class="metric-label">Max Overflow</span>
              <span class="metric-value">{{ dbStatus.max_overflow || 40 }}</span>
            </div>
            <div class="metric-item">
              <span class="metric-label">超时时间</span>
              <span class="metric-value">{{ dbStatus.timeout || 30 }}s</span>
            </div>
          </div>

          <el-divider />

          <div class="chart-container">
            <div ref="dbChartRef" class="chart"></div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 磁盘空间与网络 -->
    <el-row :gutter="20" style="margin-top: 20px">
      <!-- 磁盘空间 -->
      <el-col :span="12">
        <el-card class="monitor-card">
          <template #header>
            <div class="card-header">
              <span>磁盘空间</span>
              <el-tag :type="diskUsage > 80 ? 'danger' : diskUsage > 60 ? 'warning' : 'success'">
                {{ diskUsage }}%
              </el-tag>
            </div>
          </template>

          <div class="metric-list">
            <div class="metric-item">
              <span class="metric-label">总空间</span>
              <span class="metric-value">{{ formatBytes(diskStatus.total || 0) }}</span>
            </div>
            <div class="metric-item">
              <span class="metric-label">已使用</span>
              <span class="metric-value">{{ formatBytes(diskStatus.used || 0) }}</span>
            </div>
            <div class="metric-item">
              <span class="metric-label">可用空间</span>
              <span class="metric-value">{{ formatBytes(diskStatus.free || 0) }}</span>
            </div>
          </div>

          <el-progress
            :percentage="diskUsage"
            :color="getDiskColor(diskUsage)"
            :stroke-width="20"
            style="margin-top: 20px"
          />
        </el-card>
      </el-col>

      <!-- Redis状态 -->
      <el-col :span="12">
        <el-card class="monitor-card">
          <template #header>
            <div class="card-header">
              <span>Redis状态</span>
              <el-tag type="success">连接中</el-tag>
            </div>
          </template>

          <div class="metric-list">
            <div class="metric-item">
              <span class="metric-label">连接状态</span>
              <span class="metric-value success">正常</span>
            </div>
            <div class="metric-item">
              <span class="metric-label">内存使用</span>
              <span class="metric-value">{{ redisStatus.memory_usage || 0 }} MB</span>
            </div>
            <div class="metric-item">
              <span class="metric-label">键数量</span>
              <span class="metric-value">{{ redisStatus.key_count || 0 }}</span>
            </div>
            <div class="metric-item">
              <span class="metric-label">命中率</span>
              <span class="metric-value">{{ redisStatus.hit_rate || 0 }}%</span>
            </div>
            <div class="metric-item">
              <span class="metric-label">连接数</span>
              <span class="metric-value">{{ redisStatus.connections || 0 }}</span>
            </div>
          </div>

          <el-divider />

          <div class="chart-container">
            <div ref="redisChartRef" class="chart"></div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 系统日志 -->
    <el-card class="log-card" style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <span>最近日志</span>
          <div>
            <el-select
              v-model="logLevel"
              placeholder="全部级别"
              style="width: 120px; margin-right: 10px"
            >
              <el-option label="全部" value="" />
              <el-option label="ERROR" value="ERROR" />
              <el-option label="WARNING" value="WARNING" />
              <el-option label="INFO" value="INFO" />
              <el-option label="DEBUG" value="DEBUG" />
            </el-select>
            <el-button size="small" @click="loadLogs">刷新</el-button>
          </div>
        </div>
      </template>

      <el-table :data="logs" v-loading="loadingLogs" border stripe max-height="300">
        <el-table-column prop="timestamp" label="时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.timestamp) }}
          </template>
        </el-table-column>
        <el-table-column prop="level" label="级别" width="100">
          <template #default="{ row }">
            <el-tag :type="getLogLevelType(row.level)" size="small">
              {{ row.level }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="module" label="模块" width="150" />
        <el-table-column prop="message" label="消息" min-width="300" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { Refresh, CircleCheck, Clock, Cpu, Memo } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { systemApi } from '../../api'

const loading = ref(false)
const loadingLogs = ref(false)
const logLevel = ref('')

const systemStatus = ref<any>({})
const celeryStatus = ref<any>({})
const dbStatus = ref<any>({})
const diskStatus = ref<any>({})
const redisStatus = ref<any>({})
const logs = ref<any[]>([])

const celeryChartRef = ref<HTMLDivElement>()
const dbChartRef = ref<HTMLDivElement>()
const redisChartRef = ref<HTMLDivElement>()

let celeryChart: echarts.ECharts | null = null
let dbChart: echarts.ECharts | null = null
let redisChart: echarts.ECharts | null = null
let refreshTimer: any = null

// 计算属性
const uptime = computed(() => {
  if (!systemStatus.value.start_time) return '-'
  const startTime = new Date(systemStatus.value.start_time)
  const now = new Date()
  const seconds = Math.floor((now.getTime() - startTime.getTime()) / 1000)

  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)

  return `${days}天 ${hours}小时 ${minutes}分钟`
})

const diskUsage = computed(() => {
  if (!diskStatus.value.total || !diskStatus.value.used) return 0
  return Math.round((diskStatus.value.used / diskStatus.value.total) * 100)
})

function formatTime(time: string): string {
  return new Date(time).toLocaleString('zh-CN')
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
  return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB'
}

function getDiskColor(usage: number): string {
  if (usage > 80) return '#F56C6C'
  if (usage > 60) return '#E6A23C'
  return '#67C23A'
}

function getLogLevelType(level: string): string {
  const typeMap: Record<string, string> = {
    ERROR: 'danger',
    WARNING: 'warning',
    INFO: 'info',
    DEBUG: 'success'
  }
  return typeMap[level] || 'info'
}

async function loadSystemStatus() {
  loading.value = true
  try {
    const response = await systemApi.getStatus()
    const data = response.data

    systemStatus.value = data.system || {}
    celeryStatus.value = data.celery || {}
    dbStatus.value = data.database || {}
    diskStatus.value = data.disk || {}
    redisStatus.value = data.redis || {}
  } catch (error) {
    console.error('Failed to load system status:', error)
  } finally {
    loading.value = false
  }
}

async function loadLogs() {
  loadingLogs.value = true
  try {
    // 模拟日志数据
    logs.value = [
      {
        timestamp: new Date().toISOString(),
        level: 'INFO',
        module: 'download',
        message: '成功下载雷达图片: 20260311_143000.jpg'
      },
      {
        timestamp: new Date(Date.now() - 60000).toISOString(),
        level: 'INFO',
        module: 'processing',
        message: '处理站点数据完成: 站点1, 240条记录'
      },
      {
        timestamp: new Date(Date.now() - 120000).toISOString(),
        level: 'WARNING',
        module: 'prediction',
        message: '站点3数据不足，无法进行预测'
      },
      {
        timestamp: new Date(Date.now() - 180000).toISOString(),
        level: 'ERROR',
        module: 'download',
        message: '下载失败: 20260311_142900.jpg, 连接超时'
      }
    ]
  } catch (error) {
    console.error('Failed to load logs:', error)
  } finally {
    loadingLogs.value = false
  }
}

function initCharts() {
  // Celery任务队列图表
  if (celeryChartRef.value) {
    celeryChart = echarts.init(celeryChartRef.value)
    celeryChart.setOption({
      tooltip: {},
      xAxis: { type: 'category', data: ['活跃', '等待', '完成', '失败'] },
      yAxis: { type: 'value' },
      series: [
        {
          type: 'bar',
          data: [
            celeryStatus.value.active_tasks || 0,
            celeryStatus.value.pending_tasks || 0,
            celeryStatus.value.completed_tasks || 0,
            celeryStatus.value.failed_tasks || 0
          ],
          itemStyle: {
            color: function (params: any) {
              const colors = ['#409EFF', '#E6A23C', '#67C23A', '#F56C6C']
              return colors[params.dataIndex]
            }
          }
        }
      ]
    })
  }

  // 数据库连接池图表
  if (dbChartRef.value) {
    dbChart = echarts.init(dbChartRef.value)
    dbChart.setOption({
      tooltip: {},
      xAxis: { type: 'category', data: ['活跃', '空闲'] },
      yAxis: { type: 'value' },
      series: [
        {
          type: 'bar',
          data: [
            dbStatus.value.active_connections || 0,
            dbStatus.value.idle_connections || 0
          ],
          itemStyle: {
            color: function (params: any) {
              return params.dataIndex === 0 ? '#409EFF' : '#67C23A'
            }
          }
        }
      ]
    })
  }

  // Redis状态图表
  if (redisChartRef.value) {
    redisChart = echarts.init(redisChartRef.value)
    redisChart.setOption({
      tooltip: {},
      xAxis: { type: 'category', data: ['内存', '键数量', '连接数'] },
      yAxis: { type: 'value' },
      series: [
        {
          type: 'bar',
          data: [
            redisStatus.value.memory_usage || 0,
            redisStatus.value.key_count || 0,
            redisStatus.value.connections || 0
          ],
          itemStyle: {
            color: '#F56C6C'
          }
        }
      ]
    })
  }
}

function resizeCharts() {
  celeryChart?.resize()
  dbChart?.resize()
  redisChart?.resize()
}

onMounted(() => {
  loadSystemStatus()
  loadLogs()
  initCharts()

  window.addEventListener('resize', resizeCharts)

  // 自动刷新（每10秒）
  refreshTimer = setInterval(() => {
    loadSystemStatus()
  }, 10000)
})

onUnmounted(() => {
  window.removeEventListener('resize', resizeCharts)
  celeryChart?.dispose()
  dbChart?.dispose()
  redisChart?.dispose()
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>

<style scoped>
.system-monitor-page {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
  color: #303133;
}

.status-row {
  margin-bottom: 20px;
}

.status-card {
  text-align: center;
}

.status-item {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 10px 0;
}

.status-icon {
  font-size: 40px;
  margin-right: 15px;
}

.status-icon.success {
  color: #67C23A;
}

.status-icon.primary {
  color: #409EFF;
}

.status-icon.warning {
  color: #E6A23C;
}

.status-icon.info {
  color: #909399;
}

.status-content {
  text-align: left;
}

.status-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 5px;
}

.status-value {
  font-size: 20px;
  font-weight: bold;
  color: #303133;
}

.monitor-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.metric-list {
  margin-bottom: 10px;
}

.metric-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.metric-item:last-child {
  border-bottom: none;
}

.metric-label {
  color: #606266;
}

.metric-value {
  font-weight: bold;
  color: #303133;
}

.metric-value.error {
  color: #F56C6C;
}

.metric-value.success {
  color: #67C23A;
}

.chart-container {
  height: 200px;
}

.chart {
  height: 100%;
}

.log-card {
  margin-bottom: 20px;
}

.chart-container {
  position: relative;
}
</style>
