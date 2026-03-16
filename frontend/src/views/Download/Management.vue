<template>
  <div class="download-management-page">
    <div class="page-header">
      <h2>下载管理</h2>
    </div>

    <!-- 下载控制面板 -->
    <el-card class="control-card">
      <el-form :inline="true">
        <el-form-item label="下载数量">
          <el-input-number v-model="downloadCount" :min="1" :max="10" controls-position="right" />
          <span style="margin-left: 10px; color: #909399">最近N张图片</span>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleTriggerDownload" :loading="downloading">
            {{ downloading ? '下载中...' : '立即下载' }}
          </el-button>
          <el-button @click="handleRetryFailed" :loading="retrying">
            重试失败任务
          </el-button>
          <el-button @click="loadDownloadStatus">刷新状态</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 下载状态统计 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-item">
            <div class="stat-label">总下载次数</div>
            <div class="stat-value">{{ downloadStatus.total_downloads || 0 }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-item">
            <div class="stat-label">成功率</div>
            <div class="stat-value">{{ successRate }}%</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-item">
            <div class="stat-label">失败任务</div>
            <div class="stat-value error">{{ downloadStatus.failed_count || 0 }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-item">
            <div class="stat-label">最后更新</div>
            <div class="stat-value small">{{ lastUpdateTime }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 下载历史记录 -->
    <el-card class="history-card">
      <template #header>
        <div class="card-header">
          <span>下载历史</span>
          <div>
            <el-select
              v-model="historyFilter.status"
              placeholder="全部状态"
              clearable
              style="width: 150px; margin-right: 10px"
              @change="loadDownloadHistory"
            >
              <el-option label="成功" value="success" />
              <el-option label="失败" value="failed" />
              <el-option label="重试中" value="retrying" />
            </el-select>
            <el-button size="small" @click="loadDownloadHistory">刷新</el-button>
          </div>
        </div>
      </template>

      <el-table :data="downloadHistory" v-loading="loadingHistory" border stripe max-height="500">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="observation_time" label="观测时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.observation_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="file_path" label="文件路径" min-width="200">
          <template #default="{ row }">
            {{ row.file_path || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="file_size" label="文件大小" width="100">
          <template #default="{ row }">
            {{ row.file_size ? formatFileSize(row.file_size) : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="retry_count" label="重试次数" width="100">
          <template #default="{ row }">
            {{ row.retry_count || 0 }} / {{ row.max_retries || 3 }}
          </template>
        </el-table-column>
        <el-table-column prop="error_message" label="错误信息" min-width="200">
          <template #default="{ row }">
            <span v-if="row.error_message" class="error-text">{{ row.error_message }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="downloaded_at" label="下载时间" width="180">
          <template #default="{ row }">
            {{ row.downloaded_at ? formatTime(row.downloaded_at) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'failed'"
              size="small"
              type="primary"
              @click="handleRetrySingle(row)"
            >
              重试
            </el-button>
            <el-button v-else size="small" disabled>
              -
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="historyPagination.page"
          v-model:page-size="historyPagination.page_size"
          :total="historyPagination.total"
          :page-sizes="[20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadDownloadHistory"
          @current-change="loadDownloadHistory"
        />
      </div>
    </el-card>

    <!-- 下载趋势图 -->
    <el-card class="chart-card">
      <template #header>
        <span>下载统计</span>
      </template>
      <div ref="chartRef" class="chart-container"></div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { downloadApi } from '../../api'

const loading = ref(false)
const downloading = ref(false)
const retrying = ref(false)
const loadingHistory = ref(false)

const downloadCount = ref(1)
const downloadStatus = ref<any>({})
const downloadHistory = ref<any[]>([])

const historyFilter = reactive({
  status: undefined as string | undefined
})

const historyPagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

const chartRef = ref<HTMLDivElement>()
let chartInstance: echarts.ECharts | null = null
let refreshTimer: any = null

// 计算属性
const successRate = computed(() => {
  const total = downloadStatus.value.total_downloads || 0
  const failed = downloadStatus.value.failed_count || 0
  if (total === 0) return 0
  return (((total - failed) / total) * 100).toFixed(1)
})

const lastUpdateTime = computed(() => {
  if (!downloadStatus.value.last_download_time) return '-'
  const time = new Date(downloadStatus.value.last_download_time)
  return time.toLocaleString('zh-CN')
})

function formatTime(time: string): string {
  return new Date(time).toLocaleString('zh-CN')
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

function getStatusText(status: string): string {
  const statusMap: Record<string, string> = {
    success: '成功',
    failed: '失败',
    retrying: '重试中',
    pending: '等待中'
  }
  return statusMap[status] || status
}

function getStatusTagType(status: string): string {
  const typeMap: Record<string, string> = {
    success: 'success',
    failed: 'danger',
    retrying: 'warning',
    pending: 'info'
  }
  return typeMap[status] || 'info'
}

async function loadDownloadStatus() {
  try {
    const response = await downloadApi.getDownloadStatus()
    downloadStatus.value = response.data || {}
  } catch (error) {
    console.error('Failed to load download status:', error)
  }
}

async function loadDownloadHistory() {
  loadingHistory.value = true
  try {
    const response = await downloadApi.getDownloadHistory({
      page: historyPagination.page,
      page_size: historyPagination.page_size,
      status: historyFilter.status
    })
    downloadHistory.value = response.data.items || []
    historyPagination.total = response.data.total || 0
  } catch (error) {
    console.error('Failed to load download history:', error)
    ElMessage.error('加载下载历史失败')
  } finally {
    loadingHistory.value = false
  }
}

async function handleTriggerDownload() {
  downloading.value = true
  try {
    await downloadApi.triggerDownload(downloadCount.value)
    ElMessage.success(`已触发下载 ${downloadCount.value} 张图片的任务`)
    // 延迟刷新
    setTimeout(() => {
      loadDownloadStatus()
      loadDownloadHistory()
    }, 2000)
  } catch (error) {
    console.error('Failed to trigger download:', error)
    ElMessage.error('触发下载失败')
  } finally {
    downloading.value = false
  }
}

async function handleRetryFailed() {
  retrying.value = true
  try {
    const response = await downloadApi.retryFailed(3)
    ElMessage.success(`已重试 ${response.data.retried_count || 0} 个失败任务`)
    setTimeout(() => {
      loadDownloadStatus()
      loadDownloadHistory()
    }, 2000)
  } catch (error) {
    console.error('Failed to retry failed tasks:', error)
    ElMessage.error('重试失败')
  } finally {
    retrying.value = false
  }
}

async function handleRetrySingle(record: any) {
  try {
    ElMessage.info(`重试任务 ${record.id}`)
    // 这里需要实现单个任务重试的API
    // 暂时使用批量重试
    await handleRetryFailed()
  } catch (error) {
    console.error('Failed to retry single task:', error)
  }
}

function initChart() {
  if (!chartRef.value) return

  chartInstance = echarts.init(chartRef.value)

  // 模拟数据
  const hours = Array.from({ length: 24 }, (_, i) => `${i}:00`)
  const successData = Array.from({ length: 24 }, () => Math.floor(Math.random() * 10))
  const failedData = Array.from({ length: 24 }, () => Math.floor(Math.random() * 3))

  const option = {
    title: {
      text: '24小时下载统计',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['成功', '失败'],
      top: 30
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: hours,
      axisLabel: {
        rotate: 45
      }
    },
    yAxis: {
      type: 'value',
      name: '下载数量'
    },
    series: [
      {
        name: '成功',
        type: 'bar',
        data: successData,
        itemStyle: {
          color: '#67C23A'
        }
      },
      {
        name: '失败',
        type: 'bar',
        data: failedData,
        itemStyle: {
          color: '#F56C6C'
        }
      }
    ]
  }

  chartInstance.setOption(option)
}

function resizeChart() {
  chartInstance?.resize()
}

onMounted(() => {
  loadDownloadStatus()
  loadDownloadHistory()
  initChart()

  window.addEventListener('resize', resizeChart)

  // 自动刷新（每30秒）
  refreshTimer = setInterval(() => {
    loadDownloadStatus()
    if (historyPagination.page === 1) {
      loadDownloadHistory()
    }
  }, 30000)
})

onUnmounted(() => {
  window.removeEventListener('resize', resizeChart)
  chartInstance?.dispose()
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>

<style scoped>
.download-management-page {
  padding: 0;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
  color: #303133;
}

.control-card {
  margin-bottom: 20px;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
}

.stat-item {
  padding: 10px 0;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #409EFF;
}

.stat-value.error {
  color: #F56C6C;
}

.stat-value.small {
  font-size: 14px;
  color: #606266;
}

.history-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.error-text {
  color: #F56C6C;
  font-size: 12px;
}

.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

.chart-card {
  margin-bottom: 20px;
}

.chart-container {
  height: 400px;
}
</style>
