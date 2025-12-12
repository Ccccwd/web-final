import { createPinia } from 'pinia'

const pinia = createPinia()

// 导出所有store模块
export { useUserStore } from './modules/user'
export { useTransactionStore } from './modules/transaction'
export { useBudgetStore } from './modules/budget'
export { useAccountStore } from './modules/account'

export default pinia