<template>
  <div class="dashboard" v-loading="loading">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1>财务仪表盘</h1>
      <div class="period-selector">
        <el-date-picker
          v-model="currentPeriod"
          type="month"
          placeholder="选择月份"
          format="YYYY年MM月"
          value-format="YYYY-MM"
          @change="handlePeriodChange"
          style="width: 150px"
        />
      </div>
    </div>

    <!-- 概览卡片 -->
    <div class="overview-cards">
      <div class="card income-card">
        <div class="card-icon">💰</div>
        <div class="card-content">
          <div class="card-title">本月收入</div>
          <div class="card-amount">¥{{ monthlyIncome.toLocaleString() }}</div>
          <div class="card-trend" :class="{ 'positive': overview?.monthly_summary.income_growth > 0 }">
            <span v-if="overview?.monthly_summary.income_growth">
              {{ overview.monthly_summary.income_growth > 0 ? '↑' : '↓' }}
              {{ Math.abs(overview.monthly_summary.income_growth) }}%
            </span>
          </div>
        </div>
      </div>

      <div class="card expense-card">
        <div class="card-icon">💸</div>
        <div class="card-content">
          <div class="card-title">本月支出</div>
          <div class="card-amount">¥{{ monthlyExpense.toLocaleString() }}</div>
          <div class="card-trend" :class="{ 'negative': overview?.monthly_summary.expense_growth > 0 }">
            <span v-if="overview?.monthly_summary.expense_growth">
              {{ overview.monthly_summary.expense_growth > 0 ? '↑' : '↓' }}
              {{ Math.abs(overview.monthly_summary.expense_growth) }}%
            </span>
          </div>
        </div>
      </div>

      <div class="card balance-card">
        <div class="card-icon">📊</div>
        <div class="card-content">
          <div class="card-title">本月结余</div>
          <div class="card-amount" :class="{ 'negative': monthlyBalance < 0 }">
            ¥{{ monthlyBalance.toLocaleString() }}
          </div>
          <div class="card-desc">{{ overview?.period || '' }}</div>
        </div>
      </div>

      <div class="card total-card">
        <div class="card-icon">💎</div>
        <div class="card-content">
          <div class="card-title">总资产</div>
          <div class="card-amount">¥{{ totalBalance.toLocaleString() }}</div>
          <div class="card-desc">所有账户余额</div>
        </div>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="charts-section">
      <div class="chart-row">
        <!-- 支出趋势图 -->
        <div class="chart-container">
          <div class="chart-header">
            <h3>最近7天支出趋势</h3>
          </div>
          <LineChart
            :data="trendChartData"
            height="280px"
            :show-income="false"
            :show-expense="true"
            :show-balance="false"
            title=""
          />
        </div>

        <!-- 分类占比图 -->
        <div class="chart-container">
          <div class="chart-header">
            <h3>支出分类占比</h3>
          </div>
          <PieChart
            :data="categoryChartData"
            height="280px"
            title=""
            :show-legend="true"
          />
        </div>
      </div>
    </div>

    <!-- 快速操作 -->
    <div class="quick-actions">
      <div class="section-title">
        <h3>快速操作</h3>
      </div>
      <div class="action-buttons">
        <el-button type="primary" size="large" @click="$router.push('/transaction/add')">
          <el-icon><Plus /></el-icon>
          记一笔
        </el-button>
        <el-button size="large" @click="$router.push('/statistics')">
          <el-icon><DataAnalysis /></el-icon>
          查看统计
        </el-button>
        <el-button size="large" @click="$router.push('/budget')">
          <el-icon><Wallet /></el-icon>
          预算管理
        </el-button>
        <el-button size="large" @click="$router.push('/wechat/import')">
          <el-icon><Upload /></el-icon>
          导入账单
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useStatisticsStore } from '@/stores/statistics'
import LineChart from '@/components/charts/LineChart.vue'
import PieChart from '@/components/charts/PieChart.vue'
import { Plus, DataAnalysis, Wallet, Upload } from '@element-plus/icons-vue'

const statisticsStore = useStatisticsStore()

// 响应式数据
const currentPeriod = ref(new Date().toISOString().slice(0, 7)) // YYYY-MM

// 计算属性
const { loading, overview, monthlyIncome, monthlyExpense, monthlyBalance, totalBalance } = statisticsStore

// 趋势图数据
const trendChartData = computed(() => {
  if (!overview?.trend_data) return []
  return overview.trend_data.map(item => ({
    date: item.date,
    expense: item.amount,
    income: 0,
    balance: 0
  }))
})

// 分类图数据
const categoryChartData = computed(() => {
  if (!overview?.category_distribution) return []
  return overview.category_distribution.map(item => ({
    name: item.name,
    value: item.amount,
    color: item.color,
    icon: item.icon
  }))
})

// 方法
const handlePeriodChange = async (period: string) => {
  if (!period) return

  const [year, month] = period.split('-').map(Number)
  await statisticsStore.fetchOverview({
    current_year: year,
    current_month: month
  })
}

// 生命周期
onMounted(async () => {
  const [year, month] = currentPeriod.value.split('-').map(Number)
  await statisticsStore.fetchOverview({
    current_year: year,
    current_month: month
  })
})
</script>

<style scoped>
.dashboard {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.period-selector {
  display: flex;
  align-items: center;
}

/* 概览卡片 */
.overview-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  transition: transform 0.2s, box-shadow 0.2s;
}

.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.card-icon {
  font-size: 32px;
  margin-right: 16px;
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
}

.income-card .card-icon {
  background: rgba(82, 196, 26, 0.1);
}

.expense-card .card-icon {
  background: rgba(255, 77, 79, 0.1);
}

.balance-card .card-icon {
  background: rgba(24, 144, 255, 0.1);
}

.total-card .card-icon {
  background: rgba(250, 173, 20, 0.1);
}

.card-content {
  flex: 1;
}

.card-title {
  font-size: 14px;
  color: #6b7280;
  margin-bottom: 4px;
}

.card-amount {
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 4px;
}

.card-amount.negative {
  color: #ef4444;
}

.card-trend {
  font-size: 12px;
  color: #6b7280;
}

.card-trend.positive {
  color: #52c41a;
}

.card-trend.negative {
  color: #ff4d4f;
}

.card-desc {
  font-size: 12px;
  color: #9ca3af;
}

/* 图表区域 */
.charts-section {
  margin-bottom: 24px;
}

.chart-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.chart-container {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.chart-header {
  margin-bottom: 16px;
}

.chart-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

/* 快速操作 */
.quick-actions {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.section-title {
  margin-bottom: 20px;
}

.section-title h3 {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.action-buttons {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.action-buttons .el-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .overview-cards {
    grid-template-columns: 1fr;
  }

  .chart-row {
    grid-template-columns: 1fr;
  }

  .action-buttons {
    flex-direction: column;
  }

  .action-buttons .el-button {
    width: 100%;
    justify-content: center;
  }
}
</style>