<template>
  <el-dialog
    v-model="dialogVisible"
    :title="isEdit ? '编辑预算' : '创建预算'"
    width="500px"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="100px"
      @submit.prevent
    >
      <el-form-item label="预算类型" prop="period_type">
        <el-select
          v-model="formData.period_type"
          placeholder="请选择预算类型"
          style="width: 100%"
          @change="handlePeriodTypeChange"
        >
          <el-option label="月度预算" value="monthly" />
          <el-option label="年度预算" value="yearly" />
        </el-select>
      </el-form-item>

      <el-form-item label="年份" prop="year">
        <el-select
          v-model="formData.year"
          placeholder="请选择年份"
          style="width: 100%"
        >
          <el-option
            v-for="year in availableYears"
            :key="year"
            :label="`${year}年`"
            :value="year"
          />
        </el-select>
      </el-form-item>

      <el-form-item
        v-if="formData.period_type === 'monthly'"
        label="月份"
        prop="month"
      >
        <el-select
          v-model="formData.month"
          placeholder="请选择月份"
          style="width: 100%"
        >
          <el-option
            v-for="month in 12"
            :key="month"
            :label="`${month}月`"
            :value="month"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="分类" prop="category_id">
        <el-select
          v-model="formData.category_id"
          placeholder="请选择分类（不选则为总预算）"
          style="width: 100%"
          clearable
          filterable
        >
          <el-option-group label="支出分类">
            <el-option
              v-for="category in expenseCategories"
              :key="category.id"
              :label="category.name"
              :value="category.id"
            >
              <span style="margin-right: 8px">{{ category.icon }}</span>
              {{ category.name }}
            </el-option>
          </el-option-group>
          <el-option-group label="收入分类">
            <el-option
              v-for="category in incomeCategories"
              :key="category.id"
              :label="category.name"
              :value="category.id"
            >
              <span style="margin-right: 8px">{{ category.icon }}</span>
              {{ category.name }}
            </el-option>
          </el-option-group>
        </el-select>
      </el-form-item>

      <el-form-item label="预算金额" prop="amount">
        <el-input
          v-model="amountInput"
          type="text"
          placeholder="请输入预算金额"
          @input="handleAmountInput"
        >
          <template #prefix>¥</template>
        </el-input>
      </el-form-item>

      <el-form-item label="预警阈值" prop="alert_threshold">
        <el-slider
          v-model="formData.alert_threshold"
          :min="50"
          :max="100"
          :step="5"
          show-stops
          show-input
          style="width: 100%"
        />
        <div class="threshold-help">
          当预算使用率达到 {{ formData.alert_threshold }}% 时触发预警
        </div>
      </el-form-item>

      <el-form-item label="启用状态" prop="is_enabled">
        <el-switch
          v-model="formData.is_enabled"
          active-text="启用"
          inactive-text="禁用"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          {{ isEdit ? '更新' : '创建' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useBudgetStore } from '@/stores/budget'
import { useCategoryStore } from '@/stores/category'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import type { Budget, CreateBudgetData, UpdateBudgetData } from '@/types/budget'

interface Props {
  modelValue: boolean
  budget?: Budget | null
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'success'): void
}

const props = withDefaults(defineProps<Props>(), {
  budget: null
})

const emit = defineEmits<Emits>()

const budgetStore = useBudgetStore()
const categoryStore = useCategoryStore()

// 响应式数据
const formRef = ref<FormInstance>()
const submitting = ref(false)
const amountInput = ref('')

// 表单数据
const formData = ref<CreateBudgetData>({
  category_id: undefined,
  amount: 0,
  period_type: 'monthly',
  year: new Date().getFullYear(),
  month: new Date().getMonth() + 1,
  alert_threshold: 80,
  is_enabled: true
})

// 计算属性
const dialogVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const isEdit = computed(() => !!props.budget)

const availableYears = computed(() => {
  const currentYear = new Date().getFullYear()
  return Array.from({ length: 5 }, (_, i) => currentYear - i)
})

const expenseCategories = computed(() => {
  return categoryStore.categories.filter(c => c.type === 'expense')
})

const incomeCategories = computed(() => {
  return categoryStore.categories.filter(c => c.type === 'income')
})

// 表单验证规则
const formRules: FormRules = {
  period_type: [
    { required: true, message: '请选择预算类型', trigger: 'change' }
  ],
  year: [
    { required: true, message: '请选择年份', trigger: 'change' }
  ],
  month: [
    {
      validator: (rule, value, callback) => {
        if (formData.value.period_type === 'monthly' && !value) {
          callback(new Error('请选择月份'))
        } else {
          callback()
        }
      },
      trigger: 'change'
    }
  ],
  amount: [
    { required: true, message: '请输入预算金额', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value <= 0) {
          callback(new Error('预算金额必须大于0'))
        } else if (value > 9999999.99) {
          callback(new Error('预算金额不能超过9,999,999.99'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ],
  alert_threshold: [
    { required: true, message: '请设置预警阈值', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value < 50 || value > 100) {
          callback(new Error('预警阈值必须在50%-100%之间'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 方法
const handlePeriodTypeChange = () => {
  if (formData.value.period_type === 'yearly') {
    formData.value.month = undefined
  } else {
    formData.value.month = new Date().getMonth() + 1
  }
}

const handleAmountInput = (value: string) => {
  // 移除非数字字符，保留小数点
  const cleanValue = value.replace(/[^\d.]/g, '')
  // 确保只有一个小数点
  const parts = cleanValue.split('.')
  const formattedValue = parts[0] + (parts[1] ? '.' + parts[1].slice(0, 2) : '')

  amountInput.value = formattedValue
  formData.value.amount = parseFloat(formattedValue) || 0
}

const resetForm = () => {
  formData.value = {
    category_id: undefined,
    amount: 0,
    period_type: 'monthly',
    year: new Date().getFullYear(),
    month: new Date().getMonth() + 1,
    alert_threshold: 80,
    is_enabled: true
  }
  amountInput.value = ''
  formRef.value?.resetFields()
}

const initFormData = () => {
  if (props.budget) {
    formData.value = {
      category_id: props.budget.category?.id,
      amount: props.budget.amount,
      period_type: props.budget.period_type,
      year: props.budget.year,
      month: props.budget.month,
      alert_threshold: props.budget.alert_threshold,
      is_enabled: props.budget.is_enabled
    }
    amountInput.value = props.budget.amount.toString()
  } else {
    resetForm()
  }
}

const handleClose = () => {
  dialogVisible.value = false
  resetForm()
}

const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    submitting.value = true

    if (isEdit.value && props.budget) {
      // 更新预算
      await budgetStore.updateBudgetItem(props.budget.id, {
        amount: formData.value.amount,
        alert_threshold: formData.value.alert_threshold,
        is_enabled: formData.value.is_enabled
      })
      ElMessage.success('预算更新成功')
    } else {
      // 创建预算
      await budgetStore.createBudgetItem(formData.value)
      ElMessage.success('预算创建成功')
    }

    emit('success')
    handleClose()
  } catch (error) {
    console.error('提交失败:', error)
  } finally {
    submitting.value = false
  }
}

// 监听器
watch(() => props.modelValue, (visible) => {
  if (visible) {
    initFormData()
  }
})

watch(() => props.budget, () => {
  if (props.modelValue) {
    initFormData()
  }
})

// 生命周期
onMounted(() => {
  if (!categoryStore.categories.length) {
    categoryStore.fetchCategories()
  }
})
</script>

<style scoped>
.threshold-help {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>