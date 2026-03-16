<template>
  <div class="data-query-container">
    <!-- 放大按钮（浮动在右上角） -->
    <el-button
      v-if="!isPreviewExpanded"
      class="expand-button"
      type="primary"
      :icon="FullScreen"
      @click="toggleExpand"
      size="small"
    >
      全屏预览
    </el-button>
    <el-button
      v-else
      class="expand-button expanded"
      type="warning"
      :icon="Aim"
      @click="toggleExpand"
      size="small"
    >
      退出全屏
    </el-button>

    <el-row :gutter="20">
      <!-- 左侧：数据查询表格 -->
      <el-col :span="isPreviewExpanded ? 0 : 8" v-show="!isPreviewExpanded">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>雷达数据查询</span>
            </div>
          </template>

          <!-- 查询表单 -->
          <el-form :inline="true" :model="queryForm" class="query-form">
            <el-form-item label="站点">
              <el-select
                v-model="queryForm.site_id"
                placeholder="请选择站点"
                clearable
                style="width: 200px"
              >
                <el-option
                  v-for="site in sites"
                  :key="site.id"
                  :label="site.station_name"
                  :value="site.id"
                />
              </el-select>
            </el-form-item>

            <el-form-item label="开始时间">
              <el-date-picker
                v-model="queryForm.start_time"
                type="datetime"
                placeholder="选择开始时间"
                format="YYYY-MM-DD HH:mm:ss"
                value-format="YYYY-MM-DD HH:mm:ss"
                style="width: 200px"
              />
            </el-form-item>

            <el-form-item label="结束时间">
              <el-date-picker
                v-model="queryForm.end_time"
                type="datetime"
                placeholder="选择结束时间"
                format="YYYY-MM-DD HH:mm:ss"
                value-format="YYYY-MM-DD HH:mm:ss"
                style="width: 200px"
              />
            </el-form-item>

            <el-form-item label="最小dBZ">
              <el-input-number
                v-model="queryForm.min_dbz"
                :min="-10"
                :max="75"
                :precision="1"
                placeholder="最小值"
                style="width: 150px"
              />
            </el-form-item>

            <el-form-item label="最大dBZ">
              <el-input-number
                v-model="queryForm.max_dbz"
                :min="-10"
                :max="75"
                :precision="1"
                placeholder="最大值"
                style="width: 150px"
              />
            </el-form-item>

            <el-form-item>
              <el-button type="primary" :icon="Search" @click="handleQuery">
                查询
              </el-button>
              <el-button :icon="Refresh" @click="handleReset">
                重置
              </el-button>
              <el-button :icon="DataAnalysis" @click="handleShowStatistics">
                统计分析
              </el-button>
              <el-button :icon="Download" @click="handleExportCSV" :loading="exporting">
                导出CSV
              </el-button>
            </el-form-item>
          </el-form>

          <!-- 数据表格 -->
          <el-table
            v-loading="loading"
            :data="dataList"
            stripe
            style="width: 100%"
            @row-click="handleRowClick"
            highlight-current-row
          >
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="site_id" label="站点ID" width="100" />
            <el-table-column label="观测时间" width="180">
              <template #default="{ row }">
                {{ formatDateTime(row.observation_time) }}
              </template>
            </el-table-column>
            <el-table-column prop="dbz_value" label="dBZ值" width="100">
              <template #default="{ row }">
                <el-tag :type="getDbzTagType(row.dbz_value)">
                  {{ row.dbz_value?.toFixed(1) || '-' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="dbz_category" label="分类" width="120" />
            <el-table-column label="云影响系数" width="120">
              <template #default="{ row }">
                {{ (row.cloud_impact_factor * 100).toFixed(1) }}%
              </template>
            </el-table-column>
            <el-table-column label="像素坐标" width="150">
              <template #default="{ row }">
                <span v-if="row.pixel_x !== undefined && row.pixel_y !== undefined">
                  {{ row.pixel_x }}, {{ row.pixel_y }}
                </span>
                <span v-else style="color: #999;">-</span>
              </template>
            </el-table-column>
            <el-table-column label="创建时间" width="180">
              <template #default="{ row }">
                {{ formatDateTime(row.created_at) }}
              </template>
            </el-table-column>
          </el-table>

          <!-- 分页 -->
          <div class="pagination-container">
            <el-pagination
              v-model:current-page="pagination.page"
              v-model:page-size="pagination.pageSize"
              :total="pagination.total"
              :page-sizes="[20, 50, 100, 200, 500, 1000]"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="handleQuery"
              @current-change="handleQuery"
            />
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：雷达图片预览 -->
      <el-col :span="isPreviewExpanded ? 24 : 16">
        <RadarImagePreview
          ref="radarPreviewRef"
          :selected-data="selectedRow"
          :is-expanded="isPreviewExpanded"
        />
      </el-col>
    </el-row>

    <!-- 统计对话框 -->
    <el-dialog
      v-model="statisticsDialogVisible"
      title="数据统计分析"
      width="800px"
    >
      <div v-loading="loadingStatistics">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="记录总数">
            {{ statistics.total_records || 0 }}
          </el-descriptions-item>
          <el-descriptions-item label="统计天数">
            {{ statistics.days || 0 }} 天
          </el-descriptions-item>
          <el-descriptions-item label="平均dBZ">
            {{ statistics.avg_dbz?.toFixed(2) || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="最大dBZ">
            {{ statistics.max_dbz?.toFixed(2) || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="最小dBZ">
            {{ statistics.min_dbz?.toFixed(2) || '-' }}
          </el-descriptions-item>
        </el-descriptions>

        <el-divider>dBZ分类分布</el-divider>

        <div v-if="statistics.category_distribution">
          <el-row :gutter="20">
            <el-col
              v-for="(count, category) in statistics.category_distribution"
              :key="category"
              :span="6"
            >
              <el-card>
                <div class="category-stat">
                  <div class="category-name">{{ category }}</div>
                  <div class="category-count">{{ count }} 次</div>
                </div>
              </el-card>
            </el-col>
          </el-row>
        </div>
      </div>

      <template #footer>
        <el-button @click="statisticsDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh, DataAnalysis, FullScreen, Aim, Download } from '@element-plus/icons-vue'
import { dataApi, siteApi, type Site, type RadarData } from '@/api/modules'
import RadarImagePreview from '@/components/RadarImagePreview.vue'
import dayjs from 'dayjs'

const loading = ref(false)
const loadingStatistics = ref(false)
const statisticsDialogVisible = ref(false)
const isPreviewExpanded = ref(false)
const exporting = ref(false)

const sites = ref<Site[]>([])
const dataList = ref<RadarData[]>([])
const selectedRow = ref<RadarData | null>(null)

// 引用雷达预览组件
const radarPreviewRef = ref<InstanceType<typeof RadarImagePreview> | null>(null)

// 切换全屏预览
function toggleExpand() {
  isPreviewExpanded.value = !isPreviewExpanded.value
}

const queryForm = reactive({
  site_id: undefined as number | undefined,
  start_time: '',
  end_time: '',
  min_dbz: undefined as number | undefined,
  max_dbz: undefined as number | undefined
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const statistics = reactive({
  total_records: 0,
  days: 0,
  avg_dbz: 0,
  max_dbz: 0,
  min_dbz: 0,
  category_distribution: {} as Record<string, number>
})

// 处理行点击事件
function handleRowClick(row: RadarData) {
  selectedRow.value = row
}

// 加载站点列表
async function loadSites() {
  try {
    const response = await siteApi.getList({ page: 1, page_size: 100 })
    sites.value = response.data.data.items
  } catch (error) {
    console.error('Failed to load sites:', error)
  }
}

// 查询数据
async function handleQuery() {
  try {
    loading.value = true

    const params: any = {
      page: pagination.page,
      page_size: pagination.pageSize
    }

    if (queryForm.site_id) params.site_id = queryForm.site_id
    if (queryForm.start_time) params.start_time = queryForm.start_time
    if (queryForm.end_time) params.end_time = queryForm.end_time
    if (queryForm.min_dbz !== undefined) params.min_dbz = queryForm.min_dbz
    if (queryForm.max_dbz !== undefined) params.max_dbz = queryForm.max_dbz

    const response = await dataApi.query(params)

    dataList.value = response.data.data.items
    pagination.total = response.data.data.total

    if (dataList.value.length === 0) {
      ElMessage.info('未查询到数据，请调整查询条件')
    } else {
      // 查询成功后，自动播放当前站点的雷达图片
      if (queryForm.site_id && radarPreviewRef.value) {
        radarPreviewRef.value.playSiteImages(
          queryForm.site_id,
          queryForm.start_time,
          queryForm.end_time
        )
      }
    }
  } catch (error) {
    console.error('Failed to query data:', error)
  } finally {
    loading.value = false
  }
}

// 重置查询
function handleReset() {
  // 重置为默认站点和时间范围
  if (sites.value.length > 0) {
    const firstSite = sites.value[0]
    queryForm.site_id = firstSite.id
  }

  const now = dayjs()
  queryForm.end_time = now.format('YYYY-MM-DD HH:mm:ss')
  queryForm.start_time = now.subtract(24, 'hour').format('YYYY-MM-DD HH:mm:ss')
  queryForm.min_dbz = undefined
  queryForm.max_dbz = undefined
  pagination.page = 1
  dataList.value = []
  pagination.total = 0
  selectedRow.value = null

  // 重新执行查询
  handleQuery()
}

// 显示统计
async function handleShowStatistics() {
  if (!queryForm.site_id) {
    ElMessage.warning('请先选择站点')
    return
  }

  try {
    loadingStatistics.value = true
    statisticsDialogVisible.value = true

    const response = await dataApi.getStatistics({
      site_id: queryForm.site_id,
      days: 7
    })

    const stats = response.data.data.statistics || {}
    statistics.total_records = response.data.data.total_records
    statistics.days = response.data.data.days
    statistics.avg_dbz = stats.avg_dbz || 0
    statistics.max_dbz = stats.max_dbz || 0
    statistics.min_dbz = stats.min_dbz || 0
    statistics.category_distribution = stats.category_distribution || {}
  } catch (error) {
    console.error('Failed to load statistics:', error)
  } finally {
    loadingStatistics.value = false
  }
}

// 格式化日期时间
function formatDateTime(dateStr: string) {
  return dayjs(dateStr).format('YYYY-MM-DD HH:mm:ss')
}

// 获取dBZ标签类型
function getDbzTagType(dbz: number) {
  if (dbz >= 50) return 'danger'
  if (dbz >= 40) return 'warning'
  if (dbz >= 30) return 'success'
  if (dbz >= 20) return 'info'
  return ''
}

// 导出CSV - 直接使用表格中显示的数据
function handleExportCSV() {
  if (dataList.value.length === 0) {
    ElMessage.warning('没有数据可导出，请先查询数据')
    return
  }

  try {
    exporting.value = true

    // CSV 表头（与表格列一致）
    const headers = ['ID', '站点ID', '观测时间', 'dBZ值', '分类', '云影响系数', '像素坐标', '创建时间']

    // 构建 CSV 内容，使用表格中当前显示的数据
    const csvRows = [
      headers.join(','),
      ...dataList.value.map((item: any) => [
        item.id,
        item.site_id,
        formatDateTime(item.observation_time),
        item.dbz_value?.toFixed(1) || '',
        item.dbz_category || '',
        ((item.cloud_impact_factor || 0) * 100).toFixed(1) + '%',
        item.pixel_x !== undefined && item.pixel_y !== undefined ? `${item.pixel_x},${item.pixel_y}` : '',
        formatDateTime(item.created_at)
      ].join(','))
    ]

    const csvContent = csvRows.join('\n')
    const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })

    // 创建下载链接
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `雷达数据_${dayjs().format('YYYYMMDD_HHmmss')}.csv`

    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)

    URL.revokeObjectURL(url)

    ElMessage.success(`成功导出 ${dataList.value.length} 条数据`)
  } catch (error) {
    console.error('Failed to export CSV:', error)
    ElMessage.error('导出CSV失败')
  } finally {
    exporting.value = false
  }
}

onMounted(() => {
  loadSites().then(() => {
    // 自动选择第一个站点并查询
    if (sites.value.length > 0) {
      const firstSite = sites.value[0]
      queryForm.site_id = firstSite.id

      // 设置默认时间范围为最近24小时
      const now = dayjs()
      const endTime = now.format('YYYY-MM-DD HH:mm:ss')
      const startTime = now.subtract(24, 'hour').format('YYYY-MM-DD HH:mm:ss')

      queryForm.start_time = startTime
      queryForm.end_time = endTime

      // 自动执行查询
      handleQuery()
    }
  })
})
</script>

<style scoped>
.data-query-container {
  padding: 20px;
  position: relative;
}

/* 放大按钮 */
.expand-button {
  position: fixed;
  top: 100px;
  right: 30px;
  z-index: 1000;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.2);
}

.expand-button.expanded {
  top: 100px;
  right: 30px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.query-form {
  margin-bottom: 20px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.category-stat {
  text-align: center;
  padding: 10px 0;
}

.category-name {
  font-size: 14px;
  color: #606266;
  margin-bottom: 8px;
}

.category-count {
  font-size: 20px;
  font-weight: bold;
  color: #409eff;
}

/* 表格行点击高亮 */
:deep(.el-table__body tr:hover > td) {
  cursor: pointer;
}

:deep(.el-table__body tr.current-row > td) {
  background-color: #ecf5ff;
}
</style>
