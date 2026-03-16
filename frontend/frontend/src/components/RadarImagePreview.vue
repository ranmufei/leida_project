<template>
  <div class="radar-preview-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>雷达图片预览 - 站点定位</span>
          <div class="header-actions">
            <!-- 校准模式控制 -->
            <template v-if="!calibrationMode">
              <el-button
                type="warning"
                size="small"
                :icon="Aim"
                @click="startCalibrationMode"
                style="margin-right: 10px"
              >
                标注控制点
              </el-button>
            </template>
            <template v-else>
              <el-button
                type="info"
                size="small"
                @click="exitCalibrationMode"
                style="margin-right: 10px"
              >
                退出校准
              </el-button>
              <el-button
                type="success"
                size="small"
                @click="executeCalibration"
                :loading="calibrating"
                :disabled="controlPoints.length < 3"
                style="margin-right: 10px"
              >
                执行校准 ({{ controlPoints.length }}/3)
              </el-button>
            </template>

            <!-- 自动播放控制 -->
            <el-switch
              v-model="autoPlay"
              active-text="自动播放"
              inactive-text="手动"
              @change="handleAutoPlayChange"
              style="margin-right: 10px"
            />
            <!-- 播放速度控制 -->
            <el-select
              v-model="playSpeed"
              size="small"
              style="width: 100px; margin-right: 10px"
              @change="handleSpeedChange"
            >
              <el-option label="0.5x" :value="2000" />
              <el-option label="1x" :value="1000" />
              <el-option label="2x" :value="500" />
              <el-option label="5x" :value="200" />
            </el-select>
            <!-- 手动控制按钮 -->
            <el-button-group style="margin-right: 10px">
              <el-button
                size="small"
                :icon="VideoPause"
                @click="pausePlay"
                :disabled="!autoPlay"
              >
                暂停
              </el-button>
              <el-button
                size="small"
                :icon="VideoPlay"
                @click="startPlay"
                :disabled="autoPlay"
              >
                播放
              </el-button>
              <el-button
                size="small"
                @click="previousImage"
                :disabled="imageList.length === 0"
              >
                上一张
              </el-button>
              <el-button
                size="small"
                @click="nextImage"
                :disabled="imageList.length === 0"
              >
                下一张
              </el-button>
            </el-button-group>
            <el-button
              type="primary"
              size="small"
              :icon="Refresh"
              @click="refreshImage"
              :loading="loading"
            >
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <!-- 播放进度条 -->
      <div v-if="imageList.length > 0" class="playback-progress">
        <div class="progress-info">
          <span>{{ currentImageIndex + 1 }} / {{ imageList.length }}</span>
          <span>{{ formatDateTime(currentImage.observation_time) }}</span>
        </div>
        <el-progress
          :percentage="progressPercentage"
          :show-text="false"
          style="margin-top: 5px"
        />
      </div>

      <div v-if="!selectedData && !autoPlay && imageList.length === 0" class="no-selection">
        <el-empty description="请在左侧表格中选择一条数据查看雷达图片定位" />
      </div>

      <div v-else class="preview-content">
        <!-- 坐标映射信息 -->
        <div class="coordinate-mapping-info" v-if="selectedData">
          <el-alert
            title="坐标映射关系"
            type="info"
            :closable="false"
            show-icon
          >
            <template #default>
              <div class="mapping-details">
                <div class="mapping-item">
                  <span class="mapping-label">🌍 经纬度坐标:</span>
                  <span class="mapping-value">
                    经度 {{ selectedData.longitude?.toFixed(6) || '-' }}°,
                    纬度 {{ selectedData.latitude?.toFixed(6) || '-' }}°
                  </span>
                </div>
                <div class="mapping-item">
                  <span class="mapping-label">📍 像素坐标:</span>
                  <span class="mapping-value">
                    X: {{ selectedData.pixel_x || '-' }},
                    Y: {{ selectedData.pixel_y || '-' }}
                  </span>
                </div>
              </div>
            </template>
          </el-alert>
        </div>

        <!-- 图片详细信息 -->
        <div class="image-info" v-if="selectedData">
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="站点ID">
              {{ selectedData.site_id }}
            </el-descriptions-item>
            <el-descriptions-item label="观测时间">
              {{ formatDateTime(selectedData.observation_time) }}
            </el-descriptions-item>
            <el-descriptions-item label="dBZ值">
              <el-tag :type="getDbzTagType(selectedData.dbz_value)">
                {{ selectedData.dbz_value?.toFixed(1) || '-' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="RGB值">
              {{ selectedData.rgb_value || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="数据质量">
              <el-tag :type="selectedData.data_quality === 'good' ? 'success' : 'warning'">
                {{ selectedData.data_quality || '-' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="云影响系数">
              {{ ((selectedData.cloud_impact_factor || 0) * 100).toFixed(1) }}%
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <!-- 雷达图片显示区域 -->
        <div class="radar-image-wrapper" v-loading="loading">
          <!-- 校准模式提示 -->
          <div v-if="calibrationMode" class="calibration-mode-alert">
            <el-alert
              title="校准模式：请在地图上点击标注控制点"
              type="warning"
              :closable="false"
              show-icon
            >
              <template #default>
                <p>已标注 {{ controlPoints.length }} 个控制点，至少需要3个</p>
                <p style="font-size: 12px; color: #666;">点击地图位置后输入对应的经纬度坐标</p>
              </template>
            </el-alert>
          </div>

          <div class="image-container" @click="handleImageClick">
            <img
              ref="radarImage"
              :src="imageUrl"
              @load="onImageLoad"
              @error="onImageError"
              alt="雷达图片"
              class="radar-image"
            />

            <!-- 十字准线辅助线 -->
            <div
              v-if="hasValidCoordinates"
              class="crosshair-h"
              :style="{ top: `${selectedData.pixel_y}px` }"
            ></div>
            <div
              v-if="hasValidCoordinates"
              class="crosshair-v"
              :style="{ left: `${selectedData.pixel_x}px` }"
            ></div>

            <!-- 站点标记 -->
            <div
              v-if="hasValidCoordinates"
              class="site-marker"
              :style="{
                left: `${selectedData.pixel_x}px`,
                top: `${selectedData.pixel_y}px`
              }"
            >
              <div class="marker-dot"></div>
              <div class="marker-ring"></div>
              <div class="marker-info">
                <div class="info-title">站点 {{ selectedData.site_id }}</div>
                <div class="info-coords">
                  <div>经度: {{ selectedData.longitude?.toFixed(6) || '-' }}°</div>
                  <div>纬度: {{ selectedData.latitude?.toFixed(6) || '-' }}°</div>
                  <div>像素: ({{ selectedData.pixel_x }}, {{ selectedData.pixel_y }})</div>
                </div>
              </div>
            </div>

            <!-- 控制点标记（校准模式下显示） -->
            <div
              v-for="cp in controlPoints"
              :key="cp.id"
              class="control-point-marker"
              :style="{
                left: `${cp.pixel_x}px`,
                top: `${cp.pixel_y}px`
              }"
            >
              <div class="cp-marker-cross">
                <div class="cp-cross-h"></div>
                <div class="cp-cross-v"></div>
              </div>
              <div class="cp-marker-label">{{ cp.name }}</div>
            </div>
          </div>
        </div>

        <!-- 控制点列表（校准模式下显示） -->
        <div v-if="calibrationMode || controlPoints.length > 0" class="control-points-panel">
          <div class="panel-header">
            <span>已标注控制点 ({{ controlPoints.length }})</span>
            <el-button
              v-if="controlPoints.length > 0"
              type="danger"
              size="small"
              @click="async () => { for (const cp of controlPoints) { await deleteControlPoint(cp.id) } }"
            >
              清空全部
            </el-button>
          </div>
          <el-table :data="controlPoints" size="small" max-height="200">
            <el-table-column prop="name" label="名称" width="120" />
            <el-table-column label="像素坐标" width="100">
              <template #default="{ row }">
                ({{ row.pixel_x }}, {{ row.pixel_y }})
              </template>
            </el-table-column>
            <el-table-column label="经纬度" width="150">
              <template #default="{ row }">
                {{ row.longitude.toFixed(4) }}, {{ row.latitude.toFixed(4) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="80">
              <template #default="{ row }">
                <el-button
                  type="danger"
                  size="small"
                  link
                  @click="deleteControlPoint(row.id)"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- 图例说明 -->
        <div class="legend-info">
          <el-collapse>
            <el-collapse-item title="dBZ色标图例 (中国气象局标准)" name="1">
              <div class="color-legend">
                <div class="legend-item">
                  <span class="color-box" style="background: rgb(0, 0, 0);"></span>
                  <span>无回波 (0-5 dBZ)</span>
                </div>
                <div class="legend-item">
                  <span class="color-box" style="background: rgb(78, 156, 240);"></span>
                  <span>极弱回波 (5-10 dBZ)</span>
                </div>
                <div class="legend-item">
                  <span class="color-box" style="background: rgb(100, 230, 234);"></span>
                  <span>弱回波 (10-15 dBZ)</span>
                </div>
                <div class="legend-item">
                  <span class="color-box" style="background: rgb(109, 251, 61);"></span>
                  <span>中低回波 (15-20 dBZ)</span>
                </div>
                <div class="legend-item">
                  <span class="color-box" style="background: rgb(78, 216, 0);"></span>
                  <span>中等回波 (20-25 dBZ)</span>
                </div>
                <div class="legend-item">
                  <span class="color-box" style="background: rgb(49, 145, 0);"></span>
                  <span>中高回波 (25-30 dBZ)</span>
                </div>
                <div class="legend-item">
                  <span class="color-box" style="background: rgb(250, 255, 0);"></span>
                  <span>强回波 (30-35 dBZ)</span>
                </div>
                <div class="legend-item">
                  <span class="color-box" style="background: rgb(231, 204, 2);"></span>
                  <span>很强回波 (35-40 dBZ)</span>
                </div>
                <div class="legend-item">
                  <span class="color-box" style="background: rgb(241, 143, 5);"></span>
                  <span>严重回波 (40-45 dBZ)</span>
                </div>
                <div class="legend-item">
                  <span class="color-box" style="background: rgb(237, 0, 5);"></span>
                  <span>极端回波 (45-50 dBZ)</span>
                </div>
                <div class="legend-item">
                  <span class="color-box" style="background: rgb(214, 0, 0);"></span>
                  <span>剧烈回波 (50-55 dBZ)</span>
                </div>
                <div class="legend-item">
                  <span class="color-box" style="background: rgb(192, 0, 0);"></span>
                  <span>剧烈回波 (55-60 dBZ)</span>
                </div>
                <div class="legend-item">
                  <span class="color-box" style="background: rgb(242, 2, 240);"></span>
                  <span>剧烈回波 (60-65 dBZ)</span>
                </div>
                <div class="legend-item">
                  <span class="color-box" style="background: rgb(150, 0, 181);"></span>
                  <span>剧烈回波 (65-70 dBZ)</span>
                </div>
                <div class="legend-item">
                  <span class="color-box" style="background: rgb(173, 145, 240);"></span>
                  <span>最大回波 (70+ dBZ)</span>
                </div>
              </div>
            </el-collapse-item>
          </el-collapse>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, VideoPlay, VideoPause, Aim } from '@element-plus/icons-vue'
import { imageApi, calibrationApi, type ControlPointData } from '@/api/modules'
import type { RadarData } from '@/api/modules'
import dayjs from 'dayjs'

interface Props {
  selectedData: RadarData | null
  isExpanded?: boolean
  siteIdForPlay?: number | null  // 新增：用于指定播放的站点ID
}

const props = withDefaults(defineProps<Props>(), {
  isExpanded: false,
  siteIdForPlay: null
})

const loading = ref(false)
const imageUrl = ref('')
const radarImage = ref<HTMLImageElement>()

// 自动播放相关
const autoPlay = ref(true) // 默认开启自动播放
const playSpeed = ref(1000) // 默认1x速度
const imageList = ref<any[]>([])
const currentImageIndex = ref(0)
const playTimer = ref<number | null>(null)
const currentImage = ref<any>(null)

// 校准模式相关
const calibrationMode = ref(false)
const controlPoints = ref<ControlPointData[]>([])
const calibrating = ref(false)

// 检查是否有有效的坐标
const hasValidCoordinates = computed(() => {
  return props.selectedData &&
         props.selectedData.pixel_x !== undefined &&
         props.selectedData.pixel_y !== undefined &&
         props.selectedData.pixel_x !== null &&
         props.selectedData.pixel_y !== null
})

// 计算播放进度
const progressPercentage = computed(() => {
  if (imageList.value.length === 0) return 0
  return ((currentImageIndex.value + 1) / imageList.value.length) * 100
})

// 获取最近24小时的雷达图片列表（支持分页获取所有图片）
const fetchRecentImages = async (showError: boolean = false) => {
  try {
    loading.value = true
    const allImages: any[] = []
    let page = 1
    const pageSize = 300 // 使用更大的page_size

    // 循环获取所有图片
    while (true) {
      const response = await imageApi.getList({
        page: page,
        page_size: pageSize,
        sort_by: 'observation_time',
        sort_order: 'asc' // 按时间升序，方便播放
      })

      if (response.data.data.items.length === 0) {
        break
      }

      // 过滤出成功下载的图片
      const successImages = response.data.data.items
        .filter((img: any) => img.download_status === 'success')

      allImages.push(...successImages)

      // 如果返回的图片少于page_size，说明已经是最后一页了
      if (response.data.data.items.length < pageSize) {
        break
      }

      page++
    }

    // 只保留最近24小时的图片
    const now = new Date()
    const twentyFourHoursAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000)

    imageList.value = allImages.filter((img: any) => {
      const obsTime = new Date(img.observation_time)
      return obsTime >= twentyFourHoursAgo
    })

    console.log(`获取到 ${imageList.value.length} 张最近24小时的雷达图片`)

    // 从第一张开始播放
    if (imageList.value.length > 0) {
      currentImageIndex.value = 0
      showImage(currentImageIndex.value)
    }
  } catch (error) {
    console.error('Failed to fetch recent images:', error)
    if (showError) {
      ElMessage.error('加载雷达图片列表失败')
    }
    // 静默失败，不显示错误消息
    imageList.value = []
  } finally {
    loading.value = false
  }
}

// 显示指定索引的图片
const showImage = (index: number) => {
  if (index < 0 || index >= imageList.value.length) return

  currentImageIndex.value = index
  currentImage.value = imageList.value[index]
  imageUrl.value = imageApi.getPreviewUrl(imageList.value[index].id)
}

// 下一张图片
const nextImage = () => {
  if (imageList.value.length === 0) return

  let nextIndex = currentImageIndex.value + 1
  if (nextIndex >= imageList.value.length) {
    nextIndex = 0 // 循环播放
  }
  showImage(nextIndex)
}

// 上一张图片
const previousImage = () => {
  if (imageList.value.length === 0) return

  let prevIndex = currentImageIndex.value - 1
  if (prevIndex < 0) {
    prevIndex = imageList.value.length - 1
  }
  showImage(prevIndex)
}

// 开始自动播放
const startPlay = () => {
  autoPlay.value = true
  startTimer()
}

// 暂停播放
const pausePlay = () => {
  autoPlay.value = false
  stopTimer()
}

// 启动定时器
const startTimer = () => {
  stopTimer() // 先清除已有的定时器
  playTimer.value = window.setInterval(() => {
    nextImage()
  }, playSpeed.value)
}

// 停止定时器
const stopTimer = () => {
  if (playTimer.value !== null) {
    clearInterval(playTimer.value)
    playTimer.value = null
  }
}

// 处理自动播放开关变化
const handleAutoPlayChange = (enabled: boolean) => {
  if (enabled) {
    startTimer()
  } else {
    stopTimer()
  }
}

// 处理播放速度变化
const handleSpeedChange = () => {
  if (autoPlay.value) {
    // 重新启动定时器以应用新速度
    startTimer()
  }
}

// 刷新图片
const refreshImage = () => {
  fetchRecentImages()
}

// 为指定站点加载并播放图片
const playSiteImages = async (siteId: number, queryStartTime?: string, queryEndTime?: string) => {
  try {
    loading.value = true
    stopTimer() // 停止当前播放

    console.log(`为站点 ${siteId} 加载图片...`)

    // 获取所有雷达图片
    const allImages: any[] = []
    let page = 1
    const pageSize = 300

    while (true) {
      const response = await imageApi.getList({
        page: page,
        page_size: pageSize,
        sort_by: 'observation_time',
        sort_order: 'asc'
      })

      if (response.data.data.items.length === 0) break

      const successImages = response.data.data.items
        .filter((img: any) => img.download_status === 'success')
      allImages.push(...successImages)

      if (response.data.data.items.length < pageSize) break
      page++
    }

    // 如果指定了时间范围，进行过滤
    let filteredImages = allImages
    if (queryStartTime && queryEndTime) {
      const startTime = new Date(queryStartTime)
      const endTime = new Date(queryEndTime)
      filteredImages = allImages.filter((img: any) => {
        const obsTime = new Date(img.observation_time)
        return obsTime >= startTime && obsTime <= endTime
      })
    }

    imageList.value = filteredImages
    console.log(`为站点 ${siteId} 加载了 ${imageList.value.length} 张图片`)

    if (imageList.value.length > 0) {
      currentImageIndex.value = 0
      showImage(0)
      autoPlay.value = true
      startTimer()
    } else {
      ElMessage.info('该时间段没有找到雷达图片')
    }
  } catch (error) {
    console.error('Failed to load site images:', error)
    ElMessage.error('加载站点图片失败')
  } finally {
    loading.value = false
  }
}

// 暴露方法给父组件
defineExpose({
  playSiteImages
})

// 图片加载完成
const onImageLoad = () => {
  console.log('雷达图片加载成功，使用原始尺寸显示')
  if (radarImage.value) {
    const naturalWidth = radarImage.value.naturalWidth
    const naturalHeight = radarImage.value.naturalHeight
    console.log('图片原始尺寸:', { width: naturalWidth, height: naturalHeight })

    // 确保 image-container 的大小与图片原始尺寸一致
    const container = radarImage.value.parentElement
    if (container) {
      container.style.width = `${naturalWidth}px`
      container.style.height = `${naturalHeight}px`
      console.log('✅ 已设置 image-container 尺寸为图片原始尺寸')
    }
  }
}

// 图片加载错误
const onImageError = () => {
  // 静默处理图片加载错误，不显示错误提示
  console.log('雷达图片加载失败，将自动跳过')
  loading.value = false
  // 自动跳过到下一张图片
  if (autoPlay.value && imageList.value.length > 0) {
    nextImage()
  }
}

// 格式化日期时间
const formatDateTime = (dateStr: string) => {
  return dayjs(dateStr).format('YYYY-MM-DD HH:mm:ss')
}

// 获取dBZ标签类型
const getDbzTagType = (dbz: number) => {
  if (dbz >= 50) return 'danger'
  if (dbz >= 40) return 'warning'
  if (dbz >= 30) return 'success'
  if (dbz >= 20) return 'info'
  return ''
}

// ========== 校准相关方法 ==========

// 开始校准模式
const startCalibrationMode = () => {
  calibrationMode.value = true
  autoPlay.value = false
  pausePlay()
  ElMessage.info('已进入校准模式，请在地图上点击标注控制点')
}

// 退出校准模式
const exitCalibrationMode = () => {
  calibrationMode.value = false
}

// 加载控制点列表
const loadControlPoints = async () => {
  try {
    console.log('正在加载控制点...')
    const response = await calibrationApi.getControlPoints()
    console.log('控制点API响应:', response)
    const items = response.data.data.items
    console.log('控制点列表:', items)

    // 检查图片容器的实际大小
    if (radarImage.value) {
      const container = radarImage.value.parentElement
      console.log('📦 图片容器信息:', {
        container_size: container ? { width: container.offsetWidth, height: container.offsetHeight } : null,
        image_natural_size: { width: radarImage.value.naturalWidth, height: radarImage.value.naturalHeight },
        image_display_size: { width: radarImage.value.width, height: radarImage.value.height },
        control_points: items.map((cp: any) => ({
          id: cp.id,
          name: cp.name,
          pixel: `(${cp.pixel_x}, ${cp.pixel_y})`,
          geo: `(${cp.longitude}, ${cp.latitude})`
        }))
      })
    }

    controlPoints.value = items
    console.log('已设置 controlPoints.value, 长度:', controlPoints.value.length)
  } catch (error) {
    console.error('加载控制点失败:', error)
  }
}

// 处理图片点击事件（校准模式下采集控制点）
const handleImageClick = async (event: MouseEvent) => {
  if (!calibrationMode.value) return

  // 使用图片元素获取正确的边界，并考虑缩放比例
  if (!radarImage.value) return

  const naturalWidth = radarImage.value.naturalWidth
  const naturalHeight = radarImage.value.naturalHeight

  // 底部图例区域高度（像素）
  const LEGEND_HEIGHT = 120

  // 获取 image-container 的边界矩形（因为控制点标记是相对于它定位的）
  const container = radarImage.value.parentElement
  if (!container) return

  const containerRect = container.getBoundingClientRect()

  // 计算鼠标相对于容器左上角的坐标
  const relativeX = event.clientX - containerRect.left
  const relativeY = event.clientY - containerRect.top

  // 检查点击是否在容器范围内
  if (relativeX < 0 || relativeX > containerRect.width ||
      relativeY < 0 || relativeY > containerRect.height) {
    console.warn('⚠️ 点击位置超出容器范围')
    return
  }

  // 直接使用相对坐标作为像素坐标（因为容器大小等于图片原始尺寸）
  const pixelX = Math.round(relativeX)
  const pixelY = Math.round(relativeY)

  // 边界检查
  const finalPixelX = Math.max(0, Math.min(pixelX, naturalWidth - 1))
  const finalPixelY = Math.max(0, Math.min(pixelY, naturalHeight - 1))

  // 检查是否点击在底部图例区域
  const mapHeight = naturalHeight - LEGEND_HEIGHT
  if (finalPixelY > mapHeight) {
    ElMessage.warning(`请点击地图区域，不要点击底部图例区域（Y坐标应小于${mapHeight}）`)
    console.warn(`⚠️ 点击位置在图例区域: pixel_y=${finalPixelY} > map_height=${mapHeight}`)
    return
  }

  console.log('🖱️ 点击坐标详情:', {
    event: { clientX: event.clientX, clientY: event.clientY },
    containerRect: { left: containerRect.left, top: containerRect.top, width: containerRect.width, height: containerRect.height },
    relative: { x: relativeX, y: relativeY },
    pixel_raw: { x: pixelX, y: pixelY },
    pixel_final: { x: finalPixelX, y: finalPixelY },
    natural_size: { width: naturalWidth, height: naturalHeight },
    map_height: mapHeight
  })

  try {
    const { value } = await ElMessageBox.prompt(
      '请输入该位置的经纬度（格式: 经度,纬度，例如: 116.4074,39.9042）',
      `标注控制点 #${controlPoints.value.length + 1}`,
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputPattern: /^-?\d+(\.\d+)?,-?\d+(\.\d+)?$/,
        inputErrorMessage: '请输入正确的经纬度格式（例如: 116.4074,39.9042）'
      }
    )

    if (value) {
      const [lon, lat] = value.split(',').map(Number)
      const name = `控制点${controlPoints.value.length + 1}`

      await calibrationApi.addControlPoint({
        pixel_x: finalPixelX,
        pixel_y: finalPixelY,
        longitude: lon,
        latitude: lat,
        name
      })

      ElMessage.success(`控制点 "${name}" 已添加`)
      await loadControlPoints()
    }
  } catch (error) {
    // 用户取消或输入错误，不做处理
  }
}

// 执行校准
const executeCalibration = async () => {
  if (controlPoints.value.length < 3) {
    ElMessage.warning(`至少需要3个控制点进行校准，当前只有${controlPoints.value.length}个`)
    return
  }

  try {
    calibrating.value = true
    const response = await calibrationApi.calibrate()

    if (response.data.data.success) {
      ElMessage.success('校准完成！请刷新页面验证定位准确性')

      // 显示误差信息
      const errors = response.data.data.errors || []
      if (errors.length > 0) {
        const avgErrorLon = errors.reduce((sum: number, e: any) => sum + e.error_lon, 0) / errors.length
        const avgErrorLat = errors.reduce((sum: number, e: any) => sum + e.error_lat, 0) / errors.length
        ElMessage.info(`平均误差: 经度 ${avgErrorLon.toFixed(6)}°, 纬度 ${avgErrorLat.toFixed(6)}°`)
      }

      calibrationMode.value = false
    }
  } catch (error) {
    ElMessage.error('校准失败')
    console.error('Calibration error:', error)
  } finally {
    calibrating.value = false
  }
}

// 删除控制点
const deleteControlPoint = async (id: number) => {
  try {
    await calibrationApi.deleteControlPoint(id)
    ElMessage.success('控制点已删除')
    await loadControlPoints()
  } catch (error) {
    ElMessage.error('删除失败')
    console.error('Delete control point error:', error)
  }
}

// 组件挂载时加载控制点
// 查找最接近指定时间的图片索引
const findClosestImageIndex = (targetTime: Date): number => {
  if (imageList.value.length === 0) return 0

  let closestIndex = 0
  let minDiff = Math.abs(new Date(imageList.value[0].observation_time).getTime() - targetTime.getTime())

  for (let i = 1; i < imageList.value.length; i++) {
    const diff = Math.abs(new Date(imageList.value[i].observation_time).getTime() - targetTime.getTime())
    if (diff < minDiff) {
      minDiff = diff
      closestIndex = i
    }
  }

  return closestIndex
}

// 监听选中数据变化
watch(() => props.selectedData, (newData) => {
  if (newData) {
    // 用户选择了站点数据，自动跳转到对应时间的图片
    const targetTime = new Date(newData.observation_time)
    const closestIndex = findClosestImageIndex(targetTime)

    console.log(`跳转到最接近的图片: 索引 ${closestIndex}, 时间 ${imageList.value[closestIndex]?.observation_time}`)

    showImage(closestIndex)

    // 暂停自动播放，让用户查看定位
    pausePlay()
  }
})

// 组件挂载时启动自动播放
onMounted(() => {
  loadControlPoints()
  fetchRecentImages(false)  // 不显示错误消息
  if (autoPlay.value) {
    startTimer()
  }
})

// 组件卸载时清理定时器
onUnmounted(() => {
  stopTimer()
})
</script>

<style scoped>
.radar-preview-container {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.header-actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.no-selection {
  padding: 40px 0;
  text-align: center;
}

.preview-content {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

/* 播放进度 */
.playback-progress {
  margin-bottom: 15px;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 4px;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: #606266;
  margin-bottom: 5px;
}

/* 坐标映射信息 */
.coordinate-mapping-info {
  margin-bottom: 5px;
}

.mapping-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 8px;
}

.mapping-item {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
}

.mapping-label {
  font-weight: bold;
  color: #409eff;
  min-width: 120px;
}

.mapping-value {
  color: #333;
  font-family: 'Courier New', monospace;
}

.image-info {
  margin-bottom: 5px;
}

.radar-image-wrapper {
  position: relative;
  width: 100%;
  min-height: 400px;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #f5f5f5;
  border-radius: 4px;
  overflow: auto;
  padding: 20px;
}

.image-container {
  position: relative;
  display: inline-block;
}

/* 关键：图片使用原始尺寸，不缩放 */
.radar-image {
  display: block;
  width: auto;
  height: auto;
  border: 1px solid #ddd;
  border-radius: 4px;
}

/* 十字准线 */
.crosshair-h,
.crosshair-v {
  position: absolute;
  background: rgba(255, 0, 0, 0.3);
  pointer-events: none;
  z-index: 5;
}

.crosshair-h {
  left: 0;
  right: 0;
  height: 1px;
  border-top: 1px dashed rgba(255, 0, 0, 0.5);
}

.crosshair-v {
  top: 0;
  bottom: 0;
  width: 1px;
  border-left: 1px dashed rgba(255, 0, 0, 0.5);
}

/* 站点标记 */
.site-marker {
  position: absolute;
  transform: translate(-50%, -50%);
  z-index: 10;
  pointer-events: none;
}

.marker-dot {
  width: 12px;
  height: 12px;
  background: #ff0000;
  border: 2px solid #ffffff;
  border-radius: 50%;
  box-shadow: 0 0 0 2px rgba(255, 0, 0, 0.5),
              0 2px 4px rgba(0, 0, 0, 0.3);
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation: dot-pulse 2s infinite;
}

@keyframes dot-pulse {
  0%, 100% {
    box-shadow: 0 0 0 2px rgba(255, 0, 0, 0.5),
                0 2px 4px rgba(0, 0, 0, 0.3);
  }
  50% {
    box-shadow: 0 0 0 6px rgba(255, 0, 0, 0.3),
                0 2px 8px rgba(0, 0, 0, 0.4);
  }
}

.marker-ring {
  width: 24px;
  height: 24px;
  border: 2px solid #ff0000;
  border-radius: 50%;
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  opacity: 0.6;
  animation: ring-expand 2s infinite;
}

@keyframes ring-expand {
  0% {
    width: 24px;
    height: 24px;
    opacity: 0.6;
  }
  100% {
    width: 48px;
    height: 48px;
    opacity: 0;
  }
}

.marker-info {
  position: absolute;
  top: 30px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0, 0, 0, 0.9);
  color: #fff;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 12px;
  white-space: nowrap;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
  min-width: 200px;
}

.info-title {
  font-weight: bold;
  font-size: 13px;
  margin-bottom: 6px;
  padding-bottom: 6px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.3);
  color: #409eff;
}

.info-coords {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-family: 'Courier New', monospace;
  font-size: 11px;
  line-height: 1.4;
}

/* 控制点标记 */
.control-point-marker {
  position: absolute;
  transform: translate(-50%, -50%);
  z-index: 15;
  pointer-events: none;
}

.cp-marker-cross {
  position: relative;
  width: 20px;
  height: 20px;
}

.cp-cross-h {
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 2px;
  background: #00ff00;
  transform: translateY(-50%);
}

.cp-cross-v {
  position: absolute;
  left: 50%;
  top: 0;
  bottom: 0;
  width: 2px;
  background: #00ff00;
  transform: translateX(-50%);
}

.cp-marker-label {
  position: absolute;
  top: 12px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0, 255, 0, 0.9);
  color: #000;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 11px;
  font-weight: bold;
  white-space: nowrap;
}

/* 校准模式提示 */
.calibration-mode-alert {
  margin-bottom: 10px;
}

/* 控制点面板 */
.control-points-panel {
  margin-top: 15px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 10px;
  background: #fafafa;
}

.control-points-panel .panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  font-weight: bold;
}

.legend-info {
  margin-top: 10px;
}

.color-legend {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 10px;
  padding: 10px 0;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.color-box {
  width: 30px;
  height: 20px;
  border: 1px solid #ccc;
  border-radius: 2px;
  flex-shrink: 0;
}
</style>
