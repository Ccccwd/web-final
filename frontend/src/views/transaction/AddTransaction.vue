<template>
  <div class="add-transaction">
    <div class="header">
      <h2>快速记账</h2>
    </div>

    <!-- 交易类型选择 -->
    <div class="transaction-type-selector">
      <div class="type-tabs">
        <div
          v-for="type in transactionTypes"
          :key="type.value"
          :class="['type-tab', { active: formData.type === type.value }]"
          @click="selectTransactionType(type.value)"
        >
          <span class="type-icon">{{ type.icon }}</span>
          <span class="type-label">{{ type.label }}</span>
        </div>
      </div>
    </div>

    <!-- 金额输入 -->
    <div class="amount-section">
      <div class="amount-label">金额</div>
      <div class="amount-input-wrapper">
        <span class="currency-symbol">¥</span>
        <input
          v-model="amountInput"
          class="amount-input"
          type="text"
          placeholder="0.00"
          @input="handleAmountInput"
        />
      </div>
    </div>

    <!-- 表单内容 -->
    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-position="top"
      class="transaction-form"
    >
      <!-- 分类选择 -->
      <el-form-item label="分类" prop="category_id" v-if="formData.type !== 'transfer'">
        <div class="category-grid">
          <div
            v-for="category in filteredCategories"
            :key="category.id"
            :class="[
              'category-item',
              { active: formData.category_id === category.id }
            ]"
            @click="selectCategory(category)"
          >
            <div class="category-icon">{{ category.icon || '📝' }}</div>
            <div class="category-name">{{ category.name }}</div>
          </div>
        </div>
        <div v-if="filteredCategories.length === 0" class="no-categories">
          暂无分类，请先添加分类
        </div>
      </el-form-item>

      <!-- 账户选择 -->
      <el-form-item label="账户" prop="account_id">
        <el-select
          v-model="formData.account_id"
          placeholder="选择账户"
          style="width: 100%"
        >
          <el-option
            v-for="account in accounts"
            :key="account.id"
            :label="`${account.name} (余额: ¥${account.balance})`"
            :value="account.id"
          >
            <div class="account-option">
              <span class="account-icon">{{ account.icon || '💳' }}</span>
              <span class="account-name">{{ account.name }}</span>
              <span class="account-balance">¥{{ account.balance }}</span>
            </div>
          </el-option>
        </el-select>
      </el-form-item>

      <!-- 转账专用字段 -->
      <template v-if="formData.type === 'transfer'">
        <el-form-item label="转入账户" prop="to_account_id">
          <el-select
            v-model="formData.to_account_id"
            placeholder="选择转入账户"
            style="width: 100%"
          >
            <el-option
              v-for="account in transferAccounts"
              :key="account.id"
              :label="`${account.name} (余额: ¥${account.balance})`"
              :value="account.id"
            >
              <div class="account-option">
                <span class="account-icon">{{ account.icon || '💳' }}</span>
                <span class="account-name">{{ account.name }}</span>
                <span class="account-balance">¥{{ account.balance }}</span>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
      </template>

      <!-- 交易时间 -->
      <el-form-item label="交易时间" prop="transaction_date">
        <el-date-picker
          v-model="formData.transaction_date"
          type="datetime"
          placeholder="选择时间"
          format="YYYY-MM-DD HH:mm:ss"
          value-format="YYYY-MM-DD HH:mm:ss"
          style="width: 100%"
        />
      </el-form-item>

      <!-- 备注 -->
      <el-form-item label="备注">
        <el-input
          v-model="formData.remark"
          type="textarea"
          :rows="2"
          placeholder="添加备注..."
          maxlength="200"
          show-word-limit
        />
      </el-form-item>

      <!-- 标签 -->
      <el-form-item label="标签">
        <el-input
          v-model="formData.tags"
          placeholder="添加标签，用逗号分隔"
          maxlength="200"
        />
      </el-form-item>

      <!-- 地点 -->
      <el-form-item label="地点">
        <el-input
          v-model="formData.location"
          placeholder="添加地点..."
          maxlength="100"
        />
      </el-form-item>
    </el-form>

    <!-- 提交按钮 -->
    <div class="submit-section">
      <el-button
        type="primary"
        size="large"
        style="width: 100%"
        :loading="submitting"
        @click="submitTransaction"
      >
        {{ submitButtonText }}
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElForm } from 'element-plus'
import { useRouter } from 'vue-router'
import type { FormInstance, FormRules } from 'element-plus'
import * as transactionApi from '@/api/transaction'
import * as categoryApi from '@/api/category'
import * as accountApi from '@/api/account'

const router = useRouter()

// 交易类型选项
const transactionTypes = [
  { value: 'expense', label: '支出', icon: '💸' },
  { value: 'income', label: '收入', icon: '💰' },
  { value: 'transfer', label: '转账', icon: '💱' }
]

// 表单数据
const formData = reactive({
  type: 'expense',
  amount: 0,
  category_id: null,
  account_id: null,
  to_account_id: null,
  transaction_date: '',
  remark: '',
  tags: '',
  location: ''
})

// 金额输入
const amountInput = ref('')
const submitting = ref(false)

// 表单引用
const formRef = ref<FormInstance>()

// 数据列表
const categories = ref([])
const accounts = ref([])

// 表单验证规则
const formRules: FormRules = {
  category_id: [
    { required: true, message: '请选择分类', trigger: 'change' }
  ],
  account_id: [
    { required: true, message: '请选择账户', trigger: 'change' }
  ],
  to_account_id: [
    { required: true, message: '请选择转入账户', trigger: 'change' }
  ],
  transaction_date: [
    { required: true, message: '请选择交易时间', trigger: 'change' }
  ]
}

