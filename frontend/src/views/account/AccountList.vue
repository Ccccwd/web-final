<template>
  <div class="account-management">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1>账户管理</h1>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>
        添加账户
      </el-button>
    </div>

    <!-- 账户统计卡片 -->
    <div class="stats-cards">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-value">¥{{ accountSummary.total_balance?.toLocaleString() || '0' }}</div>
              <div class="stat-label">总资产</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-value">{{ accountSummary.account_count || 0 }}</div>
              <div class="stat-label">账户数量</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-value">{{ getAccountCountByType('cash') }}</div>
              <div class="stat-label">现金账户</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-value">{{ getAccountCountByType('bank') }}</div>
              <div class="stat-label">银行账户</div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 筛选和搜索 -->
    <div class="filter-section">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-select v-model="filters.type" placeholder="账户类型" clearable @change="loadAccounts">
            <el-option label="全部类型" value="" />
            <el-option label="现金" value="cash" />
            <el-option label="银行" value="bank" />
            <el-option label="微信" value="wechat" />
            <el-option label="支付宝" value="alipay" />
            <el-option label="信用卡" value="credit_card" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-select v-model="filters.is_enabled" placeholder="状态" clearable @change="loadAccounts">
            <el-option label="全部状态" value="" />
            <el-option label="启用" :value="true" />
            <el-option label="禁用" :value="false" />
          </el-select>
        </el-col>
        <el-col :span="12">
          <el-button @click="resetFilters">重置</el-button>
          <el-button type="primary" @click="loadAccounts">刷新</el-button>
        </el-col>
      </el-row>
    </div>

    <!-- 账户列表 -->
    <div class="account-list">
      <el-table :data="accounts" v-loading="loading" stripe>
        <el-table-column prop="name" label="账户名称" min-width="150">
          <template #default="{ row }">
            <div class="account-name">
              <el-icon class="account-icon" :style="{ color: row.color }">
                <component :is="getAccountIcon(row.type)" />
              </el-icon>
              <span>{{ row.name }}</span>
              <el-tag v-if="row.is_default" type="success" size="small" style="margin-left: 8px">默认</el-tag>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getAccountTypeTag(row.type)">
              {{ getAccountTypeName(row.type) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="balance" label="余额" width="150" align="right">
          <template #default="{ row }">
            <span :class="getBalanceClass(row.balance)">
              ¥{{ Number(row.balance).toLocaleString() }}
            </span>
          </template>
        </el-table-column>

        <el-table-column prop="is_enabled" label="状态" width="80">
          <template #default="{ row }">
            <el-switch
              v-model="row.is_enabled"
              @change="toggleAccountStatus(row)"
            />
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewAccountDetail(row)">详情</el-button>
            <el-button size="small" type="primary" @click="editAccount(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteAccount(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 转账对话框 -->
    <el-dialog v-model="showTransferDialog" title="账户转账" width="500px">
      <el-form :model="transferForm" :rules="transferRules" ref="transferFormRef" label-width="100px">
        <el-form-item label="转出账户" prop="from_account_id">
          <el-select v-model="transferForm.from_account_id" placeholder="选择转出账户" style="width: 100%">
            <el-option
              v-for="account in enabledAccounts"
              :key="account.id"
              :label="`${account.name} (余额: ¥${Number(account.balance).toLocaleString()})`"
              :value="account.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="转入账户" prop="to_account_id">
          <el-select v-model="transferForm.to_account_id" placeholder="选择转入账户" style="width: 100%">
            <el-option
              v-for="account in enabledAccounts"
              :key="account.id"
              :label="`${account.name} (余额: ¥${Number(account.balance).toLocaleString()})`"
              :value="account.id"
              :disabled="account.id === transferForm.from_account_id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="转账金额" prop="amount">
          <el-input-number
            v-model="transferForm.amount"
            :min="0.01"
            :max="getMaxTransferAmount()"
            :precision="2"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="转账时间" prop="transaction_date">
          <el-date-picker
            v-model="transferForm.transaction_date"
            type="datetime"
            placeholder="选择转账时间"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="备注">
          <el-input v-model="transferForm.remark" placeholder="转账备注" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showTransferDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmTransfer" :loading="transferLoading">确认转账</el-button>
      </template>
    </el-dialog>

    <!-- 创建/编辑账户对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      :title="editingAccount ? '编辑账户' : '添加账户'"
      width="600px"
    >
      <el-form :model="accountForm" :rules="accountRules" ref="accountFormRef" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="账户名称" prop="name">
              <el-input v-model="accountForm.name" placeholder="请输入账户名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="账户类型" prop="type">
              <el-select v-model="accountForm.type" placeholder="选择账户类型" style="width: 100%">
                <el-option label="现金" value="cash" />
                <el-option label="银行" value="bank" />
                <el-option label="微信" value="wechat" />
                <el-option label="支付宝" value="alipay" />
                <el-option label="信用卡" value="credit_card" />
                <el-option label="饭卡" value="meal_card" />
                <el-option label="其他" value="other" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="初始余额" prop="initial_balance">
              <el-input-number
                v-model="accountForm.initial_balance"
                :min="0"
                :precision="2"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="图标">
              <el-input v-model="accountForm.icon" placeholder="图标名称">
                <template #prefix>
                  <el-icon>
                    <component :is="accountForm.icon || 'Money'" />
                  </el-icon>
                </template>
              </el-input>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="颜色">
              <el-color-picker v-model="accountForm.color" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="默认账户">
              <el-switch v-model="accountForm.is_default" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="描述">
          <el-input v-model="accountForm.description" type="textarea" :rows="2" placeholder="账户描述" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="cancelEdit">取消</el-button>
        <el-button type="primary" @click="saveAccount" :loading="saveLoading">
          {{ editingAccount ? '更新' : '创建' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 账户详情抽屉 -->
    <el-drawer v-model="showDetailDrawer" title="账户详情" size="50%">
      <div v-if="selectedAccount" class="account-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="账户名称">{{ selectedAccount.name }}</el-descriptions-item>
          <el-descriptions-item label="账户类型">
            <el-tag :type="getAccountTypeTag(selectedAccount.type)">
              {{ getAccountTypeName(selectedAccount.type) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="当前余额">
            <span :class="getBalanceClass(selectedAccount.balance)">
              ¥{{ Number(selectedAccount.balance).toLocaleString() }}
            </span>
          </el-descriptions-item>
          <el-descriptions-item label="初始余额">
            ¥{{ Number(selectedAccount.initial_balance).toLocaleString() }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="selectedAccount.is_enabled ? 'success' : 'danger'">
              {{ selectedAccount.is_enabled ? '启用' : '禁用' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="默认账户">
            <el-tag v-if="selectedAccount.is_default" type="success">是</el-tag>
            <span v-else>否</span>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatDate(selectedAccount.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ formatDate(selectedAccount.updated_at) }}</el-descriptions-item>
        </el-descriptions>

        <!-- 余额历史图表 -->
        <div class="balance-history" v-if="balanceHistory.length > 0">
          <h3>余额变化趋势</h3>
          <div class="history-chart">
            <LineChart
              :data="balanceChartData"
              :options="chartOptions"
              height="300px"
            />
          </div>
        </div>

        <!-- 最近交易记录 -->
        <div class="recent-transactions">
          <h3>最近交易记录</h3>
          <el-table :data="recentTransactions" size="small">
            <el-table-column prop="transaction_date" label="时间" width="180">
              <template #default="{ row }">
                {{ formatDate(row.transaction_date) }}
              </template>
            </el-table-column>
            <el-table-column prop="type" label="类型" width="100">
              <template #default="{ row }">
                <el-tag :type="row.type === 'income' ? 'success' : 'danger'">
                  {{ row.type === 'income' ? '收入' : '支出' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="amount" label="金额" width="120" align="right">
              <template #default="{ row }">
                <span :class="row.type === 'income' ? 'income' : 'expense'">
                  ¥{{ Number(row.amount).toLocaleString() }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="remark" label="备注" />
          </el-table>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Money, CreditCard, Wallet, Iphone, Food } from '@element-plus/icons-vue'
import { accountApi } from '@/api/accounts'
import { formatCurrency, formatDate } from '@/utils/format'
import LineChart from '@/components/charts/LineChart.vue'

// 响应式数据
const loading = ref(false)
const accounts = ref([])
const accountSummary = ref({})
const showCreateDialog = ref(false)
const showTransferDialog = ref(false)
const showDetailDrawer = ref(false)
const editingAccount = ref(null)
const selectedAccount = ref(null)
const transferLoading = ref(false)
const saveLoading = ref(false)
const balanceHistory = ref([])
const recentTransactions = ref([])

// 筛选条件
const filters = reactive({
  type: '',
  is_enabled: null
})

// 表单数据
const accountForm = reactive({
  name: '',
  type: '',
  initial_balance: 0,
  icon: '',
  color: '#409EFF',
  is_default: false,
  description: ''
})

const transferForm = reactive({
  from_account_id: null,
  to_account_id: null,
  amount: 0,
  transaction_date: new Date(),
  remark: ''
})

// 表单验证规则
const accountRules = {
  name: [{ required: true, message: '请输入账户名称', trigger: 'blur' }],
  type: [{ required: true, message: '请选择账户类型', trigger: 'change' }]
}

const transferRules = {
  from_account_id: [{ required: true, message: '请选择转出账户', trigger: 'change' }],
  to_account_id: [{ required: true, message: '请选择转入账户', trigger: 'change' }],
  amount: [{ required: true, message: '请输入转账金额', trigger: 'blur' }]
}

// 计算属性
const enabledAccounts = computed(() => {
  return accounts.value.filter(account => account.is_enabled)
})

const balanceChartData = computed(() => {
  return {
    labels: balanceHistory.value.map(item => formatDate(item.created_at)),
    datasets: [{
      label: '账户余额',
      data: balanceHistory.value.map(item => Number(item.amount_after)),
      borderColor: '#409EFF',
      backgroundColor: 'rgba(64, 158, 255, 0.1)',
      tension: 0.4
    }]
  }
})

const chartOptions = {
  responsive: true,
  plugins: {
    legend: {
      display: true
    }
  },
  scales: {
    y: {
      beginAtZero: false,
      ticks: {
        callback: function(value) {
          return '¥' + value.toLocaleString()
        }
      }
    }
  }
}

// 方法定义
const loadAccounts = async () => {
  try {
    loading.value = true
    const params = {}
    if (filters.type) params.type = filters.type
    if (filters.is_enabled !== null) params.is_enabled = filters.is_enabled

    const response = await accountApi.getAccounts(params)
    accounts.value = response.data.accounts

    // 加载账户统计
    const summaryResponse = await accountApi.getAccountSummary()
    accountSummary.value = summaryResponse.data
  } catch (error) {
    ElMessage.error('加载账户列表失败')
  } finally {
    loading.value = false
  }
}

const resetFilters = () => {
  filters.type = ''
  filters.is_enabled = null
  loadAccounts()
}

const getAccountTypeName = (type) => {
  const typeMap = {
    cash: '现金',
    bank: '银行',
    wechat: '微信',
    alipay: '支付宝',
    credit_card: '信用卡',
    meal_card: '饭卡',
    other: '其他'
  }
  return typeMap[type] || type
}

const getAccountTypeTag = (type) => {
  const tagMap = {
    cash: '',
    bank: 'success',
    wechat: 'success',
    alipay: 'success',
    credit_card: 'warning',
    meal_card: 'info',
    other: 'info'
  }
  return tagMap[type] || ''
}

const getAccountIcon = (type) => {
  const iconMap = {
    cash: Money,
    bank: CreditCard,
    wechat: Iphone,
    alipay: Iphone,
    credit_card: CreditCard,
    meal_card: Food,
    other: Wallet
  }
  return iconMap[type] || Wallet
}

const getBalanceClass = (balance) => {
  if (Number(balance) > 0) return 'balance-positive'
  if (Number(balance) < 0) return 'balance-negative'
  return 'balance-zero'
}

const getAccountCountByType = (type) => {
  if (!accountSummary.value.type_stats) return 0
  return accountSummary.value.type_stats[type]?.count || 0
}

const toggleAccountStatus = async (account) => {
  try {
    await accountApi.updateAccount(account.id, { is_enabled: account.is_enabled })
    ElMessage.success('账户状态更新成功')
  } catch (error) {
    account.is_enabled = !account.is_enabled // 回滚状态
    ElMessage.error('更新账户状态失败')
  }
}

const editAccount = (account) => {
  editingAccount.value = account
  Object.assign(accountForm, {
    name: account.name,
    type: account.type,
    initial_balance: Number(account.initial_balance),
    icon: account.icon,
    color: account.color,
    is_default: account.is_default,
    description: account.description
  })
  showCreateDialog.value = true
}

const saveAccount = async () => {
  try {
    saveLoading.value = true
    if (editingAccount.value) {
      await accountApi.updateAccount(editingAccount.value.id, accountForm)
      ElMessage.success('账户更新成功')
    } else {
      await accountApi.createAccount(accountForm)
      ElMessage.success('账户创建成功')
    }
    showCreateDialog.value = false
    loadAccounts()
  } catch (error) {
    ElMessage.error('保存账户失败')
  } finally {
    saveLoading.value = false
  }
}

const cancelEdit = () => {
  showCreateDialog.value = false
  editingAccount.value = null
  Object.assign(accountForm, {
    name: '',
    type: '',
    initial_balance: 0,
    icon: '',
    color: '#409EFF',
    is_default: false,
    description: ''
  })
}

const deleteAccount = async (account) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除账户"${account.name}"吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await accountApi.deleteAccount(account.id)
    ElMessage.success('账户删除成功')
    loadAccounts()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除账户失败')
    }
  }
}

const viewAccountDetail = async (account) => {
  selectedAccount.value = account
  showDetailDrawer.value = true

  try {
    // 加载余额历史
    const historyResponse = await accountApi.getBalanceHistory(account.id)
    balanceHistory.value = historyResponse.data

    // 加载最近交易记录（这里需要调用交易API）
    // recentTransactions.value = await transactionApi.getRecentTransactions(account.id)
  } catch (error) {
    console.error('加载账户详情失败:', error)
  }
}

const getMaxTransferAmount = () => {
  if (!transferForm.from_account_id) return 0
  const fromAccount = accounts.value.find(acc => acc.id === transferForm.from_account_id)
  return fromAccount ? Number(fromAccount.balance) : 0
}

const confirmTransfer = async () => {
  try {
    transferLoading.value = true
    await accountApi.transfer(transferForm)
    ElMessage.success('转账成功')
    showTransferDialog.value = false
    loadAccounts()
  } catch (error) {
    ElMessage.error('转账失败')
  } finally {
    transferLoading.value = false
  }
}

// 生命周期
onMounted(() => {
  loadAccounts()
})
</script>

<style scoped>
.account-management {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0;
  font-size: 24px;
  color: #303133;
}

.stats-cards {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
}

.stat-item {
  padding: 20px;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #409EFF;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.filter-section {
  margin-bottom: 20px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.account-list {
  background: white;
  border-radius: 8px;
  overflow: hidden;
}

.account-name {
  display: flex;
  align-items: center;
}

.account-icon {
  margin-right: 8px;
  font-size: 18px;
}

.balance-positive {
  color: #67C23A;
  font-weight: bold;
}

.balance-negative {
  color: #F56C6C;
  font-weight: bold;
}

.balance-zero {
  color: #909399;
}

.income {
  color: #67C23A;
}

.expense {
  color: #F56C6C;
}

.account-detail {
  padding: 20px;
}

.balance-history,
.recent-transactions {
  margin-top: 30px;
}

.balance-history h3,
.recent-transactions h3 {
  margin-bottom: 15px;
  color: #303133;
}

.history-chart {
  margin-top: 15px;
}
</style>
