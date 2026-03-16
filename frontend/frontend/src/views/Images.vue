<template>
  <div class="images-page">
    <el-card class="header-card">
      <template #header>
        <div class="card-header">
          <span class="title">
            <el-icon><Picture /></el-icon>
            雷达图片管理
          </span>
        </div>
      </template>

      <!-- 统计信息 -->
      <el-row :gutter="20" v-loading="statsLoading">
        <el-col :span="6" v-for="stat in statistics" :key="stat.label">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-value">{{ stat.value }}</div>
              <div class="stat-label">{{ stat.label }}</div>
            </div>
            <div class="stat-icon" :class="stat.type">
              <el-icon><component :is="stat.icon" /></el-icon>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 筛选和排序 -->
      <el-form :inline="true" :model="queryForm" class="filter-form">
        <el-form-item label="排序字段">
          <el-select v-model="queryForm.sort_by" @change="fetchImages">
            <el-option label="观测时间" value="observation_time" />
            <el-option label="下载时间" value="download_time" />
            <el-option label="文件大小" value="file_size" />
          </el-select>
        </el-form-item>

        <el-form-item label="排序方向">
          <el-select v-model="queryForm.sort_order" @change="fetchImages">
            <el-option label="降序" value="desc" />
            <el-option label="升序" value="asc" />
          </el-select>
        </el-form-item>

        <el-form-item label="状态">
          <el-select v-model="queryForm.status" @change="fetchImages" clearable>
            <el-option label="全部" value="" />
            <el-option label="成功" value="success" />
            <el-option label="失败" value="failed" />
            <el-option label="待处理" value="pending" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="fetchImages" :icon="Refresh">
            刷新
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 图片列表 -->
    <el-card class="images-card">
      <el-table
        :data="images"
        v-loading="loading"
        stripe
        style="width: 100%"
        @sort-change="handleSortChange"
      >
        <el-table-column type="index" label="#" width="60" />

        <el-table-column label="预览" width="120">
          <template #default="{ row }">
            <el-image
              v-if="row.download_status === 'success'"
              :src="getPreviewUrl(row.id)"
              fit="cover"
              class="image-thumbnail"
              :preview-src-list="previewImages"
              :initial-index="getPreviewIndex(row.id)"
              preview-teleported
            >
              <template #error>
                <div class="image-error">
                  <el-icon><PictureFilled /></el-icon>
                </div>
              </template>
            </el-image>
            <el-tag v-else type="danger" size="small">失败</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="original_filename" label="原始文件名" min-width="250">
          <template #default="{ row }">
            <el-tooltip :content="row.original_filename" placement="top">
              <span class="filename-text">{{ row.original_filename || row.filename }}</span>
            </el-tooltip>
          </template>
        </el-table-column>

        <el-table-column prop="observation_time" label="观测时间" width="180" sortable>
          <template #default="{ row }">
            {{ formatDateTime(row.observation_time) }}
          </template>
        </el-table-column>

        <el-table-column prop="original_time_str" label="原始时间" width="140">
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ row.original_time_str || '-' }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="file_size" label="文件大小" width="100" sortable>
          <template #default="{ row }">
            {{ row.file_size ? formatFileSize(row.file_size) : '-' }}
          </template>
        </el-table-column>

        <el-table-column prop="download_time" label="下载时间" width="180" sortable>
          <template #default="{ row }">
            {{ row.download_time ? formatDateTime(row.download_time) : '-' }}
          </template>
        </el-table-column>

        <el-table-column prop="download_status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag v-if="row.download_status === 'success'" type="success" size="small">
              成功
            </el-tag>
            <el-tag v-else-if="row.download_status === 'failed'" type="danger" size="small">
              失败
            </el-tag>
            <el-tag v-else type="warning" size="small">
              待处理
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.download_status === 'success'"
              type="primary"
              size="small"
              @click="previewImage(row)"
            >
              预览
            </el-button>
            <el-button
              type="danger"
              size="small"
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 图片预览对话框 -->
    <el-dialog
      v-model="previewDialogVisible"
      title="图片预览"
      width="80%"
      center
    >
      <div class="preview-container" v-if="currentImage">
        <el-descriptions :column="2" border class="image-info">
          <el-descriptions-item label="文件名">
            {{ currentImage.original_filename || currentImage.filename }}
          </el-descriptions-item>
          <el-descriptions-item label="观测时间">
            {{ formatDateTime(currentImage.observation_time) }}
          </el-descriptions-item>
          <el-descriptions-item label="原始时间">
            {{ currentImage.original_time_str || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="文件大小">
            {{ currentImage.file_size ? formatFileSize(currentImage.file_size) : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="下载时间">
            {{ currentImage.download_time ? formatDateTime(currentImage.download_time) : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="MD5">
            {{ currentImage.md5_hash || '-' }}
          </el-descriptions-item>
        </el-descriptions>

        <div class="preview-image-wrapper">
          <el-image
            :src="getPreviewUrl(currentImage.id)"
            fit="contain"
            class="preview-image"
          >
            <template #error>
              <div class="image-error-large">
                <el-icon :size="100"><PictureFilled /></el-icon>
                <p>图片加载失败</p>
              </div>
            </template>
          </el-image>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Picture,
  PictureFilled,
  Refresh,
  Download,
  DataLine,
  SuccessFilled,
  CircleCloseFilled,
  Clock
} from '@element-plus/icons-vue'
import { imageApi, type RadarImage } from '@/api/modules'

// 数据
const loading = ref(false)
const statsLoading = ref(false)
const images = ref<RadarImage[]>([])
const statistics = ref([
  { label: '总图片', value: 0, icon: DataLine, type: 'primary' },
  { label: '成功', value: 0, icon: SuccessFilled, type: 'success' },
  { label: '失败', value: 0, icon: CircleCloseFilled, type: 'danger' },
  { label: '总大小', value: '0 MB', icon: Download, type: 'warning' }
])

const queryForm = reactive({
  sort_by: 'observation_time',
  sort_order: 'desc',
  status: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const previewDialogVisible = ref(false)
const currentImage = ref<RadarImage | null>(null)

// 计算属性
const previewImages = computed(() => {
  return images.value
    .filter(img => img.download_status === 'success')
    .map(img => imageApi.getPreviewUrl(img.id))
})

// 方法
const fetchImages = async () => {
  loading.value = true
  try {
    const response = await imageApi.getList({
      page: pagination.page,
      page_size: pagination.pageSize,
      sort_by: queryForm.sort_by,
      sort_order: queryForm.sort_order,
      status: queryForm.status || undefined
    })

    if (response.data.code === 200) {
      const data = response.data.data
      images.value = data.items
      pagination.total = data.total
    }
  } catch (error) {
    ElMessage.error('获取图片列表失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

const fetchStatistics = async () => {
  statsLoading.value = true
  try {
    const response = await imageApi.getStatistics()
    if (response.data.code === 200) {
      const stats = response.data.data
      statistics.value[0].value = stats.total_images
      statistics.value[1].value = stats.success_count
      statistics.value[2].value = stats.failed_count
      statistics.value[3].value = `${stats.total_size_mb} MB`
    }
  } catch (error) {
    console.error('获取统计信息失败', error)
  } finally {
    statsLoading.value = false
  }
}

const handlePageChange = (page: number) => {
  pagination.page = page
  fetchImages()
}

const handleSizeChange = (size: number) => {
  pagination.pageSize = size
  pagination.page = 1
  fetchImages()
}

const handleSortChange = () => {
  // Element Plus表格排序
  fetchImages()
}

const handleDelete = async (image: RadarImage) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除图片 "${image.original_filename || image.filename}" 吗？`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const response = await imageApi.delete(image.id)
    if (response.data.code === 200) {
      ElMessage.success('删除成功')
      fetchImages()
      fetchStatistics()
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
      console.error(error)
    }
  }
}

const previewImage = (image: RadarImage) => {
  currentImage.value = image
  previewDialogVisible.value = true
}

const getPreviewUrl = (id: number) => {
  return imageApi.getPreviewUrl(id)
}

const getPreviewIndex = (id: number) => {
  return previewImages.value.findIndex(url => url.includes(`/images/${id}/preview`))
}

const formatDateTime = (dateTime: string) => {
  if (!dateTime) return '-'
  return new Date(dateTime).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatFileSize = (bytes: number) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

// 生命周期
onMounted(() => {
  fetchImages()
  fetchStatistics()
})
</script>

<style scoped>
.images-page {
  padding: 20px;
}

.header-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  font-size: 18px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.stat-card {
  position: relative;
  overflow: hidden;
}

.stat-content {
  padding: 10px;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.stat-icon {
  position: absolute;
  right: 20px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 40px;
  opacity: 0.2;
}

.stat-icon.primary {
  color: #409eff;
}

.stat-icon.success {
  color: #67c23a;
}

.stat-icon.danger {
  color: #f56c6c;
}

.stat-icon.warning {
  color: #e6a23c;
}

.filter-form {
  margin-top: 20px;
}

.images-card {
  min-height: 400px;
}

.image-thumbnail {
  width: 80px;
  height: 80px;
  border-radius: 4px;
  cursor: pointer;
}

.image-error {
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f5f7fa;
  color: #909399;
  font-size: 24px;
}

.filename-text {
  display: inline-block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.preview-container {
  padding: 20px;
}

.image-info {
  margin-bottom: 20px;
}

.preview-image-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
  background-color: #f5f7fa;
  border-radius: 4px;
  padding: 20px;
}

.preview-image {
  max-width: 100%;
  max-height: 70vh;
}

.image-error-large {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #909399;
}

.image-error-large p {
  margin-top: 10px;
  font-size: 16px;
}
</style>
