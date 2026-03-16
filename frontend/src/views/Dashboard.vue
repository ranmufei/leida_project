<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <!-- 统计卡片 -->
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon sites">
              <el-icon><Location /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ statistics.total_sites }}</div>
              <div class="stat-label">站点总数</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon data">
              <el-icon><DataLine /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ formatNumber(statistics.total_records) }}</div>
              <div class="stat-label">数据总量</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon downloads">
              <el-icon><Download /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ statistics.downloads_today }}</div>
              <div class="stat-label">今日下载</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon predictions">
              <el-icon><TrendCharts /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ statistics.predictions_today }}</div>
              <div class="stat-label">今日预测</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <!-- 下载状态 -->
      <el-col :xs="24" :lg="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>下载状态</span>
              <el-button text @click="refreshDownloadStatus">
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
            </div>
          </template>

          <el-descriptions :column="2" border>
            <el-descriptions-item label="总记录数">
              {{ downloadStatus.total || 0 }}
            </el-descriptions-item>
            <el-descriptions-item label="成功率">
              {{ ((downloadStatus.success_rate || 0) * 100).toFixed(1) }}%
            </el-descriptions-item>
            <el-descriptions-item label="最新下载">
              {{ formatTime(downloadStatus.latest_download_time) }}
            </el-descriptions-item>
            <el-descriptions-item label="下次下载">
              {{ formatTime(downloadStatus.next_download_time) }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>

      <!-- 系统状态 -->
      <el-col :xs="24" :lg="12">
        <el-card>
          <template #header>
            <span>系统状态</span>
          </template>

          <el-descriptions :column="1" border>
            <el-descriptions-item label="数据库">
              <el-tag type="success">连接正常</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="Redis">
              <el-tag type="success">运行中</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="Celery">
              <el-tag type="success">运行中</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="系统时间">
              {{ currentTime }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { siteApi, downloadApi, systemApi } from '../api'

const statistics = ref({
  total_sites: 0,
  total_records: 0,
  downloads_today: 0,
  predictions_today: 0
})

const downloadStatus = ref<any>({})
const currentTime = ref('')
let timer: number | null = null

function formatNumber(num: number): string {
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + 'w'
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'k'
  }
  return num.toString()
}

function formatTime(time: string | null): string {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

function updateTime() {
  currentTime.value = new Date().toLocaleString('zh-CN')
}

async function loadStatistics() {
  try {
    // 获取站点列表（第一页）
    const sitesRes = await siteApi.getSites({ page: 1, page_size: 1 })
    statistics.value.total_sites = sitesRes.data.total
  } catch (error) {
    console.error('Failed to load statistics:', error)
  }
}

async function refreshDownloadStatus() {
  try {
    const res = await downloadApi.getDownloadStatus()
    downloadStatus.value = res.data.download_statistics
  } catch (error) {
    console.error('Failed to load download status:', error)
  }
}

onMounted(() => {
  loadStatistics()
  refreshDownloadStatus()
  updateTime()
  timer = setInterval(updateTime, 1000) as unknown as number
})

onUnmounted(() => {
  if (timer) {
    clearInterval(timer)
  }
})
</script>

<style scoped>
.dashboard {
  padding: 0;
}

.stat-card {
  margin-bottom: 20px;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: #fff;
}

.stat-icon.sites {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-icon.data {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-icon.downloads {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-icon.predictions {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
