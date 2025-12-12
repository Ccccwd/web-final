import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/home/Dashboard.vue')
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/Login.vue')
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/auth/Register.vue')
  },
  {
    path: '/transactions',
    name: 'Transactions',
    component: () => import('@/views/transaction/TransactionList.vue')
  },
  {
    path: '/transactions/add',
    name: 'AddTransaction',
    component: () => import('@/views/transaction/AddTransaction.vue')
  },
  {
    path: '/statistics',
    name: 'Statistics',
    component: () => import('@/views/statistics/Overview.vue')
  },
  {
    path: '/budgets',
    name: 'Budgets',
    component: () => import('@/views/budget/BudgetList.vue')
  },
  {
    path: '/accounts',
    name: 'Accounts',
    component: () => import('@/views/account/AccountList.vue')
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/settings/Settings.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router