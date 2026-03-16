<template>
  <div class="prediction-page">
    <div class="page-header">
      <h2>预测展示</h2>
    </div>

    <!-- 预测控制面板 -->
    <el-card class="control-card">
      <el-form :inline="true" :model="predictionForm">
        <el-form-item label="站点">
          <el-select
            v-model="predictionForm.site_id"
            placeholder="请选择站点"
            clearable
            style="width: 200px"
          >
            <el-option
              v-for="site in sites"
              :key="site.id"
              :label="site.name"
              :value="site.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="预测方法">
          <el-select v-model="predictionForm.method" placeholder="请选择方法" style="width: 150px">
            <el-option
              v-for="method in predictionMethods"
              :key="method.name"
              :label="method.display_name"
              :value="method.name"
            >
              <div>
                <div>{{ method.display_name }}</div>
                <div style="font-size: 12px; color: #909399">{{ method.description }}</div>
              </div>
            </el-option>
          </el-select>
        </el-form-item>

        <el-form-item label="预测时长">
          <el-select v-model="predictionForm.horizon" placeholder="请选择" style="width: 120px">
            <el-option label="1小时" :value="60" />
            <el-option label="2小时" :value="120" />
            <el-option label="4小时" :value="240" />
            <el-option label="6小时" :value="360" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            @click="handleCreatePrediction"
            :loading="predicting"
            :disabled="!predictionForm.site_id"
          >
            {{ predicting ? '预测中...' : '开始预测' }}
          </el-button>
          <el-button @click="handleLoadLatest" :disabled="!predictionForm.site_id">
            查看最新
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 预测结果展示 -->
    <el-row :gutter="20" v-if="predictionResult">
      <!-- 预测结果统计 -->
      <el-col :span="24">
        <el-card class="result-card">
          <template #header>
            <div class="card-header">
              <span>预测结果 - 站点: {{ getSiteName(predictionResult.site_id) }}</span>
              <el-tag :type="getMethodTagType(predictionResult.model_type)">
                {{ getMethodDisplayName(predictionResult.model_type) }}
              </el-tag>
            </div>
          </template>

          <!-- 统计信息 -->
          <el-row :gutter="20" class="stats-row">
            <el-col :span="6">
              <div class="stat-item">
                <div class="stat-label">预测时间点</div>
                <div class="stat-value">{{ predictionResult.predictions?.length || 0 }} 个</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="stat-item">
                <div class="stat-label">预测时长</div>
                <div class="stat-value">{{ predictionResult.prediction_horizon || 0 }} 分钟</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="stat-item">
                <div class="stat-label">平均dBZ</div>
                <div class="stat-value">{{ averagePredictedDbz }}</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="stat-item">
                <div class="stat-label">最大dBZ</div>
                <div class="stat-value">{{ maxPredictedDbz }}</div>
              </div>
            </el-col>
          </el-row>

          <!-- 预测图表 -->
          <div class="chart-container">
            <DbzChart
              :data="chartData"
              title="预测趋势图"
              height="400px"
              :show-confidence="showConfidence"
            />
            <div class="chart-controls">
              <el-checkbox v-model="showConfidence">显示置信区间</el-checkbox>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 预测数据表格 -->
      <el-col :span="24" style="margin-top: 20px">
        <el-card class="table-card">
          <template #header>
            <span>详细数据</span>
          </template>
          <el-table :data="predictionResult.predictions" border stripe max-height="400">
            <el-table-column prop="time_step" label="时间步" width="80" />
            <el-table-column prop="prediction_time" label="预测时间" width="180">
              <template #default="{ row }">
                {{ formatTime(row.prediction_time) }}
              </template>
            </el-table-column>
            <el-table-column prop="predicted_dbz" label="预测dBZ" width="100">
              <template #default="{ row }">
                <el-tag :type="getDbzTagType(row.predicted_dbz)">
                  {{ row.predicted_dbz }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="confidence_lower" label="置信下限" width="100">
              <template #default="{ row }">
                {{ row.confidence_lower ?? '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="confidence_upper" label="置信上限" width="100">
              <template #default="{ row }">
                {{ row.confidence_upper ?? '-' }}
              </template>
            </el-table-column>
            <el-table-column label="置信区间宽度" width="120">
              <template #default="{ row }">
                {{
                  row.confidence_lower && row.confidence_upper
                    ? (row.confidence_upper - row.confidence_lower).toFixed(2)
                    : '-'
                }}
              </template>
            </el-table-column>
            <el-table-column prop="confidence" label="置信度" width="100">
              <template #default="{ row }">
                <el-progress
                  v-if="row.confidence"
                  :percentage="Math.round(row.confidence * 100)"
                  :color="getConfidenceColor(row.confidence)"
                />
                <span v-else>-</span>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 历史预测记录 -->
    <el-card class="history-card" v-if="predictionForm.site_id">
      <template #header>
        <div class="card-header">
          <span>历史预测记录</span>
          <el-button size="small" @click="loadPredictionHistory">刷新</el-button>
        </div>
      </template>

      <el-table :data="historyRecords" v-loading="loadingHistory" border stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="prediction_time" label="预测时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.prediction_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="model_type" label="模型" width="120">
          <template #default="{ row }">
            <el-tag :type="getMethodTagType(row.model_type)" size="small">
              {{ getMethodDisplayName(row.model_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="predicted_dbz" label="预测dBZ" width="100" />
        <el-table-column prop="prediction_horizon" label="预测时长(分)" width="120" />
        <el-table-column prop="prediction_accuracy" label="准确率" width="100">
          <template #default="{ row }">
            {{ row.prediction_accuracy ? `${(row.prediction_accuracy * 100).toFixed(1)}%` : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="historyPagination.page"
          v-model:page-size="historyPagination.page_size"
          :total="historyPagination.total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="loadPredictionHistory"
          @current-change="loadPredictionHistory"
        />
      </div>
    </el-card>

    <!-- 空状态 -->
    <el-empty v-if="!predictionResult && !predicting" description="请选择站点并开始预测" />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import DbzChart from '../../components/charts/DbzChart.vue'
import { predictionApi } from '../../api'
import type { PredictionResult, PredictionMethod } from '../../types/data'

const loading = ref(false)
const predicting = ref(false)
const loadingHistory = ref(false)
const sites = ref<any[]>([])
const predictionMethods = ref<PredictionMethod[]>([])
const predictionResult = ref<any>(null)
const historyRecords = ref<any[]>([])
const showConfidence = ref(true)

const predictionForm = reactive({
  site_id: undefined as number | undefined,
  method: 'prophet',
  horizon: 360
})

const historyPagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

// 图表数据
const chartData = computed(() => {
  if (!predictionResult.value?.predictions) return []

  return predictionResult.value.predictions.map((p: any) => ({
    observation_time: p.prediction_time,
    dbz_value: p.predicted_dbz,
    data_source: 'predicted',
    confidence_lower: p.confidence_lower,
    confidence_upper: p.confidence_upper
  }))
})

// 统计数据
const averagePredictedDbz = computed(() => {
  if (!predictionResult.value?.predictions) return '-'
  const values = predictionResult.value.predictions.map((p: any) => p.predicted_dbz)
  return (values.reduce((a: number, b: number) => a + b, 0) / values.length).toFixed(2)
})

const maxPredictedDbz = computed(() => {
  if (!predictionResult.value?.predictions) return '-'
  const values = predictionResult.value.predictions.map((p: any) => p.predicted_dbz)
  return Math.max(...values).toFixed(2)
})

function formatTime(time: string): string {
  return new Date(time).toLocaleString('zh-CN')
}

function getSiteName(siteId: number): string {
  const site = sites.value.find(s => s.id === siteId)
  return site?.name || `站点${siteId}`
}

function getMethodDisplayName(method: string): string {
  const methodMap: Record<string, string> = {
    optical_flow: '光流法',
    prophet: 'Prophet',
    ensemble: '集成预测'
  }
  return methodMap[method] || method
}

function getMethodTagType(method: string): string {
  const typeMap: Record<string, string> = {
    optical_flow: 'success',
    prophet: 'warning',
    ensemble: 'primary'
  }
  return typeMap[method] || 'info'
}

function getDbzTagType(dbz: number): string {
  if (dbz < 10) return 'info'
  if (dbz < 20) return 'success'
  if (dbz < 30) return ''
  if (dbz < 40) return 'warning'
  return 'danger'
}

function getConfidenceColor(confidence: number): string {
  if (confidence >= 0.8) return '#67C23A'
  if (confidence >= 0.6) return '#E6A23C'
  return '#F56C6C'
}

async function loadSites() {
  try {
    const response = await fetch('http://localhost:8000/api/v1/sites/', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })
    const result = await response.json()
    sites.value = result.data.items || []
  } catch (error) {
    console.error('Failed to load sites:', error)
  }
}

async function loadPredictionMethods() {
  try {
    const response = await predictionApi.getMethods()
    predictionMethods.value = response.data.methods || []
  } catch (error) {
    console.error('Failed to load prediction methods:', error)
  }
}

async function handleCreatePrediction() {
  if (!predictionForm.site_id) {
    ElMessage.warning('请先选择站点')
    return
  }

  predicting.value = true
  try {
    const response = await predictionApi.createPrediction(predictionForm.site_id, {
      method: predictionForm.method,
      prediction_horizon_minutes: predictionForm.horizon
    })

    if (response.data.task_id) {
      ElMessage.success(`预测任务已创建，任务ID: ${response.data.task_id}`)
      // 轮询获取结果
      pollPredictionResult(response.data.task_id)
    }
  } catch (error) {
    console.error('Failed to create prediction:', error)
    ElMessage.error('创建预测任务失败')
  } finally {
    predicting.value = false
  }
}

async function pollPredictionResult(taskId: string) {
  // 简化版：直接加载最新预测
  // 实际应用中应该轮询任务状态
  setTimeout(() => {
    handleLoadLatest()
  }, 2000)
}

async function handleLoadLatest() {
  if (!predictionForm.site_id) return

  loading.value = true
  try {
    const response = await predictionApi.getLatestPrediction(predictionForm.site_id)
    predictionResult.value = response.data
    loadPredictionHistory()
  } catch (error) {
    console.error('Failed to load latest prediction:', error)
    ElMessage.error('加载预测结果失败')
  } finally {
    loading.value = false
  }
}

async function loadPredictionHistory() {
  if (!predictionForm.site_id) return

  loadingHistory.value = true
  try {
    const response = await predictionApi.getPredictionHistory(predictionForm.site_id, {
      page: historyPagination.page,
      page_size: historyPagination.page_size
    })
    historyRecords.value = response.data.items || []
    historyPagination.total = response.data.total || 0
  } catch (error) {
    console.error('Failed to load prediction history:', error)
    ElMessage.error('加载历史记录失败')
  } finally {
    loadingHistory.value = false
  }
}

onMounted(() => {
  loadSites()
  loadPredictionMethods()
})
</script>

<style scoped>
.prediction-page {
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

.result-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-item {
  text-align: center;
  padding: 10px 0;
  background: #f5f7fa;
  border-radius: 4px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 20px;
  font-weight: bold;
  color: #409EFF;
}

.chart-container {
  margin-top: 20px;
}

.chart-controls {
  margin-top: 10px;
  text-align: center;
}

.table-card {
  margin-top: 20px;
}

.history-card {
  margin-top: 20px;
}

.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>
