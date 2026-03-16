<template>
  <div class="dashboard-container">
    <el-row :gutter="20">
      <!-- 统计卡片 -->
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon" color="#409eff"><OfficeBuilding /></el-icon>
            <div class="stat-info">
              <div class="stat-value">{{ stats.totalSites }}</div>
              <div class="stat-label">总站点数</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon" color="#67c23a"><DataLine /></el-icon>
            <div class="stat-info">
              <div class="stat-value">{{ stats.totalData }}</div>
              <div class="stat-label">雷达数据</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon" color="#e6a23c"><TrendCharts /></el-icon>
            <div class="stat-info">
              <div class="stat-value">{{ stats.totalPredictions }}</div>
              <div class="stat-label">预测任务</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon" color="#f56c6c"><Download /></el-icon>
            <div class="stat-info">
              <div class="stat-value">{{ stats.downloadTasks }}</div>
              <div class="stat-label">下载任务</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 快捷操作 -->
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>快捷操作</span>
            </div>
          </template>
          <el-space wrap>
            <el-button type="primary" :icon="Plus" @click="$router.push('/sites')">
              新建站点
            </el-button>
            <el-button type="success" :icon="TrendCharts" @click="$router.push('/predictions')">
              创建预测
            </el-button>
            <el-button type="warning" :icon="Download" @click="handleTriggerDownload">
              触发下载
            </el-button>
            <el-button type="info" :icon="DataLine" @click="$router.push('/data')">
              查询数据
            </el-button>
          </el-space>
        </el-card>
      </el-col>
    </el-row>

    <!-- 系统状态 -->
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :xs="24" :lg="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>系统状态</span>
            </div>
          </template>
          <div v-loading="loadingSystem">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="系统状态">
                <el-tag :type="systemInfo.status === 'running' ? 'success' : 'danger'">
                  {{ systemInfo.status === 'running' ? '运行中' : '异常' }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="CPU使用率">
                {{ systemInfo.cpu_percent }}%
              </el-descriptions-item>
              <el-descriptions-item label="内存使用率">
                {{ systemInfo.memory_percent }}%
              </el-descriptions-item>
              <el-descriptions-item label="磁盘使用率">
                {{ systemInfo.disk_percent }}%
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>下载状态</span>
            </div>
          </template>
          <div v-loading="loadingDownload">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="总任务数">
                {{ downloadStats.total || 0 }}
              </el-descriptions-item>
              <el-descriptions-item label="成功">
                <el-tag type="success">{{ downloadStats.success || 0 }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="失败">
                <el-tag type="danger">{{ downloadStats.failed || 0 }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="成功率">
                {{ (downloadStats.success_rate * 100).toFixed(1) }}%
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  OfficeBuilding,
  DataLine,
  TrendCharts,
  Download,
  Plus
} from '@element-plus/icons-vue'
import { siteApi, downloadApi, systemApi } from '@/api/modules'

// 统计数据
const stats = reactive({
  totalSites: 0,
  totalData: 0,
  totalPredictions: 0,
  downloadTasks: 0
})

// 系统信息
const systemInfo = reactive({
  status: 'unknown',
  cpu_percent: 0,
  memory_percent: 0,
  disk_percent: 0
})

// 下载统计
const downloadStats = reactive({
  total: 0,
  success: 0,
  failed: 0,
  success_rate: 0
})

const loadingSystem = ref(false)
const loadingDownload = ref(false)

// 加载站点统计
async function loadSiteStats() {
  try {
    const response = await siteApi.getList({ page: 1, page_size: 1 })
    stats.totalSites = response.data.data.total
  } catch (error) {
    console.error('Failed to load site stats:', error)
  }
}

// 加载系统信息
async function loadSystemInfo() {
  try {
    loadingSystem.value = true
    const response = await systemApi.getInfo()
    const data = response.data.data

    systemInfo.status = 'running'
    systemInfo.cpu_percent = data.resources?.cpu?.percent || 0
    systemInfo.memory_percent = data.resources?.memory?.percent || 0
    systemInfo.disk_percent = data.resources?.disk?.percent || 0
  } catch (error) {
    console.error('Failed to load system info:', error)
  } finally {
    loadingSystem.value = false
  }
}

// 加载下载状态
async function loadDownloadStatus() {
  try {
    loadingDownload.value = true
    const response = await downloadApi.getStatus()
    const data = response.data.data.download_statistics

    downloadStats.total = data.total || 0
    downloadStats.success = data.success || 0
    downloadStats.failed = data.failed || 0
    downloadStats.success_rate = data.success_rate || 0
    stats.downloadTasks = data.total || 0
  } catch (error) {
    console.error('Failed to load download status:', error)
  } finally {
    loadingDownload.value = false
  }
}

// 触发下载
async function handleTriggerDownload() {
  try {
    const response = await downloadApi.trigger()
    ElMessage.success(response.data.data.message || '下载任务已创建')
    await loadDownloadStatus()
  } catch (error) {
    console.error('Failed to trigger download:', error)
  }
}

onMounted(() => {
  loadSiteStats()
  loadSystemInfo()
  loadDownloadStatus()
})
</script>

<style scoped>
.dashboard-container {
  padding: 20px;
}

.stat-card {
  margin-bottom: 20px;
}

.stat-content {
  display: flex;
  align-items: center;
  padding: 10px 0;
}

.stat-icon {
  font-size: 48px;
  margin-right: 20px;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #303133;
  line-height: 1;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}
</style>
