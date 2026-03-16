<template>
  <div class="downloads-container">
    <el-row :gutter="20">
      <!-- 下载状态卡片 -->
      <el-col :xs="24" :lg="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>下载任务状态</span>
              <el-button
                type="primary"
                :icon="Refresh"
                @click="loadDownloadStatus"
              >
                刷新
              </el-button>
            </div>
          </template>

          <div v-loading="loading">
            <el-statistic direction="vertical" :value="downloadStats.total">
              <template #title>
                <div style="display: flex; align-items: center; gap: 8px">
                  <el-icon><Download /></el-icon>
                  <span>总任务数</span>
                </div>
              </template>
            </el-statistic>

            <el-row :gutter="16" style="margin-top: 20px">
              <el-col :span="8">
                <el-statistic :value="downloadStats.success">
                  <template #title>
                    <el-tag type="success" size="small">成功</el-tag>
                  </template>
                </el-statistic>
              </el-col>
              <el-col :span="8">
                <el-statistic :value="downloadStats.failed">
                  <template #title>
                    <el-tag type="danger" size="small">失败</el-tag>
                  </template>
                </el-statistic>
              </el-col>
              <el-col :span="8">
                <el-statistic :value="downloadStats.pending">
                  <template #title>
                    <el-tag type="info" size="small">待处理</el-tag>
                  </template>
                </el-statistic>
              </el-col>
            </el-row>

            <el-divider />

            <div>
              <div style="margin-bottom: 10px">成功率</div>
              <el-progress
                :percentage="(downloadStats.success_rate * 100).toFixed(2)"
                :color="getSuccessRateColor(downloadStats.success_rate)"
              />
            </div>

            <el-descriptions :column="1" border style="margin-top: 20px">
              <el-descriptions-item label="下次下载时间">
                {{ downloadStats.next_download_time || '未设置' }}
              </el-descriptions-item>
              <el-descriptions-item label="下载间隔">
                每 {{ downloadStats.download_interval_minutes }} 分钟
              </el-descriptions-item>
              <el-descriptions-item label="最近下载">
                {{ downloadStats.latest_download_time || '暂无' }}
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </el-card>
      </el-col>

      <!-- 手动操作卡片 -->
      <el-col :xs="24" :lg="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>手动操作</span>
            </div>
          </template>

          <div class="manual-actions">
            <el-alert
              title="手动触发下载"
              type="info"
              :closable="false"
              style="margin-bottom: 20px"
            >
              手动触发将下载最新的雷达图像数据，下载过程会在后台异步执行。
            </el-alert>

            <el-form :model="manualForm" label-width="120px">
              <el-form-item label="下载数量">
                <el-input-number
                  v-model="manualForm.count"
                  :min="1"
                  :max="10"
                  style="width: 200px"
                />
                <span style="margin-left: 10px; color: #909399">张图片</span>
              </el-form-item>

              <el-form-item>
                <el-button
                  type="primary"
                  :icon="Download"
                  :loading="triggering"
                  @click="handleTriggerDownload"
                >
                  {{ triggering ? '触发中...' : '立即触发下载' }}
                </el-button>
              </el-form-item>
            </el-form>

            <el-divider />

            <div class="download-log">
              <h4>下载日志</h4>
              <el-timeline>
                <el-timeline-item
                  v-for="(log, index) in downloadLogs"
                  :key="index"
                  :timestamp="log.time"
                  :type="log.type"
                >
                  {{ log.message }}
                </el-timeline-item>
              </el-timeline>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 下载配置 -->
    <el-card style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <span>下载配置</span>
        </div>
      </template>

      <el-form :model="configForm" label-width="150px" style="max-width: 600px">
        <el-form-item label="自动下载">
          <el-switch v-model="configForm.auto_download" />
          <span style="margin-left: 10px; color: #909399">
            启用后将按设定间隔自动下载
          </span>
        </el-form-item>

        <el-form-item label="下载间隔">
          <el-input-number
            v-model="configForm.interval"
            :min="1"
            :max="1440"
            :disabled="!configForm.auto_download"
            style="width: 200px"
          />
          <span style="margin-left: 10px; color: #909399">分钟</span>
        </el-form-item>

        <el-form-item label="数据源URL">
          <el-input
            v-model="configForm.data_source_url"
            placeholder="请输入数据源URL"
            :disabled="!configForm.auto_download"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSaveConfig">
            保存配置
          </el-button>
          <el-button @click="handleResetConfig">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Download, Refresh } from '@element-plus/icons-vue'
