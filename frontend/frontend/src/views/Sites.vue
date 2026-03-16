<template>
  <div class="sites-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>气象站点管理</span>
          <el-button type="primary" :icon="Plus" @click="handleCreate">
            新建站点
          </el-button>
        </div>
      </template>

      <!-- 搜索表单 -->
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="站点名称">
          <el-input
            v-model="searchForm.station_name"
            placeholder="请输入站点名称"
            clearable
            @clear="handleSearch"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">
            搜索
          </el-button>
          <el-button :icon="Refresh" @click="handleReset">
            重置
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 站点表格 -->
      <el-table
        v-loading="loading"
        :data="siteList"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="station_name" label="站点名称" min-width="150" />
        <el-table-column prop="station_id" label="站点代码" width="120" />
        <el-table-column prop="region" label="区域" width="100" />
        <el-table-column label="位置" width="200">
          <template #default="{ row }">
            <span>{{ row.longitude?.toFixed(4) }}, {{ row.latitude?.toFixed(4) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="station_type" label="站点类型" width="100" />
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : row.status === 'disabled' ? 'info' : 'danger'">
              {{ row.status === 'active' ? '启用' : row.status === 'disabled' ? '禁用' : '异常' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="handleView(row)">查看</el-button>
            <el-button size="small" type="primary" @click="handleEdit(row)">
              编辑
            </el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadSites"
          @current-change="loadSites"
        />
      </div>
    </el-card>

    <!-- 站点表单对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
      @close="handleDialogClose"
    >
      <el-form
        ref="siteFormRef"
        :model="siteForm"
        :rules="siteRules"
        label-width="120px"
      >
        <el-form-item label="站点名称" prop="station_name">
          <el-input v-model="siteForm.station_name" placeholder="请输入站点名称" />
        </el-form-item>

        <el-form-item label="站点代码" prop="station_id">
          <el-input v-model="siteForm.station_id" placeholder="请输入站点代码" />
        </el-form-item>

        <el-form-item label="经度" prop="longitude">
          <el-input-number
            v-model="siteForm.longitude"
            :min="-180"
            :max="180"
            :precision="6"
            :step="0.0001"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="纬度" prop="latitude">
          <el-input-number
            v-model="siteForm.latitude"
            :min="-90"
            :max="90"
            :precision="6"
            :step="0.0001"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="区域" prop="region">
          <el-select v-model="siteForm.region" placeholder="请选择区域" style="width: 100%">
            <el-option label="华北" value="华北" />
            <el-option label="华东" value="华东" />
            <el-option label="华南" value="华南" />
            <el-option label="华中" value="华中" />
            <el-option label="西南" value="西南" />
            <el-option label="西北" value="西北" />
            <el-option label="东北" value="东北" />
          </el-select>
        </el-form-item>

        <el-form-item label="地址" prop="address">
          <el-input
            v-model="siteForm.address"
            type="textarea"
            :rows="2"
            placeholder="请输入站点地址"
          />
        </el-form-item>

        <el-form-item label="站点类型" prop="station_type">
          <el-input v-model="siteForm.station_type" placeholder="请输入站点类型" />
        </el-form-item>

        <el-form-item label="最大重试次数" prop="max_retries">
          <el-input-number
            v-model="siteForm.max_retries"
            :min="0"
            :max="10"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="状态" prop="status">
          <el-select v-model="siteForm.status" placeholder="请选择状态" style="width: 100%">
            <el-option label="启用" value="active" />
            <el-option label="禁用" value="disabled" />
            <el-option label="异常" value="error" />
          </el-select>
        </el-form-item>

        <el-form-item label="备注" prop="remark">
          <el-input
            v-model="siteForm.remark"
            type="textarea"
            :rows="3"
            placeholder="请输入备注"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Search, Refresh } from '@element-plus/icons-vue'
import { siteApi, type Site } from '@/api/modules'

const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const dialogTitle = ref('')
const siteFormRef = ref<FormInstance>()

const searchForm = reactive({
  station_name: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const siteList = ref<Site[]>([])

const siteForm = reactive<Partial<Site>>({
  station_name: '',
  station_id: '',
  longitude: 0,
  latitude: 0,
  address: '',
  region: '',
  station_type: '',
  max_retries: 3,
  status: 'active',
  remark: ''
})

const siteRules: FormRules = {
  station_name: [{ required: true, message: '请输入站点名称', trigger: 'blur' }],
  station_id: [{ required: true, message: '请输入站点代码', trigger: 'blur' }],
  longitude: [{ required: true, message: '请输入经度', trigger: 'blur' }],
  latitude: [{ required: true, message: '请输入纬度', trigger: 'blur' }]
}

// 加载站点列表
async function loadSites() {
  try {
    loading.value = true
    const params: any = {
      page: pagination.page,
      page_size: pagination.pageSize
    }
    if (searchForm.station_name) {
      params.station_name = searchForm.station_name
    }

    const response = await siteApi.getList(params)

    siteList.value = response.data.data.items
    pagination.total = response.data.data.total
  } catch (error) {
    console.error('Failed to load sites:', error)
  } finally {
    loading.value = false
  }
}

// 搜索
function handleSearch() {
  pagination.page = 1
  loadSites()
}

// 重置
function handleReset() {
  searchForm.station_name = ''
  pagination.page = 1
  loadSites()
}

// 新建
function handleCreate() {
  dialogTitle.value = '新建站点'
  Object.assign(siteForm, {
    station_name: '',
    station_id: '',
    longitude: 0,
    latitude: 0,
    address: '',
    region: '',
    station_type: '',
    max_retries: 3,
    status: 'active',
    remark: ''
  })
  // Clear id for new record
  delete (siteForm as any).id
  dialogVisible.value = true
}

// 查看
function handleView(row: Site) {
  const statusText = row.status === 'active' ? '启用' : row.status === 'disabled' ? '禁用' : '异常'
  ElMessageBox.alert(
    `
    <p><strong>站点名称：</strong>${row.station_name}</p>
    <p><strong>站点代码：</strong>${row.station_id}</p>
    <p><strong>位置：</strong>${row.longitude?.toFixed(4)}, ${row.latitude?.toFixed(4)}</p>
    <p><strong>区域：</strong>${row.region || '-'}</p>
    <p><strong>地址：</strong>${row.address || '-'}</p>
    <p><strong>站点类型：</strong>${row.station_type || '-'}</p>
    <p><strong>状态：</strong>${statusText}</p>
    <p><strong>重试次数：</strong>${row.retry_count || 0} / ${row.max_retries || 3}</p>
    <p><strong>最后同步：</strong>${row.last_sync_time || '-'}</p>
    <p><strong>最后同步状态：</strong>${row.last_sync_status || '-'}</p>
    ${row.last_error_message ? `<p><strong>错误信息：</strong>${row.last_error_message}</p>` : ''}
    <p><strong>备注：</strong>${row.remark || '-'}</p>
    `,
    '站点详情',
    {
      dangerouslyUseHTMLString: true,
      confirmButtonText: '关闭'
    }
  )
}

// 编辑
function handleEdit(row: Site) {
  dialogTitle.value = '编辑站点'
  Object.assign(siteForm, row)
  dialogVisible.value = true
}

// 删除
async function handleDelete(row: Site) {
  try {
    await ElMessageBox.confirm(
      `确定要删除站点"${row.station_name}"吗？`,
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await siteApi.delete(row.id)
    ElMessage.success('删除成功')
    loadSites()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('Failed to delete site:', error)
    }
  }
}

// 提交表单
async function handleSubmit() {
  if (!siteFormRef.value) return

  try {
    await siteFormRef.value.validate()
    submitting.value = true

    if ((siteForm as any).id) {
      // 编辑
      await siteApi.update((siteForm as any).id, siteForm)
      ElMessage.success('更新成功')
    } else {
      // 新建
      await siteApi.create(siteForm)
      ElMessage.success('创建成功')
    }

    dialogVisible.value = false
    loadSites()
  } catch (error) {
    console.error('Failed to submit site:', error)
  } finally {
    submitting.value = false
  }
}

// 关闭对话框
function handleDialogClose() {
  if (siteFormRef.value) {
    siteFormRef.value.resetFields()
  }
}

onMounted(() => {
  loadSites()
})
</script>

<style scoped>
.sites-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-form {
  margin-bottom: 20px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