// 计算属性
const filteredCategories = computed(() => {
  if (formData.type === 'transfer') return []
  const type = formData.type === 'expense' ? 'expense' : 'income'
  return categories.value.filter(cat => cat.type === type)
})

const transferAccounts = computed(() => {
  return accounts.value.filter(acc => acc.id !== formData.account_id)
})

const submitButtonText = computed(() => {
  const typeMap = {
    expense: '添加支出',
    income: '添加收入',
    transfer: '添加转账'
  }
  return typeMap[formData.type] || '添加交易'
})

// 方法
const selectTransactionType = (type: string) => {
  formData.type = type
  formData.category_id = null
  formData.to_account_id = null
}

const selectCategory = (category: any) => {
  formData.category_id = category.id
}

const handleAmountInput = () => {
  // 移除非数字字符（保留小数点）
  let value = amountInput.value.replace(/[^\d.]/g, '')

  // 确保只有一个小数点
  const parts = value.split('.')
  if (parts.length > 2) {
    value = parts[0] + '.' + parts.slice(1).join('')
  }

  // 限制小数位数为2位
  if (parts.length === 2 && parts[1].length > 2) {
    value = parts[0] + '.' + parts[1].slice(0, 2)
  }

  amountInput.value = value
  formData.amount = parseFloat(value) || 0
}

const loadData = async () => {
  try {
    // 设置默认时间为当前时间
    const now = new Date()
    formData.transaction_date = now.toISOString().slice(0, 19).replace('T', ' ')

    // 加载分类
    const categoriesResponse = await categoryApi.getCategories()
    categories.value = categoriesResponse.data.categories || []

    // 加载账户
    const accountsResponse = await accountApi.getAccounts()
    accounts.value = accountsResponse.data.accounts || []

    // 设置默认账户
    if (accounts.value.length > 0) {
      const defaultAccount = accounts.value.find(acc => acc.is_default)
      formData.account_id = defaultAccount ? defaultAccount.id : accounts.value[0].id
    }

  } catch (error) {
    console.error('加载数据失败:', error)
    ElMessage.error('加载数据失败')
  }
}

const submitTransaction = async () => {
  if (!formRef.value) return

  try {
    // 验证表单
    await formRef.value.validate()

    // 验证金额
    if (formData.amount <= 0) {
      ElMessage.error('请输入有效的金额')
      return
    }

    // 验证转账账户
    if (formData.type === 'transfer' && formData.account_id === formData.to_account_id) {
      ElMessage.error('转出账户和转入账户不能相同')
      return
    }

    submitting.value = true

    // 提交数据
    const submitData: any = {
      ...formData,
      amount: formData.amount
    }

    await transactionApi.createTransaction(submitData)

    ElMessage.success('记账成功')

    // 跳转到交易列表
    router.push('/transactions')

  } catch (error: any) {
    console.error('提交失败:', error)
    ElMessage.error(error.response?.data?.message || '提交失败')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.add-transaction {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
}

.header {
  text-align: center;
  margin-bottom: 30px;
}

.header h2 {
  font-size: 24px;
  font-weight: 600;
  color: #333;
  margin: 0;
}

.transaction-type-selector {
  margin-bottom: 30px;
}

.type-tabs {
  display: flex;
  gap: 10px;
  background: #f5f5f5;
  padding: 4px;
  border-radius: 12px;
}

.type-tab {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  background: transparent;
  border: none;
  font-size: 14px;
  color: #666;
}

.type-tab:hover {
  background: rgba(0, 0, 0, 0.05);
}

.type-tab.active {
  background: #fff;
  color: #409eff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.type-icon {
  margin-right: 6px;
  font-size: 18px;
}

.amount-section {
  margin-bottom: 30px;
  text-align: center;
}

.amount-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 10px;
}

.amount-input-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
}

.currency-symbol {
  font-size: 32px;
  font-weight: 600;
  color: #333;
}

.amount-input {
  font-size: 32px;
  font-weight: 600;
  border: none;
  outline: none;
  background: transparent;
  color: #333;
  width: 200px;
  text-align: right;
}

.amount-input::placeholder {
  color: #ccc;
}

.transaction-form {
  margin-bottom: 30px;
}

.category-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
  gap: 12px;
}

.category-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 8px;
  border: 2px solid #eee;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  background: #fff;
}

.category-item:hover {
  border-color: #409eff;
  transform: translateY(-2px);
}

.category-item.active {
  border-color: #409eff;
  background: #ecf5ff;
  color: #409eff;
}

.category-icon {
  font-size: 20px;
  margin-bottom: 4px;
}

.category-name {
  font-size: 12px;
  text-align: center;
  word-break: break-all;
}

.no-categories {
  text-align: center;
  color: #999;
  padding: 20px;
  background: #f5f5f5;
  border-radius: 8px;
}

.account-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.account-icon {
  font-size: 16px;
}

.account-name {
  flex: 1;
}

.account-balance {
  color: #999;
  font-size: 12px;
}

.submit-section {
  margin-top: 30px;
}

@media (max-width: 768px) {
  .add-transaction {
    padding: 16px;
  }

  .type-tabs {
    flex-direction: column;
    gap: 4px;
  }

  .type-tab {
    padding: 10px;
  }

  .amount-input {
    font-size: 24px;
    width: 150px;
  }

  .category-grid {
    grid-template-columns: repeat(auto-fill, minmax(70px, 1fr));
    gap: 8px;
  }

  .category-item {
    padding: 8px 4px;
  }

  .category-icon {
    font-size: 18px;
  }

  .category-name {
    font-size: 11px;
  }
}
</style>