import { downloadApi } from '@/api/modules'
import dayjs from 'dayjs'

const loading = ref(false)
const triggering = ref(false)

const downloadStats = reactive({
  total: 0,
  success: 0,
  failed: 0,
  pending: 0,
  success_rate: 0,
  next_download_time: '',
  download_interval_minutes: 0,
  latest_download_time: ''
})

const manualForm = reactive({
  count: 1
})

const configForm = reactive({
  auto_download: true,
  interval: 6,
  data_source_url: ''
})

const downloadLogs = ref([
  {
    time: dayjs().format('YYYY-MM-DD HH:mm:ss'),
    message: '下载管理页面已加载',
    type: 'primary'
  }
])

// 加载下载状态
async function loadDownloadStatus() {
  try {
    loading.value = true
    const response = await downloadApi.getStatus()
    const data = response.data.data

    downloadStats.total = data.download_statistics?.total || 0
    downloadStats.success = data.download_statistics?.success || 0
    downloadStats.failed = data.download_statistics?.failed || 0
    downloadStats.pending = data.download_statistics?.pending || 0
    downloadStats.success_rate = data.download_statistics?.success_rate || 0
    downloadStats.next_download_time = formatDateTime(data.next_download_time)
    downloadStats.download_interval_minutes = data.download_interval_minutes || 6
    downloadStats.latest_download_time = formatDateTime(
      data.download_statistics?.latest_download_time
    )

    // 更新配置表单
    configForm.interval = downloadStats.download_interval_minutes
  } catch (error) {
    console.error('Failed to load download status:', error)
  } finally {
    loading.value = false
  }
}

// 触发下载
async function handleTriggerDownload() {
  try {
    triggering.value = true

    const response = await downloadApi.trigger()
    const message = response.data.data.message || '下载任务已创建'

    ElMessage.success(message)

    // 添加日志
    downloadLogs.value.unshift({
      time: dayjs().format('YYYY-MM-DD HH:mm:ss'),
      message: `手动触发下载: ${message}`,
      type: 'success'
    })

    // 刷新状态
    await loadDownloadStatus()
  } catch (error) {
    console.error('Failed to trigger download:', error)

    downloadLogs.value.unshift({
      time: dayjs().format('YYYY-MM-DD HH:mm:ss'),
      message: '触发下载失败',
      type: 'danger'
    })
  } finally {
    triggering.value = false
  }
}

// 保存配置
function handleSaveConfig() {
  ElMessage.success('配置已保存（演示功能）')

  downloadLogs.value.unshift({
    time: dayjs().format('YYYY-MM-DD HH:mm:ss'),
    message: `配置已更新: 间隔${configForm.interval}分钟`,
    type: 'primary'
  })
}

// 重置配置
function handleResetConfig() {
  configForm.auto_download = true
  configForm.interval = 6
  configForm.data_source_url = ''
  ElMessage.info('配置已重置')
}

// 格式化日期时间
function formatDateTime(dateStr: string) {
  if (!dateStr) return '-'
  return dayjs(dateStr).format('YYYY-MM-DD HH:mm:ss')
}

// 获取成功率颜色
function getSuccessRateColor(rate: number) {
  if (rate >= 0.9) return '#67c23a'
  if (rate >= 0.7) return '#e6a23c'
  return '#f56c6c'
}

onMounted(() => {
  loadDownloadStatus()
})
</script>

<style scoped>
.downloads-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.manual-actions {
  padding: 10px 0;
}

.download-log {
  margin-top: 20px;
}

.download-log h4 {
  margin-top: 0;
  margin-bottom: 15px;
  color: #303133;
}
</style>
