<template>
  <el-input
    v-model="displayValue"
    :placeholder="placeholder"
    :size="size"
    :disabled="disabled"
    :clearable="clearable"
    class="amount-input"
    @input="handleInput"
    @blur="handleBlur"
    @focus="handleFocus"
    @change="handleChange"
  >
    <template #prefix>
      <span class="amount-prefix">{{ currency }}</span>
    </template>
  </el-input>
</template>

<script setup lang="ts">
import { ref, watch, computed, nextTick } from 'vue'
import { ElMessage } from 'element-plus'

interface Props {
  modelValue?: number | string
  currency?: string
  placeholder?: string
  size?: 'large' | 'default' | 'small'
  disabled?: boolean
  clearable?: boolean
  min?: number
  max?: number
  precision?: number
  allowNegative?: boolean
}

interface Emits {
  (e: 'update:modelValue', value: number): void
  (e: 'change', value: number): void
  (e: 'blur', event: FocusEvent): void
  (e: 'focus', event: FocusEvent): void
}

const props = withDefaults(defineProps<Props>(), {
  currency: '¥',
  placeholder: '请输入金额',
  size: 'default',
  disabled: false,
  clearable: true,
  min: 0,
  max: 999999999,
  precision: 2,
  allowNegative: false
})

const emit = defineEmits<Emits>()

// 内部值
const internalValue = ref('')
const isFocused = ref(false)

// 格式化显示值
const displayValue = computed({
  get: () => {
    if (isFocused.value) {
      return internalValue.value
    }

    if (!internalValue.value || internalValue.value === '0') {
      return ''
    }

    const num = parseFloat(internalValue.value)
    if (isNaN(num)) return ''

    return num.toFixed(props.precision)
  },
  set: (value: string) => {
    internalValue.value = value
  }
})

// 验证并格式化输入值
const formatInputValue = (value: string): string => {
  // 移除所有非数字和小数点的字符（除了负号）
  let formatted = value.replace(/[^\d.-]/g, '')

  // 处理负号
  if (!props.allowNegative) {
    formatted = formatted.replace(/-/g, '')
  } else {
    // 只允许开头有一个负号
    const parts = formatted.split('-')
    if (parts.length > 2) {
      formatted = '-' + parts.slice(1).join('')
    } else if (parts.length === 2 && parts[0] !== '') {
      formatted = parts[1]
    }
  }

  // 处理小数点
  const decimalIndex = formatted.indexOf('.')
  if (decimalIndex !== -1) {
    // 保留第一个小数点，删除其他小数点
    const integerPart = formatted.substring(0, decimalIndex)
    const decimalPart = formatted.substring(decimalIndex + 1).replace(/\./g, '')

    // 限制小数位数
    const limitedDecimalPart = decimalPart.substring(0, props.precision)
    formatted = integerPart + '.' + limitedDecimalPart
  }

  return formatted
}

// 验证数值范围
const validateRange = (value: number): boolean => {
  if (value < props.min) {
    ElMessage.warning(`金额不能小于 ${props.currency}${props.min}`)
    return false
  }
  if (value > props.max) {
    ElMessage.warning(`金额不能大于 ${props.currency}${props.max}`)
    return false
  }
  return true
}

// 处理输入
const handleInput = (value: string): void => {
  const formatted = formatInputValue(value)
  internalValue.value = formatted

  // 尝试解析数值
  const numValue = parseFloat(formatted)
  if (!isNaN(numValue) && formatted !== '' && formatted !== '-') {
    if (validateRange(numValue)) {
      emit('update:modelValue', numValue)
    }
  }
}

// 处理失去焦点
const handleBlur = (event: FocusEvent): void => {
  isFocused.value = false

  const value = parseFloat(internalValue.value)
  if (!isNaN(value) && internalValue.value !== '' && internalValue.value !== '-') {
    if (validateRange(value)) {
      emit('update:modelValue', value)
      emit('change', value)
    }
  }

  emit('blur', event)
}

// 处理获得焦点
const handleFocus = (event: FocusEvent): void => {
  isFocused.value = true

  // 如果有初始值，显示原始数字以便编辑
  if (props.modelValue && props.modelValue !== 0) {
    internalValue.value = props.modelValue.toString()
  }

  emit('focus', event)
}

// 处理变化
const handleChange = (): void => {
  const value = parseFloat(internalValue.value)
  if (!isNaN(value) && internalValue.value !== '' && internalValue.value !== '-') {
    if (validateRange(value)) {
      emit('change', value)
    }
  }
}

// 监听外部值变化
watch(
  () => props.modelValue,
  (newValue) => {
    if (newValue === undefined || newValue === null) {
      internalValue.value = ''
    } else if (!isFocused.value) {
      internalValue.value = newValue.toString()
    }
  },
  { immediate: true }
)
</script>

<style scoped>
.amount-input {
  width: 100%;
}

.amount-prefix {
  font-weight: 500;
  color: #606266;
}

:deep(.el-input__inner) {
  text-align: left;
}
</style>