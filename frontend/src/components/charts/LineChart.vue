<template>
  <div ref="chartRef" class="line-chart" :style="{ width, height }"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import type { ECOption } from '@/types/common'

interface DataItem {
  date: string
  income?: number
  expense?: number
  balance?: number
  value?: number
}

interface Props {
  data: DataItem[]
  width?: string
  height?: string
  title?: string
  showIncome?: boolean
  showExpense?: boolean
  showBalance?: boolean
  smooth?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  width: '100%',
  height: '300px',
  title: '',
  showIncome: true,
  showExpense: true,
  showBalance: false,
  smooth: true
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

  const dates = props.data.map(item => item.date)

  const series: any[] = []

  if (props.showIncome) {
    series.push({
      name: '收入',
      type: 'line',
      data: props.data.map(item => item.income || 0),
      smooth: props.smooth,
      itemStyle: {
        color: '#52c41a'
      },
      areaStyle: {
        opacity: 0.3,
        color: {
          type: 'linear',
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [{
            offset: 0, color: 'rgba(82, 196, 26, 0.3)'
          }, {
            offset: 1, color: 'rgba(82, 196, 26, 0.05)'
          }]
        }
      }
    })
  }

  if (props.showExpense) {
    series.push({
      name: '支出',
      type: 'line',
      data: props.data.map(item => item.expense || 0),
      smooth: props.smooth,
      itemStyle: {
        color: '#ff4d4f'
      },
      areaStyle: {
        opacity: 0.3,
        color: {
          type: 'linear',
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [{
            offset: 0, color: 'rgba(255, 77, 79, 0.3)'
          }, {
            offset: 1, color: 'rgba(255, 77, 79, 0.05)'
          }]
        }
      }
    })
  }

  if (props.showBalance) {
    series.push({
      name: '净收入',
      type: 'line',
      data: props.data.map(item => item.balance || item.value || 0),
      smooth: props.smooth,
      itemStyle: {
        color: '#1890ff'
      }
    })
  }

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
        type: 'cross',
        label: {
          backgroundColor: '#6a7985'
        }
      },
      formatter: (params: any) => {
        let html = `<div>${params[0].axisValue}</div>`
        params.forEach((param: any) => {
          html += `<div style="margin: 2px 0">
            <span style="display:inline-block;margin-right:5px;border-radius:10px;width:10px;height:10px;background-color:${param.color}"></span>
            ${param.seriesName}: ¥${param.value.toLocaleString()}
          </div>`
        })
        return html
      }
    },
    legend: {
      data: series.map(s => s.name),
      top: props.title ? 30 : 10,
      right: 20
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: props.title ? 80 : 60,
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: dates,
      axisLine: {
        lineStyle: {
          color: '#e0e0e0'
        }
      },
      axisLabel: {
        color: '#666'
      }
    },
    yAxis: {
      type: 'value',
      axisLine: {
        lineStyle: {
          color: '#e0e0e0'
        }
      },
      axisLabel: {
        color: '#666',
        formatter: (value: number) => `¥${value.toLocaleString()}`
      },
      splitLine: {
        lineStyle: {
          color: '#f0f0f0'
        }
      }
    },
    series
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
.line-chart {
  width: 100%;
  height: 100%;
}
</style>