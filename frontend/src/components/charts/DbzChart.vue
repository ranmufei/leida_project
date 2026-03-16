<template>
  <div ref="chartRef" class="dbz-chart" :style="{ height: height, width: width }"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onUnmounted, computed } from 'vue'
import * as echarts from 'echarts'
import type { EChartsOption } from 'echarts'

interface DataPoint {
  observation_time: string
  dbz_value: number
  data_source?: 'actual' | 'predicted'
  confidence_lower?: number
  confidence_upper?: number
}

interface Props {
  data: DataPoint[]
  title?: string
  height?: string
  width?: string
  showConfidence?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  title: 'dBZ值变化趋势',
  height: '400px',
  width: '100%',
  showConfidence: true
})

const chartRef = ref<HTMLDivElement>()
let chartInstance: echarts.ECharts | null = null

const chartOption = computed<EChartsOption>(() => {
  // 分离实际数据和预测数据
  const actualData = props.data.filter(d => d.data_source === 'actual' || !d.data_source)
  const predictedData = props.data.filter(d => d.data_source === 'predicted')

  // X轴时间点
  const xData = props.data.map(d => {
    const date = new Date(d.observation_time)
    return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
  })

  // 实际dBZ值
  const actualValues = actualData.map(d => d.dbz_value)

  // 预测dBZ值
  const predictedValues = predictedData.map(d => d.dbz_value)

  // 置信区间
  const confidenceLower = predictedData.map(d => d.confidence_lower ?? d.dbz_value)
  const confidenceUpper = predictedData.map(d => d.confidence_upper ?? d.dbz_value)

  return {
    title: {
      text: props.title,
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 'bold'
      }
    },
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        let result = `${params[0].axisValue}<br/>`
        params.forEach((param: any) => {
          result += `${param.marker} ${param.seriesName}: ${param.value} dBZ<br/>`
        })
        return result
      }
    },
    legend: {
      data: ['实际值', '预测值', '置信区间'],
      top: 30
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: xData,
      axisLabel: {
        rotate: 45
      }
    },
    yAxis: {
      type: 'value',
      name: 'dBZ',
      min: 0,
      max: 75
    },
    series: [
      {
        name: '实际值',
        type: 'line',
        data: actualValues,
        smooth: true,
        lineStyle: {
          width: 2,
          color: '#409EFF'
        },
        itemStyle: {
          color: '#409EFF'
        }
      },
      {
        name: '预测值',
        type: 'line',
        data: predictedValues,
        smooth: true,
        lineStyle: {
          width: 2,
          type: 'dashed',
          color: '#67C23A'
        },
        itemStyle: {
          color: '#67C23A'
        }
      },
      ...(props.showConfidence && predictedData.length > 0 ? [
        {
          name: '置信区间',
          type: 'line',
          data: confidenceUpper,
          lineStyle: {
            opacity: 0
          },
          stack: 'confidence',
          areaStyle: {
            color: 'rgba(103, 194, 58, 0.1)'
          },
          showSymbol: false
        } as any,
        {
          name: '置信区间下界',
          type: 'line',
          data: confidenceLower,
          lineStyle: {
            opacity: 0
          },
          stack: 'confidence',
          areaStyle: {
            color: 'rgba(103, 194, 58, 0.2)'
          },
          showSymbol: false
        } as any
      ] : [])
    ]
  }
})

function initChart() {
  if (!chartRef.value) return

  chartInstance = echarts.init(chartRef.value)
  chartInstance.setOption(chartOption.value)
}

function resizeChart() {
  chartInstance?.resize()
}

watch(
  () => [props.data, props.title, props.showConfidence],
  () => {
    chartInstance?.setOption(chartOption.value, true)
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
.dbz-chart {
  min-height: 300px;
}
</style>
