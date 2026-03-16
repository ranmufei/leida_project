<template>
  <div class="data-query-page">
    <div class="page-header">
      <h2>数据查询</h2>
    </div>

    <!-- 查询表单 -->
    <el-card class="search-card">
      <el-form :inline="true" :model="queryForm">
        <el-form-item label="站点">
          <el-select
            v-model="queryForm.site_id"
            placeholder="请选择站点"
            clearable
            multiple
            collapse-tags
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

        <el-form-item label="时间范围">
          <el-date-picker
            v-model="queryForm.dateRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DD HH:mm:ss"
            :default-time="defaultTime"
          />
        </el-form-item>

        <el-form-item label="数据源">
          <el-select v-model="queryForm.data_source" placeholder="全部" clearable style="width: 120px">
            <el-option label="实际数据" value="actual" />
            <el-option label="预测数据" value="predicted" />
          </el-select>
        </el-form-item>

        <el-form-item label="dBZ范围">
          <el-input-number
            v-model="queryForm.dbz_min"
            :min="0"
            :max="75"
            placeholder="最小值"
            controls-position="right"
            style="width: 100px"
          />
          <span style="margin: 0 5px">-</span>
          <el-input-number
            v-model="queryForm.dbz_max"
            :min="0"
            :max="75"
            placeholder="最大值"
            controls-position="right"
            style="width: 100px"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleQuery" :loading="loading">
            查询
          </el-button>
          <el-button @click="handleReset">重置</el-button>
          <el-button type="success" @click="handleExport" :disabled="data.length === 0">
            导出CSV
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 数据统计 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-item">
            <div class="stat-label">查询结果</div>
            <div class="stat-value">{{ pagination.total }} 条</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-item">
            <div class="stat-label">平均dBZ</div>
            <div class="stat-value">{{ averageDbz }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-item">
            <div class="stat-label">最大dBZ</div>
            <div class="stat-value">{{ maxDbz }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-item">
            <div class="stat-label">最小dBZ</div>
            <div class="stat-value">{{ minDbz }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表展示 -->
    <el-card class="chart-card">
      <template #header>
        <div class="card-header">
          <span>数据趋势图</span>
          <el-switch
            v-model="showChart"
            active-text="显示图表"
            inactive-text="隐藏图表"
          />
        </div>
      </template>
      <DbzChart
        v-if="showChart && data.length > 0"
        :data="data"
        :height="'400px'"
        :show-confidence="true"
      />
      <el-empty v-else-if="!showChart" description="图表已隐藏" />
      <el-empty v-else description="暂无数据" />
    </el-card>

    <!-- 数据表格 -->
    <el-card class="table-card">
      <el-table :data="data" v-loading="loading" border stripe max-height="500">
        <el-table-column prop="site_id" label="站点ID" width="80" />
        <el-table-column prop="observation_time" label="观测时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.observation_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="dbz_value" label="dBZ值" width="100">
          <template #default="{ row }">
            <el-tag :type="getDbzTagType(row.dbz_value)">
              {{ row.dbz_value }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="dbz_category" label="等级" width="100" />
        <el-table-column prop="cloud_impact_factor" label="云影响因子" width="120">
          <template #default="{ row }">
            {{ (row.cloud_impact_factor * 100).toFixed(1) }}%
          </template>
        </el-table-column>
        <el-table-column prop="data_source" label="数据源" width="100">
          <template #default="{ row }">
            <el-tag :type="row.data_source === 'actual' ? 'success' : 'warning'">
              {{ row.data_source === 'actual' ? '实际' : '预测' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="data_quality" label="数据质量" width="100">
          <template #default="{ row }">
            <el-tag :type="getQualityTagType(row.data_quality)">
              {{ row.data_quality }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="rgb_value" label="RGB值" width="150">
          <template #default="{ row }">
            <div
              v-if="row.rgb_value"
              class="color-box"
              :style="{ backgroundColor: `rgb(${row.rgb_value})` }"
            ></div>
            <span v-else>-</span>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :total="pagination.total"
          :page-sizes="[20, 50, 100, 200]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleQuery"
          @current-change="handleQuery"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import DbzChart from '../../components/charts/DbzChart.vue'
import { dataApi } from '../../api'
import type { SiteRadarData } from '../../types/data'

const loading = ref(false)
const data = ref<SiteRadarData[]>([])
const sites = ref<any[]>([])
const showChart = ref(true)

const defaultTime: [Date, Date] = [
  new Date(2000, 1, 1, 0, 0, 0),
  new Date(2000, 2, 1, 23, 59, 59)
]

const queryForm = reactive({
  site_id: [] as number[],
  dateRange: [] as string[],
  data_source: undefined as string | undefined,
  dbz_min: undefined as number | undefined,
  dbz_max: undefined as number | undefined
})

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

// 计算统计数据
const averageDbz = computed(() => {
  if (data.value.length === 0) return '-'
  const sum = data.value.reduce((acc, curr) => acc + curr.dbz_value, 0)
  return (sum / data.value.length).toFixed(2)
})

const maxDbz = computed(() => {
  if (data.value.length === 0) return '-'
  return Math.max(...data.value.map(d => d.dbz_value)).toFixed(2)
})

const minDbz = computed(() => {
  if (data.value.length === 0) return '-'
  return Math.min(...data.value.map(d => d.dbz_value)).toFixed(2)
})

function formatTime(time: string): string {
  return new Date(time).toLocaleString('zh-CN')
}

function getDbzTagType(dbz: number): string {
  if (dbz < 10) return 'info'
  if (dbz < 20) return 'success'
  if (dbz < 30) return ''
  if (dbz < 40) return 'warning'
  return 'danger'
}

function getQualityTagType(quality: string): string {
  if (quality === 'excellent') return 'success'
  if (quality === 'good') return ''
  if (quality === 'fair') return 'warning'
  return 'danger'
}

async function handleQuery() {
  loading.value = true
  try {
    const params: any = {
      page: pagination.page,
      page_size: pagination.page_size
    }

    if (queryForm.site_id.length > 0) {
      params.site_id = queryForm.site_id.join(',')
    }

    if (queryForm.dateRange && queryForm.dateRange.length === 2) {
      params.start_time = queryForm.dateRange[0]
      params.end_time = queryForm.dateRange[1]
    }

    if (queryForm.data_source) {
      params.data_source = queryForm.data_source
    }

    if (queryForm.dbz_min !== undefined) {
      params.dbz_min = queryForm.dbz_min
    }

    if (queryForm.dbz_max !== undefined) {
      params.dbz_max = queryForm.dbz_max
    }

    const response = await dataApi.queryData(params)
    data.value = response.data.items
    pagination.total = response.data.total
  } catch (error) {
    console.error('Failed to query data:', error)
    ElMessage.error('查询数据失败')
  } finally {
    loading.value = false
  }
}

function handleReset() {
  queryForm.site_id = []
  queryForm.dateRange = []
  queryForm.data_source = undefined
  queryForm.dbz_min = undefined
  queryForm.dbz_max = undefined
  pagination.page = 1
  data.value = []
  pagination.total = 0
}

async function handleExport() {
  try {
    const params: any = {}

    if (queryForm.site_id.length > 0) {
      params.site_id = queryForm.site_id.join(',')
    }

    if (queryForm.dateRange && queryForm.dateRange.length === 2) {
      params.start_time = queryForm.dateRange[0]
      params.end_time = queryForm.dateRange[1]
    }

    if (queryForm.data_source) {
      params.data_source = queryForm.data_source
    }

    if (queryForm.dbz_min !== undefined) {
      params.dbz_min = queryForm.dbz_min
    }

    if (queryForm.dbz_max !== undefined) {
      params.dbz_max = queryForm.dbz_max
    }

    await dataApi.exportData(params)
    ElMessage.success('导出请求已提交，请稍后查看')
  } catch (error) {
    console.error('Failed to export data:', error)
    ElMessage.error('导出失败')
  }
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

onMounted(() => {
  loadSites()
  // 设置默认时间范围为最近24小时
  const now = new Date()
  const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000)
  queryForm.dateRange = [
    yesterday.toISOString().slice(0, 19).replace('T', ' '),
    now.toISOString().slice(0, 19).replace('T', ' ')
  ]
  handleQuery()
})
</script>

<style scoped>
.data-query-page {
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

.search-card {
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

.chart-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.table-card {
  min-height: 400px;
}

.color-box {
  width: 40px;
  height: 20px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  display: inline-block;
}

.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>
