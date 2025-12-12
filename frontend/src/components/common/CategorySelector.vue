<template>
  <el-select
    v-model="selectedValue"
    :placeholder="placeholder"
    :size="size"
    :disabled="disabled"
    :clearable="clearable"
    :filterable="filterable"
    class="category-selector"
    @change="handleChange"
    @clear="handleClear"
  >
    <template v-if="showTypeLabel">
      <el-option-group label="支出分类" v-if="expenseCategories.length > 0">
        <el-option
          v-for="category in expenseCategories"
          :key="category.id"
          :label="category.name"
          :value="category.id"
        >
          <div class="category-option">
            <span class="category-icon" :style="{ color: category.color }">
              {{ category.icon }}
            </span>
            <span class="category-name">{{ category.name }}</span>
            <span v-if="showParentName && category.parent_name" class="category-parent">
              {{ category.parent_name }}
            </span>
          </div>
        </el-option>
      </el-option-group>
      <el-option-group label="收入分类" v-if="incomeCategories.length > 0">
        <el-option
          v-for="category in incomeCategories"
          :key="category.id"
          :label="category.name"
          :value="category.id"
        >
          <div class="category-option">
            <span class="category-icon" :style="{ color: category.color }">
              {{ category.icon }}
            </span>
            <span class="category-name">{{ category.name }}</span>
            <span v-if="showParentName && category.parent_name" class="category-parent">
              {{ category.parent_name }}
            </span>
          </div>
        </el-option>
      </el-option-group>
    </template>
    <template v-else>
      <el-option
        v-for="category in filteredCategories"
        :key="category.id"
        :label="category.name"
        :value="category.id"
      >
        <div class="category-option">
          <span class="category-icon" :style="{ color: category.color }">
            {{ category.icon }}
          </span>
          <span class="category-name">{{ category.name }}</span>
          <span v-if="showParentName && category.parent_name" class="category-parent">
            {{ category.parent_name }}
          </span>
        </div>
      </el-option>
    </template>
  </el-select>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useTransactionStore } from '@/store/modules/transaction'
import { TransactionType, Category } from '@/types'

interface Props {
  modelValue?: number | null
  type?: TransactionType | null
  placeholder?: string
  size?: 'large' | 'default' | 'small'
  disabled?: boolean
  clearable?: boolean
  filterable?: boolean
  showTypeLabel?: boolean
  showParentName?: boolean
  includeSystem?: boolean
  includeCustom?: boolean
}

interface Emits {
  (e: 'update:modelValue', value: number | null): void
  (e: 'change', value: number | null, category?: Category): void
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: '请选择分类',
  size: 'default',
  disabled: false,
  clearable: true,
  filterable: true,
  showTypeLabel: true,
  showParentName: true,
  includeSystem: true,
  includeCustom: true
})

const emit = defineEmits<Emits>()

const transactionStore = useTransactionStore()

// 选中的值
const selectedValue = ref<number | null>(props.modelValue || null)

// 过滤分类
const filteredCategories = computed(() => {
  let categories = transactionStore.categories

  // 按类型过滤
  if (props.type) {
    categories = categories.filter(c => c.type === props.type)
  }

  // 按系统/自定义过滤
  if (!props.includeSystem) {
    categories = categories.filter(c => !c.is_system)
  }
  if (!props.includeCustom) {
    categories = categories.filter(c => c.is_system)
  }

  // 构建层级结构
  return categories.map(category => {
    const parentCategory = transactionStore.categories.find(c => c.id === category.parent_id)
    return {
      ...category,
      parent_name: parentCategory?.name
    }
  })
})

// 支出分类
const expenseCategories = computed(() => {
  return filteredCategories.value.filter(c => c.type === TransactionType.EXPENSE)
})

// 收入分类
const incomeCategories = computed(() => {
  return filteredCategories.value.filter(c => c.type === TransactionType.INCOME)
})

// 获取选中的分类
const getSelectedCategory = (categoryId: number): Category | undefined => {
  return transactionStore.categories.find(c => c.id === categoryId)
}

// 处理选择变化
const handleChange = (value: number | null): void => {
  selectedValue.value = value
  emit('update:modelValue', value)

  if (value) {
    const category = getSelectedCategory(value)
    emit('change', value, category)
  } else {
    emit('change', null)
  }
}

// 处理清除
const handleClear = (): void => {
  handleChange(null)
}

// 监听外部值变化
watch(
  () => props.modelValue,
  (newValue) => {
    selectedValue.value = newValue || null
  },
  { immediate: true }
)

// 如果分类列表为空，尝试获取
if (transactionStore.categories.length === 0) {
  transactionStore.fetchCategories()
}
</script>

<style scoped>
.category-selector {
  width: 100%;
}

.category-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.category-icon {
  font-size: 16px;
  width: 20px;
  text-align: center;
}

.category-name {
  flex: 1;
  font-weight: 500;
}

.category-parent {
  font-size: 12px;
  color: #909399;
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 4px;
}

:deep(.el-select-dropdown__item) {
  height: auto;
  padding: 8px 12px;
  line-height: 1.5;
}

:deep(.el-option-group__title) {
  padding: 8px 12px;
  font-weight: 600;
  color: #303133;
  background: #f5f7fa;
}
</style>