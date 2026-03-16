<template>
  <div ref="chartRef" class="line-chart" :style="{ height: height, width: width }"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import type { EChartsOption } from 'echarts'

interface Props {
  option: EChartsOption
  height?: string
  width?: string
}

const props = withDefaults(defineProps<Props>(), {
  height: '400px',
  width: '100%'
})

const chartRef = ref<HTMLDivElement>()
let chartInstance: echarts.ECharts | null = null

function initChart() {
  if (!chartRef.value) return

  chartInstance = echarts.init(chartRef.value)
  chartInstance.setOption(props.option)
}

function resizeChart() {
  chartInstance?.resize()
}

watch(
  () => props.option,
  (newOption) => {
    chartInstance?.setOption(newOption, true)
  },
  { deep: true }
)

onMounted(() => {
  initChart()
  window.addEventListener('resize', resizeChart)
})

onUnmounted(() => {
  chartInstance?.dispose()
  window.removeEventListener('resize', resizeChart)
})

defineExpose({
  resize: resizeChart,
  getInstance: () => chartInstance
})
</script>

<style scoped>
.line-chart {
  min-height: 300px;
}
</style>
