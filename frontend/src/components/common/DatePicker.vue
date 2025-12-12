<template>
  <el-date-picker
    v-model="selectedDate"
    :type="type"
    :placeholder="placeholder"
    :size="size"
    :disabled="disabled"
    :clearable="clearable"
    :editable="editable"
    :format="format"
    :value-format="valueFormat"
    :shortcuts="shortcuts"
    :disabled-date="disabledDate"
    class="date-picker"
    @change="handleChange"
    @blur="handleBlur"
    @focus="handleFocus"
  />
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import dayjs from 'dayjs'

interface Props {
  modelValue?: string | Date | null
  type?: 'date' | 'datetime' | 'daterange' | 'datetimerange'
  placeholder?: string
  size?: 'large' | 'default' | 'small'
  disabled?: boolean
  clearable?: boolean
  editable?: boolean
  format?: string
  valueFormat?: string
  disabledDate?: (date: Date) => boolean
  showShortcuts?: boolean
  maxDate?: string | Date
  minDate?: string | Date
  defaultToToday?: boolean
}

interface Emits {
  (e: 'update:modelValue', value: string | Date | null): void
  (e: 'change', value: string | Date | null): void
  (e: 'blur', event: FocusEvent): void
  (e: 'focus', event: FocusEvent): void
}

const props = withDefaults(defineProps<Props>(), {
  type: 'date',
  placeholder: '请选择日期',
  size: 'default',
  disabled: false,
  clearable: true,
  editable: true,
  format: 'YYYY-MM-DD',
  valueFormat: 'YYYY-MM-DD',
  showShortcuts: true,
  defaultToToday: true,
  maxDate: undefined,
  minDate: undefined
})

const emit = defineEmits<Emits>()

// 选中的日期
const selectedDate = ref<string | Date | null>(props.modelValue || null)

// 快捷选项
const shortcuts = computed(() => {
  if (!props.showShortcuts || props.type.includes('range')) {
    return undefined
  }

  return [
    {
      text: '今天',
      value: () => new Date()
    },
    {
      text: '昨天',
      value: () => {
        const date = new Date()
        date.setDate(date.getDate() - 1)
        return date
      }
    },
    {
      text: '本周一',
      value: () => {
        const date = new Date()
        const day = date.getDay() || 7
        date.setDate(date.getDate() - day + 1)
        return date
      }
    },
    {
      text: '本月1日',
      value: () => {
        const date = new Date()
        date.setDate(1)
        return date
      }
    }
  ]
})

// 日期禁用逻辑
const disabledDateComputed = computed(() => {
  if (props.disabledDate) {
    return props.disabledDate
  }

  return (date: Date) => {
    const today = new Date()
    today.setHours(0, 0, 0, 0)

    // 默认不能选择未来日期
    if (date > today) {
      return true
    }

    // 检查最大日期限制
    if (props.maxDate) {
      const maxDate = new Date(props.maxDate)
      maxDate.setHours(23, 59, 59, 999)
      if (date > maxDate) {
        return true
      }
    }

    // 检查最小日期限制
    if (props.minDate) {
      const minDate = new Date(props.minDate)
      minDate.setHours(0, 0, 0, 0)
      if (date < minDate) {
        return true
      }
    }

    return false
  }
})

// 获取默认日期
const getDefaultDate = (): Date => {
  if (props.defaultToToday) {
    return new Date()
  }
  return new Date()
}

// 处理日期变化
const handleChange = (value: string | Date | null): void => {
  selectedDate.value = value
  emit('update:modelValue', value)
  emit('change', value)
}

// 处理失去焦点
const handleBlur = (event: FocusEvent): void => {
  emit('blur', event)
}

// 处理获得焦点
const handleFocus = (event: FocusEvent): void => {
  emit('focus', event)
}

// 初始化日期
if (!props.modelValue && props.defaultToToday && props.type !== 'daterange' && props.type !== 'datetimerange') {
  const defaultDate = getDefaultDate()
  selectedDate.value = dayjs(defaultDate).format(props.valueFormat)
  emit('update:modelValue', selectedDate.value)
}

// 监听外部值变化
watch(
  () => props.modelValue,
  (newValue) => {
    selectedDate.value = newValue || null
  },
  { immediate: true }
)
</script>

<style scoped>
.date-picker {
  width: 100%;
}

:deep(.el-date-editor) {
  width: 100%;
}

:deep(.el-date-editor.el-input) {
  width: 100%;
}
</style>