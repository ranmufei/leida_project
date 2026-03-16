<template>
  <div class="predictions-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>预测管理</span>
        </div>
      </template>

      <!-- 创建预测 -->
      <el-form :inline="true" :model="predictForm" class="predict-form">
        <el-form-item label="站点">
          <el-select
            v-model="predictForm.site_id"
            placeholder="请选择站点"
            style="width: 250px"
          >
            <el-option
              v-for="site in sites"
              :key="site.id"
              :label="`${site.name} (${site.code})`"
              :value="site.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="预测方法">
          <el-select
            v-model="predictForm.model_type"
            placeholder="请选择预测方法"
            style="width: 250px"
          >
            <el-option
              v-for="method in predictionMethods"
              :key="method.id"
              :label="method.name"
              :value="method.id"
            >
              <div>
                <div>{{ method.name }}</div>
                <div style="font-size: 12px; color: #909399">
                  {{ method.description }}
                </div>
              </div>
            </el-option>
          </el-select>
        </el-form-item>

        <el-form-item label="预测时长">
          <el-select
            v-model="predictForm.hours"
            placeholder="请选择时长"
            style="width: 150px"
          >
            <el-option label="6 小时" :value="6" />
            <el-option label="12 小时" :value="12" />
            <el-option label="24 小时" :value="24" />
            <el-option label="48 小时" :value="48" />
            <el-option label="72 小时" :value="72" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            :icon="MagicStick"
            :loading="creating"
            @click="handleCreatePrediction"
          >
            {{ creating ? '创建中...' : '创建预测' }}
          </el-button>
        </el-form-item>
      </el-form>

      <el-divider />

      <!-- 预测结果 -->
      <div v-if="currentPrediction" class="prediction-result">
        <h3>最新预测结果</h3>

        <el-descriptions :column="2" border>
          <el-descriptions-item label="预测ID">
            {{ currentPrediction.prediction_id }}
          </el-descriptions-item>
          <el-descriptions-item label="站点ID">
            {{ currentPrediction.site_id }}
          </el-descriptions-item>
          <el-descriptions-item label="预测方法">
            <el-tag>{{ getMethodName(currentPrediction.model_type) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="预测时间">
            {{ formatDateTime(currentPrediction.prediction_time) }}
          </el-descriptions-item>
          <el-descriptions-item label="预测dBZ值">
            <el-tag type="primary" size="large">
              {{ currentPrediction.predicted_dbz?.toFixed(2) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="置信区间">
            [
            {{ currentPrediction.confidence_lower?.toFixed(2) }},
            {{ currentPrediction.confidence_upper?.toFixed(2) }}
            ]
          </el-descriptions-item>
          <el-descriptions-item label="预测时长">
            {{ Math.floor((currentPrediction.prediction_horizon || 0) / 60) }} 小时
          </el-descriptions-item>
          <el-descriptions-item label="准确度">
            <el-progress
              :percentage="
                ((currentPrediction.prediction_accuracy || 0) * 100).toFixed(0)
              "
              :color="getAccuracyColor(currentPrediction.prediction_accuracy)"
            />
          </el-descriptions-item>
        </el-descriptions>

        <div v-if="currentPrediction.is_cached" class="cache-notice">
          <el-alert
            title="注意：这是缓存的预测结果"
            type="info"
            :closable="false"
            show-icon
          />
        </div>
      </div>

      <div v-else class="no-prediction">
        <el-empty description="暂无预测结果，请创建预测任务" />
      </div>
    </el-card>

    <!-- 预测历史 -->
    <el-card style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <span>预测方法说明</span>
        </div>
      </template>

      <el-space wrap>
        <el-card v-for="method in predictionMethods" :key="method.id" style="width: 300px">
          <template #header>
            <div class="method-header">
              <el-icon><TrendCharts /></el-icon>
              <span>{{ method.name }}</span>
            </div>
          </template>
          <div class="method-description">
            {{ method.description }}
          </div>
          <el-divider />
          <div class="method-params">
            <div><strong>参数:</strong></div>
            <div v-for="(param, key) in method.parameters" :key="key" style="margin-top: 5px">
              <el-tag size="small">{{ param.description }}</el-tag>
              <div style="font-size: 12px; color: #909399; margin-top: 3px">
                默认: {{ param.default }} | 范围: {{ param.min }} - {{ param.max }}
              </div>
            </div>
          </div>
        </el-card>
      </el-space>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { MagicStick, TrendCharts } from '@element-plus/icons-vue'
import { predictionApi, siteApi, type Site, type Prediction } from '@/api/modules'
import dayjs from 'dayjs'

const sites = ref<Site[]>([])
const predictionMethods = ref<any[]>([])
const currentPrediction = ref<any>(null)
const creating = ref(false)

const predictForm = reactive({
  site_id: undefined as number | undefined,
  model_type: 'prophet',
  hours: 24
})

// 加载站点列表
async function loadSites() {
  try {
    const response = await siteApi.getList({ page: 1, page_size: 100 })
    sites.value = response.data.data.items

    // 默认选择第一个站点
    if (sites.value.length > 0) {
      predictForm.site_id = sites.value[0].id
    }
  } catch (error) {
    console.error('Failed to load sites:', error)
  }
}

// 加载预测方法
async function loadPredictionMethods() {
  try {
    const response = await predictionApi.getMethods()
    predictionMethods.value = response.data.data.methods
  } catch (error) {
    console.error('Failed to load prediction methods:', error)
  }
}

// 创建预测
async function handleCreatePrediction() {
  if (!predictForm.site_id) {
    ElMessage.warning('请选择站点')
    return
  }

  try {
    creating.value = true

    const response = await predictionApi.create({
      site_id: predictForm.site_id,
      model_type: predictForm.model_type,
      hours: predictForm.hours
    })

    currentPrediction.value = response.data.data

    if (currentPrediction.value.is_cached) {
      ElMessage.info('使用缓存的预测结果')
    } else {
      ElMessage.success('预测任务创建成功')
    }
  } catch (error) {
    console.error('Failed to create prediction:', error)
  } finally {
    creating.value = false
  }
}

// 格式化日期时间
function formatDateTime(dateStr: string) {
  return dayjs(dateStr).format('YYYY-MM-DD HH:mm:ss')
}

// 获取方法名称
function getMethodName(modelType: string) {
  const method = predictionMethods.value.find((m) => m.id === modelType)
  return method ? method.name : modelType
}

// 获取准确度颜色
function getAccuracyColor(accuracy: number) {
  if (accuracy >= 0.9) return '#67c23a'
  if (accuracy >= 0.8) return '#e6a23c'
  if (accuracy >= 0.7) return '#f56c6c'
  return '#909399'
}

onMounted(() => {
  loadSites()
  loadPredictionMethods()
})
</script>

<style scoped>
.predictions-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.predict-form {
  margin-bottom: 20px;
}

.prediction-result {
  padding: 20px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.prediction-result h3 {
  margin-top: 0;
  margin-bottom: 20px;
  color: #303133;
}

.cache-notice {
  margin-top: 20px;
}

.no-prediction {
  padding: 40px 0;
  text-align: center;
}

.method-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.method-description {
  min-height: 60px;
  color: #606266;
  font-size: 14px;
}

.method-params {
  font-size: 13px;
}
</style>
