<template>
  <div ref="chartRef" class="pie-chart" :style="{ width, height }"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import type { ECOption } from '@/types/common'

interface Props {
  data: Array<{
    name: string
    value: number
    color?: string
    icon?: string
  }>
  width?: string
  height?: string
  showLegend?: boolean
  showTooltip?: boolean
  title?: string
}

const props = withDefaults(defineProps<Props>(), {
  width: '100%',
  height: '300px',
  showLegend: true,
  showTooltip: true,
  title: ''
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
    tooltip: props.showTooltip ? {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)'
    } : undefined,
    legend: props.showLegend ? {
      orient: 'vertical',
      right: 10,
      top: 'center',
      formatter: (name: string) => {
        const item = props.data.find(d => d.name === name)
        return item?.icon ? `${item.icon} ${name}` : name
      }
    } : undefined,
    series: [
      {
        name: props.title || '分类统计',
        type: 'pie',
        radius: props.showLegend ? ['40%', '70%'] : '60%',
        center: props.showLegend ? ['35%', '50%'] : ['50%', '50%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 6,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: !props.showLegend,
          position: 'outside',
          formatter: '{b}: {d}%'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 16,
            fontWeight: 'bold'
          }
        },
        data: props.data.map(item => ({
          name: item.name,
          value: item.value,
          itemStyle: {
            color: item.color || '#999'
          }
        }))
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
.pie-chart {
  width: 100%;
  height: 100%;
}
</style>