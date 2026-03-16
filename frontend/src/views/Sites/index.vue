<template>
  <div class="sites-page">
    <div class="page-header">
      <h2>站点管理</h2>
      <el-button type="primary" :icon="'Plus'" @click="showAddDialog">
        添加站点
      </el-button>
    </div>

    <!-- 搜索表单 -->
    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm">
        <el-form-item label="站点名称">
          <el-input v-model="searchForm.name" placeholder="请输入站点名称" clearable />
        </el-form-item>
        <el-form-item label="区域">
          <el-input v-model="searchForm.region" placeholder="请输入区域" clearable />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.is_active" placeholder="请选择" clearable>
            <el-option label="启用" :value="true" />
            <el-option label="禁用" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadSites">查询</el-button>
          <el-button @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 站点列表 -->
    <el-card class="table-card">
      <el-table :data="sites" v-loading="loading" border stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="站点名称" min-width="120" />
        <el-table-column prop="code" label="站点编码" width="120" />
        <el-table-column prop="longitude" label="经度" width="100" />
        <el-table-column prop="latitude" label="纬度" width="100" />
        <el-table-column prop="region" label="区域" width="100" />
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewDetail(row)">查看</el-button>
            <el-button size="small" type="primary" @click="editSite(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteSite(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadSites"
          @current-change="loadSites"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { siteApi } from '../../api'
import type { Site } from '../../types/site'

const router = useRouter()

const loading = ref(false)
const sites = ref<Site[]>([])

const searchForm = reactive({
  name: '',
  region: '',
  is_active: undefined as boolean | undefined
})

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

function formatTime(time: string): string {
  return new Date(time).toLocaleString('zh-CN')
}

async function loadSites() {
  loading.value = true
  try {
    const response = await siteApi.getSites({
      page: pagination.page,
      page_size: pagination.page_size,
      ...searchForm
    })

    sites.value = response.data.items
    pagination.total = response.data.total
  } catch (error) {
    console.error('Failed to load sites:', error)
    ElMessage.error('加载站点列表失败')
  } finally {
    loading.value = false
  }
}

function resetSearch() {
  searchForm.name = ''
  searchForm.region = ''
  searchForm.is_active = undefined
  pagination.page = 1
  loadSites()
}

function showAddDialog() {
  ElMessage.info('添加站点功能开发中...')
}

function viewDetail(site: Site) {
  router.push(`/sites/${site.id}`)
}

function editSite(site: Site) {
  ElMessage.info('编辑站点功能开发中...')
}

async function deleteSite(site: Site) {
  try {
    await ElMessageBox.confirm(`确定要删除站点 "${site.name}" 吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await siteApi.deleteSite(site.id)
    ElMessage.success('删除成功')
    loadSites()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete site:', error)
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  loadSites()
})
</script>

<style scoped>
.sites-page {
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

.search-card {
  margin-bottom: 20px;
}

.table-card {
  min-height: 400px;
}

.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>
