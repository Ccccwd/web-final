<template>
  <div ref="chartRef" class="bar-chart" :style="{ width, height }"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import type { ECOption } from '@/types/common'

interface DataItem {
  name: string
  value: number
  color?: string
}

interface Props {
  data: DataItem[]
  width?: string
  height?: string
  title?: string
  horizontal?: boolean
  showValue?: boolean
  maxItems?: number
}

const props = withDefaults(defineProps<Props>(), {
  width: '100%',
  height: '300px',
  title: '',
  horizontal: false,
  showValue: true,
  maxItems: 10
})

const chartRef = ref<HTMLElement>()
let chartInstance: echarts.ECharts | null = null

const initChart = () => {
  if (!chartRef.value) return

  chartInstance = echarts.init(chartRef.value)
  updateChart()
}

const updateChart = () => {
  if (!chartInstance) return

  // 限制显示数量，取前N项
  const displayData = props.data.slice(0, props.maxItems)
  const names = displayData.map(item => item.name)
  const values = displayData.map(item => item.value)

  const option: ECOption = {
    title: props.title ? {
      text: props.title,
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 'bold',
        color: '#333'
      }
    } : undefined,
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      formatter: (params: any) => {
        const param = Array.isArray(params) ? params[0] : params
        return `${param.name}<br/>${param.seriesName}: ¥${param.value.toLocaleString()}`
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: props.title ? 80 : 60,
      containLabel: true
    },
    xAxis: {
      type: props.horizontal ? 'value' : 'category',
      data: props.horizontal ? undefined : names,
      axisLine: {
        lineStyle: {
          color: '#e0e0e0'
        }
      },
      axisLabel: {
        color: '#666',
        rotate: props.horizontal ? 0 : (names.length > 6 ? 45 : 0),
        formatter: props.horizontal ? (value: number) => `¥${value.toLocaleString()}` : undefined
      }
    },
    yAxis: {
      type: props.horizontal ? 'category' : 'value',
      data: props.horizontal ? names : undefined,
      axisLine: {
        lineStyle: {
          color: '#e0e0e0'
        }
      },
      axisLabel: {
        color: '#666',
        formatter: props.horizontal ? undefined : (value: number) => `¥${value.toLocaleString()}`
      },
      splitLine: {
        lineStyle: {
          color: '#f0f0f0'
        }
      }
    },
    series: [
      {
        name: '金额',
        type: 'bar',
        data: values.map((value, index) => ({
          value,
          itemStyle: {
            color: displayData[index].color || '#1890ff',
            borderRadius: props.horizontal ? [0, 4, 4, 0] : [4, 4, 0, 0]
          }
        })),
        barWidth: '60%',
        label: props.showValue ? {
          show: true,
          position: props.horizontal ? 'right' : 'top',
          formatter: (params: any) => `¥${params.value.toLocaleString()}`,
          color: '#666',
          fontSize: 12
        } : undefined
      }
    ]
  }

  chartInstance.setOption(option)
}

const resizeChart = () => {
  if (chartInstance) {
    chartInstance.resize()
  }
}

// 监听数据变化
watch(() => props.data, () => {
  nextTick(() => {
    updateChart()
  })
}, { deep: true })

// 监听窗口大小变化
const handleResize = () => {
  resizeChart()
}

onMounted(() => {
  nextTick(() => {
    initChart()
    window.addEventListener('resize', handleResize)
  })
})

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.bar-chart {
  width: 100%;
  height: 100%;
}
</style>