<template>
  <el-select
    v-model="selectedValue"
    :placeholder="placeholder"
    :size="size"
    :disabled="disabled"
    :clearable="clearable"
    :filterable="filterable"
    class="account-selector"
    @change="handleChange"
    @clear="handleClear"
  >
    <el-option
      v-for="account in filteredAccounts"
      :key="account.id"
      :label="`${account.name} (${formatAmount(account.balance)})`"
      :value="account.id"
    >
      <div class="account-option">
        <span class="account-icon" :style="{ color: account.color }">
          {{ getAccountIcon(account.type) }}
        </span>
        <div class="account-info">
          <div class="account-name">
            {{ account.name }}
            <el-tag v-if="account.is_default" type="primary" size="small">默认</el-tag>
          </div>
          <div class="account-balance">余额: {{ formatAmount(account.balance) }}</div>
        </div>
      </div>
    </el-option>
  </el-select>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useAccountStore } from '@/store/modules/account'
import { Account, AccountType } from '@/types'
import { formatAmount, getAccountTypeText } from '@/utils/format'

interface Props {
  modelValue?: number | null
  placeholder?: string
  size?: 'large' | 'default' | 'small'
  disabled?: boolean
  clearable?: boolean
  filterable?: boolean
  showBalance?: boolean
  includeDisabled?: boolean
  accountTypes?: AccountType[]
}

interface Emits {
  (e: 'update:modelValue', value: number | null): void
  (e: 'change', value: number | null, account?: Account): void
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: '请选择账户',
  size: 'default',
  disabled: false,
  clearable: true,
  filterable: true,
  showBalance: true,
  includeDisabled: false,
  accountTypes: () => []
})

const emit = defineEmits<Emits>()

const accountStore = useAccountStore()

// 选中的值
const selectedValue = ref<number | null>(props.modelValue || null)

// 账户图标映射
const accountIcons: Record<AccountType, string> = {
  cash: '💵',
  bank: '🏦',
  wechat: '💚',
  alipay: '💙',
  meal_card: '💛',
  credit_card: '💳',
  other: '📦'
}

// 获取账户图标
const getAccountIcon = (type: AccountType): string => {
  return accountIcons[type] || accountIcons.other
}

// 过滤账户
const filteredAccounts = computed(() => {
  let accounts = accountStore.accounts

  // 按启用状态过滤
  if (!props.includeDisabled) {
    accounts = accounts.filter(a => a.is_active)
  }

  // 按账户类型过滤
  if (props.accountTypes.length > 0) {
    accounts = accounts.filter(a => props.accountTypes.includes(a.type))
  }

  // 按余额排序（默认账户在前，然后按余额排序）
  return accounts.sort((a, b) => {
    if (a.is_default && !b.is_default) return -1
    if (!a.is_default && b.is_default) return 1
    return b.balance - a.balance
  })
})

// 获取选中的账户
const getSelectedAccount = (accountId: number): Account | undefined => {
  return accountStore.accounts.find(a => a.id === accountId)
}

// 处理选择变化
const handleChange = (value: number | null): void => {
  selectedValue.value = value
  emit('update:modelValue', value)

  if (value) {
    const account = getSelectedAccount(value)
    emit('change', value, account)
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

// 如果账户列表为空，尝试获取
if (accountStore.accounts.length === 0) {
  accountStore.fetchAccounts()
}
</script>

<style scoped>
.account-selector {
  width: 100%;
}

.account-option {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 4px 0;
}

.account-icon {
  font-size: 18px;
  width: 24px;
  text-align: center;
  flex-shrink: 0;
}

.account-info {
  flex: 1;
  min-width: 0;
}

.account-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.account-balance {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

:deep(.el-select-dropdown__item) {
  height: auto;
  padding: 8px 12px;
  line-height: 1.5;
}

:deep(.el-tag) {
  margin-left: 8px;
}
</style>