<template>
  <div class="statistics-overview" v-loading="loading">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>统计分析</h2>
    </div>

    <!-- 筛选器 -->
    <div class="filters-section">
      <el-card class="filter-card">
        <div class="filter-row">
          <div class="filter-item">
            <label>统计类型</label>
            <el-select v-model="statisticsType" @change="handleTypeChange" style="width: 120px">
              <el-option label="收支趋势" value="trend" />
              <el-option label="分类统计" value="category" />
            </el-select>
          </div>

          <!-- 趋势分析筛选器 -->
          <template v-if="statisticsType === 'trend'">
            <div class="filter-item">
              <label>时间周期</label>
              <el-select v-model="trendPeriod" @change="handleTrendPeriodChange" style="width: 120px">
                <el-option label="按日" value="daily" />
                <el-option label="按周" value="weekly" />
                <el-option label="按月" value="monthly" />
                <el-option label="按年" value="yearly" />
              </el-select>
            </div>
            <div class="filter-item">
              <label>开始日期</label>
              <el-date-picker
                v-model="dateRange.start"
                type="date"
                placeholder="开始日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                @change="handleDateRangeChange"
              />
            </div>
            <div class="filter-item">
              <label>结束日期</label>
              <el-date-picker
                v-model="dateRange.end"
                type="date"
                placeholder="结束日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                @change="handleDateRangeChange"
              />
            </div>
          </template>

          <!-- 分类统计筛选器 -->
          <template v-if="statisticsType === 'category'">
            <div class="filter-item">
              <label>交易类型</label>
              <el-select v-model="categoryType" @change="handleCategoryTypeChange" style="width: 120px">
                <el-option label="支出" value="expense" />
                <el-option label="收入" value="income" />
              </el-select>
            </div>
            <div class="filter-item">
              <label>统计周期</label>
              <el-select v-model="categoryPeriod" @change="handleCategoryPeriodChange" style="width: 120px">
                <el-option label="按月" value="monthly" />
                <el-option label="按年" value="yearly" />
              </el-select>
            </div>
            <div class="filter-item">
              <label>年份</label>
              <el-select v-model="selectedYear" @change="handleYearChange" style="width: 120px">
                <el-option
                  v-for="year in availableYears"
                  :key="year"
                  :label="`${year}年`"
                  :value="year"
                />
              </el-select>
            </div>
            <div class="filter-item" v-if="categoryPeriod === 'monthly'">
              <label>月份</label>
              <el-select v-model="selectedMonth" @change="handleMonthChange" style="width: 120px">
                <el-option
                  v-for="month in 12"
                  :key="month"
                  :label="`${month}月`"
                  :value="month"
                />
              </el-select>
            </div>
          </template>

          <div class="filter-item">
            <el-button type="primary" @click="exportData" :loading="exporting">
              <el-icon><Download /></el-icon>
              导出Excel
            </el-button>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 趋势分析 -->
    <div v-if="statisticsType === 'trend'" class="trend-section">
      <el-card class="chart-card">
        <div class="chart-header">
          <h3>收支趋势分析</h3>
          <div class="chart-legend">
            <span class="legend-item income">
              <i class="legend-dot"></i>收入
            </span>
            <span class="legend-item expense">
              <i class="legend-dot"></i>支出
            </span>
            <span class="legend-item balance">
              <i class="legend-dot"></i>净收入
            </span>
          </div>
        </div>
        <LineChart
          :data="trendChartData"
          height="400px"
          :show-income="true"
          :show-expense="true"
          :show-balance="true"
          title=""
        />
      </el-card>
    </div>

    <!-- 分类统计 -->
    <div v-if="statisticsType === 'category'" class="category-section">
      <div class="category-charts">
        <el-card class="chart-card">
          <div class="chart-header">
            <h3>{{ categoryType === 'expense' ? '支出' : '收入' }}分类占比</h3>
          </div>
          <PieChart
            :data="categoryPieData"
            height="400px"
            title=""
            :show-legend="true"
          />
        </el-card>

        <el-card class="chart-card">
          <div class="chart-header">
            <h3>{{ categoryType === 'expense' ? '支出' : '收入' }}分类排行</h3>
          </div>
          <BarChart
            :data="categoryBarData"
            height="400px"
            title=""
            :horizontal="true"
            :show-value="true"
            :max-items="10"
          />
        </el-card>
      </div>

      <!-- 分类详情表格 -->
      <el-card class="table-card">
        <div class="chart-header">
          <h3>{{ categoryType === 'expense' ? '支出' : '收入' }}分类详情</h3>
        </div>
        <el-table :data="categoryTableData" stripe style="width: 100%">
          <el-table-column prop="icon" label="图标" width="60" align="center">
            <template #default="{ row }">
              <span style="font-size: 20px">{{ row.icon }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="name" label="分类名称" />
          <el-table-column prop="amount" label="金额" align="right" width="150">
            <template #default="{ row }">
              <span class="amount-text">¥{{ row.amount.toLocaleString() }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="count" label="笔数" align="center" width="100" />
          <el-table-column prop="percentage" label="占比" align="right" width="120">
            <template #default="{ row }">
              <span class="percentage-text">{{ row.percentage }}%</span>
            </template>
          </el-table-column>
          <el-table-column prop="average" label="平均金额" align="right" width="150">
            <template #default="{ row }">
              ¥{{ (row.amount / row.count).toLocaleString() }}
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useStatisticsStore } from '@/stores/statistics'
import { getCategoryStatistics, getTrend, exportExcel } from '@/api/statistics'
import LineChart from '@/components/charts/LineChart.vue'
import PieChart from '@/components/charts/PieChart.vue'
import BarChart from '@/components/charts/BarChart.vue'
import { Download } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const statisticsStore = useStatisticsStore()

// 响应式数据
const loading = ref(false)
const exporting = ref(false)
const statisticsType = ref('trend')

// 趋势分析相关
const trendPeriod = ref('monthly')
const dateRange = ref({
  start: '',
  end: ''
})

// 分类统计相关
const categoryType = ref('expense')
const categoryPeriod = ref('monthly')
const selectedYear = ref(new Date().getFullYear())
const selectedMonth = ref(new Date().getMonth() + 1)

// 可选年份
const availableYears = computed(() => {
  const currentYear = new Date().getFullYear()
  return Array.from({ length: 5 }, (_, i) => currentYear - i)
})

// 计算属性
const { trendData, categoryStats } = statisticsStore

// 趋势图数据
const trendChartData = computed(() => {
  return trendData.map(item => ({
    date: item.date,
    income: item.income,
    expense: item.expense,
    balance: item.balance
  }))
})

// 分类饼图数据
const categoryPieData = computed(() => {
  if (!categoryStats?.categories) return []
  return categoryStats.categories.map(item => ({
    name: item.name,
    value: item.amount,
    color: item.color,
    icon: item.icon
  }))
})

// 分类柱状图数据
const categoryBarData = computed(() => {
  if (!categoryStats?.categories) return []
  return categoryStats.categories.map(item => ({
    name: item.name,
    value: item.amount,
    color: item.color
  }))
})

// 分类表格数据
const categoryTableData = computed(() => {
  if (!categoryStats?.categories) return []
  return categoryStats.categories.map(item => ({
    ...item,
    average: item.amount / item.count
  }))
})

// 方法
const handleTypeChange = () => {
  if (statisticsType.value === 'trend') {
    loadTrendData()
  } else {
    loadCategoryData()
  }
}

const handleTrendPeriodChange = () => {
  loadTrendData()
}

const handleDateRangeChange = () => {
  loadTrendData()
}

const handleCategoryTypeChange = () => {
  loadCategoryData()
}

const handleCategoryPeriodChange = () => {
  loadCategoryData()
}

const handleYearChange = () => {
  loadCategoryData()
}

const handleMonthChange = () => {
  loadCategoryData()
}

const loadTrendData = async () => {
  try {
    loading.value = true
    await statisticsStore.fetchTrend({
      period: trendPeriod.value as any,
      start_date: dateRange.value.start || undefined,
      end_date: dateRange.value.end || undefined
    })
  } catch (error) {
    ElMessage.error('加载趋势数据失败')
  } finally {
    loading.value = false
  }
}

const loadCategoryData = async () => {
  try {
    loading.value = true
    await statisticsStore.fetchCategoryStatistics({
      transaction_type: categoryType.value as any,
      period: categoryPeriod.value as any,
      year: selectedYear.value,
      month: categoryPeriod.value === 'monthly' ? selectedMonth.value : undefined
    })
  } catch (error) {
    ElMessage.error('加载分类数据失败')
  } finally {
    loading.value = false
  }
}

const exportData = async () => {
  try {
    exporting.value = true

    const params = {
      transaction_type: (statisticsType.value === 'category' ? categoryType.value : 'all') as 'income' | 'expense' | 'all',
      start_date: dateRange.value.start || new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().slice(0, 10),
      end_date: dateRange.value.end || new Date().toISOString().slice(0, 10)
    }

    const response = await exportExcel(params)
    ElMessage.success('导出成功')

    // 下载文件
    const link = document.createElement('a')
    link.href = `/api/download/${response.data.data.filename}`
    link.download = response.data.data.filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  } catch (error) {
    ElMessage.error('导出失败')
  } finally {
    exporting.value = false
  }
}

// 生命周期
onMounted(() => {
  // 初始化默认数据
  const now = new Date()
  const sixMonthsAgo = new Date(now.getFullYear(), now.getMonth() - 6, 1)

  dateRange.value = {
    start: sixMonthsAgo.toISOString().slice(0, 10),
    end: now.toISOString().slice(0, 10)
  }

  loadTrendData()
})
</script>

<style scoped>
.statistics-overview {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 100vh;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

/* 筛选器 */
.filters-section {
  margin-bottom: 24px;
}

.filter-card {
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.filter-row {
  display: flex;
  gap: 20px;
  align-items: end;
  flex-wrap: wrap;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-item label {
  font-size: 14px;
  color: #374151;
  font-weight: 500;
}

/* 图表区域 */
.trend-section,
.category-section {
  margin-bottom: 24px;
}

.chart-card {
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.chart-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.chart-legend {
  display: flex;
  gap: 20px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: #6b7280;
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.legend-item.income .legend-dot {
  background-color: #52c41a;
}

.legend-item.expense .legend-dot {
  background-color: #ff4d4f;
}

.legend-item.balance .legend-dot {
  background-color: #1890ff;
}

/* 分类图表 */
.category-charts {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 24px;
}

/* 表格 */
.table-card {
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.amount-text {
  font-weight: 600;
  color: #1f2937;
}

.percentage-text {
  font-weight: 600;
  color: #1890ff;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .filter-row {
    flex-direction: column;
    align-items: stretch;
  }

  .filter-item {
    width: 100%;
  }

  .category-charts {
    grid-template-columns: 1fr;
  }

  .chart-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
}
</style>
