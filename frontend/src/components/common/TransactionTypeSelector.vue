<template>
  <el-radio-group
    v-model="selectedType"
    :size="size"
    :disabled="disabled"
    class="transaction-type-selector"
    @change="handleChange"
  >
    <el-radio
      v-for="option in typeOptions"
      :key="option.value"
      :label="option.value"
      :border="border"
      class="type-radio"
    >
      <div class="type-content">
        <span class="type-icon" :style="{ color: option.color }">
          {{ option.icon }}
        </span>
        <span class="type-text">{{ option.label }}</span>
      </div>
    </el-radio>
  </el-radio-group>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { TransactionType } from '@/types'

interface Props {
  modelValue?: TransactionType
  size?: 'large' | 'default' | 'small'
  disabled?: boolean
  border?: boolean
  types?: TransactionType[]
}

interface Emits {
  (e: 'update:modelValue', value: TransactionType): void
  (e: 'change', value: TransactionType): void
}

const props = withDefaults(defineProps<Props>(), {
  size: 'default',
  disabled: false,
  border: true,
  types: () => [TransactionType.INCOME, TransactionType.EXPENSE, TransactionType.TRANSFER]
})

const emit = defineEmits<Emits>()

// 选中的类型
const selectedType = ref<TransactionType>(props.modelValue || TransactionType.EXPENSE)

// 类型选项配置
const typeConfig: Record<TransactionType, { label: string; icon: string; color: string }> = {
  [TransactionType.INCOME]: { label: '收入', icon: '➕', color: '#67c23a' },
  [TransactionType.EXPENSE]: { label: '支出', icon: '➖', color: '#f56c6c' },
  [TransactionType.TRANSFER]: { label: '转账', icon: '🔄', color: '#409eff' }
}

// 可选的类型选项
const typeOptions = computed(() => {
  return props.types.map(type => ({
    value: type,
    ...typeConfig[type]
  }))
})

// 处理类型变化
const handleChange = (value: TransactionType): void => {
  selectedType.value = value
  emit('update:modelValue', value)
  emit('change', value)
}

// 监听外部值变化
watch(
  () => props.modelValue,
  (newValue) => {
    if (newValue) {
      selectedType.value = newValue
    }
  },
  { immediate: true }
)
</script>

<style scoped>
.transaction-type-selector {
  display: flex;
  gap: 12px;
  width: 100%;
}

.type-radio {
  flex: 1;
}

:deep(.el-radio__input) {
  display: none;
}

.type-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 16px;
  border-radius: 6px;
  transition: all 0.3s ease;
  cursor: pointer;
  user-select: none;
}

:deep(.el-radio.is-bordered .el-radio__label) {
  padding-left: 0;
  width: 100%;
}

.type-icon {
  font-size: 18px;
}

.type-text {
  font-weight: 500;
  color: #606266;
}

:deep(.el-radio.is-bordered) {
  border-radius: 6px;
  border: 1px solid #dcdfe6;
  background: #fff;
  transition: all 0.3s ease;
}

:deep(.el-radio.is-bordered:hover) {
  border-color: #c0c4cc;
}

:deep(.el-radio.is-bordered.is-checked) {
  border-color: #409eff;
  background: #ecf5ff;
}

:deep(.el-radio.is-bordered.is-checked .type-text) {
  color: #409eff;
  font-weight: 600;
}

/* 不同类型的选中状态 */
:deep(.el-radio.is-bordered.is-checked) {
  border-width: 2px;
}

:deep(.el-radio.is-bordered.is-checked[aria-label="收入"]) {
  border-color: #67c23a;
  background: #f0f9ff;
}

:deep(.el-radio.is-bordered.is-checked[aria-label="收入"] .type-text) {
  color: #67c23a;
}

:deep(.el-radio.is-bordered.is-checked[aria-label="支出"]) {
  border-color: #f56c6c;
  background: #fef0f0;
}

:deep(.el-radio.is-bordered.is-checked[aria-label="支出"] .type-text) {
  color: #f56c6c;
}

:deep(.el-radio.is-bordered.is-checked[aria-label="转账"]) {
  border-color: #409eff;
  background: #ecf5ff;
}

:deep(.el-radio.is-bordered.is-checked[aria-label="转账"] .type-text) {
  color: #409eff;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .transaction-type-selector {
    flex-direction: column;
    gap: 8px;
  }

  .type-content {
    padding: 10px 12px;
  }

  .type-icon {
    font-size: 16px;
  }

  .type-text {
    font-size: 14px;
  }
}
</style>