<template>
  <div class="transaction-list">
    <!-- 页面头部 -->
    <div class="header">
      <div class="title">
        <h2>交易记录</h2>
      </div>
      <div class="actions">
        <el-button type="primary" @click="goToAddTransaction">
          <el-icon><Plus /></el-icon>
          记一笔
        </el-button>
        <el-button @click="showImportDialog = true">
          <el-icon><Upload /></el-icon>
          导入账单
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="summary-cards">
      <div class="summary-card income">
        <div class="card-icon">💰</div>
        <div class="card-content">
          <div class="card-label">总收入</div>
          <div class="card-value">¥{{ summary.total_income }}</div>
        </div>
      </div>
      <div class="summary-card expense">
        <div class="card-icon">💸</div>
        <div class="card-content">
          <div class="card-label">总支出</div>
          <div class="card-value">¥{{ summary.total_expense }}</div>
        </div>
      </div>
      <div class="summary-card balance">
        <div class="card-icon">💵</div>
        <div class="card-content">
          <div class="card-label">净收入</div>
          <div class="card-value">¥{{ summary.net_income }}</div>
        </div>
      </div>
      <div class="summary-card count">
        <div class="card-icon">📊</div>
        <div class="card-content">
          <div class="card-label">交易次数</div>
          <div class="card-value">{{ summary.transaction_count }}</div>
        </div>
      </div>
    </div>

    <!-- 筛选区域 -->
    <div class="filter-section">
      <el-form :model="filters" :inline="true" class="filter-form">
        <el-form-item label="交易类型">
          <el-select
            v-model="filters.type"
            placeholder="全部类型"
            clearable
            style="width: 120px"
          >
            <el-option label="支出" value="expense" />
            <el-option label="收入" value="income" />
            <el-option label="转账" value="transfer" />
          </el-select>
        </el-form-item>

        <el-form-item label="分类">
          <el-select
            v-model="filters.category_id"
            placeholder="全部分类"
            clearable
            style="width: 140px"
          >
            <el-option
              v-for="category in categories"
              :key="category.id"
              :label="category.name"
              :value="category.id"
            >
              <span class="category-option">
                <span class="category-icon">{{ category.icon || '📝' }}</span>
                {{ category.name }}
              </span>
            </el-option>
          </el-select>
        </el-form-item>

        <el-form-item label="账户">
          <el-select
            v-model="filters.account_id"
            placeholder="全部账户"
            clearable
            style="width: 140px"
          >
            <el-option
              v-for="account in accounts"
              :key="account.id"
              :label="account.name"
              :value="account.id"
            >
              <span class="account-option">
                <span class="account-icon">{{ account.icon || '💳' }}</span>
                {{ account.name }}
              </span>
            </el-option>
          </el-select>
        </el-form-item>

        <el-form-item label="时间范围">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 240px"
            @change="handleDateRangeChange"
          />
        </el-form-item>

        <el-form-item>
          <el-input
            v-model="filters.keyword"
            placeholder="搜索备注、商户名称..."
            style="width: 200px"
            clearable
            @clear="searchTransactions"
            @keyup.enter="searchTransactions"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="searchTransactions">搜索</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 交易列表 -->
    <div class="transaction-table">
      <el-table
        :data="transactions"
        :loading="loading"
        empty-text="暂无交易记录"
        @sort-change="handleSortChange"
      >
        <el-table-column prop="transaction_date" label="时间" width="160" sortable>
          <template #default="{ row }">
            <div class="transaction-date">
              {{ formatDate(row.transaction_date) }}
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="type" label="类型" width="80">
          <template #default="{ row }">
            <el-tag
              :type="getTypeTagType(row.type)"
              size="small"
              effect="light"
            >
              {{ getTypeLabel(row.type) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="category_name" label="分类" width="100">
          <template #default="{ row }">
            <div class="category-cell" v-if="row.category_name">
              <span class="category-icon">{{ row.category_icon || '📝' }}</span>
              <span>{{ row.category_name }}</span>
            </div>
            <span v-else>-</span>
          </template>
        </el-table-column>

        <el-table-column prop="amount" label="金额" width="120" sortable>
          <template #default="{ row }">
            <div :class="['amount-cell', row.type]">
              {{ formatAmount(row.amount, row.type) }}
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="account_name" label="账户" width="100">
          <template #default="{ row }">
            <div class="account-cell">
              <span class="account-icon">{{ getAccountIcon(row) }}</span>
              <span>{{ row.account_name }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="to_account_name" label="转入账户" width="100" v-if="hasTransfers">
          <template #default="{ row }">
            <div class="account-cell" v-if="row.to_account_name">
              <span class="account-icon">→</span>
              <span>{{ row.to_account_name }}</span>
            </div>
            <span v-else>-</span>
          </template>
        </el-table-column>

        <el-table-column prop="remark" label="备注" min-width="150">
          <template #default="{ row }">
            <div class="remark-cell">
              <div v-if="row.merchant_name" class="merchant-name">
                {{ row.merchant_name }}
              </div>
              <div class="remark-text">{{ row.remark || '-' }}</div>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="source" label="来源" width="80">
          <template #default="{ row }">
            <el-tag
              :type="getSourceTagType(row.source)"
              size="small"
              effect="plain"
            >
              {{ getSourceLabel(row.source) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              link
              size="small"
              @click="editTransaction(row)"
            >
              编辑
            </el-button>
            <el-button
              type="danger"
              link
              size="small"
              @click="deleteTransaction(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :total="pagination.total"
          :page-sizes="[20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </div>

    <!-- 导入对话框 -->
    <WechatImport
      v-model="showImportDialog"
      @success="handleImportSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Upload, Search } from '@element-plus/icons-vue'
import * as transactionApi from '@/api/transaction'
import * as categoryApi from '@/api/category'
import * as accountApi from '@/api/account'
import WechatImport from '@/components/import/WechatImport.vue'

const router = useRouter()

// 数据状态
const loading = ref(false)
const transactions = ref([])
const categories = ref([])
const accounts = ref([])
const summary = ref({
  total_income: '0.00',
  total_expense: '0.00',
  net_income: '0.00',
  transaction_count: 0
})

// 筛选条件
const filters = reactive({
  type: '',
  category_id: null,
  account_id: null,
  start_date: '',
  end_date: '',
  keyword: ''
})

// 日期范围
const dateRange = ref([])

// 分页
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

// 导入对话框
const showImportDialog = ref(false)

// 排序
const sortConfig = ref({
  prop: 'transaction_date',
  order: 'descending'
})

// 计算属性
const hasTransfers = computed(() => {
  return transactions.value.some(t => t.type === 'transfer')
})

// 方法
const loadTransactions = async () => {
  try {
    loading.value = true

    const params: Record<string, any> = {
      page: pagination.page,
      page_size: pagination.page_size,
      ...filters
    }

    // 处理排序
    if (sortConfig.value.prop) {
      params.sort_by = sortConfig.value.prop
      params.sort_order = sortConfig.value.order === 'descending' ? 'desc' : 'asc'
    }

    const response = await transactionApi.getTransactions(params)
    transactions.value = response.data.data || []
    pagination.total = response.data.pagination.total || 0

  } catch (error) {
    console.error('加载交易记录失败:', error)
    ElMessage.error('加载交易记录失败')
  } finally {
    loading.value = false
  }
}

const loadSummary = async () => {
  try {
    const params: Record<string, any> = {}
    if (filters.start_date) params.start_date = filters.start_date
    if (filters.end_date) params.end_date = filters.end_date

    const response = await transactionApi.getStatistics(params)
    const data = response.data.data
    summary.value = {
      total_income: formatNumber(data.total_income || 0),
      total_expense: formatNumber(data.total_expense || 0),
      net_income: formatNumber(data.net_income || 0),
      transaction_count: data.transaction_count || 0
    }

  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

const loadCategories = async () => {
  try {
    const response = await categoryApi.getCategories()
    categories.value = response.data.data || []
  } catch (error) {
    console.error('加载分类失败:', error)
  }
}

const loadAccounts = async () => {
  try {
    const response = await accountApi.getAccounts()
    accounts.value = response.data.data.accounts || []
  } catch (error) {
    console.error('加载账户失败:', error)
  }
}

const searchTransactions = () => {
  pagination.page = 1
  loadTransactions()
  loadSummary()
}

const resetFilters = () => {
  Object.keys(filters).forEach(key => {
    filters[key] = key === 'keyword' ? '' : (key.includes('_id') ? null : '')
  })
  dateRange.value = []
  pagination.page = 1
  loadTransactions()
  loadSummary()
}

const handleDateRangeChange = (dates: any) => {
  if (dates && dates.length === 2) {
    filters.start_date = dates[0]
    filters.end_date = dates[1]
  } else {
    filters.start_date = ''
    filters.end_date = ''
  }
}

const handleSortChange = ({ prop, order }: any) => {
  sortConfig.value = { prop, order }
  loadTransactions()
}

const handlePageChange = (page: number) => {
  pagination.page = page
  loadTransactions()
}

const handleSizeChange = (size: number) => {
  pagination.page_size = size
  pagination.page = 1
  loadTransactions()
}

const goToAddTransaction = () => {
  router.push('/transactions/add')
}

const editTransaction = (transaction: any) => {
  router.push(`/transactions/${transaction.id}/edit`)
}

const deleteTransaction = async (transaction: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除这条交易记录吗？\n金额: ${formatAmount(transaction.amount, transaction.type)}\n备注: ${transaction.remark || '-'}`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    await transactionApi.deleteTransaction(transaction.id)
    ElMessage.success('删除成功')
    loadTransactions()
    loadSummary()

  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error(error.response?.data?.message || '删除失败')
    }
  }
}

const handleImportSuccess = () => {
  ElMessage.success('账单导入成功')
  loadTransactions()
  loadSummary()
}

// 格式化方法
const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatAmount = (amount: number, type: string) => {
  const formatted = formatNumber(amount)
  if (type === 'expense') {
    return `-¥${formatted}`
  } else {
    return `¥${formatted}`
  }
}

const formatNumber = (num: number) => {
  return Math.abs(num).toFixed(2)
}

const getTypeLabel = (type: string) => {
  const labels = {
    expense: '支出',
    income: '收入',
    transfer: '转账'
  }
  return labels[type] || type
}

const getTypeTagType = (type: string) => {
  const types = {
    expense: 'danger',
    income: 'success',
    transfer: 'info'
  }
  return types[type] || 'info'
}

const getSourceLabel = (source: string) => {
  const labels = {
    manual: '手动',
    wechat: '微信',
    import: '导入'
  }
  return labels[source] || source
}

const getSourceTagType = (source: string) => {
  const types = {
    manual: '',
    wechat: 'warning',
    import: 'info'
  }
  return types[source] || ''
}

const getAccountIcon = (transaction: any) => {
  if (transaction.type === 'transfer') {
    return '💱'
  }
  return transaction.account_icon || '💳'
}

// 监听筛选条件变化
watch([filters, dateRange], () => {
  searchTransactions()
}, { deep: true })

// 生命周期
onMounted(() => {
  loadTransactions()
  loadSummary()
  loadCategories()
  loadAccounts()
})
</script>

<style scoped>
.transaction-list {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.title h2 {
  font-size: 24px;
  font-weight: 600;
  color: #333;
  margin: 0;
}

.actions {
  display: flex;
  gap: 12px;
}

.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.summary-card {
  display: flex;
  align-items: center;
  padding: 20px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s;
}

.summary-card:hover {
  transform: translateY(-2px);
}

.summary-card.income {
  border-left: 4px solid #67c23a;
}

.summary-card.expense {
  border-left: 4px solid #f56c6c;
}

.summary-card.balance {
  border-left: 4px solid #409eff;
}

.summary-card.count {
  border-left: 4px solid #909399;
}

.card-icon {
  font-size: 32px;
  margin-right: 16px;
}

.card-content {
  flex: 1;
}

.card-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 4px;
}

.card-value {
  font-size: 20px;
  font-weight: 600;
  color: #333;
}

.filter-section {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.filter-form {
  margin: 0;
}

.category-option,
.account-option {
  display: flex;
  align-items: center;
  gap: 6px;
}

.transaction-table {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.transaction-date {
  font-size: 13px;
  color: #666;
}

.category-cell,
.account-cell {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
}

.category-icon,
.account-icon {
  font-size: 14px;
}

.amount-cell {
  font-weight: 600;
  font-size: 14px;
}

.amount-cell.income {
  color: #67c23a;
}

.amount-cell.expense {
  color: #f56c6c;
}

.amount-cell.transfer {
  color: #409eff;
}

.remark-cell {
  font-size: 13px;
}

.merchant-name {
  font-weight: 500;
  color: #333;
  margin-bottom: 2px;
}

.remark-text {
  color: #666;
}

.pagination {
  padding: 20px;
  text-align: right;
  border-top: 1px solid #ebeef5;
}

@media (max-width: 768px) {
  .transaction-list {
    padding: 16px;
  }

  .header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }

  .actions {
    justify-content: center;
  }

  .summary-cards {
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 12px;
  }

  .summary-card {
    padding: 16px;
  }

  .card-icon {
    font-size: 24px;
    margin-right: 12px;
  }

  .card-value {
    font-size: 18px;
  }

  .filter-form {
    display: block;
  }

  .filter-form :deep(.el-form-item) {
    margin-bottom: 12px;
    margin-right: 0;
  }
}
</style>
