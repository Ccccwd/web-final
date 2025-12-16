<template>
  <div class="budget-management" v-loading="loading">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>预算管理</h2>
      <div class="header-actions">
        <el-button type="primary" @click="showCreateDialog = true">
          <el-icon><Plus /></el-icon>
          添加预算
        </el-button>
        <el-button @click="refreshData">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 筛选器 -->
    <div class="filters-section">
      <el-card class="filter-card">
        <div class="filter-row">
          <div class="filter-item">
            <label>年份</label>
            <el-select v-model="filterYear" @change="handleFilterChange">
              <el-option
                v-for="year in availableYears"
                :key="year"
                :label="`${year}年`"
                :value="year"
              />
            </el-select>
          </div>
          <div class="filter-item">
            <label>月份</label>
            <el-select v-model="filterMonth" @change="handleFilterChange" clearable placeholder="全年">
              <el-option
                v-for="month in 12"
                :key="month"
                :label="`${month}月`"
                :value="month"
              />
            </el-select>
          </div>
          <div class="filter-item">
            <label>周期类型</label>
            <el-select v-model="filterPeriod" @change="handleFilterChange">
              <el-option label="全部" value="" />
              <el-option label="月度" value="monthly" />
              <el-option label="年度" value="yearly" />
            </el-select>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 预算汇总 -->
    <div class="summary-section">
      <el-card class="summary-card">
        <div class="summary-header">
          <h3>预算汇总</h3>
          <el-tag :type="getOverallStatusType(overallStatus)">
            {{ getOverallStatusText(overallStatus) }}
          </el-tag>
        </div>
        <div class="summary-stats">
          <div class="stat-item">
            <div class="stat-label">总预算</div>
            <div class="stat-value">¥{{ totalBudget.toLocaleString() }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">已使用</div>
            <div class="stat-value expense">¥{{ totalSpending.toLocaleString() }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">剩余</div>
            <div class="stat-value" :class="{ 'negative': totalBudget - totalSpending < 0 }">
              ¥{{ (totalBudget - totalSpending).toLocaleString() }}
            </div>
          </div>
          <div class="stat-item">
            <div class="stat-label">使用率</div>
            <div class="stat-value">{{ usagePercentage }}%</div>
          </div>
        </div>
        <div class="progress-section">
          <el-progress
            :percentage="usagePercentage"
            :color="getProgressColor(usagePercentage)"
            :stroke-width="8"
          />
        </div>
      </el-card>
    </div>

    <!-- 预算列表 -->
    <div class="budget-list">
      <el-card class="list-card">
        <div class="list-header">
          <h3>预算明细</h3>
          <div class="status-summary">
            <span class="status-item normal">
              <i class="status-dot"></i>正常: {{ normalCount }}
            </span>
            <span class="status-item warning">
              <i class="status-dot"></i>预警: {{ warningCount }}
            </span>
            <span class="status-item exceeded">
              <i class="status-dot"></i>超支: {{ overBudgetCount }}
            </span>
          </div>
        </div>

        <div class="budget-grid">
          <div
            v-for="budget in budgets"
            :key="budget.id"
            class="budget-card"
            :class="[budget.status, { 'disabled': !budget.is_enabled }]"
          >
            <div class="budget-header">
              <div class="budget-info">
                <span class="budget-icon">{{ budget.category?.icon || '💰' }}</span>
                <div class="budget-title">
                  <h4>{{ budget.category?.name || '总预算' }}</h4>
                  <p>{{ getPeriodText(budget) }}</p>
                </div>
              </div>
              <div class="budget-actions">
                <el-switch
                  v-model="budget.is_enabled"
                  @change="handleBudgetToggle(budget)"
                />
                <el-dropdown @command="(command) => handleBudgetAction(command, budget)">
                  <el-button text>
                    <el-icon><MoreFilled /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="edit">编辑</el-dropdown-item>
                      <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </div>

            <div class="budget-progress">
              <div class="progress-info">
                <span class="amount">¥{{ budget.actual_spending.toLocaleString() }} / ¥{{ budget.amount.toLocaleString() }}</span>
                <span class="percentage">{{ budget.percentage }}%</span>
              </div>
              <el-progress
                :percentage="budget.percentage"
                :color="getProgressColor(budget.percentage)"
                :stroke-width="6"
              />
              <div class="status-text">
                {{ getStatusText(budget.status) }}
                <span v-if="budget.status === 'exceeded'" class="over-amount">
                  (超支 ¥{{ Math.abs(budget.remaining).toLocaleString() }})
                </span>
              </div>
            </div>
          </div>

          <!-- 空状态 -->
          <div v-if="budgets.length === 0" class="empty-state">
            <el-empty description="暂无预算数据">
              <el-button type="primary" @click="showCreateDialog = true">
                创建第一个预算
              </el-button>
            </el-empty>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 预算预警 -->
    <div class="alerts-section" v-if="budgetAlerts?.alerts.length">
      <el-card class="alerts-card">
        <div class="alerts-header">
          <h3>
            <el-icon><Warning /></el-icon>
            预算预警
          </h3>
          <el-badge :value="budgetAlerts.total_count" type="danger" />
        </div>
        <div class="alerts-list">
          <div
            v-for="alert in budgetAlerts.alerts"
            :key="alert.id"
            class="alert-item"
            :class="alert.status"
          >
            <div class="alert-content">
              <div class="alert-title">
                <span class="category-icon">{{ getCategoryIcon(alert.category_name) }}</span>
                {{ alert.category_name }}
              </div>
              <div class="alert-details">
                已使用 ¥{{ alert.actual_spending.toLocaleString() }} / ¥{{ alert.budget_amount.toLocaleString() }}
                ({{ alert.percentage }}%)
              </div>
            </div>
            <div class="alert-status">
              <el-tag :type="alert.status === 'exceeded' ? 'danger' : 'warning'">
                {{ alert.status === 'exceeded' ? '已超支' : '预警' }}
              </el-tag>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 创建/编辑预算对话框 -->
    <CreateBudgetDialog
      v-model="showCreateDialog"
      :budget="editingBudget"
      @success="handleBudgetSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useBudgetStore } from '@/stores/budget'

import { useCategoryStore } from '@/stores/category'

import CreateBudgetDialog from '@/components/budget/CreateBudgetDialog.vue'
import { Plus, Refresh, MoreFilled, Warning } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { Budget } from '@/types/budget'

const budgetStore = useBudgetStore()
const categoryStore = useCategoryStore()

// 响应式数据
const loading = ref(false)
const showCreateDialog = ref(false)
const editingBudget = ref<Budget | null>(null)

// 筛选条件
const filterYear = ref(new Date().getFullYear())
const filterMonth = ref<number | null>(null)
const filterPeriod = ref('')

// 可选年份
const availableYears = computed(() => {
  const currentYear = new Date().getFullYear()
  return Array.from({ length: 5 }, (_, i) => currentYear - i)
})

// 计算属性
const { budgets, budgetAlerts, totalBudget, totalSpending, overBudgetCount, warningCount } = budgetStore

const usagePercentage = computed(() => {
  if (totalBudget === 0) return 0
  return Math.round((totalSpending / totalBudget) * 100)
})

const overallStatus = computed(() => {
  if (usagePercentage.value >= 100) return 'exceeded'
  if (usagePercentage.value >= 80) return 'warning'
  return 'normal'
})

const normalCount = computed(() => {
  return budgets.filter(b => b.status === 'normal').length
})

// 方法
const handleFilterChange = () => {
  loadData()
}

const loadData = async () => {
  try {
    loading.value = true
    await Promise.all([
      budgetStore.fetchBudgets({
        year: filterYear.value,
        month: filterMonth.value || undefined,
        period_type: filterPeriod.value || undefined
      }),
      budgetStore.fetchBudgetAlerts()
    ])
  } catch (error) {
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

const refreshData = () => {
  loadData()
}

const handleBudgetToggle = async (budget: Budget) => {
  try {
    await budgetStore.updateBudgetItem(budget.id, {
      is_enabled: budget.is_enabled
    })
    ElMessage.success('预算状态更新成功')
  } catch (error) {
    budget.is_enabled = !budget.is_enabled // 回滚状态
    ElMessage.error('更新失败')
  }
}

const handleBudgetAction = async (command: string, budget: Budget) => {
  if (command === 'edit') {
    editingBudget.value = budget
    showCreateDialog.value = true
  } else if (command === 'delete') {
    try {
      await ElMessageBox.confirm(
        `确定要删除"${budget.category?.name || '总预算'}"吗？`,
        '确认删除',
        {
          type: 'warning'
        }
      )
      await budgetStore.deleteBudgetItem(budget.id)
      ElMessage.success('删除成功')
    } catch (error) {
      if (error !== 'cancel') {
        ElMessage.error('删除失败')
      }
    }
  }
}

const handleBudgetSuccess = () => {
  showCreateDialog.value = false
  editingBudget.value = null
  loadData()
}

const getPeriodText = (budget: Budget) => {
  if (budget.period_type === 'yearly') {
    return `${budget.year}年`
  } else {
    return `${budget.year}年${budget.month}月`
  }
}

const getStatusText = (status: string) => {
  const statusMap = {
    normal: '正常',
    warning: '接近预算上限',
    exceeded: '已超支'
  }
  return statusMap[status as keyof typeof statusMap] || status
}

const getOverallStatusText = (status: string) => {
  const statusMap = {
    normal: '正常',
    warning: '预警',
    exceeded: '超支'
  }
  return statusMap[status as keyof typeof statusMap] || status
}

const getOverallStatusType = (status: string) => {
  const typeMap = {
    normal: 'success',
    warning: 'warning',
    exceeded: 'danger'
  }
  return typeMap[status as keyof typeof typeMap] || 'info'
}

const getProgressColor = (percentage: number) => {
  if (percentage >= 100) return '#f56c6c'
  if (percentage >= 80) return '#e6a23c'
  return '#67c23a'
}

const getCategoryIcon = (categoryName: string) => {
  const category = categoryStore.categories.find(c => c.name === categoryName)
  return category?.icon || '📊'
}

// 生命周期
onMounted(() => {
  // 先加载分类数据
  categoryStore.fetchCategories().then(() => {
    loadData()
  })
})
</script>

<style scoped>
.budget-management {
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

.page-header h2 {
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
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

/* 汇总卡片 */
.summary-section {
  margin-bottom: 24px;
}

.summary-card {
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.summary-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.summary-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.summary-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.stat-item {
  text-align: center;
}

.stat-label {
  font-size: 14px;
  color: #6b7280;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
}

.stat-value.expense {
  color: #ef4444;
}

.stat-value.negative {
  color: #ef4444;
}

.progress-section {
  padding: 0 10px;
}

/* 预算列表 */
.budget-list {
  margin-bottom: 24px;
}

.list-card {
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.list-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.status-summary {
  display: flex;
  gap: 20px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: #6b7280;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-item.normal .status-dot {
  background-color: #67c23a;
}

.status-item.warning .status-dot {
  background-color: #e6a23c;
}

.status-item.exceeded .status-dot {
  background-color: #f56c6c;
}

.budget-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

.budget-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  border: 2px solid transparent;
  transition: all 0.3s ease;
}

.budget-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.budget-card.warning {
  border-color: #e6a23c;
}

.budget-card.exceeded {
  border-color: #f56c6c;
}

.budget-card.disabled {
  opacity: 0.6;
}

.budget-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.budget-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.budget-icon {
  font-size: 24px;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f3f4f6;
  border-radius: 8px;
}

.budget-title h4 {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 4px 0;
}

.budget-title p {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
}

.budget-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.budget-progress .progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 14px;
}

.budget-progress .amount {
  color: #374151;
  font-weight: 500;
}

.budget-progress .percentage {
  color: #6b7280;
}

.status-text {
  font-size: 12px;
  color: #6b7280;
  margin-top: 8px;
}

.over-amount {
  color: #f56c6c;
  font-weight: 600;
}

.empty-state {
  grid-column: 1 / -1;
  padding: 40px;
  text-align: center;
}

/* 预警区域 */
.alerts-section {
  margin-bottom: 24px;
}

.alerts-card {
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border-left: 4px solid #f56c6c;
}

.alerts-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.alerts-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.alerts-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.alert-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-radius: 8px;
  border-left: 4px solid;
}

.alert-item.warning {
  background: #fef0e6;
  border-left-color: #e6a23c;
}

.alert-item.exceeded {
  background: #fef2f2;
  border-left-color: #f56c6c;
}

.alert-content {
  flex: 1;
}

.alert-title {
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.category-icon {
  font-size: 16px;
}

.alert-details {
  font-size: 14px;
  color: #6b7280;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .filter-row {
    flex-direction: column;
    align-items: stretch;
  }

  .summary-stats {
    grid-template-columns: repeat(2, 1fr);
  }

  .budget-grid {
    grid-template-columns: 1fr;
  }

  .list-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .status-summary {
    gap: 12px;
  }
}
</style>